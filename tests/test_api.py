import re
import threading

import mongomock
import pytest
import requests

from repository.pet_repository import PetRepository
from server import PetHandler, PetServer

OBJECT_ID_PATTERN = r"^[0-9a-fA-F]{24}$"


@pytest.fixture
def base_url():
    collection = mongomock.MongoClient()["virtual_pet"]["pets"]
    repository = PetRepository(collection=collection)
    server = PetServer(PetHandler, repository, host="127.0.0.1", port=0)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"

    server.shutdown()
    server.server_close()
    repository.close()


def create_pet(base_url, name="Барсик", life=10):
    response = requests.post(f"{base_url}/api/v1/pets", json={"name": name, "life": life})
    assert response.status_code == 201
    return response.json()


# ---------- GET /api/v1/pets ----------

def test_get_pets_returns_empty_list(base_url):
    response = requests.get(f"{base_url}/api/v1/pets")

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json; charset=utf-8"
    assert response.json() == []


def test_get_pets_returns_created_pets(base_url):
    create_pet(base_url, name="Барсик", life=10)
    create_pet(base_url, name="Мурзик", life=8)

    response = requests.get(f"{base_url}/api/v1/pets")

    assert response.status_code == 200
    body = response.json()
    assert [pet["name"] for pet in body] == ["Барсик", "Мурзик"]
    for pet in body:
        assert set(pet) == {"id", "name", "life", "happiness", "hunger"}


# ---------- POST /api/v1/pets ----------

def test_create_pet(base_url):
    response = requests.post(
        f"{base_url}/api/v1/pets", json={"name": "Барсик", "life": 10}
    )

    assert response.status_code == 201
    body = response.json()
    assert re.fullmatch(OBJECT_ID_PATTERN, body["id"])
    assert body == {
        "id": body["id"],
        "name": "Барсик",
        "life": 10,
        "happiness": 2,
        "hunger": 2,
    }


def test_create_pet_without_name(base_url):
    response = requests.post(f"{base_url}/api/v1/pets", json={"life": 10})

    assert response.status_code == 400
    assert response.json() == {"error": "Отсутствует имя питомца"}


def test_create_pet_with_invalid_life(base_url):
    response = requests.post(
        f"{base_url}/api/v1/pets", json={"name": "Барсик", "life": 0}
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Некорректный показатель жизни"}


def test_create_pet_with_malformed_json(base_url):
    response = requests.post(
        f"{base_url}/api/v1/pets",
        data="{not json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Некорректный JSON"}


# ---------- GET /api/v1/pets/{id} ----------

def test_get_pet_by_id(base_url):
    pet = create_pet(base_url)

    response = requests.get(f"{base_url}/api/v1/pets/{pet['id']}")

    assert response.status_code == 200
    assert response.json() == pet


def test_get_missing_pet_returns_404(base_url):
    response = requests.get(f"{base_url}/api/v1/pets/{'a' * 24}")

    assert response.status_code == 404
    assert response.json() == {"error": "Такого питомца нет"}


def test_get_pet_with_invalid_id(base_url):
    response = requests.get(f"{base_url}/api/v1/pets/not-an-id")

    assert response.status_code == 400
    assert response.json() == {"error": "Неверный формат id"}


# ---------- POST /api/v1/pets/{id}/actions ----------

def test_action_feed_decreases_hunger(base_url):
    pet = create_pet(base_url)

    response = requests.post(
        f"{base_url}/api/v1/pets/{pet['id']}/actions", json={"type": "feed"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["hunger"] == 0
    assert body["happiness"] == 2
    assert body["life"] == 10


def test_action_unknown_type(base_url):
    pet = create_pet(base_url)

    response = requests.post(
        f"{base_url}/api/v1/pets/{pet['id']}/actions", json={"type": "dance"}
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Такого действия нет"}


def test_action_on_missing_pet(base_url):
    response = requests.post(
        f"{base_url}/api/v1/pets/{'b' * 24}/actions", json={"type": "feed"}
    )

    assert response.status_code == 404
    assert response.json() == {"error": "Такого питомца нет"}


def test_action_on_invalid_id(base_url):
    response = requests.post(
        f"{base_url}/api/v1/pets/not-an-id/actions", json={"type": "feed"}
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Неверный формат id"}


def test_dead_pet_disappears_after_action(base_url):
    pet = create_pet(base_url, name="Шарик", life=1)

    first = requests.post(
        f"{base_url}/api/v1/pets/{pet['id']}/actions", json={"type": "ignore"}
    )
    assert first.status_code == 200
    assert first.json()["happiness"] == 1

    last = requests.post(
        f"{base_url}/api/v1/pets/{pet['id']}/actions", json={"type": "ignore"}
    )
    assert last.status_code == 200
    assert last.json()["happiness"] == 0

    response = requests.get(f"{base_url}/api/v1/pets/{pet['id']}")
    assert response.status_code == 404

    listing = requests.get(f"{base_url}/api/v1/pets")
    assert listing.json() == []


# ---------- Прочее ----------

def test_unknown_path_returns_404(base_url):
    response = requests.get(f"{base_url}/api/v1/unknown")

    assert response.status_code == 404
    assert response.json() == {"error": "Такого пути нет"}
