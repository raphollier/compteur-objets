import numpy as np
import pytest

from app.analyse import analyser

from scipy import ndimage 

def image_blanche(hauteur=20, largeur=20):
    return np.full((hauteur, largeur), 255, dtype=np.uint8)


def test_image_toute_blanche_ne_contient_aucun_objet():
    image = image_blanche()

    resultat = analyser(image, seuil=128)

    assert resultat["nb_objets"] == 0
    assert resultat["aire_totale"] == 0
    assert resultat["aire_moyenne"] == 0


def test_un_carre_de_10_sur_10_est_un_objet_de_100_pixels():
    image = image_blanche(hauteur=20, largeur=20)
    image[5:15, 5:15] = 0

    resultat = analyser(image, seuil=128)

    assert resultat["nb_objets"] == 1
    assert resultat["aire_totale"] == 100
    assert resultat["aire_moyenne"] == 100


def test_trois_carres_separes_sont_trois_objets():
    image = image_blanche(hauteur=10, largeur=10)
    image[1:4, 1:4] = 0      # lignes 1-3, colonnes 1-3 : carré en haut à gauche
    image[1:4, 6:9] = 0      # lignes 1-3, colonnes 6-8 : carré en haut à droite
    image[6:9, 3:6] = 0      # lignes 6-8, colonnes 3-5 : carré en bas

    resultat = analyser(image, seuil=128)

    assert resultat["nb_objets"] == 3
    assert resultat["aire_totale"] == 27


def test_deux_carres_qui_partagent_un_bord_font_un_seul_objet():
    image = image_blanche()
    image[2:5, 2:5] = 0      # lignes 2-4, colonnes 2-4
    image[2:5, 5:8] = 0      # lignes 2-4, colonnes 5-7 : collé au premier

    resultat = analyser(image, seuil=128)

    assert resultat["nb_objets"] == 1
    assert resultat["aire_totale"] == 18


def test_deux_carres_qui_se_touchent_par_un_coin_font_un_seul_objet():
    image = image_blanche()
    image[2:5, 2:5] = 0      # lignes 2-4, colonnes 2-4
    image[5:8, 5:8] = 0      # lignes 5-7, colonnes 5-7 : (4,4) touche (5,5) en diagonale

    resultat = analyser(image, seuil=128)

    assert resultat["nb_objets"] == 1
    assert resultat["aire_totale"] == 18


def test_une_forme_en_u_est_un_seul_objet():
    image = image_blanche()
    image[1:5, 1:2] = 0      # branche gauche : lignes 1-4, colonne 1
    image[1:5, 5:6] = 0      # branche droite : lignes 1-4, colonne 5
    image[4:5, 1:6] = 0      # barre du bas : ligne 4, colonnes 1-5

    resultat = analyser(image, seuil=128)

    assert resultat["nb_objets"] == 1
    assert resultat["aire_totale"] == 11


def test_deux_objets_colles_aux_bords_haut_et_bas_restent_distincts():
    image = image_blanche()
    image[0:2, 3:6] = 0      # lignes 0-1 : touche le bord du haut
    image[8:10, 3:6] = 0     # lignes 8-9 : touche le bord du bas, mêmes colonnes

    resultat = analyser(image, seuil=128)

    assert resultat["nb_objets"] == 2
    assert resultat["aire_totale"] == 12

def test_seuil_a_zero_ne_detecte_rien():
    image = image_blanche()
    image[2:5, 2:5] = 0      # un carré noir, dont les pixels valent exactement 0

    resultat = analyser(image, seuil=0)

    assert resultat["nb_objets"] == 0
    assert resultat["aire_totale"] == 0


def test_seuil_negatif_est_refuse():
    image = image_blanche()

    with pytest.raises(ValueError):
        analyser(image, seuil=-1)


def test_seuil_superieur_a_255_est_refuse():
    image = image_blanche()

    with pytest.raises(ValueError):
        analyser(image, seuil=256)


def test_objets_clairs_sur_fond_sombre_avec_l_option():
    image = np.zeros((10, 10), dtype=np.uint8)   # image entièrement noire
    image[3:6, 3:6] = 255                         # un carré blanc de 3 × 3

    resultat = analyser(image, seuil=128, objets_clairs=True)

    assert resultat["nb_objets"] == 1
    assert resultat["aire_totale"] == 9


def test_meme_resultat_que_scipy_sur_des_images_aleatoires():
    for graine in [0, 1, 2, 3, 4]:
        generateur = np.random.default_rng(graine)
        image = generateur.integers(0, 256, size=(50, 50), dtype=np.uint8)

        resultat = analyser(image, seuil=80)

        masque = image < 80
        _, nb_reference = ndimage.label(masque, structure=np.ones((3, 3)))
        assert resultat["nb_objets"] == nb_reference, f"graine {graine}"
        assert resultat["aire_totale"] == masque.sum(), f"graine {graine}"


def test_image_en_couleur_est_refusee():
    image = np.zeros((10, 10, 3), dtype=np.uint8)   # 3 canaux : une image couleur

    with pytest.raises(ValueError):
        analyser(image, seuil=128)