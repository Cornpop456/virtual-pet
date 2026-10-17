
import pytest

from pet import Pet, PetFactory, LifeLossPolicy, DeadPetError


# ---------- Создание питомца ----------

def test_create_pet():
    pet = Pet(name="Buddy", life=10)

    assert pet.name == "Buddy"
    assert pet.life == 10
    assert pet.pet_id == ''
    assert pet.happiness == 2
    assert pet.hunger == 2
    assert pet.previous_loss == 0
    assert pet.is_alive


def test_pet_factory_create():
    pet = PetFactory.create(name="Buddy", life=10)

    assert isinstance(pet, Pet)
    assert pet.name == "Buddy"
    assert pet.life == 10
    assert pet.pet_id == ''


def test_pet_factory_creates_independent_pets():
    pet1 = PetFactory.create("Buddy", 10)
    pet2 = PetFactory.create("Charlie", 20)

    assert pet1 is not pet2
    assert pet1.previous_loss == 0
    assert pet2.previous_loss == 0


# ---------- Состояние питомца ----------

@pytest.mark.parametrize(
    ("life", "happiness", "expected"),
    [
        (10, 2, True),
        (1, 1, True),
        (0, 2, False),
        (-1, 2, False),
        (10, 0, False),
        (10, -1, False),
        (0, 0, False),
    ],
)
def test_is_alive(life, happiness, expected):
    pet = Pet(
        name="Buddy",
        life=life,
        happiness=happiness,
    )

    assert pet.is_alive is expected


# ---------- Действия питомца ----------

@pytest.mark.parametrize(
    ("action", "expected_happiness", "expected_hunger"),
    [
        ("feed", 2, 0),
        ("pet", 3, 3),
        ("treat", 4, 1),
        ("walk", 3, 5),
        ("ignore", 1, 3),
    ],
)
def test_pet_actions(action, expected_happiness, expected_hunger):
    pet = Pet(name="Buddy", life=10)

    getattr(pet, action)()

    assert pet.happiness == expected_happiness
    assert pet.hunger == expected_hunger


# ---------- Политика потери жизней ----------

def test_no_life_loss_when_hunger_is_five_or_less():
    pet = Pet(name="Buddy", life=10, hunger=5, previous_loss=3)

    LifeLossPolicy.apply(pet)

    assert pet.life == 10
    assert pet.previous_loss == 0


def test_first_life_loss_is_one():
    pet = Pet(name="Buddy", life=10, hunger=6)

    LifeLossPolicy.apply(pet)

    assert pet.life == 9
    assert pet.previous_loss == 1


def test_life_loss_increases_each_time():
    pet = Pet(name="Buddy", life=10, hunger=10)

    LifeLossPolicy.apply(pet)
    LifeLossPolicy.apply(pet)
    LifeLossPolicy.apply(pet)

    # Потери: 1 + 2 + 3 = 6.
    assert pet.life == 4
    assert pet.previous_loss == 3


def test_life_loss_resets_after_feeding():
    pet = Pet(name="Buddy", life=10, hunger=10)

    LifeLossPolicy.apply(pet)
    LifeLossPolicy.apply(pet)

    assert pet.previous_loss == 2
    assert pet.life == 7

    pet.hunger = 5
    LifeLossPolicy.apply(pet)

    assert pet.previous_loss == 0
    assert pet.life == 7

    pet.hunger = 6
    LifeLossPolicy.apply(pet)

    assert pet.previous_loss == 1
    assert pet.life == 6


# ---------- Интеграция декоратора и политики ----------

def test_action_applies_life_loss_policy():
    pet = Pet(name="Buddy", life=10, hunger=5)

    pet.walk()

    # Голод: 5 + 3 = 8, потеря одной жизни.
    assert pet.hunger == 8
    assert pet.life == 9
    assert pet.previous_loss == 1


def test_action_does_not_apply_life_loss_when_hunger_is_low():
    pet = Pet(name="Buddy", life=10, hunger=2)

    pet.feed()

    assert pet.hunger == 0
    assert pet.life == 10
    assert pet.previous_loss == 0


# ---------- Мёртвый питомец ----------

@pytest.mark.parametrize(
    "action",
    ["feed", "pet", "treat", "walk", "ignore"],
)
def test_dead_pet_cannot_perform_action(action):
    pet = Pet(name="Buddy", life=0)

    with pytest.raises(
        DeadPetError,
        match="Can't perform action: pet is dead",
    ):
        getattr(pet, action)()


def test_action_is_rejected_when_happiness_is_zero():
    pet = Pet(name="Buddy", life=10, happiness=0)

    with pytest.raises(DeadPetError):
        pet.feed()


def test_rejected_action_does_not_change_state():
    pet = Pet(
        name="Buddy",
        life=0,
        happiness=2,
        hunger=3,
        previous_loss=1,
    )
    initial_state = (
        pet.life,
        pet.happiness,
        pet.hunger,
        pet.previous_loss,
    )

    with pytest.raises(DeadPetError):
        pet.walk()

    assert (
        pet.life,
        pet.happiness,
        pet.hunger,
        pet.previous_loss,
    ) == initial_state


# ---------- Уменьшение жизней ----------

def test_decrease_life():
    pet = Pet(name="Buddy", life=10)

    pet.decrease_life(3)

    assert pet.life == 7


def test_decrease_life_can_make_pet_dead():
    pet = Pet(name="Buddy", life=2)

    pet.decrease_life(2)

    assert pet.life == 0
    assert pet.is_alive is False
