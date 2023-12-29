import io
from typing import Optional, Tuple
from fetcher_py.component import Component
from fetcher_py.package import Package
from fetcher_py.downloader import Downloader
from ._registry import Registry
from requests import Session


class GemRegistry(Registry):
    def __init__(
        self,
        session: Session,
        base_url: Optional[str] = None,
    ):
        if base_url is None:
            base_url = "https://rubygems.org"

        super().__init__(session, base_url)

    def reachable(self):
        resp = self.session.head(self.base_url)
        return resp.ok

    def get_default(self, entry: Package) -> str:
        resp = self.session.get(
            f"{self.base_url}/api/versions/{entry.name}/latest.json"
        )
        resp.raise_for_status()
        data = resp.json()
        version = data.get("version")
        if version is None:
            raise ValueError(f"Could not find version for package {entry.name}")

        return version

    def get(self, entry: Package) -> Component:
        if entry.version is None:
            entry.version = self.get_default(entry)

        resp = self.session.get(
            f"{self.base_url}/api/v2/rubygems/{entry.name}/versions/{entry.version}.json"
        )
        resp.raise_for_status()
        data = resp.json()

        return Component(
            name=data.get("name", entry.name),
            version=data.get("version", entry.version),
            registry_url=self.base_url,
            homepage_url=data.get("homepage_uri") or data.get("project_uri"),
            description=data.get("info"),
            declared_licenses=data.get("licenses"),
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
        yield "src", component.raw.get("gem_uri")
