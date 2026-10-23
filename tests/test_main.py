import runpy
from pathlib import Path

MAIN_PATH = Path(__file__).resolve().parent.parent / "main.py"


def test_main_demo_runs():
    namespace = runpy.run_path(MAIN_PATH, run_name="__main__")

    repo = namespace["repo"]
    pet1 = namespace["pet1"]
    pet2 = namespace["pet2"]

    assert repo.get(pet1.pet_id) is pet1
    assert repo.get(pet2.pet_id) is pet2
