import pytest
from fetcher_py.package import Package


@pytest.mark.parametrize(
    "package_spec, expected_result",
    [
        ("pip://name@1", Package(ecosystem="pip", name="name", version="1")),
        ("pip://name@1.1", Package(ecosystem="pip", name="name", version="1.1")),
        ("pip://name@latest", Package(ecosystem="pip", name="name", version="latest")),
        ("pip://name", Package(ecosystem="pip", name="name", version=None)),
    ],
)
def test_package_parse(package_spec, expected_result):
    if expected_result is not None:
        assert Package.parse(package_spec) == expected_result
    else:
        with pytest.raises(ValueError):
            Package.parse(package_spec)


@pytest.mark.parametrize(
    "package_spec",
    [
        "None",
        "",
        " ",
    ],
)
def test_package_parse_should_fail_when_invalid_format(package_spec):
    with pytest.raises(ValueError):
        Package.parse(package_spec)
