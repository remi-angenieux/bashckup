import locale
import os
import shutil
import subprocess
from pathlib import Path

from _pytest.fixtures import fixture
from assertpy import assert_that

current_path = Path(os.path.dirname(os.path.realpath(__file__)))
tests_path = current_path / '..' / '..'
conf_path = tests_path / 'resources' / 'confs'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

"""
Run application from CLI to to do end to end test
"""


def test_cli_process(backup_folder, server_data_folder):
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
