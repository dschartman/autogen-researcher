import pytest
from lib.code_squad import CodeSquad


@pytest.fixture()
def code_squad():
    yield CodeSquad(repo_path=".code_squad/test_repo")


def test_init(code_squad):
    pass


def test_code_challenge(code_squad):
    code_squad.execute_task(
        "create a python function that adds two numbers.  assume this is a local git repo."
    )
