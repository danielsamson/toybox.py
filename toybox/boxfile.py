# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import json
import os

from typing import List
from typing import Dict

from .url import Url
from .dependency import Dependency
from .version import Version


class Boxfile:
    """Read and parse a toybox config file."""

    def __init__(self, boxfile_folder: str, empty_if_does_not_exist: bool = False):
        """Read the Boxfile for the current folder."""

        self.boxfile_path = os.path.join(boxfile_folder, 'Boxfile')

        self.url_to_string = {}
        self.json_content = {}
        self.json_toyboxes = None
        self.json_config = None
        self.json_installed = None
        self.was_modified = False
        self.installed_versions_modified = []

        if not os.path.exists(self.boxfile_path):
            if empty_if_does_not_exist is False:
                raise RuntimeError('No Boxfile found in \'' + boxfile_folder + '\'.')

            # -- If we can't find it we may still create it later.
            return

        try:
            with open(self.boxfile_path, 'r') as file:
                self.json_content = json.load(file)
        except Exception as e:
            raise SyntaxError('Malformed JSON in Boxfile \'' + self.boxfile_path + '\'.\n' + str(e) + '.')

        self.was_modified = Boxfile.maybeConvertOldBoxfile(self.json_content)

        for key in self.json_content.keys():
            value = self.json_content[key]
            value_type = type(value).__name__

            if value_type == 'dict':
                if key == 'toyboxes':
                    self.json_toyboxes = value
                    continue
                elif key == 'config':
                    self.json_config = value
                    continue
                elif key == 'installed':
                    self.json_installed = value
                    continue

            raise SyntaxError('Incorrect format for Boxfile \'' + self.boxfile_path + '\'.\nMaybe you need to upgrade toybox?')

        if self.json_toyboxes is not None:
            for toyboxes_url in self.json_toyboxes.keys():
                self.url_to_string[Url(toyboxes_url)] = toyboxes_url

    def stringForUrl(self, url: Url) -> str:
        return self.url_to_string.get(url)

    def addDependencyWithURLAt(self, url: Url, at: str):
        if self.json_toyboxes is None:
            self.json_toyboxes = self.json_content['toyboxes'] = {}

        self.json_toyboxes[url.as_string] = at
        self.url_to_string[url] = url.as_string

        self.was_modified = True

    def removeDependencyWithURL(self, url: Url):
        toyboxes_url: str = None

        if self.json_toyboxes is not None:
            toyboxes_url = self.stringForUrl(url)

        if toyboxes_url is None:
            raise SyntaxError('Couldn\'t find any dependency for URL \'' + url.as_string + '\'.')

        self.json_toyboxes.pop(toyboxes_url, None)

        if self.json_installed is not None:
            self.json_installed.pop(url.as_string, None)

        self.url_to_string.pop(url)

        self.was_modified = True

    def urls(self) -> List[str]:
        return list(self.url_to_string.keys())

    def versionsForUrl(self, url: Url) -> List[Version]:
        toyboxes_url: str = self.stringForUrl(url)
        if toyboxes_url is None:
            return []

        versions_string: str = self.json_toyboxes[toyboxes_url]
        separated_versions = versions_string.split(' ')
        if len(separated_versions) > 3:
            raise SyntaxError('Malformed version string \'' + versions_string + '\'. Too many versions.')

        new_versions: List[Version] = []
        for version in separated_versions:
            if len(version) == 0:
                continue

            for version in Version.maybeRangeFromIncompleteNumericVersion(version):
                new_version = Version(version)
                if new_version not in new_versions:
                    new_versions.append(new_version)

        return new_versions

    def setLuaImport(self, lua_import_file: str):
        if self.json_config is None:
            self.json_config = self.json_content['config'] = {}

        self.json_config['lua_import'] = lua_import_file

        self.was_modified = True

    def setAssetsSubFolder(self, sub_folder: str):
        if self.json_config is None:
            self.json_config = self.json_content['config'] = {}

        self.json_config['assets_sub_folder'] = sub_folder

        self.was_modified = True

    def setMakefile(self, makefile_path: str):
        if self.json_config is None:
            self.json_config = self.json_content['config'] = {}

        self.json_config['makefile'] = makefile_path

        self.was_modified = True

    def setIncludeHeader(self, header_path: str):
        if self.json_config is None:
            self.json_config = self.json_content['config'] = {}

        self.json_config['include_header'] = header_path

        self.was_modified = True

    def maybeInstalledVersionForUrl(self, url: Url) -> Version:
        if self.json_installed:
            version: str = self.json_installed.get(url.as_string)

            if version is not None:
                return Version(version)

        return None

    def setInstalledVersionForDependency(self, dep: Dependency, version: Version):
        if self.json_installed is None:
            self.json_installed = self.json_content['installed'] = {}

        self.json_installed[dep.url.as_string] = str(version)

        self.installed_versions_modified.append(dep.url.as_string)
        self.was_modified = True

    def maybeLuaImportFile(self) -> str:
        if self.json_config:
            return self.json_config.get('lua_import')

        return None

    def maybeAssetsSubFolder(self) -> str:
        if self.json_config:
            return self.json_config.get('assets_sub_folder')

        return None

    def maybeIncludeHeader(self) -> str:
        if self.json_config:
            return self.json_config.get('include_header')

        return None

    def maybeMakefile(self) -> str:
        if self.json_config:
            return self.json_config.get('makefile')

        return None

    def saveIfModified(self):
        if not self.was_modified:
            return

        if len(self.installed_versions_modified) != 0:
            urls_to_remove = []

            for url in self.json_installed.keys():
                if url not in self.installed_versions_modified:
                    urls_to_remove.append(url)

            for url in urls_to_remove:
                self.json_installed.pop(url, None)

        out_file = open(self.boxfile_path, 'w')
        json.dump(self.json_content, out_file, indent=4)

        out_file.close()

    def dependencies(self) -> List[Dependency]:
        deps: List[Dependency] = []

        for url in self.urls():
            dep: Dependency = Dependency(url)
            dep.addVersions(self.versionsForUrl(url))
            deps.append(dep)

        return deps

    @classmethod
    def boxfileForDependency(cls, dep: Dependency):
        return Boxfile(dep.toyboxFolder(), empty_if_does_not_exist=True)

    @classmethod
    def maybeConvertOldBoxfile(cls, json_content: Dict[str, str]) -> bool:
        old_keys = {}

        for key in json_content.keys():
            value = json_content[key]

            if type(value).__name__ == 'str':
                old_keys[key] = value

        if len(old_keys) == 0:
            return False

        toyboxes = json_content.get('toyboxes')
        if toyboxes is None:
            toyboxes = json_content['toyboxes'] = {}

        for old_key in old_keys.keys():
            toyboxes[old_key] = old_keys[key]
            json_content.pop(old_key, None)

        return True
