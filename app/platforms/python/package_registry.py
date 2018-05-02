import re

from app.package_registry import *
from app.package_version import *
from app.dependency import *


PACKAGE_URI = 'https://pypi.python.org/pypi/{0}/json'
VERSION_URI = 'https://pypi.python.org/pypi/{0}/{1}/json'

DEPENDENCY_REGEX = re.compile(
    r'^(?P<name>[\w\-\.]+)\s*'                              # name
    r'(\(.+\))?\s*'                                         # optional version
    r'(;\s*('                                               # optional semicolon
    r'.*'                                                   # optional attributes
    r'extra\s*==\s*([\'"]|\\")(?P<extra>\w+)([\'"]|\\")'    # optional extra attribute
    r'.*'                                                   # optional attributes
    r')?)?'
)


DEVELOPMENT_DEPENDENCY_KEYWORDS = (
    'test',
    'tests',
    'testing',
    'doc',
    'docs',
    'dev',
    'devel',
    'development',
    'debug',
    'debugging',
    'local'
)


def __dependency_kind(extra):
    if extra in DEVELOPMENT_DEPENDENCY_KEYWORDS:
        return DependencyKind.DEVELOPMENT
    return DependencyKind.RUNTIME


def parse_dependency(string):
    m = DEPENDENCY_REGEX.match(string)
    if m:
        return Dependency(
            name=m.group('name'),
            kind=__dependency_kind(m.group('extra'))
        )
    raise Exception(f'Could not parse dependency: {string}')


class PythonPackageRegistry(PackageRegistry):

    def _fetch_version(self, name, number):
        response = self._session.get(VERSION_URI.format(name, number))
        response.raise_for_status()
        return self.__build_package(response.json())

    def _fetch_latest_version(self, name):
        response = self._session.get(PACKAGE_URI.format(name))
        response.raise_for_status()
        return self.__build_package(response.json())

    def __extract_dependencies(self, data):
        requires_dist = data['requires_dist'] if 'requires_dist' in data else []
        if requires_dist is None:
            requires_dist = []
        return [parse_dependency(i) for i in requires_dist]

    def __filter_dependencies(self, dependencies, kind):
        return [i for i in dependencies if i.kind == kind]

    def __determine_author(self, data):
        info = data['info']
        if 'author' in info:
            if isinstance(info['author'], str) and info['author'] != '':
                return info['author']
        if 'maintainer' in info:
            if isinstance(info['maintainer'], str) and info['maintainer'] != '':
                pass
            else:
                return 'Unknown'

        return 'Unknown'

    def __build_package(self, data):
        info = data['info']
        deps = self.__extract_dependencies(info)
        return PackageVersion(
            name=info['name'],
            number=info['version'],
            licenses=self.__determine_licenses(info),
            runtime_dependencies=self.__filter_dependencies(deps, DependencyKind.RUNTIME),
            development_dependencies=[],#self.__filter_dependencies(deps, DependencyKind.DEVELOPMENT),
            author = self.__determine_author(data)
        )



    def __determine_licenses(self, data):
        license = self.__clean_license(data.get('license'))
        if license:
            return [license]
        classifiers = data.get('classifiers', None)
        if classifiers:
            license_classifiers = [c for c in classifiers if "License" in c]
            license_list = [lc.split('::')[-1].strip() for lc in license_classifiers]
            return license_list

        urls = self.__extract_repository_urls(data)
        return self._find_licenses_in_code_repository_urls(urls)

    def __clean_license(self, string):
        if string:
            license = self.__remove_unknown_token(self.__trim_lines(string))
            if license:
                return license

    def __trim_lines(self, string):
        lines = (i.strip() for i in string.splitlines())
        lines = [l for l in lines if l]
        if lines:
            line = lines[0]
            return f'{line} [...]' if len(lines) > 1 else line

    def __remove_unknown_token(self, string):
        if string and string != 'UNKNOWN':
            return string

    def __extract_repository_urls(self, data):
        keys = ['home_page', 'docs_url', 'download_url', 'bugtrack_url']
        return (self.__remove_unknown_token(data.get(i)) for i in keys if i)
