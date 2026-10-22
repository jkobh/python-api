from typing import Any

from fastapi.testclient import TestClient

type Payload = dict[str, Any]


def create_standort(client: TestClient, name: str = "Zentrale", ort: str = "Karlsruhe") -> Payload:
    response = client.post("/standorte", json={"name": name, "ort": ort})
    assert response.status_code == 201
    return response.json()


def create_maschine(client: TestClient, standort_id: str, modell: str = "Barista Pro") -> Payload:
    response = client.post(f"/standorte/{standort_id}/maschine", json={"modell": modell})
    assert response.status_code == 201
    return response.json()


def create_kaffeebohne(client: TestClient, maschine_id: str, sorte: str = "Arabica") -> Payload:
    response = client.post(f"/maschinen/{maschine_id}/kaffeebohnen", json={"sorte": sorte})
    assert response.status_code == 201
    return response.json()
