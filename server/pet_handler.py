from http.server import BaseHTTPRequestHandler
from http import HTTPStatus
import json
from typing import Any


class PetHandler(BaseHTTPRequestHandler):
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
