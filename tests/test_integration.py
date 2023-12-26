import zipfile
import requests
from fetcher_py.fetcher import Fetcher
import pytest


@pytest.mark.integration
@pytest.mark.parametrize(
    "query, name, version, license",
    [
        ("pip://numpy@1.0", "numpy", "1.0", "BSD"),
        ("npm://express@4.0.0", "express", "4.0.0", "MIT"),
        ("cargo://axum@0.1.0", "axum", "0.1.0", None),
        ("gem://coulda@0.7.1", "coulda", "0.7.1", None),
        ("hackage://aeson@2.2.1.0", "aeson", "2.2.1.0", "BSD-3-Clause"),
        ("composer://psr/http-message@2.0", "psr/http-message", "2.0", None),
        ("nuget://StackExchange.Redis@2.7.10", "StackExchange.Redis", "2.7.10", "MIT"),
        ("brew://bat", "bat", None, "Apache-2.0 or MIT"),
        (
            "oci://ghcr.io/wolfv/conda-forge/linux-64/xtensor:0.9.0-0",
            "ghcr.io/wolfv/conda-forge/linux-64/xtensor:0.9.0-0",
            None,
            None,
        ),
        (
            "git://https://github.com/sharkdp/bat.git@v0.21.0",
            "https://github.com/sharkdp/bat.git",
            "405e5f74602d8f680168ef52350150921c696d54",
            None,
        ),
    ],
)
def test_integration(query, name, version, license):
    session = requests.session()
    fetcher = Fetcher(session)
    comp = fetcher.get(query)

    assert comp.name == name
    assert comp.declared_licenses == license
    if version is not None:
        assert comp.version == version
    if not query.startswith("git://"):
        assert comp.raw is not None

    comp = fetcher.download_raw(query)
    with zipfile.ZipFile(comp, "r") as zip_file:
        assert zip_file.testzip() is None
        assert ".metadata/component.json" in zip_file.namelist()

        # more than 1 directory
        directories = {
            name.split("/")[0] for name in zip_file.namelist() if "/" in name
        }
        assert len(directories) > 1

        # Check if both directories are not empty
        for directory in directories:
            files_in_directory = [
                name for name in zip_file.namelist() if name.startswith(f"{directory}/")
            ]
            assert files_in_directory, f"Directory '{directory}' is empty"
