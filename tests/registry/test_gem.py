import io
from fetcher_py.package import Package
import pytest
from requests import Session
from unittest.mock import patch, MagicMock
import requests_mock
from fetcher_py.registry.gem import (
    GemRegistry,
)

PKG_NAME = "coulda"
PKG_VERSION = "0.7.1"

BASE_URL = "https://rubygems.org"
PKG = Package(ecosystem="gem", name=PKG_NAME, version=PKG_VERSION)
PKG_URL = f"{BASE_URL}/api/v2/rubygems/{PKG_NAME}/versions/{PKG_VERSION}.json"

PKG_WO_VERSION = Package(ecosystem="gem", name=PKG_NAME)
PKG_WO_VERSION_URL = f"{BASE_URL}/api/versions/{PKG_NAME}/latest.json"


@pytest.fixture
def registry():
    session = Session()
    base_url = BASE_URL
    return GemRegistry(session, base_url)


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
        json_data = {"name": PKG_NAME, "version": PKG_VERSION}
        m.get(PKG_URL, json=json_data)

        component = registry.get(PKG)
        assert component.name == PKG_NAME
        assert component.version == PKG_VERSION


@patch("fetcher_py.registry.gem.Downloader")
def test_download(mock_downloader, registry):
    with requests_mock.Mocker() as m:
        json_data = {"gem_uri": "http://example.com/package.tgz"}
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
            "src", "http://example.com/package.tgz"
        )
        downloader_instance.get_as_zipped.assert_called_once()


def test_get_artifact_urls(registry):
    with requests_mock.Mocker() as m:
        json_data = {"gem_uri": "http://example.com/package.tgz"}
        m.get(PKG_URL, json=json_data)

        component = registry.get(PKG)
        artifact_urls = list(registry.get_artifact_urls(component))

        assert len(artifact_urls) == 1
        kind, url = artifact_urls[0]
        assert kind == "src"
        assert url == "http://example.com/package.tgz"
