"""Détection et comptage d'objets dans une image en niveaux de gris."""

import numpy as np


def analyser(image_grise: np.ndarray, seuil: int, objets_clairs: bool = False) -> dict:
    """Compte les objets d'une image en niveaux de gris.

    Un pixel est « objet » s'il est strictement plus sombre que le seuil,
    ou strictement plus clair si objets_clairs est vrai. Un objet est un
    groupe de pixels objet reliés entre eux, diagonales comprises
    (8-connexité).

    Renvoie un dictionnaire : nb_objets, aire_totale, aire_moyenne (en pixels).
    Lève ValueError si l'image n'a pas deux dimensions, ou si le seuil
    n'est pas entre 0 et 255.
    """
    if image_grise.ndim != 2:
        raise ValueError(
            f"image en niveaux de gris attendue (2 dimensions), "
            f"reçu {image_grise.ndim} dimensions"
        )
    if not 0 <= seuil <= 255:
        raise ValueError(f"le seuil doit être entre 0 et 255, reçu : {seuil}")

    if objets_clairs:
        masque = image_grise > seuil
    else:
        masque = image_grise < seuil

    # Bouchon provisoire : remplacé au morceau 3 par les vraies mesures.
    return {"nb_objets": 0, "aire_totale": 0, "aire_moyenne": 0}