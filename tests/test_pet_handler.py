import io
import json
from bson import ObjectId
from email.message import Message
from types import SimpleNamespace

import mongomock
import pytest

from pet import PetFactory
from repository.pet_repository import PetRepository
from server.pet_handler import PetHandler


@pytest.fixture
def collection():
    client = mongomock.MongoClient()
    return client["virtual_pet"]["pets"]


@pytest.fixture
def repo(collection):
    return PetRepository(collection=collection)


class SilentPetHandler(PetHandler):
    def log_message(self, format, *args):
        pass


def build_handler(repo, path, body=None):
    """Собирает PetHandler без сокета: запрос подаётся через rfile,
    ответ записывается в wfile."""
    handler = object.__new__(SilentPetHandler)
    handler.server = SimpleNamespace(repository=repo)
    handler.path = path
    handler.requestline = path
    handler.request_version = "HTTP/1.1"
    handler.headers = Message()
    handler._headers_buffer = []
    handler.wfile = io.BytesIO()

    if isinstance(body, str):
        raw = body.encode("utf-8")
    elif isinstance(body, (dict, list)):
        raw = json.dumps(body).encode("utf-8")
    else:
        raw = body or b""

    handler.rfile = io.BytesIO(raw)
    if raw:
        handler.headers["Content-Length"] = str(len(raw))

    return handler


def send(handler, method):
    getattr(handler, method)()
    return parse_response(handler.wfile.getvalue())


def parse_response(raw):
    head, _, body = raw.partition(b"\r\n\r\n")
    status_line, *header_lines = head.split(b"\r\n")
    status = int(status_line.split()[1])
    body_json = json.loads(body.decode("utf-8"))
    return status, body_json


def create_pet(repo, name="Buddy", life=10):
    pet = PetFactory.create(name=name, life=life)
    repo.save(pet)
    return pet


# ---------- GET /api/v1/pets ----------

def test_get_empty_pets_list(repo):
    status, body = send(build_handler(repo, "/api/v1/pets"), "do_GET")

    assert status == 200
    assert body == []


def test_get_pets_list_returns_saved_pets(repo):
    create_pet(repo, name="Buddy", life=10)
    create_pet(repo, name="Charlie", life=7)

    status, body = send(build_handler(repo, "/api/v1/pets"), "do_GET")

    assert status == 200
    assert [pet["name"] for pet in body] == ["Buddy", "Charlie"]
    for pet in body:
        assert set(pet) == {"id", "name", "life", "happiness", "hunger"}


# ---------- GET /api/v1/pets/{id} ----------

def test_get_pet_by_id(repo):
    pet = create_pet(repo)

    status, body = send(build_handler(repo, f"/api/v1/pets/{pet.pet_id}"), "do_GET")

    assert status == 200
    assert body == {
        "id": pet.pet_id,
        "name": "Buddy",
        "life": 10,
        "happiness": 2,
        "hunger": 2,
    }


def test_get_pet_invalid_id(repo):
    status, body = send(build_handler(repo, "/api/v1/pets/not-an-id"), "do_GET")

    assert status == 400
    assert body == {"error": "Неверный формат id"}


def test_get_pet_not_found(repo):
    status, body = send(build_handler(repo, f"/api/v1/pets/{ObjectId()}"), "do_GET")

    assert status == 404
    assert body == {"error": "Такого питомца нет"}


def test_get_unknown_path(repo):
    status, body = send(build_handler(repo, "/api/v1/unknown"), "do_GET")

    assert status == 404
    assert body == {"error": "Такого пути нет"}


# ---------- POST /api/v1/pets ----------

def test_create_pet(repo, collection):
    status, body = send(
        build_handler(repo, "/api/v1/pets", {"name": "Барсик", "life": 8}),
        "do_POST",
    )

    assert status == 201
    assert set(body) == {"id", "name", "life", "happiness", "hunger"}
    assert body["name"] == "Барсик"
    assert body["life"] == 8
    assert body["happiness"] == 2
    assert body["hunger"] == 2

    assert collection.count_documents({}) == 1


@pytest.mark.parametrize("body", [
    {"life": 10},
    {"name": "", "life": 10},
    {"name": 42, "life": 10},
])
def test_create_pet_invalid_name(repo, body):
    status, response = send(build_handler(repo, "/api/v1/pets", body), "do_POST")

    assert status == 400
    assert response == {"error": "Отсутствует имя питомца"}


@pytest.mark.parametrize("life", [None, 0, -1, "10", 1.5, True])
def test_create_pet_invalid_life(repo, life):
    status, response = send(
        build_handler(repo, "/api/v1/pets", {"name": "Buddy", "life": life}),
        "do_POST",
    )

    assert status == 400
    assert response == {"error": "Некорректный показатель жизни"}


def test_create_pet_malformed_json(repo):
    status, response = send(
        build_handler(repo, "/api/v1/pets", "{not json"), "do_POST"
    )

    assert status == 400
    assert response == {"error": "Некорректный JSON"}


