"""Crates.io

TODO: Use Index Format (even for private??)
TODO: Private registry custom format
TODO: Check Rate limits
TODO: Premptively download index
"""
import io
import json
from typing import Optional, Tuple
from fetcher_py.component import Component
from fetcher_py.package import Package
from fetcher_py.downloader import Downloader
from ._registry import Registry
from requests import Session
from urllib.parse import urlparse

DEFAULT_BASE_URL = "https://crates.io/api/v1/crates"


def mk_index_url(name):
    if len(name) == 1:
        return f"https://index.crates.io/1/{name}"
    if len(name) == 2:
        return f"https://index.crates.io/2/{name}"
    if len(name) == 3:
        return f"https://index.crates.io/3/{name[0]}/{name[1:]}"
    return f"https://index.crates.io/{name[0:2]}/{name[2:4]}/{name}"


# https://index.crates.io/ax/um/axum
def mk_download_url(name, version):
    return f"https://static.crates.io/crates/{name}/{name}-{version}.crate"


def extract_version_from_index_line(line):
    parsed_line = json.loads(line)
    return parsed_line.get("vers"), parsed_line


def get_host(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


class CargoRegistry(Registry):
    def __init__(self, session: Session, base_url: Optional[str] = None):
        base_url = base_url or DEFAULT_BASE_URL
        super().__init__(session, base_url)

    def reachable(self):
        resp = self.session.head(self.base_url)
        return resp.ok

    def get_default(self, entry: Package) -> str:
        resp = self.session.get(f"{self.base_url}/{entry.name}")
        resp.raise_for_status()
        data = resp.json()

        # Assume that the first version in the list is the default version
        default_version = data[0]["version"]
        return default_version

    def get(self, entry: Package) -> Component:
        data = None
        if self.base_url == DEFAULT_BASE_URL and entry.version is not None:
            index_url = mk_index_url(entry.name)
            resp = self.session.get(index_url)
            resp.raise_for_status()

            for line in resp.text.splitlines():
                version_from_line, raw = extract_version_from_index_line(line)
                if version_from_line == entry.version:
                    data = raw
                    data["num"] = entry.version
                    break

            if data is None:
                raise ValueError(f"{entry.version} does not exist!")

        else:
            if entry.version is None:
                entry.version = self.get_default(entry)

            resp = self.session.get(f"{self.base_url}/{entry.name}/{entry.version}")
            resp.raise_for_status()
            data = resp.json()

        return Component(
            name=data.get("name", entry.name),
            version=data.get("num", entry.version),
            registry_url=self.base_url,
            homepage_url=data.get("homepage") or data.get("repository"),
            description=data.get("description"),
            declared_licenses=data.get("license"),
            raw=data,
        )

    def raw(self, entry: Package) -> Tuple[Component, bytes]:
        component = self.get(entry)
        downloader = Downloader()
        for kind, url in self.get_artifact_urls(component):
            downloader.add(kind, url)

        return component, downloader.get_as_zipped()

    def download(self, entry: Package) -> io.BytesIO:
        _, io_bytes = self.raw(entry)
        return io_bytes

    def get_artifact_urls(self, component: Component):
        if self.base_url == DEFAULT_BASE_URL:
            yield "src", mk_download_url(component.name, component.version)
        else:
            dl_path = component.raw.get("dl_path")
            if dl_path is None:
                raise ValueError("expected to have dl_path in component.raw")

            host = get_host(self.base_url)
            yield "src", f"{host}/{dl_path}"
