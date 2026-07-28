# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import os
import platform

from typing import List

from .git import Git
from .version import Version
from .url import Url
from .exceptions import DependencyError
from .utils import Utils
from .paths import Paths


class Dependency:
    """A helper class for toybox dependencies."""

    def __init__(self, url: Url):
        """Create a dependency given a URL and a tag or branch."""

        self.url = url

        self.git = Git(self.url)

        self.versions = []
        self.last_version_installed = None
        self.last_version_resolved = None
        self.box_file = None

    def __str__(self):
        string_version = self.url.as_string + '@'

        if len(self.versions) > 1:
            string_version += '('

        separator = ''
        for version in self.versions:
            string_version += separator
            if version.isLocal():
                string_version += 'local'
            else:
                string_version += version.original_version

            separator = ' '

        if len(self.versions) > 1:
            string_version += ')'

        return string_version

    def subFolder(self) -> str:
        return Paths.escapeOutToyboxPath(os.path.join(self.url.server, self.url.username, self.url.repo_name))

    def toyboxFolder(self) -> str:
        return os.path.join(Paths.toyboxesFolder(), self.subFolder())

    def toyboxBackupFolder(self) -> str:
        return os.path.join(Paths.toyboxesBackupFolder(), self.subFolder())

    def toyboxAssetsFolder(self) -> str:
        return os.path.join(self.toyboxFolder(), 'assets')

    def assetsFolder(self, maybe_sub_folder: str = None) -> str:
        if maybe_sub_folder is None:
            maybe_sub_folder = self.subFolder()

        return os.path.join(Paths.assetsFolder(), maybe_sub_folder)

    def assetsBackupFolder(self, maybe_sub_folder: str = None) -> str:
        if maybe_sub_folder is None:
            maybe_sub_folder = self.subFolder()

        return os.path.join(Paths.toyboxesFolder(), 'assets', maybe_sub_folder)

    def resolveVersion(self) -> Version:
        if self.last_version_resolved is not None:
            return self.last_version_resolved

        branch = None
        versions = None

        try:
            for version in self.versions:
                if version.isLocal():
                    return version
                elif version.isBranch():
                    if branch is not None:
                        raise DependencyError

                    if self.git.isABranch(version.original_version):
                        commit_hash = self.git.getLatestCommitHashForBranch(version.original_version)
                        if commit_hash is None:
                            raise DependencyError

                        branch = Version(version.original_version + '@' + commit_hash)
                else:
                    if branch is not None:
                        raise DependencyError

                    if versions is None:
                        versions = self.git.listTagVersions()

                    versions = version.includedVersionsIn(versions)

            if branch is not None:
                self.last_version_resolved = branch
            elif versions is None:
                raise DependencyError
            else:
                if len(versions) > 0:
                    self.last_version_resolved = versions[-1]
                else:
                    raise DependencyError

            return self.last_version_resolved

        except DependencyError:
            raise DependencyError('Can\'t resolve version with \'' + self.originalVersions() + '\' for \'' + self.url.as_string + '\'.')

    def replaceVersions(self, versions: List[Version]):
        self.versions = []
        self.addVersions(versions)

    def addVersions(self, versions: List[Version]):
        for version in versions:
            if version not in self.versions:
                self.versions.append(version)
                self.last_version_resolved = None

    def existsInBackup(self):
        return os.path.exists(self.toyboxBackupFolder())

    def isATag(self, name: str) -> bool:
        return self.git.isATag(name)

    def isABranch(self, name: str) -> bool:
        return self.git.isABranch(name)

    def originalVersions(self) -> str:
        result: str = ''

        for version in self.versions:
            if len(result) != 0:
                result += ' '

            result += version.original_version

        return result

    def installIn(self, toyboxes_folder: str) -> Version:
        version_resolved = self.resolveVersion()

        if version_resolved is None:
            raise DependencyError('Can\'t resolve version with \'' + self.originalVersions() + '\' for \'' + self.url.as_string + '\'.')

        if self.last_version_installed is not None and self.last_version_installed.original_version == version_resolved.original_version:
            return

        folder = self.toyboxFolder()
        self.deleteToyboxFolder()

        if version_resolved.isLocal():
            system_name = platform.system()
            if system_name == 'Darwin' or system_name == 'Linux':
                # -- On macOs and Linux we can use softlinks to point to a local version of a toybox.
                Utils.softlinkFromTo(version_resolved.original_version, folder)
            else:
                Utils.copyFromTo(version_resolved.original_version, folder)
        else:
            os.makedirs(folder, exist_ok=True)

            self.git.cloneIn(version_resolved.original_version, folder)

        dependency_git_folder = os.path.join(folder, '.git')
        Utils.deleteFolder(dependency_git_folder, force_delete=True)

        self.last_version_installed = version_resolved

        return version_resolved

    def deleteToyboxFolder(self):
        Utils.deleteFolder(self.toyboxFolder())
