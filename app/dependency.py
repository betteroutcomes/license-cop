from enum import Enum

from app.data_object import *


class DependencyKind(Enum):
    RUNTIME = 1
    DEVELOPMENT = 2

    def __str__(self):
        if self == DependencyKind.RUNTIME:
            return 'runtime'
        elif self == DependencyKind.DEVELOPMENT:
            return 'development'


class Dependency(DataObject):

    def __init__(self, name, kind, number=None):
        self.name = name
        self.kind = kind
        self.number = number

    @staticmethod
    def runtime(name, number=None):
        return Dependency(name, DependencyKind.RUNTIME, number)

    @staticmethod
    def development(name, number=None):
        return Dependency(name, DependencyKind.DEVELOPMENT, number)

    @property
    def is_runtime(self):
        return self.kind == DependencyKind.RUNTIME

    @property
    def is_development(self):
        return self.kind == DependencyKind.DEVELOPMENT

    def __str__(self):
        number = 'latest' if self.number is None else self.number
        return f'[{self.kind}] {self.name}:{number}'

    def __repr__(self):
        return str(self)
