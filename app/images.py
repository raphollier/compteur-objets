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


def tableau_en_png(tableau: np.ndarray) -> bytes:
    """Encode un tableau de gris (uint8) en image PNG."""
    tampon = io.BytesIO()
    Image.fromarray(tableau).save(tampon, format="PNG")
    return tampon.getvalue()


def masque_en_png(masque: np.ndarray) -> bytes:
    """Encode un masque binaire en image PNG : objets en blanc, fond en noir."""
    return tableau_en_png((masque * 255).astype(np.uint8))


def charger_image(chemin: str) -> np.ndarray:
    """Relit une image préparée depuis le disque, en tableau de gris."""
    return np.array(Image.open(chemin))