-- Schéma de la base du compteur d'objets.
-- Exécuté automatiquement au premier démarrage du conteneur PostgreSQL.

CREATE TABLE images (
    id             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom_origine    TEXT        NOT NULL,
    nom_fichier    TEXT        NOT NULL,
    largeur        INTEGER     NOT NULL,
    hauteur        INTEGER     NOT NULL,
    date_envoi     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE analyses (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    image_id      INTEGER          NOT NULL REFERENCES images (id) ON DELETE CASCADE,
    seuil         INTEGER          NOT NULL CHECK (seuil BETWEEN 0 AND 255),
    objets_clairs BOOLEAN          NOT NULL DEFAULT FALSE,
    nb_objets     INTEGER          NOT NULL,
    aire_totale   BIGINT           NOT NULL,
    aire_moyenne  DOUBLE PRECISION NOT NULL,
    date_analyse  TIMESTAMPTZ      NOT NULL DEFAULT now()
);

CREATE INDEX analyses_image_id_idx ON analyses (image_id);