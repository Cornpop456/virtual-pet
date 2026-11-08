import threading

import mongomock
import requests

from repository.pet_repository import PetRepository
from server import PetHandler, PetServer


def test_start_serves_requests_until_shutdown():
    collection = mongomock.MongoClient()["virtual_pet"]["pets"]
    server = PetServer(
        PetHandler,
        PetRepository(collection=collection),
        host="127.0.0.1",
        port=0,
    )

    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    response = requests.get(f"{base_url}/api/v1/pets")

    assert response.status_code == 200
    assert response.json() == []

    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
    assert not thread.is_alive()
