"""Accès à la base de données : toutes les requêtes SQL du projet."""

import os

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

ADRESSE_BASE = os.environ.get(
    "DATABASE_URL",
    "postgresql://compteur:motdepasse_dev@127.0.0.1:5432/compteur",
)

reserve = ConnectionPool(
    ADRESSE_BASE, min_size=1, max_size=5, open=True, kwargs={"row_factory": dict_row}
)


def creer_image(nom_origine: str, chemin_fichier: str, largeur: int, hauteur: int) -> dict:
    """Enregistre une image et renvoie la ligne créée."""
    with reserve.connection() as connexion:
        resultat = connexion.execute(
            """
            INSERT INTO images (nom_origine, chemin_fichier, largeur, hauteur)
            VALUES (%s, %s, %s, %s)
            RETURNING id, nom_origine, chemin_fichier, largeur, hauteur, date_envoi
            """,
            (nom_origine, chemin_fichier, largeur, hauteur),
        )
        return resultat.fetchone()


def lire_image(image_id: int) -> dict | None:
    """Renvoie la ligne de l'image, ou None si elle n'existe pas."""
    with reserve.connection() as connexion:
        resultat = connexion.execute("SELECT * FROM images WHERE id = %s", (image_id,))
        return resultat.fetchone()


def creer_analyse(
    image_id: int,
    seuil: int,
    objets_clairs: bool,
    nb_objets: int,
    aire_totale: int,
    aire_moyenne: float,
) -> dict:
    """Enregistre une analyse et renvoie la ligne créée."""
    with reserve.connection() as connexion:
        resultat = connexion.execute(
            """
            INSERT INTO analyses (image_id, seuil, objets_clairs, nb_objets, aire_totale, aire_moyenne)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, image_id, seuil, objets_clairs, nb_objets, aire_totale,
                      aire_moyenne, date_analyse AS date
            """,
            (image_id, seuil, objets_clairs, nb_objets, aire_totale, aire_moyenne),
        )
        return resultat.fetchone()


def analyses_de_image(image_id: int) -> list[dict]:
    """Les analyses d'une image, de la plus ancienne à la plus récente."""
    with reserve.connection() as connexion:
        resultat = connexion.execute(
            """
            SELECT id, image_id, seuil, objets_clairs, nb_objets, aire_totale,
                   aire_moyenne, date_analyse AS date
            FROM analyses
            WHERE image_id = %s
            ORDER BY id
            """,
            (image_id,),
        )
        return resultat.fetchall()


def liste_analyses(limit: int, offset: int) -> list[dict]:
    """Toutes les analyses, de la plus récente à la plus ancienne, par pages."""
    with reserve.connection() as connexion:
        resultat = connexion.execute(
            """
            SELECT id, image_id, seuil, objets_clairs, nb_objets, aire_totale,
                   aire_moyenne, date_analyse AS date
            FROM analyses
            ORDER BY id DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        return resultat.fetchall()