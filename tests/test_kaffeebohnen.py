import uuid

from fastapi.testclient import TestClient

from tests.factories import create_kaffeebohne, create_maschine, create_standort


class TestKaffeebohneCreate:
    def test_legt_kaffeebohne_an(self, client: TestClient) -> None:
        standort = create_standort(client)
        maschine = create_maschine(client, standort["id"])
        kaffeebohne = create_kaffeebohne(client, maschine["id"])
        assert kaffeebohne["sorte"] == "Arabica"
        assert kaffeebohne["maschine_id"] == maschine["id"]

    def test_unbekannte_maschine_ist_404(self, client: TestClient) -> None:
        response = client.post(
            f"/maschinen/{uuid.uuid4()}/kaffeebohnen", json={"sorte": "Arabica"}
        )
        assert response.status_code == 404


class TestKaffeebohneRead:
    def test_listet_sortiert_und_filtert(self, client: TestClient) -> None:
        standort = create_standort(client)
        maschine = create_maschine(client, standort["id"])
        create_kaffeebohne(client, maschine["id"], sorte="Robusta")
        create_kaffeebohne(client, maschine["id"], sorte="Arabica")
        alle = client.get(f"/maschinen/{maschine['id']}/kaffeebohnen").json()
        assert [item["sorte"] for item in alle] == ["Arabica", "Robusta"]
        gefiltert = client.get(
            f"/maschinen/{maschine['id']}/kaffeebohnen", params={"sorte": "rob"}
        ).json()
        assert [item["sorte"] for item in gefiltert] == ["Robusta"]

    def test_fremde_kaffeebohne_ist_404(self, client: TestClient) -> None:
        erster_standort = create_standort(client, name="Erster")
        zweiter_standort = create_standort(client, name="Zweiter")
        erste_maschine = create_maschine(client, erster_standort["id"])
        zweite_maschine = create_maschine(client, zweiter_standort["id"])
        kaffeebohne = create_kaffeebohne(client, erste_maschine["id"])
        response = client.get(
            f"/maschinen/{zweite_maschine['id']}/kaffeebohnen/{kaffeebohne['id']}"
        )
        assert response.status_code == 404


class TestKaffeebohneUpdate:
    def test_erhoeht_version(self, client: TestClient) -> None:
        standort = create_standort(client)
        maschine = create_maschine(client, standort["id"])
        kaffeebohne = create_kaffeebohne(client, maschine["id"])
        response = client.put(
            f"/maschinen/{maschine['id']}/kaffeebohnen/{kaffeebohne['id']}",
            json={"sorte": "Robusta", "version": kaffeebohne["version"]},
        )
        assert response.status_code == 200
        assert response.json()["sorte"] == "Robusta"
        assert response.json()["version"] == 1


class TestKaffeebohneDelete:
    def test_soft_delete_blendet_aus(self, client: TestClient) -> None:
        standort = create_standort(client)
        maschine = create_maschine(client, standort["id"])
        kaffeebohne = create_kaffeebohne(client, maschine["id"])
        response = client.delete(
            f"/maschinen/{maschine['id']}/kaffeebohnen/{kaffeebohne['id']}"
        )
        assert response.status_code == 204
        verbleibend = client.get(f"/maschinen/{maschine['id']}/kaffeebohnen").json()
        assert verbleibend == []