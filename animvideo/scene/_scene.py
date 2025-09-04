import abc
from animvideo.config import Config
from typing import Callable

class Scene(abc.ABC):
    def __init__(self, config: Config):
        self.config = config
        self.create()

    @property
    @abc.abstractmethod
    def time(self) -> float:
        ...

    @time.setter
    @abc.abstractmethod
    def time(self, value: float):
        ...

    @abc.abstractmethod
    def create(self):
        ...

    @abc.abstractmethod
    def save(self, filename: str):
        ...

    @abc.abstractmethod
    def tobytes(self) -> bytes:
        ...

    @abc.abstractmethod
    def consume_bytes(self, consumer: Callable[[bytes], int]):
        ...
