from repository import PetRepository
from server import PetServer, PetHandler

if __name__ == '__main__':
    repository = PetRepository()

    server = PetServer(PetHandler, repository)

    print(
        f"Starting server on {server.server_address[0]}:{server.server_address[1]}")
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
        repository.close()
