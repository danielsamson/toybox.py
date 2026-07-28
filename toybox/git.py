# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import subprocess

from typing import List
from typing import Dict

from .version import Version
from .url import Url


class Git:
    """Utility methods for git repos."""

    def __init__(self, url: Url):
        """Setup access to the git repo at url."""

        self.url = 'https://' + url.as_string + '.git'
        self.refs = None
        self.tags = None
        self.tag_versions = None
        self.branches = None
        self.head_branch = None
        self.latest_version = None

    def git(self, arguments: str, folder: str = None):
        commands = ['git'] + arguments.split()

        url = self.url.replace('https://', 'https://anonymous:@')
        commands.append(url)

        if folder is not None:
            commands.append(folder)

        try:
            process = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                if str(stdout).startswith('b"usage: git'):
                    # -- git is giving us the usage info back it seems.
                    raise SyntaxError('Invalid git command line')
                else:
                    error = str(stderr)[2:-1]
                    if error.startswith('fatal: not a git repository (or any of the parent directories): .git'):
                        raise RuntimeError('Error: Your project folder needs to be a git repo for certain commands to work correctly. Try `git init` to create one.')

                    # -- Or maybe something else went wrong.
                    error = error.split('\\n')[0]

                    if error == 'remote: Invalid username or password.':
                        raise RuntimeError('Cannot access git repo at \'' + self.url + '\'. Maybe it is private?')
                    else:
                        raise RuntimeError('Error running git: ' + error)

            # -- Output is bracketed with b'' when converted from bytes.
            return str(stdout)[2:-1]
        except RuntimeError:
            raise
        except SyntaxError:
            raise
        except Exception as e:
            raise RuntimeError('Error running git: ' + str(e))

    def listRefs(self) -> Dict[str, str]:
        if self.refs is None:
            self.refs = {}
            for ref in self.git('ls-remote --refs').split('\\n'):
                refs_index = ref.find('refs/')
                if refs_index >= 0:
                    self.refs[ref[refs_index + 5:]] = ref[:40]

        return self.refs

    def listBranches(self) -> Dict[str, str]:
        if self.branches is None:
            self.branches = {}
            refs = self.listRefs()
            for ref in refs.keys():
                if ref.startswith('heads/'):
                    self.branches[ref[6:]] = refs[ref]

        return self.branches

    def getHeadBranch(self) -> str:
        if self.head_branch is None:
            for line in self.git('remote show').split('\\n'):
                if line.startswith('  HEAD branch:'):
                    self.head_branch = line[15:]

            if self.head_branch is None:
                raise RuntimeError('Cannot find head branch for \'' + self.url + '\'.')

        return self.head_branch

    def listTags(self) -> List[str]:
        if self.tags is None:
            self.tags = []
            for ref in self.listRefs().keys():
                if ref.startswith('tags/'):
                    tag = ref[5:]
                    if not tag.startswith('@'):
                        self.tags.append(tag)

        return self.tags

    def listTagVersions(self) -> List[Version]:
        if self.tag_versions is None:
            self.tag_versions = []

            for tag in self.listTags():
                try:
                    self.tag_versions.append(Version(tag))
                except ValueError:
                    pass

            self.tag_versions = sorted(self.tag_versions)

        return self.tag_versions

    def getLatestVersion(self) -> Version:
        if self.latest_version is None:
            all_versions = self.listTagVersions()

            if len(all_versions) > 0:
                self.latest_version = all_versions[-1]

        return self.latest_version

    def getLatestCommitHashForBranch(self, branch_name: str) -> str:
        return self.listBranches().get(branch_name)

    def isABranch(self, name: str) -> bool:
        return name in self.listBranches()

    def isATag(self, name: str) -> bool:
        for tag in self.listTags():
            if tag == name:
                return True

        return False

    def cloneIn(self, tag: str, folder: str):
        self.git('clone --quiet --depth 1 --branch ' + tag, folder)
