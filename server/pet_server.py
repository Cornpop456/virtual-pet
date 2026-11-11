from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from repository import PetRepository


class PetServer(ThreadingHTTPServer):
    def __init__(
        self,
        handlerClass: type[BaseHTTPRequestHandler],
        repository: PetRepository,
        host: str = "",
        port: int = 8008,
    ) -> None:
        super().__init__((host, port), handlerClass)
        self.repository = repository

    def start(self) -> None:
        self.serve_forever()
