import io
import os
import tempfile
from typing import Optional, Tuple
import zipfile
from fetcher_py.component import Component
from fetcher_py.package import Package
from fetcher_py.registry._registry import Registry
from requests import Session
from git import Repo


class GitRegistry(Registry):
    def __init__(
        self,
        session: Session,
        base_url: Optional[str] = None,
    ):
        super().__init__(session, base_url)

    def reachable(self):
        raise NotImplementedError()

    def get(self, entry: Package) -> Component:
        data = None
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.clone_from(
                entry.name, temp_dir, branch=entry.version, single_branch=True
            )
            try:
                if entry.version:
                    repo.git.checkout(entry.version)

                data = {
                    "name": entry.name,
                    "version": repo.head.object.hexsha,
                    "registry_url": entry.name,
                    "homepage_url": None,
                    "description": None,
                    "declared_licenses": None,
                    "raw": None,
                }

            finally:
                repo.close()

        return Component(**data)

    def raw(self, entry: Package) -> Tuple[Component, bytes]:
        zip_data = io.BytesIO()

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.clone_from(
                entry.name, temp_dir, branch=entry.version, single_branch=True
            )
            try:
                if entry.version:
                    repo.git.checkout(entry.version)
                data = {
                    "name": entry.name,
                    "version": repo.head.object.hexsha,
                    "registry_url": entry.name,
                    "homepage_url": None,
                    "description": None,
                    "declared_licenses": None,
                    "raw": None,
                }

            finally:
                repo.close()

            with zipfile.ZipFile(zip_data, "w") as zip_file:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zip_file.write(file_path, arcname=arcname)

            return Component(**data), zip_data

    def download(self, entry: Package) -> io.BytesIO:
        _, io_bytes = self.raw(entry)
        return io_bytes
