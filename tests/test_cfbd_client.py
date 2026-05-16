import responses
import pytest

from ingestion.cfbd_ingest.services.cfbd_client import CFBDClient

temp = CFBDClient("fake_key")

def test_testing():
    assert True

def test_testing2():
    assert False