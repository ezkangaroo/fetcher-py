import dataclasses
import io
import json
from typing import Optional

import requests
from fetcher_py.component import Component
from fetcher_py.package import Package
from fetcher_py.downloader import Downloader
from fetcher_py.registry._registry import Registry
from requests import Session


class UrlRegistry(Registry):
    def __init__(
        self,
        session: Session,
        base_url: Optional[str] = None,
    ):
        super().__init__(session, base_url)

    def reachable(self):
        try:
            response = self.session.head("https://www.google.com", timeout=5)
            return response.status_code // 100 == 2
        except requests.ConnectionError:
            return False

    def get_default(self, entry: Package) -> str:
        raise NotImplementedError("There can be no versioning for url based package")

    def get(self, entry: Package) -> Component:
        resp = self.session.get(f"{entry.ecosystem}://{entry.name}")
        resp.raise_for_status()
        data = {
            "name": entry.name,
            "version": None,
            "registry_url": self.base_url,
            "homepage_url": None,
            "description": None,
            "declared_licenses": None,
            "raw": {"url": f"{entry.ecosystem}://{entry.name}"},
        }

        return Component(**data)

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
        yield "url", component.raw.get("url")
