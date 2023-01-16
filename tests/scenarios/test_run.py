import locale
import os
import shutil
import subprocess
from pathlib import Path

from _pytest.fixtures import fixture
from assertpy import assert_that

current_path = Path(os.path.dirname(os.path.realpath(__file__)))
tests_path = current_path / '..'
conf_path = tests_path / 'confs'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

"""
Run application from CLI to to do end to end test
"""


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


def test_cli_process(output_folder):
    """
    GOAL: Test application launch as a CLI process
    Based on tar test
    """
    # Given
    config_file = conf_path / 'tar.yml'
    # When
    process = subprocess.run(['bashckup', 'backup', 'file', '--config-file', str(config_file)], capture_output=True)

    # Then
    assert_that(process.returncode).is_equal_to(0)
    assert_that(process.stdout).is_not_empty()
    assert_that(process.stderr).is_empty()
