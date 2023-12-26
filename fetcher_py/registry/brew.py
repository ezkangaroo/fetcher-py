import dataclasses
import io
import json
from typing import Optional
from fetcher_py.component import Component
from fetcher_py.package import Package
from fetcher_py.downloader import Downloader
from ._registry import Registry
from requests import Session

class BrewRegistry(Registry):
    def __init__(
        self,
        session: Session,
        base_url: Optional[str] = None,
    ):
        if base_url is None:
            base_url = "https://formulae.brew.sh/api/formula"

        super().__init__(session, base_url)

    def reachable(self):
        resp = self.session.head(self.base_url)
        return resp.ok

    def get_default(self, entry: Package) -> str:
        resp = self.session.get(
            f"{self.base_url}/{entry.name}.json"
        )
        resp.raise_for_status()
        data = resp.json()
        version = data.get("versions", {}).get('stable')
        if version is None:
            raise ValueError(f"Could not find version for package {entry.name}")

        return version

    def get(self, entry: Package) -> Component:
        resp = self.session.get(
            f"{self.base_url}/{entry.name}.json"
        )
        resp.raise_for_status()
        data = resp.json()
        version = data.get("versions", {}).get('stable')

        return Component(
            name=data.get("name", entry.name),
            version=version,
            registry_url=self.base_url,
            homepage_url=data.get("homepage"),
            description=data.get("desc"),
            declared_licenses=data.get("license"),
            raw=data,
        )

    def download(self, entry: Package) -> io.BytesIO:
        component = self.get(entry)
        downloader = Downloader()

        for kind, url in self.get_artifact_urls(component):
            downloader.add(kind, url)

        downloader.add_metadata(
            "component.json", json.dumps(dataclasses.asdict(component), indent=4)
        )
        return downloader.get_as_zipped()

    def get_artifact_urls(self, component: Component):
        src_url = component.raw.get("urls", {}).get('stable', {}).get("url")
        if src_url:
            yield "src", src_url