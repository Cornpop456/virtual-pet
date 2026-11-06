from http.server import ThreadingHTTPServer
from repository import PetRepository

from .pet_handler import PetHandler


class PetServer(ThreadingHTTPServer):
    def __init__(
        self,
        repository: PetRepository,
        host: str = "",
        port: int = 8008,
    ) -> None:
        super().__init__((host, port), PetHandler)
        self.repository = repository

    def start(self) -> None:
        self.serve_forever()
