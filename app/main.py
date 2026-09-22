"""Le service web : les routes HTTP du compteur d'objets."""

import itertools
import threading

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel

from app.images import preparer_image

TAILLE_FICHIER_MAX = 10 * 1024 * 1024  # 10 Mo

app = FastAPI(title="Compteur d'objets")

# Stockage PROVISOIRE, en mémoire : tout disparaît quand le serveur s'arrête.
# Il sera remplacé par PostgreSQL à l'étape 3.
images = {}
_numeros = itertools.count(start=1)
_verrou = threading.Lock()


class ImageEnvoyee(BaseModel):
    id: int
    nom_origine: str
    largeur: int
    hauteur: int


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
        image_id = next(_numeros)

    nom_origine = fichier.filename or "sans_nom"
    images[image_id] = {"nom_origine": nom_origine, "tableau": tableau}

    hauteur, largeur = tableau.shape
    return ImageEnvoyee(id=image_id, nom_origine=nom_origine, largeur=largeur, hauteur=hauteur)