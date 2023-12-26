from dataclasses import dataclass


@dataclass
class Package:
    ecosystem: str
    name: str
    version: str = None

    def raise_for_resolved(self):
        if self.version is None or self.version.strip() == "":
            raise ValueError(
                f"expected to have version for {self.name} but got: {self.version}!"
            )

    @classmethod
    def parse(cls, package_spec):
        parts = package_spec.rsplit("@", 1)

        if len(parts) == 2:
            identifier, version = parts
        else:
            identifier, version = package_spec, None

        if version == "null":
            version = None

        identifier_parts = identifier.split("://", 1)
        if len(identifier_parts) != 2:
            raise ValueError("Invalid package identifier format")

        ecosystem, rest = identifier_parts
        return cls(ecosystem=ecosystem, name=rest, version=version)
