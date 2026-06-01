import json
import pytest
from unittest.mock import MagicMock, patch

from ingestion.cfbd_ingest.chalicelib.s3_writer import BronzeWriter

# NOTE: tmp_path is a fixture provided by pytest, built in to the pytest library and cleaned up after each test

class TestBronzeWriter:
    def test_writes_to_local_disk(self, tmp_path):
        writer = BronzeWriter(local_root=str(tmp_path))
        data = [{"id": 1, "name": "SEC"}]
        key = writer.write_entity("conferences", data, ingest_time="2026-05-26T10-00-00Z")

        file_path = tmp_path / key
        assert file_path.exists()

        with open(file_path) as f:
            envelope = json.load(f)

        assert envelope["entity"] == "conferences"
        assert envelope["source"] == "cfbdata"
        assert envelope["record_count"] == 1
        assert envelope["payload"] == data

    def test_constructs_correct_path(self, tmp_path):
        writer = BronzeWriter(local_root=str(tmp_path))
        key = writer.write_entity("games", [], params={"year": 2024}, ingest_time="2026-05-26T10-00-00Z")

        assert key.startswith("bronze/source=cfbdata/entity=games/ingest_date=2026-05-26/")
        assert key.endswith(".json")
        assert "games_" in key

        assert (tmp_path / key).exists()

    def test_includes_params_in_envelope(self, tmp_path):
        writer = BronzeWriter(local_root=str(tmp_path))
        writer.write_entity("teams", [], params={"year": 2024}, ingest_time="2026-05-26T10-00-00Z")

        partition = tmp_path / "bronze/source=cfbdata/entity=teams/ingest_date=2026-05-26"
        files = list(partition.iterdir())
        assert len(files) == 1

        with open(files[0]) as f:
            envelope = json.load(f)

        assert envelope["params"] == {"year": 2024}

    def test_empty_data(self, tmp_path):
        writer = BronzeWriter(local_root=str(tmp_path))
        key = writer.write_entity("games", [], ingest_time="2026-05-26T10-00-00Z")

        with open(tmp_path / key) as f:
            envelope = json.load(f)

        assert envelope["record_count"] == 0
        assert envelope["payload"] == []

    def test_single_dict_writes_record_count_one(self, tmp_path):
        writer = BronzeWriter(local_root=str(tmp_path))
        key = writer.write_entity("venue", {"id": 1}, ingest_time="2026-05-26T10-00-00Z")

        with open(tmp_path / key) as f:
            envelope = json.load(f)

        assert envelope["record_count"] == 1
        assert envelope["payload"] == {"id": 1}

    @patch("boto3.client")
    def test_writes_to_s3(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        writer = BronzeWriter(bucket="my-bucket")
        data = [{"id": 1}]
        key = writer.write_entity("games", data, ingest_time="2026-05-26T10-00-00Z")

        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "my-bucket"
        assert call_kwargs["Key"] == key

        body = json.loads(call_kwargs["Body"])
        assert body["entity"] == "games"
        assert body["payload"] == data

    def test_raises_if_both_bucket_and_local(self):
        with pytest.raises(ValueError, match="Specify either"):
            BronzeWriter(bucket="b", local_root="/tmp")

    def test_auto_generates_timestamp(self, tmp_path):
        writer = BronzeWriter(local_root=str(tmp_path))
        key = writer.write_entity("games", [])

        assert "T" in key
        assert key.endswith(".json")
        # Verify file was written
        assert (tmp_path / key).exists()


