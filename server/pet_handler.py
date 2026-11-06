from http.server import BaseHTTPRequestHandler
from http import HTTPStatus
from . import PetServer
import json
from typing import Any


class PetHandler(BaseHTTPRequestHandler):
    """
    Обработчик запросов для PetServer.
    self.server.repository используется для доступа
    к экземпляру PetRepository, связанному с сервером.
    """
    server: PetServer  # type: ignore

    def do_GET(self) -> None:
        data = {"message": "Привет! Это сервер для обработки запросов о питомцах."}
        self._send_json(data)

    def _send_json(self, json_data: Any) -> None:
        data = json.dumps(json_data, ensure_ascii=False).encode('utf-8')

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()

        self.wfile.write(data)
