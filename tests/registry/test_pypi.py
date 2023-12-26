import io
from fetcher_py.package import Package
import pytest
from requests import Session
from unittest.mock import patch, MagicMock
import requests_mock
from fetcher_py.registry.pypi import PypiRegistry

PKG = Package(ecosystem="pip", name="numpy", version="1.18.5")
PKG_WO_VERSION = Package(ecosystem="pip", name="numpy")


@pytest.fixture
def registry():
    session = Session()
    base_url = "https://pypi.org"
    return PypiRegistry(session, base_url)


def test_reachable(registry):
    with requests_mock.Mocker() as m:
        m.head("https://pypi.org", status_code=200)
        assert registry.reachable()

        m.head("https://pypi.org", status_code=404)
        assert not registry.reachable()


def test_get_default(registry):
    with requests_mock.Mocker() as m:
        m.get("https://pypi.org/numpy/json", json={"info": {"version": "1.18.5"}})
        default_version = registry.get_default(PKG_WO_VERSION)
        assert default_version == "1.18.5"


def test_get(registry):
    with requests_mock.Mocker() as m:
        json_data = {"info": {"name": "numpy", "version": "1.18.5"}}
        m.get("https://pypi.org/numpy/1.18.5/json", json=json_data)

        component = registry.get(PKG)
        assert component.name == "numpy"
        assert component.version == "1.18.5"


@patch("fetcher_py.registry.pypi.Downloader")
def test_download(mock_downloader, registry):
    with requests_mock.Mocker() as m:
        json_data = {
            "urls": [{"packagetype": "sdist", "url": "http://example.com/package.zip"}]
        }
        m.get("https://pypi.org/numpy/1.18.5/json", json=json_data)

        downloader_instance = MagicMock()
        downloader_instance.get_as_zipped.return_value = io.BytesIO(
            b"mocked_downloaded_data"
        )
        mock_downloader.return_value = downloader_instance

        downloaded_bytes = registry.download(PKG)
        assert downloaded_bytes.getvalue() == b"mocked_downloaded_data"

        mock_downloader.assert_called_once_with()
        downloader_instance.add.assert_called_once_with(
            "sdist", "http://example.com/package.zip"
        )
        downloader_instance.get_as_zipped.assert_called_once()


def test_get_artifact_urls(registry):
    with requests_mock.Mocker() as m:
        json_data = {
            "urls": [{"packagetype": "sdist", "url": "http://example.com/package.zip"}]
        }
        m.get("https://pypi.org/numpy/1.18.5/json", json=json_data)

        component = registry.get(PKG)
        artifact_urls = list(registry.get_artifact_urls(component))

        assert len(artifact_urls) == 1
        kind, url = artifact_urls[0]
        assert kind == "sdist"
        assert url == "http://example.com/package.zip"
