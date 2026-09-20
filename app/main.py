"""Le service web : les routes HTTP du compteur d'objets."""

from fastapi import FastAPI

app = FastAPI(title="Compteur d'objets")


@app.get("/sante")
def sante():
    """Dit simplement que le service répond."""
    return {"statut": "ok"}