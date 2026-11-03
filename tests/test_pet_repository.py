import pytest

from pet import Pet, DeadPetError
from repository.pet_repository import PetRepository


# ---------- Сохранение ----------

def test_save_generates_id_for_unsaved_pet():
    pet = Pet(name="Buddy", life=10)
    repo = PetRepository()

    repo.save(pet)

    assert pet.pet_id != ""
    assert repo.get(pet.pet_id) is pet


def test_save_keeps_existing_id():
    pet = Pet(name="Buddy", life=10, pet_id="abc123")
    repo = PetRepository()

    repo.save(pet)

    assert pet.pet_id == "abc123"
    assert repo.get("abc123") is pet


def test_save_overwrites_pet_with_same_id():
    pet = Pet(name="Buddy", life=10, pet_id="abc123")
    renamed = Pet(name="Rex", life=5, pet_id="abc123")
    repo = PetRepository()

    repo.save(pet)
    repo.save(renamed)

    assert len(repo.pets) == 1
    assert repo.get("abc123") is renamed


def test_save_dead_pet_raises():
    pet = Pet(name="Buddy", life=0)
    repo = PetRepository()

    with pytest.raises(DeadPetError, match="Can't save dead pet"):
        repo.save(pet)

    assert repo.pets == {}


# ---------- Получение ----------

def test_get_existing_pet():
    pet = Pet(name="Buddy", life=10, pet_id="abc123")
    repo = PetRepository()
    repo.save(pet)

    assert repo.get("abc123") is pet


def test_get_missing_pet_returns_none():
    repo = PetRepository()

    assert repo.get("no-such-id") is None


# ---------- Удаление ----------

def test_remove_deletes_pet():
    pet = Pet(name="Buddy", life=10, pet_id="abc123")
    repo = PetRepository()
    repo.save(pet)

    repo.remove("abc123")

    assert repo.get("abc123") is None


def test_remove_missing_pet_does_not_raise():
    repo = PetRepository()

    repo.remove("no-such-id")
