"""Le service web : les routes HTTP du compteur d'objets."""

import itertools
import threading
from datetime import datetime, timezone                      # NOUVEAU

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, Field                        # NOUVEAU : Field

from app.analyse import analyser                             # NOUVEAU
from app.images import preparer_image

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