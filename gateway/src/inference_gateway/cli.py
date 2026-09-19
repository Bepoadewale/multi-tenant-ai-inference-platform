import json
import os

import httpx
import typer

app = typer.Typer(help="Inference platform API client")
URL = os.getenv("INFERENCE_GATEWAY_URL", "http://127.0.0.1:8080")
TOKEN = os.getenv("INFERENCE_API_TOKEN", "local-search-token")


def get(path):
    return httpx.get(
        f"{URL}{path}", headers={"Authorization": f"Bearer {TOKEN}"}, timeout=10
    ).json()


@app.command()
def models():
    typer.echo(json.dumps(get("/v1/models"), indent=2))


@app.command()
def capacity():
    typer.echo(json.dumps(get("/platform/v1/capacity"), indent=2))


@app.command()
def usage(tenant: str):
    typer.echo(json.dumps(get(f"/platform/v1/usage/{tenant}"), indent=2))
