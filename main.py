from pet import PetFactory
from repository.pet_repository import PetRepository

if __name__ == '__main__':
    pet1 = PetFactory.create("Bob", 10)
    pet2 = PetFactory.create("Margaret", 5)

    repo = PetRepository()

    print(pet1)
    print(pet2)

    repo.save(pet1)
    repo.save(pet2)

    print(pet1)
    print(pet2)

