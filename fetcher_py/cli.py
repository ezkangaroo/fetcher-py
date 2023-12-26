import dataclasses
import logging
import click
import requests
from fetcher_py.fetcher import (
    Fetcher,
)
from click_help_colors import HelpColorsGroup
import json

logging.basicConfig(
    format="[%(levelname)-8s] %(message)s",
    level="DEBUG",
)


@click.group(
    cls=HelpColorsGroup, help_headers_color="yellow", help_options_color="green"
)
def cli():
    """
    Command-line tool for fetching and inspecting package
    artifacts.

    \b
    Package query follows format:
    ----------------------------
        <ecosystem>://<name>@<version>

    \b
    Examples:
    ---------
        - pip://numpy@1.0.0
        - pip://numpy
        - http://example.com/file.zip
        - https://examplessl.com/file.zip
        - git://somegithost.com/user/repo.git
        - git://somegithost.com/user/repo.git@commit_hash
        - git://somegithost.com/user/repo.git@branch
        - git://somegithost.com/user/repo.git@git_tag

    \b
    Command Examples:
    -----------------
        >> get pip://numpy@1.0.0 # json of metadata
        >> get pip://numpy@1.0.0 | jq
        >> download pip://numpy@1.0.0 > artifacts.zip
        >> download pip://numpy@1.0.0 -o some/path/where/to/write/artifacts.zip
    """
    pass


@cli.command()
@click.argument("package_query", metavar="PACKAGE_QUERY")
@click.option(
    "--out", "-o", type=click.Path(), help="Output file path for downloaded package."
)
def download(package_query, out):
    """Download a package based on the provided query.

    \b
    Any artifact (binary or src code) of the package is
    zipped together. Each artifact is placed under directory
    (whose name is artifact kind). Special .metadata directory
    is also created, which has
        .
        - ./metadata/component.json (raw component metadata)
        - ./metadata/urls.txt (url used to download)

    \b
    Note that, it retrieves all artifacts, regardless of host
    machine's os/arch etc. For example, 'numpy' package may have
    had artifact for say, for linux, macOs, windows (and respective
    python versions). We will fetch all artifact regardless of
    compatibility.

    \b
    Examples:
    ---------

    \b
      >> fetcher download pip://numpy@1.26.0 > artifact.zip
      .
      >> fetcher download pip://numpy@1.0.0 --o artifact.zip
      .
      # >> unzip -l artifact.zip
      #
      #  Archive:  artifact.zip
      #   Length       Date    Time    Name
      #  ---------  ---------- -----   ----
      #  1892264    12-24-2023 21:14   bdist_wininst/numpy-1.0.1.dev3460.win32-py2.4.exe
      #    13405    12-24-2023 21:14   .metadata/component.json
      #      185    12-24-2023 21:14   .metadata/urls.txt
      #  ---------                     -------
      #  1905854                       3 files
    """
    fetcher = Fetcher(requests.session())
    if not out:
        stream = fetcher.download_raw(package_query)
        click.echo(stream.getvalue(), nl=False)
    else:
        fetcher.download(package_query, out)
        click.echo(f"wrote file to {out}")


@cli.command()
@click.argument("package_query", metavar="PACKAGE_QUERY")
def get(package_query):
    """Get information about a package based on the provided query.

    \b
    Examples:
    ---------

    \b
      # returns json in stdout, including metadata
      # associated with the package!
      >> fetcher get pip://numpy@1.0.0
      #
      # {
      #     name: ....
      #     version: ...
      #     home_page: ...
      #     ....
      #     raw: ... # <- raw content as seen from registry
      # }

    \b
      # default to latest (if no version is provided)
      >> fetcher get pip://numpy

    \b
      # you can pipe stdout to other tools
      >> fetcher get pip://numpy@1.0.0 | jq
      >> fetcher get pip://numpy@1.0.0 > out_component.txt
    """

    fetcher = Fetcher(requests.session())
    comp = fetcher.get(package_query)
    json_str = json.dumps(dataclasses.asdict(comp))
    click.echo(f"{json_str}")


if __name__ == "__main__":
    cli()
