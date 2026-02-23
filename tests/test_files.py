import os
import tempfile
from pybackup.engine.files import FilesBackupEngine


def test_file_backup_creates_archive():
    """
    Ensure file backup creates an archive file.
    """
    with tempfile.TemporaryDirectory() as source_dir:
        test_file = os.path.join(source_dir, "data.txt")
        with open(test_file, "w") as f:
            f.write("hello backup")

        with tempfile.TemporaryDirectory() as backup_dir:
            engine = FilesBackupEngine(
                source_path=source_dir,
                backup_path=backup_dir,
            )

            archive = engine.backup()

            assert os.path.exists(archive)
            assert archive.endswith(".tar.gz")