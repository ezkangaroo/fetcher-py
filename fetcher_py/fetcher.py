import io
import logging
import os
from pathlib import Path
from typing import Dict
import requests
from fetcher_py.component import Component
from fetcher_py.package import Package
from fetcher_py.protocol.git import GitRegistry
from fetcher_py.protocol.url import UrlRegistry
from fetcher_py.registry.brew import BrewRegistry
from fetcher_py.registry.cargo import CargoRegistry
from fetcher_py.registry.composer import ComposerRegistry
from fetcher_py.registry.cpan import CpanRegistry
from fetcher_py.registry.gem import GemRegistry
from fetcher_py.registry.hackage import HackageRegistry
from fetcher_py.registry.npm import NpmRegistry
from fetcher_py.registry.nuget import NuGetRegistry
from fetcher_py.registry.oci import OciRegistry
from fetcher_py.registry.pypi import PypiRegistry
from fetcher_py.registry._registry import Registry

ECOSYSTEM_REGISTRIES: Dict[str, Registry] = {
    "pip": PypiRegistry,
    "npm": NpmRegistry,
    "cargo": CargoRegistry,
    "cpan": CpanRegistry,
    "composer": ComposerRegistry,
    "gem": GemRegistry,
    "hackage": HackageRegistry,
    "http": UrlRegistry,
    "https": UrlRegistry,
    "nuget": NuGetRegistry,
    "brew": BrewRegistry,
    "oci": OciRegistry,
    "git": GitRegistry,
}

logger = logging.getLogger(__name__)


class Fetcher:
    def __init__(self, session: requests.Session):
        """
        Initialize the Fetcher with a requests session.

        Parameters:
        - session: A requests.Session object.
        """
        self.session = session

    def get(self, query) -> Component:
        """
        Get information about a package.

        Parameters:
        - query: Package query string.

        Returns:
        - Component object representing the package.
        """
        package = Package.parse(query)
        return self._get_registry(package.ecosystem).get(package)

    def download_raw(self, query) -> io.BytesIO:
        """
        Download the raw content of a package.

        Parameters:
        - query: Package query string.

        Returns:
        - Raw bytes of the downloaded content.
        """
        package = Package.parse(query)
        return self._get_registry(package.ecosystem).download(package)

    def download(self, query: str, destination: Path):
        """
        Download a package to the specified destination.

        Parameters:
        - query: Package query string.
        - destination: Destination path for downloading the package.
        """
        package = Package.parse(query)
        downloaded_bytes = self._get_registry(package.ecosystem).download(package)

        parent = os.path.dirname(destination)
        if parent != "":
            os.makedirs(parent, exist_ok=True)

        with open(destination, "wb") as file:
            file.write(downloaded_bytes.getvalue())

    def _get_registry(self, ecosystem):
        """
        Get the appropriate registry based on the ecosystem.

        Parameters:
        - ecosystem: Name of the ecosystem (e.g., 'pip').

        Returns:
        - Registry object for the specified ecosystem.
        """
        if ecosystem not in ECOSYSTEM_REGISTRIES:
            raise ValueError(f"Unsupported ecosystem: {ecosystem}")

        return ECOSYSTEM_REGISTRIES[ecosystem](self.session)
