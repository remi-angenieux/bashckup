import os
import shutil
from pathlib import Path

from _pytest.fixtures import fixture

tests_path = Path(os.path.dirname(os.path.realpath(__file__)))


@fixture(autouse=True)
def change_test_dir(monkeypatch):
    """ Change working directory to test folder """
    monkeypatch.chdir(tests_path)


@fixture
def backup_folder():
    """ Create and remove a folder """
    backup_path = tests_path / 'backup'
    os.makedirs(backup_path, exist_ok=True)
    yield backup_path
    # Clear output folder
    shutil.rmtree(backup_path)


@fixture
def server_data_folder():
    """ Copy resources/testFolder to server_data_folder then remove it """
    server_data_path = tests_path / 'serverData'
    shutil.copytree(tests_path / 'resources' / 'testFolder', server_data_path)
    yield server_data_path
    # Clear output folder
    shutil.rmtree(server_data_path)
