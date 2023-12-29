import dataclasses
import io
import json
import logging
import tempfile
from typing import Optional
import zipfile
from fetcher_py.component import Component
from fetcher_py.package import Package
from ._registry import Registry
from requests import Session
import oras.provider
import os

logger = logging.getLogger(__name__)


class MyProvider(oras.provider.Registry):
    def inspect(self, *args, **kwargs):
        container = super().get_container(kwargs["target"])
        super().load_configs(container)
        return super().get_manifest(container)

    def pull(self, *args, **kwargs):
        container = super().get_container(kwargs["target"])
        super().load_configs(container)
        manifest = super().get_manifest(container)
        outdir = kwargs.get("outdir")
        files = []
        for layer in manifest.get("layers", []):
            filename = (layer.get("annotations") or {}).get(
                oras.defaults.annotation_title, layer["digest"]
            )
            outfile = oras.utils.sanitize_path(outdir, os.path.join(outdir, filename))
            self.download_blob(container, layer["digest"], outfile)
            files.append(outfile)

        return files


class OciRegistry(Registry):
    def __init__(
        self,
        session: Session,
        base_url: Optional[str] = None,
    ):
        self.provider = MyProvider()
        super().__init__(session, base_url)

    def reachable(self):
        return None

    def get(self, entry: Package) -> Component:
        data = self.provider.inspect(target=entry.name)
        return Component(
            name=entry.name,
            version=None,
            registry_url=None,
            homepage_url=None,
            declared_licenses=None,
            description=None,
            raw=data,
        )

    def raw(self, entry: Package) -> io.BytesIO:
        zip_data = io.BytesIO()
        component = self.get(entry)
        with tempfile.TemporaryDirectory() as temp_dir:
            # write metadata
            metadata_dir = os.path.join(temp_dir, ".metadata")
            os.makedirs(metadata_dir)
            component_json_path = os.path.join(metadata_dir, "component.json")
            with open(component_json_path, "w") as json_file:
                json.dump(dataclasses.asdict(component), json_file, indent=2)

            # write blobs
            dist_dir = os.path.join(temp_dir, "dist")
            os.makedirs(dist_dir)
            self.provider.pull(target=entry.name, outdir=dist_dir)
            with zipfile.ZipFile(zip_data, "w") as zip_file:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zip_file.write(file_path, arcname=arcname)

        return component, zip_data

    def download(self, entry: Package) -> io.BytesIO:
        _, io_bytes = self.raw(entry)
        return io_bytes
