from bson import ObjectId
import mongomock
import pytest

from pet import DeadPetError, Pet
from repository.pet_repository import PetRepository


@pytest.fixture
def collection():
    client = mongomock.MongoClient()
    return client["test_virtual_pet"]["pets"]


@pytest.fixture
def repo(collection):
    return PetRepository(collection=collection)


# ---------- Сохранение ----------

def test_save_generates_mongodb_id_for_unsaved_pet(repo, collection):
    pet = Pet(name="Buddy", life=10)

    repo.save(pet)

    assert ObjectId.is_valid(pet.pet_id)
    assert collection.count_documents({}) == 1
    assert collection.find_one({"_id": ObjectId(pet.pet_id)}) == {
        "_id": ObjectId(pet.pet_id),
        "name": "Buddy",
        "life": 10,
        "happiness": 2,
        "hunger": 2,
        "previous_loss": 0,
    }


def test_save_keeps_existing_mongodb_id(repo, collection):
    pet_id = str(ObjectId())
    pet = Pet(name="Buddy", life=10, pet_id=pet_id)

    repo.save(pet)

    assert pet.pet_id == pet_id
    assert collection.count_documents({"_id": ObjectId(pet_id)}) == 1


def test_save_replaces_document_with_same_id(repo, collection):
    pet_id = str(ObjectId())
    pet = Pet(name="Buddy", life=10, pet_id=pet_id)
    renamed = Pet(name="Rex", life=5, pet_id=pet_id)

    repo.save(pet)
    repo.save(renamed)

    assert collection.count_documents({}) == 1
    assert repo.get(pet_id).name == "Rex"


def test_save_dead_pet_raises(repo, collection):
    pet = Pet(name="Buddy", life=0)

    with pytest.raises(DeadPetError, match="Can't save dead pet"):
        repo.save(pet)

    assert collection.count_documents({}) == 0


def test_save_rejects_invalid_existing_id(repo):
    pet = Pet(name="Buddy", life=10, pet_id="abc123")

    with pytest.raises(ValueError, match="Invalid pet id"):
        repo.save(pet)


# ---------- Получение ----------

def test_get_existing_pet(repo):
    pet = Pet(name="Buddy", life=10)
    repo.save(pet)

    result = repo.get(pet.pet_id)

    assert result == pet
    assert result is not pet


def test_get_missing_pet_returns_none(repo):
    assert repo.get(str(ObjectId())) is None


def test_get_invalid_id_returns_none(repo):
    assert repo.get("no-such-id") is None


def test_get_all_returns_all_pets(repo):
    buddy = Pet(
        name="Buddy",
        life=10,
        happiness=4,
        hunger=6,
        previous_loss=2,
    )
    charlie = Pet(name="Charlie", life=7)
    repo.save(buddy)
    repo.save(charlie)

    result = repo.get_all()

    assert result == [buddy, charlie]
    assert result[0] is not buddy
    assert result[1] is not charlie


# ---------- Удаление ----------

def test_remove_deletes_pet(repo, collection):
    pet = Pet(name="Buddy", life=10)
    repo.save(pet)

    repo.remove(pet.pet_id)

    assert collection.count_documents({}) == 0
    assert repo.get(pet.pet_id) is None


def test_remove_missing_pet_does_not_raise(repo):
    repo.remove(str(ObjectId()))


def test_remove_invalid_id_does_not_raise(repo):
    repo.remove("no-such-id")
