import tempfile
import os
from src.storage import init_db, save_rankings, get_latest_rankings


def test_storage_roundtrip(tmp_path):
    db = tmp_path / "test.db"
    db_path = str(db)
    init_db(db_path)
    sample = [{"artist": "A", "song": "S", "points": 100}]
    save_rankings(db_path, sample)
    loaded = get_latest_rankings(db_path)
    assert loaded == sample
