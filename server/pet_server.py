from http.server import ThreadingHTTPServer

from .pet_handler import PetHandler


class PetServer(ThreadingHTTPServer):
    def __init__(
        self,
        host: str = "",
        port: int = 8008,
    ) -> None:
        super().__init__((host, port), PetHandler)

    def start(self) -> None:
        self.serve_forever()
