# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import os
import webbrowser

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from .git import Git
from .version import Version
from .paths import Paths
from .utils import Utils
from .url import Url


class ToyStore:
    """Access the toybox toystore for easing naming."""

    def __init__(self, force_update: bool = False):
        """Read the toy store from its git repo."""

        update_store: bool = True

        if force_update is False and not Utils.fileOlderThan(ToyStore.storeFilePath(),
                                                             time_in_seconds=(24 * 60 * 60)):
            # -- If the existing store file is less than 24 hours old, we keep it.
            update_store: bool = False

        if update_store:
            ToyStore.updateStoreFromRepo()

        self.store = None

        with open(ToyStore.storeFilePath(), mode="rb") as fp:
            self.store = tomllib.load(fp)

    def maybeUrlForName(self, name: str) -> Url:
        if self.store is not None:
            toybox_entry = self.store.get(name)
            if toybox_entry is not None:
                return toybox_entry["url"]

        return None

    def content(self):
        if self.store is None:
            return

        print('Currently available in the toystore:')

        for name, entry in self.store.items():
            print('   ' + name + ' -> ' + entry['url'])

    def info(self, name):
        if self.store is None or name is None:
            return

        if name not in self.store:
            print('ERROR: There is no toybox named \'' + name + '\' in the toystore.')
            return

        entry = self.store[name]

        print('         url: ' + entry.get('url', 'None provided'))
        print(' description: ' + entry.get('description', 'None provided'))
        print('      author: ' + entry.get('author', 'None provided'))
        print('     license: ' + entry.get('license', 'None provided'))

    def repo(self, name):
        if self.store is None or name is None:
            return

        if name not in self.store:
            print('ERROR: There is no toybox named \'' + name + '\' in the toystore.')
            return

        entry = self.store[name]

        webbrowser.open(entry['url'], new=1)

    @classmethod
    def updateStoreFromRepo(cls) -> None:
        print('Updating the toystore...')
        folder: str = ToyStore.storeFolderPath()

        if os.path.exists(folder):
            Utils.deleteFolder(folder, force_delete=True)

        repo: Git = Git(Url('https://code.malenfant.net/didier/toystore'))

        head_branch = repo.getHeadBranch()
        commit_hash = repo.getLatestCommitHashForBranch(head_branch)

        repo.cloneIn(Version(head_branch + '@' + commit_hash).original_version, folder)

    @classmethod
    def storeFolderPath(cls) -> str:
        return os.path.join(Paths.tempFolder(), 'store')

    @classmethod
    def storeFilePath(cls) -> str:
        return os.path.join(ToyStore.storeFolderPath(), 'toystore.toml')
