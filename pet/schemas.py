from dataclasses import dataclass

from pet import Pet


@dataclass(frozen=True, slots=True)
class PetStat:
    id: str
    name: str
    life: int
    happiness: int
    hunger: int

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "life": self.life,
            "happiness": self.happiness,
            "hunger": self.hunger,
        }

def pet_to_pet_stat(pet: Pet) -> PetStat:
    if pet.pet_id is None:
        raise ValueError("Cannot create response for an unsaved pet")

    return PetStat(
        id=pet.pet_id,
        name=pet.name,
        life=pet.life,
        happiness=pet.happiness,
        hunger=pet.hunger,
    )