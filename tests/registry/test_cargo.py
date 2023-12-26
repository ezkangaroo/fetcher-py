import io
from unittest.mock import MagicMock, patch
from fetcher_py.package import Package
import pytest
import requests_mock
from requests import Session

from fetcher_py.registry.cargo import (
    CargoRegistry,
    mk_index_url,
    mk_download_url,
    extract_version_from_index_line,
    get_host,
)

PKG_NAME = "rand"
PKG_VERSION = "0.8.4"

BASE_URL = "https://crates.io/api/v1/crates"
PKG = Package(ecosystem="cargo", name=PKG_NAME, version=PKG_VERSION)
PKG_URL = f"{BASE_URL}/{PKG_NAME}/{PKG_VERSION}"

PKG_WO_VERSION = Package(ecosystem="cargo", name=PKG_NAME)
PKG_WO_VERSION_URL = f"{BASE_URL}/{PKG_NAME}"


@pytest.mark.parametrize(
    "name, expected_url",
    [
        ("a", "https://index.crates.io/1/a"),
        ("ab", "https://index.crates.io/2/ab"),
        ("abc", "https://index.crates.io/3/a/bc"),
        ("abcd", "https://index.crates.io/ab/cd/abcd"),
        ("abcde", "https://index.crates.io/ab/cd/abcde"),
    ],
)
def test_mk_index_url(name, expected_url):
    result = mk_index_url(name)
    assert result == expected_url


@pytest.mark.parametrize(
    "name, version, expected_url",
    [
        ("axum", "1.2.3", "https://static.crates.io/crates/axum/axum-1.2.3.crate"),
        (
            "your_crate",
            "4.5.6",
            "https://static.crates.io/crates/your_crate/your_crate-4.5.6.crate",
        ),
    ],
)
def test_mk_download_url(name, version, expected_url):
    result = mk_download_url(name, version)
    assert result == expected_url


@pytest.mark.parametrize(
    "line, expected_result",
    [
        ('{"vers": "1.2.3"}', ("1.2.3", {"vers": "1.2.3"})),
        ('{"vers": "4.5.6"}', ("4.5.6", {"vers": "4.5.6"})),
        ('{"other_field": "value"}', (None, {"other_field": "value"})),
    ],
)
def test_extract_version_from_index_line(line, expected_result):
    result = extract_version_from_index_line(line)
    assert result == expected_result


@pytest.mark.parametrize(
    "url, expected_host",
    [
        ("https://www.example.com/path/to/resource", "www.example.com"),
        ("https://index.crates.io/ax/um/axum", "index.crates.io"),
        ("http://localhost:8080", "localhost:8080"),
    ],
)
def test_get_host(url, expected_host):
    result = get_host(url)
    assert result == expected_host


@pytest.fixture
def registry():
    session = Session()
    base_url = BASE_URL
    return CargoRegistry(session, base_url)


def test_reachable(registry):
    with requests_mock.Mocker() as m:
        m.head(BASE_URL, status_code=200)
        assert registry.reachable()

        m.head(BASE_URL, status_code=404)
        assert not registry.reachable()


def test_get_default(registry):
    with requests_mock.Mocker() as m:
        m.get(PKG_WO_VERSION_URL, json=[{"version": PKG_VERSION}])
        default_version = registry.get_default(PKG_WO_VERSION)
        assert default_version == PKG_VERSION


def test_get(registry):
    with requests_mock.Mocker() as m:
        m.get(
            "https://index.crates.io/ra/nd/rand",
            text=f'{{"name": "{PKG_NAME}", "vers": "{PKG_VERSION}"}}',
        )
        component = registry.get(PKG)
        assert component.name == PKG_NAME
        assert component.version == PKG_VERSION


@patch("fetcher_py.registry.cargo.Downloader")
def test_download(mock_downloader, registry):
    with requests_mock.Mocker() as m:
        m.get(
            "https://index.crates.io/ra/nd/rand",
            text=f'{{"name": "{PKG_NAME}", "vers": "{PKG_VERSION}"}}',
        )

        downloader_instance = MagicMock()
        downloader_instance.get_as_zipped.return_value = io.BytesIO(
            b"mocked_downloaded_data"
        )
        mock_downloader.return_value = downloader_instance

        downloaded_bytes = registry.download(PKG)
        assert downloaded_bytes.getvalue() == b"mocked_downloaded_data"

        mock_downloader.assert_called_once_with()
        downloader_instance.add.assert_called_once_with(
            "src", "https://static.crates.io/crates/rand/rand-0.8.4.crate"
        )
        downloader_instance.get_as_zipped.assert_called_once()
