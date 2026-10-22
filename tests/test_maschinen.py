import uuid

from fastapi.testclient import TestClient

from tests.factories import create_maschine, create_standort


class TestMaschineCreate:
    def test_legt_maschine_an(self, client: TestClient) -> None:
        standort = create_standort(client)
        maschine = create_maschine(client, standort["id"])
        assert maschine["modell"] == "Barista Pro"
        assert maschine["standort_id"] == standort["id"]

    def test_zweite_maschine_am_standort_ist_409(self, client: TestClient) -> None:
        standort = create_standort(client)
        create_maschine(client, standort["id"])
        response = client.post(
            f"/standorte/{standort['id']}/maschine", json={"modell": "Zweite"}
        )
        assert response.status_code == 409

    def test_unbekannter_standort_ist_404(self, client: TestClient) -> None:
        response = client.post(
            f"/standorte/{uuid.uuid4()}/maschine", json={"modell": "Barista Pro"}
        )
        assert response.status_code == 404


class TestMaschineRead:
    def test_liefert_maschine_des_standorts(self, client: TestClient) -> None:
        standort = create_standort(client)
        create_maschine(client, standort["id"])
        response = client.get(f"/standorte/{standort['id']}/maschine")
        assert response.status_code == 200
        assert response.json()["modell"] == "Barista Pro"

    def test_standort_ohne_maschine_ist_404(self, client: TestClient) -> None:
        standort = create_standort(client)
        response = client.get(f"/standorte/{standort['id']}/maschine")
        assert response.status_code == 404


class TestMaschineUpdate:
    def test_erhoeht_version(self, client: TestClient) -> None:
        standort = create_standort(client)
        maschine = create_maschine(client, standort["id"])
        response = client.put(
            f"/standorte/{standort['id']}/maschine",
            json={"modell": "Neues Modell", "version": maschine["version"]},
        )
        assert response.status_code == 200
        assert response.json()["modell"] == "Neues Modell"
        assert response.json()["version"] == 1


class TestMaschineDelete:
    def test_soft_delete_erlaubt_neue_maschine(self, client: TestClient) -> None:
        standort = create_standort(client)
        create_maschine(client, standort["id"])
        assert client.delete(f"/standorte/{standort['id']}/maschine").status_code == 204
        assert client.get(f"/standorte/{standort['id']}/maschine").status_code == 404
        neue = create_maschine(client, standort["id"], modell="Nachfolger")
        assert neue["modell"] == "Nachfolger"

    def test_soft_delete_kaskadiert_auf_kaffeebohnen(self, client: TestClient) -> None:
        standort = create_standort(client)
        maschine = create_maschine(client, standort["id"])
        client.post(f"/maschinen/{maschine['id']}/kaffeebohnen", json={"sorte": "Arabica"})
        client.delete(f"/standorte/{standort['id']}/maschine")
        response = client.get(f"/maschinen/{maschine['id']}/kaffeebohnen")
        assert response.status_code == 404