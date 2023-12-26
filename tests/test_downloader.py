import zipfile

import pytest
import requests_mock
from fetcher_py.downloader import Downloader


@pytest.fixture
def downloader():
    return Downloader()


def test_add_method(downloader):
    downloader.add("folder1", "https://example.com/file1.txt")
    assert "folder1" in downloader.download_list
    assert "https://example.com/file1.txt" in downloader.download_list["folder1"]


def test_download_file_method_success(downloader):
    url = "https://example.com/file1.txt"
    response_content = b"Test content"

    with requests_mock.Mocker() as m:
        m.get(url, content=response_content, status_code=200)
        key, file_name, file_content_stream = downloader.download_file("folder1", url)
        print(key, file_name, file_content_stream)

    assert key == "folder1"
    assert file_name == "file1.txt"
    assert file_content_stream.read() == response_content


def test_download_file_method_failure(downloader):
    url = "https://example.com/file1.txt"

    with requests_mock.Mocker() as m:
        m.get(url, status_code=404)
        key, file_name, file_content_stream = downloader.download_file("folder1", url)

    assert key == "folder1"
    assert file_name is None
    assert "Failed to download" in file_content_stream


def test_get_as_zipped(downloader):
    urls = {
        "folder1": set(["https://example.com/file1.txt"]),
        "folder2": set(
            [
                "https://example.com/file2.txt",
                "https://example.com/file3.txt",
                "https://example.com/file4.txt",
            ]
        ),
    }

    with requests_mock.Mocker() as m:
        for key, key_urls in urls.items():
            for url in key_urls:
                content = f"Test content for {url}"
                m.get(url, content=content.encode())

        for key, key_urls in urls.items():
            for url in key_urls:
                downloader.add(key, url)

        zip_buffer = downloader.get_as_zipped()
        with zipfile.ZipFile(zip_buffer, "r") as z:
            for key, key_urls in urls.items():
                for url in key_urls:
                    file_name = url.split("/")[-1]
                    content = z.read(f"{key}/{file_name}").decode()
                    expected_content = f"Test content for {url}"
                    assert content == expected_content