def test_create_pet_json_not_object(repo):
    status, response = send(build_handler(repo, "/api/v1/pets", [1, 2]), "do_POST")

    assert status == 400
    assert response == {"error": "Ожидался JSON-объект"}


def test_post_unknown_path(repo):
    status, body = send(build_handler(repo, "/api/v1/unknown", {}), "do_POST")

    assert status == 404
    assert body == {"error": "Такого пути нет"}


# ---------- POST /api/v1/pets/{id}/actions ----------

@pytest.mark.parametrize("action, happiness, hunger", [
    ("feed", 2, 0),
    ("pet", 3, 3),
    ("treat", 4, 1),
    ("walk", 3, 5),
    ("ignore", 1, 3),
])
def test_action_changes_stats(repo, action, happiness, hunger):
    pet = create_pet(repo, life=10)

    status, body = send(
        build_handler(repo, f"/api/v1/pets/{pet.pet_id}/actions", {"type": action}),
        "do_POST",
    )

    assert status == 200
    assert body["happiness"] == happiness
    assert body["hunger"] == hunger
    assert body["life"] == 10


def test_action_persists_changes(repo):
    pet = create_pet(repo)

    send(
        build_handler(repo, f"/api/v1/pets/{pet.pet_id}/actions", {"type": "feed"}),
        "do_POST",
    )

    assert repo.get(pet.pet_id).hunger == 0


@pytest.mark.parametrize("body", [{"type": "dance"}, {}, {"type": 42}])
def test_action_unknown_type(repo, body):
    pet = create_pet(repo)

    status, response = send(
        build_handler(repo, f"/api/v1/pets/{pet.pet_id}/actions", body),
        "do_POST",
    )

    assert status == 400
    assert response == {"error": "Такого действия нет"}


def test_action_invalid_id(repo):
    status, body = send(
        build_handler(repo, "/api/v1/pets/not-an-id/actions", {"type": "feed"}),
        "do_POST",
    )

    assert status == 400
    assert body == {"error": "Неверный формат id"}


def test_action_pet_not_found(repo):
    status, body = send(
        build_handler(repo, f"/api/v1/pets/{ObjectId()}/actions", {"type": "feed"}),
        "do_POST",
    )

    assert status == 404
    assert body == {"error": "Такого питомца нет"}


def test_action_malformed_json(repo):
    pet = create_pet(repo)

    status, response = send(
        build_handler(repo, f"/api/v1/pets/{pet.pet_id}/actions", "{oops"),
        "do_POST",
    )

    assert status == 400
    assert response == {"error": "Некорректный JSON"}


def test_death_by_ignore_removes_pet(repo):
    pet = create_pet(repo, life=1)

    status, body = send(
        build_handler(repo, f"/api/v1/pets/{pet.pet_id}/actions", {"type": "ignore"}),
        "do_POST",
    )
    assert status == 200
    assert body["happiness"] == 1

    status, body = send(
        build_handler(repo, f"/api/v1/pets/{pet.pet_id}/actions", {"type": "ignore"}),
        "do_POST",
    )
    assert status == 200
    assert body["happiness"] == 0
    assert repo.get(pet.pet_id) is None


def test_death_by_starvation_removes_pet(repo):
    pet = create_pet(repo, life=2)

    for _ in range(3):
        status, body = send(
            build_handler(repo, f"/api/v1/pets/{pet.pet_id}/actions", {"type": "walk"}),
            "do_POST",
        )

    assert status == 200
    assert body["life"] == 0
    assert repo.get(pet.pet_id) is None


# ---------- Внутренняя ошибка ----------

class BrokenRepository:
    def get_all(self):
        raise RuntimeError("boom")

    def save(self, pet):
        raise RuntimeError("boom")


def test_internal_error_on_get_returns_500():
    handler = build_handler(BrokenRepository(), "/api/v1/pets")

    status, body = send(handler, "do_GET")

    assert status == 500
    assert body == {"error": "Внутренняя ошибка сервера"}


def test_internal_error_on_create_returns_500():
    handler = build_handler(
        BrokenRepository(), "/api/v1/pets", {"name": "Buddy", "life": 10}
    )

    status, body = send(handler, "do_POST")

    assert status == 500
    assert body == {"error": "Внутренняя ошибка сервера"}


def test_invalid_content_length_returns_400(repo):
    handler = build_handler(repo, "/api/v1/pets", {"name": "Buddy", "life": 10})
    del handler.headers["Content-Length"]
    handler.headers["Content-Length"] = "not-a-number"

    status, body = send(handler, "do_POST")

    assert status == 400
    assert body == {"error": "Некорректный JSON"}


def test_action_on_dead_pet_in_db_removes_it(repo, collection):
    pet_id = ObjectId()
    collection.insert_one(
        {
            "_id": pet_id,
            "name": "Ghost",
            "life": 0,
            "happiness": 2,
            "hunger": 2,
            "previous_loss": 0,
        }
    )

    status, body = send(
        build_handler(repo, f"/api/v1/pets/{pet_id}/actions", {"type": "feed"}),
        "do_POST",
    )

    assert status == 404
    assert body == {"error": "Такого питомца нет"}
    assert repo.get(str(pet_id)) is None
