import io
import os
import tempfile
import pytest
import requests
from unittest.mock import patch, MagicMock
from fetcher_py.fetcher import (
    Fetcher,
)  # Replace 'your_module' with the actual module name
from fetcher_py.package import Package
from fetcher_py.registry.pypi import PypiRegistry


@pytest.fixture
def mock_session():
    return MagicMock(spec=requests.Session)


@pytest.fixture
def fetcher(mock_session):
    return Fetcher(session=mock_session)


@pytest.mark.parametrize(
    "ecosystem, registry_class",
    [
        ("pip", PypiRegistry),
    ],
)
def test_get(fetcher, ecosystem, registry_class):
    with patch.object(registry_class, "get") as mock_get:
        mock_get.return_value = f"Mocked Component for {ecosystem}"
        result = fetcher.get(f"{ecosystem}://some_package")

    mock_get.assert_called_once_with(Package(name="some_package", ecosystem=ecosystem))
    assert result == f"Mocked Component for {ecosystem}"


@pytest.mark.parametrize(
    "ecosystem, registry_class",
    [
        ("pip", PypiRegistry),
    ],
)
def test_download_raw(fetcher, ecosystem, registry_class):
    with patch.object(registry_class, "download") as mock_download:
        mock_download.return_value = b"Mocked Raw Data for {ecosystem}"
        result = fetcher.download_raw(f"{ecosystem}://another_package")

    mock_download.assert_called_once_with(
        Package(name="another_package", ecosystem=ecosystem)
    )
    assert result == b"Mocked Raw Data for {ecosystem}"


@pytest.mark.parametrize(
    "ecosystem, registry_class",
    [
        ("pip", PypiRegistry),
    ],
)
def test_download(fetcher, ecosystem, registry_class):
    with patch.object(registry_class, "download") as mock_download:
        content = f"Mocked Raw Data for {ecosystem}".encode()
        mock_download.return_value = io.BytesIO(content)
        mock_download.return_value.seek(0)

        with tempfile.TemporaryDirectory() as temp_dir:
            destination = os.path.join(temp_dir, f"{ecosystem}_destination")
            fetcher.download(f"{ecosystem}://p1", destination)
            with open(destination, "rb") as file:
                saved_content = file.read()

                mock_download.assert_called_once_with(
                    Package(name="p1", ecosystem=ecosystem)
                )
                assert saved_content == content


@pytest.mark.parametrize(
    "invalid_query",
    [
        "invalid_ecosystem:invalid_package",
    ],
)
def test_get_with_invalid_ecosystem(fetcher, invalid_query):
    with pytest.raises(ValueError, match="Invalid package identifier format"):
        fetcher.get(invalid_query)


@pytest.mark.parametrize(
    "invalid_query",
    [
        "invalid_ecosystem:invalid_package",
    ],
)
def test_download_raw_with_invalid_ecosystem(fetcher, invalid_query):
    with pytest.raises(ValueError, match="Invalid package identifier format"):
        fetcher.download_raw(invalid_query)
