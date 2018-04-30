from collections import deque

from app.dependency_resolution import *


class DependencyResolver:
    def __init__(self, registry):
        self.__registry = registry
        self.__visited_dependencies = set()

    def resolve(self, dependency, max_depth=None, runtime_only=False):
        root = self.__build_node(dependency)
        nodes_to_expand = deque([root])

        while nodes_to_expand:
            current_node = nodes_to_expand.popleft()
            if self.__exceeds_max_depth(current_node, max_depth):
                break
            nodes_to_expand.extend(self.__expand_node(current_node, runtime_only))

        return root

    def __expand_node(self, current_node, runtime_only):
        for dependency in current_node.dependencies(runtime_only):
            child = self.__build_node(dependency)
            current_node.add_child(child)

            if child.has_dependencies(runtime_only):
                if dependency not in self.__visited_dependencies:
                    self.__visited_dependencies.add(dependency)
                    yield child
                else:
                    child.hide()

    def __exceeds_max_depth(self, node, max_depth):
        return max_depth is not None and self.__depth(node) >= max_depth

    @staticmethod
    def __depth(node):
        depth = 0
        while not node.is_root:
            node = node.parent
            depth += 1
        return depth

    def __build_node(self, dependency):
        try:
            version = self.__fetch_version(dependency)
        except PackageVersionNotFoundError as e:
            version = PackageVersionNotFound(dependency.name, dependency.number)
        return DependencyResolution(version, dependency.kind)

    def __fetch_version(self, dependency):
        #import pdb; pdb.set_trace()
        if dependency.number is not None:
            return self.__registry.fetch_version(dependency.name, dependency.number)
        else:
            return self.__registry.fetch_latest_version(dependency.name)
