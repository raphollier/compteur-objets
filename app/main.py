"""Le service web : les routes HTTP du compteur d'objets."""

import itertools
import threading
from datetime import datetime, timezone                      # NOUVEAU

from fastapi import FastAPI, HTTPException, Query, Response, UploadFile

from pydantic import BaseModel, Field                        # NOUVEAU : Field

from app.analyse import analyser, calculer_masque
from app.images import masque_en_png, preparer_image

TAILLE_FICHIER_MAX = 10 * 1024 * 1024  # 10 Mo

app = FastAPI(title="Compteur d'objets")

# Stockage PROVISOIRE, en mémoire : tout disparaît quand le serveur s'arrête.
# Il sera remplacé par PostgreSQL à l'étape 3.
images = {}
analyses = {}                                                # NOUVEAU
_numeros_images = itertools.count(start=1)                   # renommé
_numeros_analyses = itertools.count(start=1)                 # NOUVEAU
_verrou = threading.Lock()


class ImageEnvoyee(BaseModel):
    id: int
    nom_origine: str
    largeur: int
    hauteur: int


class DemandeAnalyse(BaseModel):                             # NOUVEAU
    seuil: int = Field(ge=0, le=255)
    objets_clairs: bool = False


class Analyse(BaseModel):                                    # NOUVEAU
    id: int
    image_id: int
    seuil: int
    objets_clairs: bool
    nb_objets: int
    aire_totale: int
    aire_moyenne: float
    date: datetime


@app.get("/sante")
def sante():
    """Dit simplement que le service répond."""
    return {"statut": "ok"}


@app.post("/images", status_code=201)
def envoyer_image(fichier: UploadFile) -> ImageEnvoyee:
    """Reçoit une photo, la prépare, et lui attribue un numéro."""
    contenu = fichier.file.read(TAILLE_FICHIER_MAX + 1)
    if len(contenu) > TAILLE_FICHIER_MAX:
        raise HTTPException(status_code=413, detail="fichier trop volumineux (10 Mo maximum)")

    try:
        tableau = preparer_image(contenu)
    except ValueError as erreur:
        raise HTTPException(status_code=415, detail=str(erreur))

    with _verrou:
        image_id = next(_numeros_images)

    nom_origine = fichier.filename or "sans_nom"
    images[image_id] = {"nom_origine": nom_origine, "tableau": tableau}

    hauteur, largeur = tableau.shape
    return ImageEnvoyee(id=image_id, nom_origine=nom_origine, largeur=largeur, hauteur=hauteur)


@app.post("/images/{image_id}/analyses", status_code=201)    # NOUVEAU
def lancer_analyse(image_id: int, demande: DemandeAnalyse) -> Analyse:
    """Compte les objets d'une image déjà envoyée, avec le seuil demandé."""
    image = images.get(image_id)
    if image is None:
        raise HTTPException(status_code=404, detail=f"aucune image n° {image_id}")

    resultat = analyser(image["tableau"], demande.seuil, demande.objets_clairs)

    with _verrou:
        analyse_id = next(_numeros_analyses)

    analyse = Analyse(
        id=analyse_id,
        image_id=image_id,
        seuil=demande.seuil,
        objets_clairs=demande.objets_clairs,
        date=datetime.now(timezone.utc),
        **resultat,
    )
    analyses[analyse_id] = analyse
    return analyse

@app.get("/images/{image_id}/analyses")
def historique_image(image_id: int) -> list[Analyse]:
    """Toutes les analyses d'une image, de la plus ancienne à la plus récente."""
    if image_id not in images:
        raise HTTPException(status_code=404, detail=f"aucune image n° {image_id}")

    return [analyse for analyse in analyses.values() if analyse.image_id == image_id]


@app.get("/analyses")
def liste_analyses(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Analyse]:
    """Toutes les analyses, de la plus récente à la plus ancienne, par pages."""
    plus_recentes_d_abord = sorted(analyses.values(), key=lambda a: a.id, reverse=True)
    return plus_recentes_d_abord[offset : offset + limit]


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
    image = images.get(image_id)
    if image is None:
        raise HTTPException(status_code=404, detail=f"aucune image n° {image_id}")

    masque = calculer_masque(image["tableau"], seuil, objets_clairs)
    return Response(content=masque_en_png(masque), media_type="image/png")