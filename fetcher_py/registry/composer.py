import dataclasses
import io
import json
from typing import Optional
from fetcher_py.component import Component
from fetcher_py.package import Package
from fetcher_py.downloader import Downloader
from ._registry import Registry
from requests import Session


class ComposerRegistry(Registry):
    def __init__(
        self,
        session: Session,
        base_url: Optional[str] = None,
    ):
        if base_url is None:
            base_url = "https://repo.packagist.org"

        super().__init__(session, base_url)

    def reachable(self):
        resp = self.session.head(self.base_url)
        return resp.ok

    def get_default(self, entry: Package) -> str:
        resp = self.session.get(f"{self.base_url}/p2/{entry.name}.json")
        resp.raise_for_status()
        data = resp.json()

        for pkg, pkg_versions in data.get("packages", {}).items():
            if pkg == entry.name:
                return pkg_versions[0].get("version")

    def get(self, entry: Package) -> Component:
        if entry.version is None:
            entry.version = self.get_default(entry)

        resp = self.session.get(f"{self.base_url}/p2/{entry.name}.json")
        resp.raise_for_status()
        data = resp.json()

        raw_data = None
        for pkg, pkg_versions in data.get("packages", {}).items():
            if pkg == entry.name:
                for pkg_version in pkg_versions:
                    print("pkg_version", pkg_version)
                    if (
                        pkg_version.get("version") == entry.version
                        or pkg_version.get("version_normalized") == entry.version
                    ):
                        raw_data = pkg_version
                        break

        if raw_data is None:
            raise ValueError(f"could not find {entry.version} for {entry.name}")

        return Component(
            name=raw_data.get("name", entry.name),
            version=raw_data.get("version", entry.version),
            registry_url=self.base_url,
            homepage_url=raw_data.get("homepage") or data.get("source", {}).get("url"),
            description=raw_data.get("info"),
            declared_licenses=raw_data.get("licenses"),
            raw=raw_data,
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
        yield "src", component.raw.get("dist", {}).get("url")
