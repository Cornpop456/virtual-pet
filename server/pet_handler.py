import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Any

from pet import DeadPetError, Pet, PetFactory
from pet.schemas import pet_to_pet_stat

from .pet_server import PetServer

PETS_URL = "/api/v1/pets"

PET_URL_RE = re.compile(r"^/api/v1/pets/([^/]+)$")
ACTION_URL_RE = re.compile(r"^/api/v1/pets/([^/]+)/actions$")
PET_ID_RE = re.compile(r"^[0-9a-fA-F]{24}$")

ACTIONS = {
    "feed": Pet.feed,
    "pet": Pet.pet,
    "treat": Pet.treat,
    "walk": Pet.walk,
    "ignore": Pet.ignore,
}


class PetHandler(BaseHTTPRequestHandler):
    """
    Обработчик запросов для PetServer.
    self.server.repository используется для доступа
    к экземпляру PetRepository, связанному с сервером.

    Маршруты (см. docs/openapi.yaml):
        GET  /api/v1/pets             — список питомцев
        POST /api/v1/pets             — создать питомца
        GET  /api/v1/pets/{id}        — статистика питомца
        POST /api/v1/pets/{id}/actions — выполнить действие
    """

    server: PetServer  # type: ignore

    def do_GET(self) -> None:
        try:
            if self.path == PETS_URL:
                self._handle_list_pets()
            elif match := PET_URL_RE.match(self.path):
                self._handle_get_pet(match.group(1))
            else:
                self._send_error(HTTPStatus.NOT_FOUND, "Такого пути нет")
        except Exception:
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR, "Внутренняя ошибка сервера"
            )

    def do_POST(self) -> None:
        try:
            if self.path == PETS_URL:
                self._handle_create_pet()
            elif match := ACTION_URL_RE.match(self.path):
                self._handle_action(match.group(1))
            else:
                self._send_error(HTTPStatus.NOT_FOUND, "Такого пути нет")
        except Exception:
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR, "Внутренняя ошибка сервера"
            )

    def _handle_list_pets(self) -> None:
        pets = [pet_to_pet_stat(p).to_dict() for p in self.server.repository.get_all()]
        self._send_json(pets)

    def _handle_get_pet(self, pet_id: str) -> None:
        if not PET_ID_RE.match(pet_id):
            self._send_error(HTTPStatus.BAD_REQUEST, "Неверный формат id")
            return

        pet = self.server.repository.get(pet_id)
        if pet is None:
            self._send_error(HTTPStatus.NOT_FOUND, "Такого питомца нет")
            return

        self._send_json(pet_to_pet_stat(pet).to_dict())

    def _handle_create_pet(self) -> None:
        body = self._read_json_object()
        if body is None:
            return

        name = body.get("name")
        if not isinstance(name, str) or not name:
            self._send_error(HTTPStatus.BAD_REQUEST, "Отсутствует имя питомца")
            return

        life = body.get("life")
        if not isinstance(life, int) or isinstance(life, bool) or life < 1:
            self._send_error(HTTPStatus.BAD_REQUEST, "Некорректный показатель жизни")
            return

        pet = PetFactory.create(name=name, life=life)
        self.server.repository.save(pet)
        self._send_json(pet_to_pet_stat(pet).to_dict(), HTTPStatus.CREATED)

    def _handle_action(self, pet_id: str) -> None:
        if not PET_ID_RE.match(pet_id):
            self._send_error(HTTPStatus.BAD_REQUEST, "Неверный формат id")
            return

        body = self._read_json_object()
        if body is None:
            return

        action_type = body.get("type")
        action = ACTIONS.get(action_type) if isinstance(action_type, str) else None
        if action is None:
            self._send_error(HTTPStatus.BAD_REQUEST, "Такого действия нет")
            return

        pet = self.server.repository.get(pet_id)
        if pet is None:
            self._send_error(HTTPStatus.NOT_FOUND, "Такого питомца нет")
            return

        try:
            action(pet)
        except DeadPetError:
            self.server.repository.remove(pet_id)
            self._send_error(HTTPStatus.NOT_FOUND, "Такого питомца нет")
            return

        # Питомец, погибший от действия, удаляется из базы:
        # документация обещает 404 на следующий запрос.
        if pet.is_alive:
            self.server.repository.save(pet)
        else:
            self.server.repository.remove(pet_id)

        self._send_json(pet_to_pet_stat(pet).to_dict())

    def _read_json_object(self) -> dict[str, Any] | None:
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b""

        try:
            body = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_error(HTTPStatus.BAD_REQUEST, "Некорректный JSON")
            return None

        if not isinstance(body, dict):
            self._send_error(HTTPStatus.BAD_REQUEST, "Ожидался JSON-объект")
            return None

        return body

    def _send_json(self, json_data: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(json_data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()

        self.wfile.write(data)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        self._send_json({"error": message}, status)
