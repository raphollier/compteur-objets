"""Le service web : les routes HTTP du compteur d'objets."""

import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import base
from app.analyse import analyser, calculer_masque
from app.images import charger_image, masque_en_png, preparer_image, tableau_en_png

TAILLE_FICHIER_MAX = 10 * 1024 * 1024  # 10 Mo
DOSSIER_IMAGES = Path(os.environ.get("DOSSIER_IMAGES", "donnees/images"))
DOSSIER_IMAGES.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Compteur d'objets")
app.mount("/static", StaticFiles(directory="static"), name="static")


class ImageEnvoyee(BaseModel):
    id: int
    nom_origine: str
    largeur: int
    hauteur: int


class DemandeAnalyse(BaseModel):
    seuil: int = Field(ge=0, le=255)
    objets_clairs: bool = False


class Analyse(BaseModel):
    id: int
    image_id: int
    seuil: int
    objets_clairs: bool
    nb_objets: int
    aire_totale: int
    aire_moyenne: float
    date: datetime


@app.get("/", include_in_schema=False)
def page_accueil() -> FileResponse:
    """Sert la page web du service."""
    return FileResponse("static/index.html", headers={"Cache-Control": "no-cache"})


@app.get("/sante")
def sante():
    """Dit simplement que le service répond."""
    return {"statut": "ok"}


@app.post("/images", status_code=201)
def envoyer_image(fichier: UploadFile) -> ImageEnvoyee:
    """Reçoit une photo, la prépare, l'enregistre sur disque et en base."""
    contenu = fichier.file.read(TAILLE_FICHIER_MAX + 1)
    if len(contenu) > TAILLE_FICHIER_MAX:
        raise HTTPException(status_code=413, detail="fichier trop volumineux (10 Mo maximum)")

    try:
        tableau = preparer_image(contenu)
    except ValueError as erreur:
        raise HTTPException(status_code=415, detail=str(erreur))

    nom_fichier = f"{uuid4().hex}.png"
    (DOSSIER_IMAGES / nom_fichier).write_bytes(tableau_en_png(tableau))

    hauteur, largeur = tableau.shape
    ligne = base.creer_image(
        nom_origine=fichier.filename or "sans_nom",
        nom_fichier=nom_fichier,
        largeur=largeur,
        hauteur=hauteur,
    )
    return ImageEnvoyee(**ligne)


@app.post("/images/{image_id}/analyses", status_code=201)
def lancer_analyse(image_id: int, demande: DemandeAnalyse) -> Analyse:
    """Compte les objets d'une image déjà envoyée, avec le seuil demandé."""
    image = base.lire_image(image_id)
    if image is None:
        raise HTTPException(status_code=404, detail=f"aucune image n° {image_id}")

    tableau = charger_image(DOSSIER_IMAGES / image["nom_fichier"])
    resultat = analyser(tableau, demande.seuil, demande.objets_clairs)

    ligne = base.creer_analyse(
        image_id=image_id,
        seuil=demande.seuil,
        objets_clairs=demande.objets_clairs,
        **resultat,
    )
    return Analyse(**ligne)


@app.get("/images/{image_id}/analyses")
def historique_image(image_id: int) -> list[Analyse]:
    """Toutes les analyses d'une image, de la plus ancienne à la plus récente."""
    if base.lire_image(image_id) is None:
        raise HTTPException(status_code=404, detail=f"aucune image n° {image_id}")

    return [Analyse(**ligne) for ligne in base.analyses_de_image(image_id)]


@app.get("/analyses")
def liste_analyses(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Analyse]:
    """Toutes les analyses, de la plus récente à la plus ancienne, par pages."""
    return [Analyse(**ligne) for ligne in base.liste_analyses(limit, offset)]


@app.get(
    "/images/{image_id}/masque",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
)
def voir_masque(
    image_id: int,
    seuil: int = Query(ge=0, le=255),
    objets_clairs: bool = False,
) -> Response:
    """Montre l'image binarisée : en blanc, ce qui sera compté comme objet."""
    image = base.lire_image(image_id)
    if image is None:
        raise HTTPException(status_code=404, detail=f"aucune image n° {image_id}")

    tableau = charger_image(DOSSIER_IMAGES / image["nom_fichier"])
    masque = calculer_masque(tableau, seuil, objets_clairs)
    return Response(content=masque_en_png(masque), media_type="image/png")


@app.get(
    "/images/{image_id}/fichier",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
)
def voir_image(image_id: int) -> FileResponse:
    """Renvoie l'image préparée (niveaux de gris, réduite)."""
    image = base.lire_image(image_id)
    if image is None:
        raise HTTPException(status_code=404, detail=f"aucune image n° {image_id}")

    return FileResponse(
        DOSSIER_IMAGES / image["nom_fichier"],
        media_type="image/png",
        headers={"Cache-Control": "no-cache"},
    )