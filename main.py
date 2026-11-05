from server import PetServer

if __name__ == '__main__':
    server = PetServer()
    print(
        f"Starting server on {server.server_address[0]}:{server.server_address[1]}")
    server.start()
