import io
from typing import Optional, Tuple
from fetcher_py.component import Component
from fetcher_py.package import Package
from fetcher_py.downloader import Downloader
from ._registry import Registry
from requests import Session


class PypiRegistry(Registry):
    def __init__(self, session: Session, base_url: Optional[str] = None):
        if base_url is None:
            base_url = "https://pypi.org/pypi"

        super().__init__(session, base_url)

    def reachable(self):
        resp = self.session.head(self.base_url)
        return resp.ok

    def get_default(self, entry: Package) -> str:
        resp = self.session.get(f"{self.base_url}/{entry.name}/json")
        resp.raise_for_status()
        data = resp.json()
        version = data.get("info", {}).get("version")
        if version is None:
            raise ValueError("could not find version: {data}")

        return version

    def get(self, entry: Package) -> Component:
        if entry.version is None:
            entry.version = self.get_default(entry)

        resp = self.session.get(f"{self.base_url}/{entry.name}/{entry.version}/json")
        resp.raise_for_status()
        data = resp.json()
        info = data.get("info", {})

        return Component(
            name=info.get("name", entry.name),
            version=info.get("version", entry.version),
            registry_url=self.base_url,
            homepage_url=info.get("home_page") or info.get("project_url"),
            description=info.get("description"),
            declared_licenses=info.get("license"),
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
        for url in component.raw["urls"]:
            yield url["packagetype"], url["url"]
