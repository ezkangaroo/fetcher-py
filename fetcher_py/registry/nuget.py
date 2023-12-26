import dataclasses
import io
import json
from typing import Optional
from fetcher_py.component import Component
from fetcher_py.package import Package
from fetcher_py.downloader import Downloader
from ._registry import Registry
import requests


class NugetIndex:
    def __init__(self, session: requests.Session, index_url) -> None:
        self.session = session
        self.index_url = index_url
        self.index_data = self._get_index_data()
        self.registration_data = None

    def _remove_trailing_slash(self, url: str) -> str:
        return url.rstrip("/")

    def _get_index_data(self):
        response = self.session.get(f"{self.index_url}/index.json")
        response.raise_for_status()
        return response.json()

    def _get_catalog_url(self) -> str:
        for resource in self.index_data.get("resources", []):
            if (
                resource.get("@type") == "RegistrationsBaseUrl"
                or "URL of Azure storage where NuGet package registration info is stored"
                in resource.get("comment", "")
            ):
                return self._remove_trailing_slash(resource["@id"])
        raise ValueError("Catalog URL not found in index resources.")

    def any_version(self, package_name: str) -> str:
        catalog_url = self._get_catalog_url()
        resp = self.session.get(f"{catalog_url}/{package_name.lower()}/index.json")
        resp.raise_for_status()

        pkg_index = resp.json()
        items = pkg_index.get("items", [])

        if len(items) > 0:
            child_items = items[-1].get("items", [])
            if len(child_items) > 0:
                return child_items[-1].get("catalogEntry", {}).get("version")

        raise ValueError(f"could not find any version for {package_name}")

    def package_version_url(self, package_name: str, version: str) -> str:
        catalog_url = self._get_catalog_url()
        package_url = f"{catalog_url}/{package_name.lower()}/{version.lower()}.json"

        if self.registration_data is None:
            resp = self.session.get(package_url)
            resp.raise_for_status()
            self.registration_data = resp.json()

        return self.registration_data.get("catalogEntry")

    def packge_version_download_url(self, package_name: str, version: str) -> str:
        self.package_version_url(package_name, version)
        url = self.registration_data.get("packageContent")
        if url is not None:
            return url

        for resource in self.index_data.get("resources", []):
            if "PackageBaseAddress" in resource.get(
                "@type"
            ) or "Base URL of where NuGet packages are stored" in resource.get(
                "comment", ""
            ):
                url = self._remove_trailing_slash(resource["@id"])

        return f"{url}/{package_name.lower()}/{version.lower()}/{package_name.lower()}.{version.lower()}.nupkg "


class NuGetRegistry(Registry):
    def __init__(
        self,
        session: requests.Session,
        base_url: Optional[str] = None,
    ):
        if base_url is None:
            base_url = "https://api.nuget.org/v3"

        self.index = NugetIndex(session, base_url)
        super().__init__(session, base_url)

    def reachable(self):
        resp = self.session.head(self.base_url)
        return resp.ok

    def get_default(self, entry: Package) -> str:
        version = self.index.any_version(entry.name)
        if version is None:
            raise ValueError(f"could not find any version for {entry.name}")

        return version

    def get(self, entry: Package) -> Component:
        if entry.version is None:
            entry.version = self.get_default(entry)

        resp = self.session.get(
            self.index.package_version_url(entry.name, entry.version)
        )
        resp.raise_for_status()
        data = resp.json()

        return Component(
            name=data.get("id", entry.name),
            version=data.get("version", entry.version),
            registry_url=self.base_url,
            homepage_url=data.get("projectUrl"),
            description=data.get("description"),
            declared_licenses=data.get("licenseExpression") or data.get("license"),
            raw=data,
        )

    def download(self, entry: Package) -> io.BytesIO:
        component = self.get(entry)
        downloader = Downloader()
        download_url = self.index.packge_version_download_url(
            component.name, component.version
        )
        downloader.add("src", download_url)
        downloader.add_metadata(
            "component.json", json.dumps(dataclasses.asdict(component), indent=4)
        )
        return downloader.get_as_zipped()
