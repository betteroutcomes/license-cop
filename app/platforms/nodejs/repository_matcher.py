import json

from app.dependency import *
from app.repository_matcher import *
from app.manifest import *
from app.platforms.nodejs.shared import parse_dependencies, parse_author


class NodejsRepositoryMatcher(RepositoryMatcher):

    def __init__(self):
        super().__init__(['package.json'])

    def _fetch_manifest(self, repository, match):
        package_json = match.paths[0]

        data = json.loads(repository.read_text_file(package_json))

        return Manifest(
            platform='Node.js',
            repository=repository,
            paths=match.paths,
            runtime_dependencies=parse_dependencies(data, DependencyKind.RUNTIME),
            development_dependencies= [],#parse_dependencies(data, DependencyKind.DEVELOPMENT)
            author=parse_author(data)
        )
