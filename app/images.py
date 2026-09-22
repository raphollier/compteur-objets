"""Préparation des images reçues : du fichier envoyé au tableau de gris."""

import io

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

# Plus grand côté, en pixels, après réduction.
TAILLE_MAX = 1000


def preparer_image(contenu: bytes) -> np.ndarray:
    """Décode un fichier image et le prépare pour l'analyse.

    Remet la photo à l'endroit, la convertit en niveaux de gris et la réduit
    pour que son plus grand côté ne dépasse pas TAILLE_MAX pixels.

    Renvoie un tableau numpy 2D d'entiers de 0 à 255.
    Lève ValueError si le contenu n'est pas une image lisible.
    """
    try:
        image = Image.open(io.BytesIO(contenu))
        image.load()
    except (UnidentifiedImageError, OSError) as erreur:
        raise ValueError("le fichier n'est pas une image lisible") from erreur

    image = ImageOps.exif_transpose(image)
    image = image.convert("L")
    image.thumbnail((TAILLE_MAX, TAILLE_MAX))
    return np.array(image)