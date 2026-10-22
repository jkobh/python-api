import uuid

from fastapi.testclient import TestClient

from tests.factories import create_kaffeebohne, create_maschine, create_standort

STANDORT = {"name": "Zentrale", "ort": "Karlsruhe"}


class TestStandortCreate:
    def test_legt_standort_an(self, client: TestClient) -> None:
        standort = create_standort(client)
        assert standort["name"] == STANDORT["name"]
        assert standort["ort"] == STANDORT["ort"]
        assert standort["version"] == 0
        assert standort["deleted_at"] is None

    def test_vergibt_zeitsortierbare_id(self, client: TestClient) -> None:
        erster = create_standort(client, name="Erster")
        zweiter = create_standort(client, name="Zweiter")
        assert uuid.UUID(erster["id"]).version == 7
        assert erster["id"] < zweiter["id"]

    def test_lehnt_leeren_namen_ab(self, client: TestClient) -> None:
        response = client.post("/standorte", json={"name": "", "ort": "Karlsruhe"})
        assert response.status_code == 422


class TestStandortRead:
    def test_listet_standorte_sortiert(self, client: TestClient) -> None:
        create_standort(client, name="Zeta")
        create_standort(client, name="Alpha")
        response = client.get("/standorte")
        assert response.status_code == 200
        assert [item["name"] for item in response.json()] == ["Alpha", "Zeta"]

    def test_filtert_nach_name_und_ort(self, client: TestClient) -> None:
        create_standort(client, name="Zentrale", ort="Karlsruhe")
        create_standort(client, name="Filiale", ort="Bruchsal")
        response = client.get("/standorte", params={"ort": "karl"})
        assert [item["name"] for item in response.json()] == ["Zentrale"]

    def test_liefert_maschine_mit(self, client: TestClient) -> None:
        standort = create_standort(client)
        create_maschine(client, standort["id"])
        response = client.get(f"/standorte/{standort['id']}")
        assert response.json()["maschine"]["modell"] == "Barista Pro"

    def test_unbekannter_standort_ist_404(self, client: TestClient) -> None:
        response = client.get(f"/standorte/{uuid.uuid4()}")
        assert response.status_code == 404


class TestStandortUpdate:
    def test_erhoeht_version(self, client: TestClient) -> None:
        standort = create_standort(client)
        response = client.put(
            f"/standorte/{standort['id']}",
            json={"name": "Neu", "ort": "Karlsruhe", "version": standort["version"]},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Neu"
        assert response.json()["version"] == 1

    def test_veraltete_version_ist_409(self, client: TestClient) -> None:
        standort = create_standort(client)
        body = {"name": "Neu", "ort": "Karlsruhe", "version": standort["version"]}
        client.put(f"/standorte/{standort['id']}", json=body)
        response = client.put(f"/standorte/{standort['id']}", json=body)
        assert response.status_code == 409
        assert "zwischenzeitlich geändert" in response.json()["detail"]


class TestStandortDelete:
    def test_soft_delete_blendet_aus(self, client: TestClient) -> None:
        standort = create_standort(client)
        response = client.delete(f"/standorte/{standort['id']}")
        assert response.status_code == 204
        assert client.get(f"/standorte/{standort['id']}").status_code == 404
        assert client.get("/standorte").json() == []

    def test_soft_delete_kaskadiert_auf_maschine_und_bohnen(self, client: TestClient) -> None:
        standort = create_standort(client)
        maschine = create_maschine(client, standort["id"])
        kaffeebohne = create_kaffeebohne(client, maschine["id"])
        client.delete(f"/standorte/{standort['id']}")
        assert client.get(f"/maschinen/{maschine['id']}/kaffeebohnen").status_code == 404
        assert (
            client.get(f"/maschinen/{maschine['id']}/kaffeebohnen/{kaffeebohne['id']}").status_code
            == 404
        )

    def test_hard_delete_entfernt_endgueltig(self, client: TestClient) -> None:
        standort = create_standort(client)
        response = client.delete(f"/standorte/{standort['id']}", params={"hard": True})
        assert response.status_code == 204
        assert client.get(f"/standorte/{standort['id']}").status_code == 404
