from __future__ import annotations
from dataclasses import dataclass
from functools import wraps


class DeadPetError(Exception):
    pass


def apply_policy(func):
    @wraps(func)
    def wrapper(pet: Pet):
        if not pet.is_alive:
            raise DeadPetError("Can't perform action: pet is dead")
        func(pet)
        LifeLossPolicy.apply(pet)
    return wrapper

class LifeLossPolicy:
    @staticmethod
    def apply(pet: Pet) -> None:
        if pet.hunger <= 5:
            pet.previous_loss = 0
            return
        pet.previous_loss += 1
        pet.decrease_life(pet.previous_loss)


@dataclass
class Pet:
    name: str
    life: int
    pet_id: str = ""
    happiness: int = 2
    hunger: int = 2
    previous_loss: int = 0

    @property
    def is_alive(self) -> bool:
        return self.life > 0 and self.happiness > 0

    @apply_policy
    def feed(self):
        self.hunger -= 2

    @apply_policy
    def pet(self):
        self.happiness += 1
        self.hunger += 1

    @apply_policy
    def treat(self):
        self.happiness += 2
        self.hunger -= 1

    @apply_policy
    def walk(self):
        self.happiness += 1
        self.hunger += 3

    @apply_policy
    def ignore(self):
        self.happiness -= 1
        self.hunger += 1

    def decrease_life(self, life: int) -> None:
        self.life -= life
        if self.life < 0:
            self.life = 0

class PetFactory:
    @staticmethod
    def create(name: str, life: int) -> Pet:
        return Pet(name, life)
