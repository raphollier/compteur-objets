import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.main import app

client = TestClient(app)


def png_trois_carres() -> bytes:
    """Une image blanche de 200 x 100 avec trois carrés noirs séparés."""
    image = Image.new("L", (200, 100), 255)
    dessin = ImageDraw.Draw(image)
    for x in (10, 70, 130):
        dessin.rectangle([x, 20, x + 29, 49], fill=0)
    tampon = io.BytesIO()
    image.save(tampon, format="PNG")
    return tampon.getvalue()


def envoyer_image_de_test() -> int:
    """Envoie l'image de test et renvoie son numéro."""
    reponse = client.post(
        "/images", files={"fichier": ("carres.png", png_trois_carres(), "image/png")}
    )
    assert reponse.status_code == 201
    return reponse.json()["id"]


def test_sante_repond_ok():
    reponse = client.get("/sante")

    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


def test_envoyer_une_image_renvoie_son_numero_et_ses_dimensions():
    reponse = client.post(
        "/images", files={"fichier": ("carres.png", png_trois_carres(), "image/png")}
    )

    assert reponse.status_code == 201
    assert reponse.json() == {
        "id": 1,
        "nom_origine": "carres.png",
        "largeur": 200,
        "hauteur": 100,
    }


def test_envoyer_un_fichier_qui_n_est_pas_une_image_est_refuse():
    reponse = client.post("/images", files={"fichier": ("notes.txt", b"bonjour", "text/plain")})

    assert reponse.status_code == 415


def test_analyser_une_image_compte_les_objets():
    image_id = envoyer_image_de_test()

    reponse = client.post(f"/images/{image_id}/analyses", json={"seuil": 128})

    assert reponse.status_code == 201
    corps = reponse.json()
    assert corps["nb_objets"] == 3
    assert corps["aire_totale"] == 2700
    assert corps["image_id"] == image_id
    assert corps["seuil"] == 128


def test_analyser_une_image_inexistante_renvoie_404():
    reponse = client.post("/images/999/analyses", json={"seuil": 128})

    assert reponse.status_code == 404


def test_seuil_hors_bornes_est_refuse():
    image_id = envoyer_image_de_test()

    reponse = client.post(f"/images/{image_id}/analyses", json={"seuil": 300})

    assert reponse.status_code == 422


def test_historique_ne_contient_que_les_analyses_de_cette_image():
    image_a = envoyer_image_de_test()
    image_b = envoyer_image_de_test()
    client.post(f"/images/{image_a}/analyses", json={"seuil": 100})
    client.post(f"/images/{image_a}/analyses", json={"seuil": 150})
    client.post(f"/images/{image_b}/analyses", json={"seuil": 100})

    reponse = client.get(f"/images/{image_a}/analyses")

    assert reponse.status_code == 200
    analyses = reponse.json()
    assert [a["seuil"] for a in analyses] == [100, 150]


def test_historique_d_une_image_inexistante_renvoie_404():
    reponse = client.get("/images/999/analyses")

    assert reponse.status_code == 404


def test_liste_paginee_rend_les_plus_recentes_d_abord():
    image_id = envoyer_image_de_test()
    for seuil in (10, 20, 30, 40):
        client.post(f"/images/{image_id}/analyses", json={"seuil": seuil})

    page_1 = client.get("/analyses?limit=2").json()
    page_2 = client.get("/analyses?limit=2&offset=2").json()

    assert [a["seuil"] for a in page_1] == [40, 30]
    assert [a["seuil"] for a in page_2] == [20, 10]


def test_limite_de_pagination_absurde_est_refusee():
    reponse = client.get("/analyses?limit=0")

    assert reponse.status_code == 422


def test_masque_renvoie_une_image_png_de_meme_taille():
    image_id = envoyer_image_de_test()

    reponse = client.get(f"/images/{image_id}/masque?seuil=128")

    assert reponse.status_code == 200
    assert reponse.headers["content-type"] == "image/png"
    assert Image.open(io.BytesIO(reponse.content)).size == (200, 100)


def test_masque_sans_seuil_est_refuse():
    image_id = envoyer_image_de_test()

    reponse = client.get(f"/images/{image_id}/masque")

    assert reponse.status_code == 422

def test_le_navigateur_doit_redemander_la_photo_a_chaque_affichage():
    image_id = envoyer_image_de_test()

    reponse = client.get(f"/images/{image_id}/fichier")

    assert reponse.status_code == 200
    assert reponse.headers["cache-control"] == "no-cache"

def test_le_navigateur_doit_redemander_la_page_a_chaque_visite():
    reponse = client.get("/")

    assert reponse.status_code == 200
    assert reponse.headers["cache-control"] == "no-cache"