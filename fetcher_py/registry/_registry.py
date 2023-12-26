from abc import ABC, abstractmethod
from requests import Session
from fetcher_py.component import Component

from fetcher_py.package import Package


class Registry(ABC):
    def __init__(self, session: Session, base_url: str):
        self.session = session
        self.base_url = base_url

    @abstractmethod
    def reachable(self) -> bool:
        pass

    @abstractmethod
    def get(self, entry: Package) -> Component:
        pass

    @abstractmethod
    def download(self, entry: Package) -> bytes:
        pass
