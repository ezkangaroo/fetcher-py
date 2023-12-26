import io
from fetcher_py.package import Package
from fetcher_py.protocol.url import UrlRegistry
import pytest
from requests import Session
from unittest.mock import patch, MagicMock
import requests_mock


PKG_URL = "https://example.org/out-1.0.0.zip"
PKG = Package.parse("https://example.org/out-1.0.0.zip")


@pytest.fixture
def registry():
    session = Session()
    return UrlRegistry(session)


def test_reachable(registry):
    with requests_mock.Mocker() as m:
        m.head("https://www.google.com", status_code=200)
        assert registry.reachable()

        m.head("https://www.google.com", status_code=404)
        assert not registry.reachable()


def test_get_default(registry):
    with pytest.raises(NotImplementedError) as excinfo:
        registry.get_default(PKG)
    assert str(excinfo.value) == "There can be no versioning for url based package"


def test_get(registry):
    with requests_mock.Mocker() as m:
        m.get(PKG_URL, text="something")

        component = registry.get(PKG)
        assert component.name == "example.org/out-1.0.0.zip"
        assert component.version is None


@patch("fetcher_py.protocol.url.Downloader")
def test_download(mock_downloader, registry):
    with requests_mock.Mocker() as m:
        m.get(PKG_URL, text="somethings")

        downloader_instance = MagicMock()
        downloader_instance.get_as_zipped.return_value = io.BytesIO(
            b"mocked_downloaded_data"
        )
        mock_downloader.return_value = downloader_instance

        downloaded_bytes = registry.download(PKG)
        assert downloaded_bytes.getvalue() == b"mocked_downloaded_data"

        mock_downloader.assert_called_once_with()
        downloader_instance.add.assert_called_once_with("url", PKG_URL)
        downloader_instance.get_as_zipped.assert_called_once()


def test_get_artifact_urls(registry):
    with requests_mock.Mocker() as m:
        m.get(PKG_URL, text="somethings")
        component = registry.get(PKG)
        artifact_urls = list(registry.get_artifact_urls(component))

        assert len(artifact_urls) == 1
        kind, url = artifact_urls[0]
        assert kind == "url"
        assert url == PKG_URL
