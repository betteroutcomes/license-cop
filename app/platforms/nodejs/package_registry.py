import re

from app.package_registry import *
from app.package_version import *
from app.dependency import *
from app.platforms.nodejs.shared import parse_dependencies


VERSION_URI = 'http://registry.npmjs.org/{0}/{1}'
PACKAGE_URI = 'http://registry.npmjs.org/{0}'

SCOPED_PACKAGE_REGEX = r'@[\w\-\.]+/[\w\-\.]+'


class NodejsPackageRegistry(PackageRegistry):

    def _fetch_version(self, name, number):
        # There's a bug in the Node.js registry API that prevents
        # regular (and much more efficient) queries to be performed
        # for scoped package names (ex: @foo/bar). Hence, we need to
        # implement a workaround here.
        # Please refer to: https://github.com/npm/registry/issues/34
        if self.__scoped_package(name):
            return self.__fetch_version_for_scoped_package(name, number)
        version_data = self.__fetch_version_data(name, number)
        return self.__build_version(version_data)

    def _fetch_latest_version(self, name):
        return self._fetch_version(name, 'latest')

    def __fetch_version_for_scoped_package(self, name, number):
        package_data = self.__fetch_package_data(name)
        version_data = self.__extract_version_data(package_data, name, number)
        return self.__build_version(version_data)

    def __fetch_version_data(self, name, number):
        response = self._session.get(VERSION_URI.format(name, number))
        response.raise_for_status()
        return response.json()

    def __extract_version_data(self, package_data, name, number):
        if number == 'latest':
            number = package_data['dist-tags']['latest']
        if number in package_data['versions']:
            return package_data['versions'][number]
        raise PackageVersionNotFoundError(
            f'Could not find package version {name}:{number}.')

    def __fetch_package_data(self, name):
        name = self.__normalize_scoped_package_name(name)
        response = self._session.get(PACKAGE_URI.format(name))
        response.raise_for_status()
        return response.json()

    def __scoped_package(self, name):
        return re.match(SCOPED_PACKAGE_REGEX, name) is not None

    def __normalize_scoped_package_name(self, name):
        return name.replace('/', '%2F')

    def __determine_author(self, data):
        if 'author' in data:
            if 'name' in data['author']:
                return data['author']['name']
            if 'email' in data['author']:
                return data['author']['email']
            if data['author'] and isinstance(data['author'], str) and data['author'] != '':
                return data['author']
        if 'maintainers' in data:
            maintainer_list = [maintainer.get('name', maintainer.get('email', 'Unknown')) for maintainer in data['maintainers']]
            maintainer_string = ", ".join(maintainer_list)
            return maintainer_string
        return 'Unknown'

    def __build_version(self, data):

        foo = self.__determine_author(data)
        if not isinstance(foo, str):
            import pdb; pdb.set_trace()

        return PackageVersion(
            name=data['name'],
            number=data['version'],
            licenses=self.__determine_licenses(data),
            runtime_dependencies=parse_dependencies(data, DependencyKind.RUNTIME),
            development_dependencies= [],#parse_dependencies(data, DependencyKind.DEVELOPMENT),
            author = self.__determine_author(data)
        )

    def __determine_licenses(self, data):
        licenses = self.__extract_licenses(data)
        if not licenses:
            urls = self.__extract_repository_urls(data)
            return self._find_licenses_in_code_repository_urls(urls)
        return licenses

    def __extract_licenses(self, data):
        if 'license' in data:
            return self.__parse_license_field(data['license'])
        elif 'licenses' in data:
            return self.__parse_license_field(data['licenses'])
        return []

    def __parse_license_field(self, data):
        licenses = []
        if isinstance(data, str):
            licenses.append(data)
        if isinstance(data, list):
            licenses.extend(self.__try_extract_field(i, 'type') for i in data)
        return list(filter(None, licenses))

    def __extract_repository_urls(self, data):
        urls = []
        if 'repository' in data:
            urls.extend(self.__parse_repository_field(data['repository']))
        if 'repositories' in data:
            urls.extend(self.__parse_repository_field(data['repositories']))
        if 'homepage' in data:
            urls.extend(self.__parse_homepage_field(data['homepage']))
        return urls

    def __parse_repository_field(self, data):
        urls = []
        if isinstance(data, str):
            urls.append(data)
        if isinstance(data, dict) and 'url' in data:
            urls.append(data['url'])
        if isinstance(data, list):
            urls.extend(self.__try_extract_field(i, 'url') for i in data)
        return list(filter(None, urls))

    def __parse_homepage_field(self, data):
        urls = []
        if isinstance(data, str):
            urls.append(data)
        elif isinstance(data, list):
            urls.extend(data)
        return list(filter(None, urls))

    def __try_extract_field(self, data, key):
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            if key in data and isinstance(data[key], str):
                return data[key]
