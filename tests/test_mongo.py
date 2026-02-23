from pybackup.engine.mongo import MongoBackupEngine


def test_mongo_backup_command_generation():
    """
    Validate MongoDB backup command is generated correctly.
    """
    engine = MongoBackupEngine(
        host="localhost",
        port=27017,
        database="testdb",
        username="user",
        password="pass",
        backup_path="/tmp",
    )

    cmd = engine.build_command()

    assert "mongodump" in cmd
    assert "--db testdb" in cmd
    assert "--host localhost" in cmd