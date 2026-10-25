# Image du service web du compteur d'objets.

# Point de départ : une Debian minimale avec Python 3.13 déjà installé.
FROM python:3.13-slim

# Réglages de Python et de pip pour un conteneur.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Un utilisateur sans droits d'administration, et le dossier des images qui lui appartient.
RUN useradd --create-home --uid 1000 compteur \
    && mkdir -p /donnees/images \
    && chown compteur:compteur /donnees/images

WORKDIR /compteur

# Les dépendances d'abord : cette couche n'est refaite que si requirements.txt change.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Le code ensuite : il change souvent, il vient donc en dernier.
COPY app/ app/
COPY static/ static/

USER compteur
ENV DOSSIER_IMAGES=/donnees/images
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]