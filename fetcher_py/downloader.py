import json
import requests
import io
from zipfile import ZipFile
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

METADATA_DIR = ".metadata"


def serialize_sets(obj):
    if isinstance(obj, set):
        return list(obj)


class Downloader:
    def __init__(self):
        self.download_list = {}
        self.metadatas = {}
        self.session = requests.Session()

    def add(self, key, url):
        """
        Add a file to the download list.

        :param key: The key to use as the folder name in the zip file.
        :param url: The URL of the file to download.
        """
        if key == METADATA_DIR:
            raise ValueError(f"cannot have {METADATA_DIR} key for URL!")

        if key not in self.download_list:
            self.download_list[key] = set()

        self.download_list[key].add(url)

        logger.debug(f"added url={url} under key={key}")

    def add_metadata(self, name: str, value: str):
        self.metadatas[name] = value

    def download_file(self, key, url):
        """
        Helper function to download a single file.

        :param key: The key to use as the folder name in the zip file.
        :param url: The URL of the file to download.
        :return: Tuple containing key, file name, and BytesIO object with file content.
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()

            file_content = response.content
            file_name = url.split("/")[-1]
            return key, file_name, io.BytesIO(file_content)
        except Exception as e:
            return key, None, f"Failed to download {url}. Error: {str(e)}"

    def get_as_zipped(self, max_workers=None) -> io.BytesIO:
        """
        Download all files in the download list and return a ZipFile as a BytesIO stream.

        :param max_workers: The maximum number of worker threads (default is None, which uses the ThreadPool size).
        :return: BytesIO object containing the zip file content.
        """
        all_urls = set.union(*self.download_list.values())
        if len(all_urls) < 1:
            raise ValueError("no artifact url were provided to download!")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.download_file, key, url)
                for key, urls in self.download_list.items()
                for url in urls
            ]

            file_contents = []
            for future in futures:
                key, file_name, file_content_stream = future.result()
                if file_name is not None:
                    file_contents.append((key, file_name, file_content_stream))
                    logger.debug(f"Downloaded {file_name}")
                else:
                    logger.error(f"Error: {file_content_stream}")

        artifacts_persisted = 0
        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, "a") as zip_file:
            for key, file_name, file_content_stream in file_contents:
                artifacts_persisted += 1
                file_content_stream.seek(0)
                zip_file.writestr(f"{key}/{file_name}", file_content_stream.read())
                logger.debug(f"Added {key}/{file_name} to the zip file")

            for key, value in self.metadatas.items():
                zip_file.writestr(f"{METADATA_DIR}/{key}", value)
                logger.debug(f"Added {METADATA_DIR}/{key} to the zip file")

            zip_file.writestr(
                f"{METADATA_DIR}/urls.txt",
                json.dumps(self.download_list, indent=4, default=serialize_sets),
            )
            logger.debug(f"Added {METADATA_DIR}/urls.txt to the zip file")

        if artifacts_persisted < 1:
            raise ValueError("failed to download all artifacts!")

        return zip_buffer
