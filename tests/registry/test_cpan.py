import io
from fetcher_py.package import Package
import pytest
from requests import Session
from unittest.mock import patch, MagicMock
import requests_mock
from fetcher_py.registry.cpan import (
    CpanRegistry,
)

PKG_NAME = "coulda"
PKG_VERSION = "0.7.1"

BASE_URL = "https://fastapi.metacpan.org"
PKG = Package(ecosystem="gem", name=PKG_NAME, version=PKG_VERSION)
PKG_URL = f"{BASE_URL}/v1/download_url/{PKG_NAME}?version===${PKG_VERSION}"

PKG_WO_VERSION = Package(ecosystem="gem", name=PKG_NAME)
PKG_WO_VERSION_URL = f"{BASE_URL}/v1/download_url/{PKG_NAME}"


@pytest.fixture
def registry():
    session = Session()
    base_url = BASE_URL
    return CpanRegistry(session, base_url)


def test_reachable(registry):
    with requests_mock.Mocker() as m:
        m.head(BASE_URL, status_code=200)
        assert registry.reachable()

        m.head(BASE_URL, status_code=404)
        assert not registry.reachable()


def test_get_default(registry):
    with requests_mock.Mocker() as m:
        m.get(PKG_WO_VERSION_URL, json={"version": PKG_VERSION})
        default_version = registry.get_default(PKG_WO_VERSION)
        assert default_version == PKG_VERSION


def test_get(registry):
    with requests_mock.Mocker() as m:
        json_data = {"download_url": "https://example.com/example-0.01.tar.gz"}
        m.get(PKG_URL, json=json_data)

        component = registry.get(PKG)
        assert component.name == PKG_NAME
        assert component.version == PKG_VERSION


@patch("fetcher_py.registry.cpan.Downloader")
def test_download(mock_downloader, registry):
    with requests_mock.Mocker() as m:
        json_data = {"download_url": "https://example.com/example-0.01.tar.gz"}
        m.get(PKG_URL, json=json_data)
        downloader_instance = MagicMock()
        downloader_instance.get_as_zipped.return_value = io.BytesIO(
            b"mocked_downloaded_data"
        )
        mock_downloader.return_value = downloader_instance

        downloaded_bytes = registry.download(PKG)
        assert downloaded_bytes.getvalue() == b"mocked_downloaded_data"

        mock_downloader.assert_called_once_with()
        downloader_instance.add.assert_called_once_with(
            "src", "https://example.com/example-0.01.tar.gz"
        )
        downloader_instance.get_as_zipped.assert_called_once()


def test_get_artifact_urls(registry):
    with requests_mock.Mocker() as m:
        json_data = {"download_url": "https://example.com/example-0.01.tar.gz"}
        m.get(PKG_URL, json=json_data)
        component = registry.get(PKG)
        artifact_urls = list(registry.get_artifact_urls(component))

        assert len(artifact_urls) == 1
        kind, url = artifact_urls[0]
        assert kind == "src"
        assert url == "https://example.com/example-0.01.tar.gz"
