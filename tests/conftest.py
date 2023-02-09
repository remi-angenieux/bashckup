import os
import shutil
from pathlib import Path

from _pytest.fixtures import fixture

tests_path = Path(os.path.dirname(os.path.realpath(__file__)))


@fixture(autouse=True)
def change_test_dir(monkeypatch):
    """ Change working directory to test folder """
    monkeypatch.chdir(tests_path)


@fixture(autouse=True)
def output_folder():
    """ Create and remove a folder """
    output_path = tests_path / 'output'
    os.makedirs(output_path, exist_ok=True)
    yield output_path
    # Clear output folder
    for filename in os.listdir(output_path):
        file_path = os.path.join(output_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
