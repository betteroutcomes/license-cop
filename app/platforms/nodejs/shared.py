from app.dependency import *


def parse_dependencies(data, kind):
    key = 'dependencies' if kind == DependencyKind.RUNTIME else 'devDependencies'
    if key not in data:
        return []

    #Need to parse what versions of these packages we are using
    package_version_dict = data[key]
    #Now, need to account for semantic versioning modifier symbols (i.e. ^, ~, *)
    return [Dependency(package_name, kind, version) for package_name,version in package_version_dict.items()]
#
# def determine_version_number(version_string):
#     if version_string = '*' or version_string = 'x':
#         return None #Since right now if no version is specified for dep we use latest
#     if version_string.startswith('^'):
#         version_string_without_caret = version_string[1:]
#         #Now, only want major and minor versions.
#         index_of_second_period = version_string_without_caret.rfind('.')
#         return version_string_without_caret[:index_of_second_period]
#

