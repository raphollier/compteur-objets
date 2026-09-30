"""Détection et comptage d'objets dans une image en niveaux de gris."""

from collections import deque

import numpy as np

# Les 8 décalages (ligne, colonne) qui mènent d'un pixel à ses voisins,
# diagonales comprises : c'est ce qui fait la 8-connexité.
VOISINS_8 = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]


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

    masque = calculer_masque(image_grise, seuil, objets_clairs)

    aires = _mesurer_objets(masque)

    nb_objets = len(aires)
    aire_totale = sum(aires)
    aire_moyenne = aire_totale / nb_objets if nb_objets > 0 else 0

    return {
        "nb_objets": nb_objets,
        "aire_totale": aire_totale,
        "aire_moyenne": aire_moyenne,
    }


def calculer_masque(image_grise: np.ndarray, seuil: int, objets_clairs: bool = False) -> np.ndarray:
    """Renvoie le masque binaire : True là où le pixel est « objet ».

    Lève ValueError si le seuil n'est pas entre 0 et 255.
    """
    if not 0 <= seuil <= 255:
        raise ValueError(f"le seuil doit être entre 0 et 255, reçu : {seuil}")

    if objets_clairs:
        return image_grise > seuil
    return image_grise < seuil
    


def _mesurer_objets(masque: np.ndarray) -> list[int]:
    """Trouve les objets du masque et renvoie la liste de leurs aires.

    Parcours en largeur : chaque pixel objet pas encore étiqueté démarre
    un nouvel objet, dont on propage le numéro aux voisins (8-connexité)
    à l'aide d'une file, jusqu'à ce qu'elle soit vide.
    """
    hauteur, largeur = masque.shape
    etiquettes = np.zeros((hauteur, largeur), dtype=np.int32)
    aires = []

    for y in range(hauteur):
        for x in range(largeur):
            if not masque[y, x] or etiquettes[y, x] != 0:
                continue

            numero = len(aires) + 1
            etiquettes[y, x] = numero
            file = deque([(y, x)])
            aire = 1

            while file:
                cy, cx = file.popleft()
                for dy, dx in VOISINS_8:
                    vy, vx = cy + dy, cx + dx
                    if (
                        0 <= vy < hauteur
                        and 0 <= vx < largeur
                        and masque[vy, vx]
                        and etiquettes[vy, vx] == 0
                    ):
                        etiquettes[vy, vx] = numero
                        file.append((vy, vx))
                        aire += 1

            aires.append(aire)

    return aires