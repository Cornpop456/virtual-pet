import pytest

from pet import Pet
from pet.schemas import PetStat, pet_to_pet_stat


# ---------- PetStat ----------

def test_pet_stat_to_dict():
    stat = PetStat(id="abc123", name="Buddy", life=10, happiness=2, hunger=3)

    assert stat.to_dict() == {
        "id": "abc123",
        "name": "Buddy",
        "life": 10,
        "happiness": 2,
        "hunger": 3,
    }


# ---------- Преобразование Pet -> PetStat ----------

def test_pet_to_pet_stat():
    pet = Pet(name="Buddy", life=10, pet_id="abc123", happiness=2, hunger=3)

    stat = pet_to_pet_stat(pet)

    assert isinstance(stat, PetStat)
    assert stat.id == "abc123"
    assert stat.name == "Buddy"
    assert stat.life == 10
    assert stat.happiness == 2
    assert stat.hunger == 3


def test_pet_to_pet_stat_unsaved_pet_raises():
    pet = Pet(name="Buddy", life=10, pet_id=None)

    with pytest.raises(
        ValueError,
        match="Cannot create response for an unsaved pet",
    ):
        pet_to_pet_stat(pet)
