import os
import unittest
from assertpy import assert_that
from pathlib import Path

from src.actuators.readers import FileReader
from src.actuators.writers import FileWriter


class TestReadFile(unittest.TestCase):
    current_path = Path(os.path.dirname(os.path.realpath(__file__)))

    def test_generate_dry_run_backup_cmd(self):
        # Given
        global_context = {'backup-id': 'test', 'dry-run': True}
        backup_folder = self.current_path / "testFolder"
        output_folder = self.current_path / '..' / "output"
        args = {'path': str(backup_folder)}
        metadata = {}
        reader_module = FileReader(global_context, args, metadata)
        writer_module = FileWriter(global_context, {'file-name': 'test', 'path': str(output_folder)}, metadata)

        # When
        metadata.update(reader_module.prepare_module())
        metadata.update(writer_module.prepare_module())
        result = reader_module.generate_dry_run_backup_cmd()

        # Then
        assert_that(result).is_length(3)
        assert_that(result[0]).is_equal_to('tar')
        assert_that(result[1]).is_equal_to('-c')
        assert_that(result[2]).ends_with('tests/testFolder')


if __name__ == '__main__':
    unittest.main()
