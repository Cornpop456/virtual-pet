import os
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient
from pymongo.collection import Collection

from pet import DeadPetError, Pet

DATABASE_NAME = "virtual_pet"
COLLECTION_NAME = "pets"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")


class PetRepository:
    def __init__(
        self,
        collection: Collection[dict[str, Any]] | None = None,
        *,
        database_name: str = DATABASE_NAME,
        collection_name: str = COLLECTION_NAME,
    ):
        self._client: MongoClient[dict[str, Any]] | None = None

        if collection is None:
            self._client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
            )
            collection = self._client[database_name][collection_name]

        self._collection = collection

    def close(self) -> None:
        if self._client is not None:
            self._client.close()

    def save(self, pet: Pet) -> Pet:
        if not pet.is_alive:
            raise DeadPetError("Can't save dead pet")

        document = {
            "name": pet.name,
            "life": pet.life,
            "happiness": pet.happiness,
            "hunger": pet.hunger,
            "previous_loss": pet.previous_loss,
        }

        if pet.pet_id == "":
            result = self._collection.insert_one(document)
            pet.pet_id = str(result.inserted_id)
        else:
            pet_object_id = self._parse_id(pet.pet_id)
            self._collection.replace_one(
                {"_id": pet_object_id},
                {"_id": pet_object_id, **document},
                upsert=True,
            )

        return pet

    def get(self, pet_id: str) -> Pet | None:
        pet_object_id = self._parse_id_or_none(pet_id)
        if pet_object_id is None:
            return None

        document = self._collection.find_one({"_id": pet_object_id})
        if document is None:
            return None

        return Pet(
            name=document["name"],
            life=document["life"],
            pet_id=str(document["_id"]),
            happiness=document["happiness"],
            hunger=document["hunger"],
            previous_loss=document["previous_loss"]
        )

    def remove(self, pet_id: str) -> None:
        pet_object_id = self._parse_id_or_none(pet_id)
        if pet_object_id is not None:
            self._collection.delete_one({"_id": pet_object_id})

    @staticmethod
    def _parse_id(pet_id: str) -> ObjectId:
        try:
            return ObjectId(pet_id)
        except (InvalidId, TypeError) as error:
            raise ValueError(f"Invalid pet id: {pet_id}") from error

    @classmethod
    def _parse_id_or_none(cls, pet_id: str) -> ObjectId | None:
        try:
            return cls._parse_id(pet_id)
        except ValueError:
            return None
