"""Préparation commune à tous les tests : une base dédiée, vidée avant chaque test."""

import atexit
import os
import shutil
import tempfile
from pathlib import Path

import psycopg
import pytest

ADRESSE_ADMIN = os.environ.get(
    "DATABASE_ADMIN_URL", "postgresql://compteur:motdepasse_dev@127.0.0.1:5432/postgres"
)
ADRESSE_TEST = os.environ.get(
    "DATABASE_TEST_URL", "postgresql://compteur:motdepasse_dev@127.0.0.1:5432/compteur_test"
)


def _preparer_base_de_test():
    with psycopg.connect(ADRESSE_ADMIN, autocommit=True) as connexion:
        existe = connexion.execute(
            "SELECT 1 FROM pg_database WHERE datname = 'compteur_test'"
        ).fetchone()
        if existe is None:
            connexion.execute("CREATE DATABASE compteur_test")

    schema = Path("db/schema.sql").read_text(encoding="utf-8")
    with psycopg.connect(ADRESSE_TEST, autocommit=True) as connexion:
        connexion.execute("DROP TABLE IF EXISTS analyses, images")
        connexion.execute(schema)


os.environ["DATABASE_URL"] = ADRESSE_TEST

# Un dossier temporaire pour les photos des tests, supprimé à la fin.
DOSSIER_IMAGES_TEST = tempfile.mkdtemp(prefix="images_test_")
atexit.register(shutil.rmtree, DOSSIER_IMAGES_TEST, ignore_errors=True)
os.environ["DOSSIER_IMAGES"] = DOSSIER_IMAGES_TEST

_preparer_base_de_test()


@pytest.fixture(autouse=True)
def base_vide():
    """Vide les deux tables avant chaque test."""
    from app import base

    with base.reserve.connection() as connexion:
        connexion.execute("TRUNCATE images, analyses RESTART IDENTITY CASCADE")