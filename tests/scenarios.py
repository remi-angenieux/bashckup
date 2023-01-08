import os
import shutil
import unittest

from assertpy import assert_that
from pathlib import Path

from freezegun import freeze_time

from src.bashckup.bashckup import main


class TestScenarios(unittest.TestCase):
    current_path = Path(os.path.dirname(os.path.realpath(__file__)))
    output_path = current_path / 'output'

    def tearDown(self) -> None:
        for filename in os.listdir(self.output_path):
            file_path = os.path.join(self.output_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    @freeze_time('2023-07-10 15:02:10')
    def test_tar_gz_clean(self):
        # Given
        config_file = self.current_path / 'confs' / 'tar-gz-clean.yml'
        expected_output_folder = self.output_path / 'tar-gz-clean'
        # When
        main(['backup', 'file', '--config-file', str(config_file)])

        # Then
        output = []
        with os.scandir(expected_output_folder) as it:
            entry: os.DirEntry
            for entry in it:
                output.append({'file-name': entry.name, 'size': entry.stat().st_size})

        assert_that(output).is_length(2)
        snar_file = list(filter(lambda f: f['file-name'].endswith('.snar'), output))[0]
        bck_file = list(filter(lambda f: f['file-name'].endswith('.tar.gz'), output))[0]
        assert_that(snar_file['file-name']).is_equal_to('2023-07-10T15:02:10-tar-snap-w28.snar')
        assert_that(snar_file['size']).is_between(100, 100)

        assert_that(bck_file['file-name']).is_equal_to('2023-07-10T15:02:10-tar-gz-clean.tar.gz')
        assert_that(bck_file['size']).is_between(203, 204)


if __name__ == '__main__':
    unittest.main()
