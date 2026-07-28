# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import pytest
import sys
import os

# -- We need to import from our parent folder here.
sys.path.append(os.path.join(sys.path[0], '..'))

from toybox.dependency import Dependency       # noqa: E402
from toybox.dependency import DependencyError  # noqa: E402
from toybox.version import Version             # noqa: E402
from toybox.url import Url                     # noqa: E402


class MockGit:
    """Mock of a Git class for the purpose of testing the Dependency class."""

    def __init__(self, tags, branches=[]):
        """Setup access to the git repo at url."""
        self.tags = tags
        self.branches = branches

    def listTags(self):
        return self.tags

    def listTagVersions(self):
        # -- In our case we can use the same data as long as all tags passed to MockGit are version tags.
        tag_versions = []
        for tag in self.listTags():
            tag_versions.append(Version(tag))

        return tag_versions

    def listBranches(self):
        return self.branches

    def isATag(self, name):
        return name in self.tags

    def isABranch(self, name):
        return name in self.branches

    def getLatestCommitHashForBranch(self, branch):
        return 'aaf867d2725ab51a770b036c219e1cfb676e79b7'


@pytest.fixture
def dependency_object():
    dependency = Dependency(Url('code.malenfant.net/didier/MyProject.py'))
    dependency.git = MockGit(['v1.0.0', 'v1.0.2', 'v2.0.0', 'v2.1.0', 'v3.0.0', 'v3.2.3'],
                             {'main': 'aaf867d2725ab51a770b036c219e1cfb676e79b7', 'develop': '10167a78efd194d4984c3e670bec38b8ccaf97eb'})
    return dependency


@pytest.mark.parametrize('versions, expected_result', [
    ([Version('>v1.2.3')], 'v3.2.3'),
    ([Version('>=3.0.0'), Version('<4.0.0')], 'v3.2.3'),
    ([Version('<2.0.0')], 'v1.0.2'),
    ([Version('1.0.0')], 'v1.0.0'),
    ([Version('>v1.0.0'), Version('<2.0.0')], 'v1.0.2'),
    ([Version('>v1.0.0'), Version('<=2.0.0')], 'v2.0.0'),
    ([Version('/' + os.path.join('My', 'Test', 'Folder'))], '/' + os.path.join('My', 'Test', 'Folder')),
    ([Version(os.path.join('F:', 'My', 'Test', 'Folder'))], os.path.join('F:', 'My', 'Test', 'Folder')),
    ([Version('main')], 'main')
])

def test_resolveVersion(dependency_object, versions, expected_result):  # noqa: E304
    dependency_object.addVersions(versions)
    assert dependency_object.resolveVersion().original_version == expected_result


def test_resolveVersion_no_versions_added(dependency_object):
    with pytest.raises(DependencyError):
        dependency_object.resolveVersion()


def test_resolveVersion_unresolvable(dependency_object):
    dependency_object.addVersions([Version('test')])
    with pytest.raises(DependencyError):
        dependency_object.resolveVersion()


@pytest.mark.parametrize('versions, expected_results', [
    ([Version('develop')], [Version('develop')]),
    ([Version('>1.0.0'), Version('<3.0.0'), Version('<2.5.0')], [Version('>1.0.0'), Version('<3.0.0'), Version('<2.5.0')]),
    ([Version('>1.0.0'), Version('<3.0.0'), Version('<2.5.0'), Version('<3.0.0')], [Version('>1.0.0'), Version('<3.0.0'), Version('<2.5.0')]),
    ([Version('/' + os.path.join('My', 'Local', 'Folder'))], [Version('/' + os.path.join('My', 'Local', 'Folder'))]),
    ([Version(os.path.join('J:', 'My', 'Local', 'Folder'))], [Version(os.path.join('J:', 'My', 'Local', 'Folder'))])
])

def test_addVersions(dependency_object, versions, expected_results):  # noqa: E304
    dependency_object.addVersions(versions)
    assert dependency_object.versions == expected_results
