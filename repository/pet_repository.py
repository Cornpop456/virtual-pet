import secrets

from pet import Pet, DeadPetError

class PetRepository:
    def __init__(self):
        self.pets: dict[str, Pet] = {}
        self.next_id = 0

    def save(self, pet: Pet) -> None:
        if not pet.is_alive:
            raise DeadPetError("Can't save dead pet")
        if len(pet.pet_id) == 0:
            pet.pet_id = secrets.token_hex(12)
        self.pets[pet.pet_id] = pet

    def get(self, pet_id: str) -> Pet | None:
        return self.pets.get(pet_id)

    def remove(self, pet_id: str) -> None:
        self.pets.pop(pet_id, None)
