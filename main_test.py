"""Test suite for the Python API microservice."""

import json
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest
from fastapi.testclient import TestClient

from main import app, clear_data_cache, load_data


@pytest.fixture
def client() -> TestClient:
    """
    Create a test client for the FastAPI app.

    Returns:
        TestClient: FastAPI test client
    """
    return TestClient(app)


@pytest.fixture
def sample_data() -> List[Dict[str, str]]:
    """
    Provide sample data for testing.

    Returns:
        List[Dict[str, str]]: Sample data items
    """
    return [
        {
            "guid": "test-guid-1",
            "school": "Test University 1",
            "mascot": "Test Mascot 1",
            "nickname": "Testers 1",
            "location": "Test City 1, ST, USA",
            "latlong": "0.0, 0.0",
            "ncaa": "Division I",
            "conference": "Test Conference 1",
        },
        {
            "guid": "test-guid-2",
            "school": "Test University 2",
            "mascot": "Test Mascot 2",
            "nickname": "Testers 2",
            "location": "Test City 2, ST, USA",
            "latlong": "1.0, 1.0",
            "ncaa": "Division I",
            "conference": "Test Conference 2",
        },
    ]


@pytest.fixture
def temp_data_file(sample_data: List[Dict[str, str]], monkeypatch) -> Path:
    """
    Create a temporary data file for testing.

    Args:
        sample_data: Sample data to write to file
        monkeypatch: pytest monkeypatch fixture

    Returns:
        Path: Path to temporary data file
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_data, f)
        temp_path = Path(f.name)

    # Clear cache and patch settings to use temp file
    clear_data_cache()
    monkeypatch.setenv("DATA_FILE_PATH", str(temp_path))

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)
    clear_data_cache()


@pytest.fixture(autouse=True)
def reset_cache():
    """
    Reset data cache before each test.

    This ensures tests don't interfere with each other.
    """
    clear_data_cache()
    yield
    clear_data_cache()


class TestReadData:
    """Test suite for the read_data endpoint."""

    def test_read_data_success(
        self,
        client: TestClient,
        temp_data_file: Path,
        sample_data: List[Dict[str, str]],
    ) -> None:
        """Test successful retrieval of all data."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == sample_data

    def test_read_data_empty_file(
        self, client: TestClient, monkeypatch, tmp_path: Path
    ) -> None:
        """Test handling of empty data file."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("[]")

        clear_data_cache()
        monkeypatch.setenv("DATA_FILE_PATH", str(empty_file))

        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == []

    def test_read_data_missing_file(self, client: TestClient, monkeypatch) -> None:
        """Test handling of missing data file."""
        clear_data_cache()
        monkeypatch.setenv("DATA_FILE_PATH", "/nonexistent/file.json")

        response = client.get("/")
        assert response.status_code == 500
        assert "Failed to load data" in response.json()["detail"]


class TestReadDataByGuid:
    """Test suite for the read_data_by_guid endpoint."""

    def test_read_data_by_guid_success(
        self,
        client: TestClient,
        temp_data_file: Path,
        sample_data: List[Dict[str, str]],
    ) -> None:
        """Test successful retrieval of item by GUID."""
        guid = sample_data[0]["guid"]
        response = client.get(f"/{guid}")
        assert response.status_code == 200
        assert response.json() == sample_data[0]

    def test_read_data_by_guid_not_found(
        self, client: TestClient, temp_data_file: Path
    ) -> None:
        """Test handling of non-existent GUID."""
        response = client.get("/nonexistent-guid")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_read_data_by_guid_empty_guid(
        self, client: TestClient, temp_data_file: Path
    ) -> None:
        """Test handling of empty GUID."""
        # Test with URL encoded space - should be treated as empty GUID
        response = client.get("/%20")  # URL encoded space
        # Empty GUID returns 400 Bad Request (correct behavior)
        assert response.status_code == 400
        assert "GUID cannot be empty" in response.json()["detail"]

    def test_read_data_by_guid_special_characters(
        self, client: TestClient, temp_data_file: Path
    ) -> None:
        """Test handling of GUID with special characters."""
        response = client.get("/test@guid#123")
        assert response.status_code == 404


class TestHealthCheck:
    """Test suite for the health check endpoint."""

    def test_health_check_success(
        self,
        client: TestClient,
        temp_data_file: Path,
        sample_data: List[Dict[str, str]],
    ) -> None:
        """Test successful health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["data_items"] == str(len(sample_data))

    def test_health_check_unhealthy(self, client: TestClient, monkeypatch) -> None:
        """Test health check when data file is missing."""
        clear_data_cache()
        monkeypatch.setenv("DATA_FILE_PATH", "/nonexistent/file.json")

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data


class TestDataLoading:
    """Test suite for data loading functionality."""

    def test_load_data_success(
        self, temp_data_file: Path, sample_data: List[Dict[str, str]]
    ) -> None:
        """Test successful data loading."""
        clear_data_cache()
        data = load_data(str(temp_data_file))
        assert data == sample_data
        assert len(data) == 2

    def test_load_data_caching(
        self, temp_data_file: Path, sample_data: List[Dict[str, str]]
    ) -> None:
        """Test that data is cached after first load."""
        clear_data_cache()
        data1 = load_data(str(temp_data_file))
        data2 = load_data(str(temp_data_file))
        assert data1 is data2  # Same object reference due to caching

    def test_load_data_invalid_json(self, tmp_path: Path) -> None:
        """Test handling of invalid JSON file."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")

        clear_data_cache()
        with pytest.raises(Exception):  # Should raise DataLoadError
            load_data(str(invalid_file))

    def test_load_data_not_list(self, tmp_path: Path) -> None:
        """Test handling of JSON file that is not a list."""
        not_list_file = tmp_path / "not_list.json"
        not_list_file.write_text('{"key": "value"}')

        clear_data_cache()
        with pytest.raises(Exception):  # Should raise DataLoadError
            load_data(str(not_list_file))
