# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import os
import getopt
import shutil

from pathlib import Path
from typing import List

from .__about__ import __version__
from .boxfile import Boxfile
from .exceptions import ArgumentError
from .version import Version
from .dependency import Dependency
from .git import Git
from .paths import Paths
from .utils import Utils
from .files import Files
from .url import Url
from .toystore import ToyStore


class Toybox:
    """A Lua, C and asset dependency manager for the Playdate SDK."""

    def __init__(self, args):
        """Initialise toybox based on user configuration."""

        self.box_file = None
        self.dependencies = []
        self.only_update = []
        self.installed_a_local_toybox = False
        self.local_update_folder = None
        self.force_mode = False
        self.command = None
        self.argument = None
        self.second_argument = None

        try:
            # -- Gather the arguments
            opts, other_arguments = getopt.getopt(args, 'hfl:', ['help', 'debug', 'force', 'local='])

            for o, a in opts:
                if o in ('-h', '--help'):
                    self.command = 'help'
                    return
                elif o in ('-f', '--force'):
                    self.force_mode = True
                elif o in ('-l', '--local'):
                    if a is None:
                        raise ArgumentError('Missing folder argument for --local option.')

                    if not os.path.exists(a):
                        raise ArgumentError('Cannot find folder \'' + a + '\' for --local option.')

                    self.local_update_folder = a
                elif o in ('--debug'):
                    # -- We ignore this argument because it was already dealt with in the calling main() code.
                    continue

            if len(other_arguments) == 0:
                raise SyntaxError('Expected a command! Maybe start with `toybox help`?')

            number_of_arguments = len(other_arguments)

            i = 0
            argument = other_arguments[i]
            if len(argument):
                self.command = argument
            i += 1

            if i != number_of_arguments:
                argument = other_arguments[i]
                if len(argument):
                    self.argument = argument
                i += 1
                if i != number_of_arguments:
                    argument = other_arguments[i]
                    if len(argument):
                        self.second_argument = argument
                        i += 1

            if i != number_of_arguments:
                raise ArgumentError('Too many commands on command line.')

        except getopt.GetoptError:
            raise ArgumentError('Error reading arguments. Maybe start with `toybox help`?')

    def main(self):
        switch = {
            'help': self.printUsage,
            'version': Toybox.printVersion,
            'info': self.printInfo,
            'add': self.addDependency,
            'remove': self.removeDependency,
            'update': self.update,
            'check': self.checkForUpdates,
            'store': self.store,
            'set': self.set,
            'setupMakefile': self.setupMakefile
        }

        if self.command is None:
            print('No command found.\n')
            Toybox.printUsage()
            return

        method = switch.get(self.command)
        if method is None:
            raise ArgumentError('Unknow command \'' + self.command + '\'.')

        method()

        Toybox.checkForToyboxPyUpdates(self.force_mode)

    def printUsage(self):
        method = None

        if self.argument is not None:
            switch = {
                'topics': Toybox.printTopics,
                'set': Toybox.printSetUsage,
                'license': Toybox.printLicense,
                'store': Toybox.printStoreUsage
            }

            method = switch.get(self.argument)
            if method is None:
                raise ArgumentError('Error: Unknown topic \'' + self.argument + '\'.')

            method()
            return

        Toybox.printVersion()
        print('')
        print('Usage:')
        print('   toybox <options> <command> <arguments>')
        print('')
        print('The following commands are supported:')
        print('')
        print('   help <topic>             - Show a help message. topic is optional (use \'help topics\' for a list).')
        print('   version                  - Get the current version.')
        print('   info                     - List your current dependencies.')
        print('   add <name/url> <version> - Add a dependency (version is optional).')
        print('   remove <name/url>        - Remove a dependency.')
        print('   update <name/url>        - Update a dependency or all dependencies if no argument is provided.')
        print('   check                    - Check for updated toyboxes.')
        print('   store <subcommand>       - Get info about the toystore (use \'help store\' for more info).')
        print('   set <name> <value>       - Set a configuration value for this toybox.')
        print('   setupMakefile            - Setup a basic makefile project for using C toyboxes.')
        print('')
        print('The following options are supported:')
        print('')
        print('   --help/-h                - Show a help message.')
        print('   --force/-f               - Forces the execution of the update command, even if dependencies are up to date.')
        print('   --local/-l <folder>      - Update the dependencies as local, if found in this folder.')
        print('   --debug                  - Enable extra debugging information.')
        print('')

    def printInfo(self, folder: str = None, already_displayed: List[Url] = []):
        if folder is None:
            self.box_file = box_file_for_folder = Boxfile(Paths.boxfileFolder())
            print('Resolving dependencies...')
        else:
            box_file_for_folder = Boxfile(folder, empty_if_does_not_exist=True)

        dependencies = box_file_for_folder.dependencies()
        if len(dependencies) == 0 and self.box_file == box_file_for_folder:
            print('Boxfile is empty.')
            return

        for dep in dependencies:
            if dep.url in already_displayed:
                continue

            already_displayed.append(dep.url)

            info_string = '       - ' + str(dep) + ' -> '

            dep_folder = dep.toyboxFolder()
            dep_folder_exists = os.path.exists(dep_folder)

            version_installed: Version = self.box_file.maybeInstalledVersionForUrl(dep.url)
            if dep_folder_exists and version_installed is not None:
                info_string += str(version_installed)
            elif dep_folder_exists:
                info_string += 'Unknown version.'
            else:
                info_string += 'Not installed.'

            print(info_string)

            if dep_folder_exists:
                self.printInfo(dep_folder, already_displayed)

    def checkForUpdates(self, folder: str = None, already_displayed: List[Url] = []) -> bool:
        if folder is None:
            self.box_file = box_file_for_folder = Boxfile(Paths.boxfileFolder())
            print('Resolving dependencies...')
        else:
            box_file_for_folder = Boxfile(folder, empty_if_does_not_exist=True)

        dependencies = box_file_for_folder.dependencies()
        if len(dependencies) == 0 and self.box_file == box_file_for_folder:
            print('Boxfile is empty.')
            return

        something_needs_updating = False

        for dep in dependencies:
            if dep.url in already_displayed:
                continue

            already_displayed.append(dep.url)

            version_available = dep.resolveVersion()
            if version_available is None:
                continue

            dep_folder = dep.toyboxFolder()
            if os.path.exists(dep_folder) is False:
                print('       - ' + str(dep) + ' -> Version ' + str(version_available) + ' is available.')
                something_needs_updating = True
                continue

            version_installed: Version = self.box_file.maybeInstalledVersionForUrl(dep.url)
            if version_installed is None:
                print('       - ' + str(dep) + ' -> Version ' + str(version_available) + ' is available.')
                something_needs_updating = True
            else:
                if version_installed != version_available:
                    if version_available.isLocal():
                        print('       - ' + str(dep) + ' -> Local version not installed.')
                    elif version_available.isBranch():
                        print('       - ' + str(dep) + ' -> A more recent commit is available.')
                    else:
                        print('       - ' + str(dep) + ' -> Version ' + str(version_available) + ' is available.')

                    something_needs_updating = True

            something_needs_updating |= self.checkForUpdates(dep_folder, already_displayed)

        if folder is None and something_needs_updating is False:
            print('You\'re all up to date.')

        return something_needs_updating

    def addDependency(self):
        if self.argument is None:
            raise SyntaxError('Expected an argument to \'add\' command.')

        url: Url = Toybox.urlFromArgument(self.argument, self.force_mode)
        at: str = self.second_argument

        if at is None:
            dep: Dependency = Dependency(url)
            latest_version: str = dep.git.getLatestVersion()
            if latest_version is None or latest_version.majorVersion() is None:
                at = dep.git.getHeadBranch()
            else:
                at = str(latest_version.majorVersion())

        self.box_file = Boxfile(Paths.boxfileFolder(), empty_if_does_not_exist=True)
        self.box_file.addDependencyWithURLAt(url, at)
        self.box_file.saveIfModified()

        info_string = 'Added a dependency for \'' + self.argument + '@' + at + '\'.'

        print(info_string)

    def removeDependency(self):
        if self.argument is None:
            raise SyntaxError('Expected an argument to \'remove\' command.')

        url = Toybox.urlFromArgument(self.argument, self.force_mode)

        self.box_file = Boxfile(Paths.boxfileFolder())
        self.box_file.removeDependencyWithURL(url)
        self.box_file.saveIfModified()

        dep = Dependency(url)
        dep.deleteToyboxFolder()

        print('Removed a dependency for \'' + self.argument + '\'.')

    def set(self):
        if self.argument is None:
            raise ArgumentError('Expected a name argument to \'set\' command.')

        switch = {
            'lua_import': self.setLuaImport,
            'assets_sub_folder': self.setAssetsSubFolder,
            'makefile': self.setMakefile,
            'include_header': self.setIncludeHeader
        }

        if self.argument is None:
            raise ArgumentError('Expected a value to set for \'' + self.argument + '\'.')

        method = switch.get(self.argument)
        if method is None:
            raise ArgumentError('Unknown value \'' + self.argument + '\' for set command.')

        method()

    def setLuaImport(self):
        if not os.path.exists(self.second_argument):
            raise ArgumentError('Cannot find Lua file \'' + self.second_argument + '\'.')

        self.box_file = Boxfile(Paths.boxfileFolder(), empty_if_does_not_exist=True)
        self.box_file.setLuaImport(self.second_argument)
        self.box_file.saveIfModified()

        print('Set Lua import file to \'' + self.second_argument + '\'.')

    def setAssetsSubFolder(self):
        if not os.path.exists(self.second_argument):
            raise ArgumentError('Cannot find asset folder \'' + self.second_argument + '\'.')

        self.box_file = Boxfile(Paths.boxfileFolder(), empty_if_does_not_exist=True)
        self.box_file.setAssetsSubFolder(self.second_argument)
        self.box_file.saveIfModified()

        print('Set assets sub folder path to \'' + self.second_argument + '\'.')

    def setMakefile(self):
        if not os.path.exists(self.second_argument):
            raise ArgumentError('Cannot find makefile \'' + self.second_argument + '\'.')

        self.box_file = Boxfile(Paths.boxfileFolder(), empty_if_does_not_exist=True)
        self.box_file.setMakefile(self.second_argument)
        self.box_file.saveIfModified()

        print('Set makefile path to \'' + self.second_argument + '\'.')

    def setIncludeHeader(self):
        if not os.path.exists(self.second_argument):
            raise ArgumentError('Cannot find include file \'' + self.second_argument + '\'.')

        self.box_file = Boxfile(Paths.boxfileFolder(), empty_if_does_not_exist=True)
        self.box_file.setIncludeHeader(self.second_argument)
        self.box_file.saveIfModified()

        print('Set include header path to \'' + self.second_argument + '\'.')

    def store(self):
        if self.argument is None:
            raise ArgumentError('Expected a argument to \'store\' command.')

        switch = {
            'content': Toybox.storeContent,
            'info': Toybox.storeInfo,
            'repo': Toybox.storeRepo
        }

        method = switch.get(self.argument)
        if method is None:
            raise ArgumentError('Unknown argument \'' + self.argument + '\' for store command.')

        method(self.second_argument, self.force_mode)

    def installDependency(self, dep: Dependency, force_install: bool = False):
        if self.local_update_folder is not None:
            maybe_local_path = os.path.join(self.local_update_folder, dep.url.repo_name)
            if os.path.exists(maybe_local_path):
                # -- If we have a local update folder and this dep exists in it then we force install it.
                dep.replaceVersions([Version(maybe_local_path)])
                force_install = True

        dependency_is_new: bool = True
        for other_dep in self.dependencies:
            if other_dep.url == dep.url:
                other_dep.addVersions(dep.versions)
                dep = other_dep
                dependency_is_new = False

        existing_version: Version = self.box_file.maybeInstalledVersionForUrl(dep.url)
        if existing_version is None:
            # -- If we can't find an existing version then let's force install.
            force_install = True
        elif force_install is False and (len(self.only_update) == 0 or dep.url in self.only_update):
            # -- If there is no list of dependencies to only update,
            # -- or if this one is on the list let's try and install.
            force_install = self.force_mode

        can_copy_dep: bool = force_install is False and dep.existsInBackup() and dep.resolveVersion() == existing_version
        if can_copy_dep:
            # -- If we already had the same version installed, we can just copy it.
            self.copyToyboxFromBackup(dep)
            self.copyAssetsFromBackupIfAny(dep)
        else:
            version = dep.installIn(Paths.toyboxesFolder())
            if version is not None:
                installed_version: str = version.original_version

                if version.isBranch():
                    commit_hash = dep.git.getLatestCommitHashForBranch(version.original_version)
                    if commit_hash is None:
                        raise RuntimeError('Could not find latest commit hash for branch ' + version.original_version + '.')

                    installed_version += '@' + commit_hash
                elif version.isLocal():
                    self.installed_a_local_toybox = True

                print('Installed \'' + str(dep) + '\' -> ' + str(version) + '.')

                self.box_file.setInstalledVersionForDependency(dep, Version(installed_version))

            # -- If this was installed then all sub dependencies must be installed too.
            force_install = True

            self.moveAssetsFromToyboxIfAny(dep)

        dep_box_file = Boxfile.boxfileForDependency(dep)
        for child_dep in dep_box_file.dependencies():
            self.installDependency(child_dep, force_install)

        if dependency_is_new:
            self.dependencies.append(dep)

    def update(self):
        if self.argument is not None:
            url: Url = Toybox.urlFromArgument(self.argument, self.force_mode)
            self.only_update.append(url)

        self.box_file = Boxfile(Paths.boxfileFolder())

        print('Resolving dependencies...')

        Toybox.backupToyboxes()
        Toybox.backupAssets()

        try:
            for dep in self.box_file.dependencies():
                self.installDependency(dep)

            folder = Paths.toyboxesFolder()
            if os.path.exists(folder):
                Files.generateReadMeFileIn(folder)
                Files.generateLuaIncludeFile(self.dependencies)
                Files.generateMakefile(self.dependencies)
                Files.generateIncludeFile(self.dependencies)
                Files.generateLuacheckFile(self.dependencies)

            folder = Paths.assetsFolder()
            if os.path.exists(folder):
                Files.generateReadMeFileIn(folder)

            self.box_file.saveIfModified()

        except Exception:
            Toybox.restoreAssetsBackup()
            Toybox.restoreToyboxesBackup()
            raise

        Toybox.deleteToyboxesBackup()
        Toybox.deleteAssetsBackup()

        Files.restorePreCommitFileIfAny()

        if self.installed_a_local_toybox:
            Files.generatePreCommitFile()

        print('Finished.')

    def setupMakefile(self):
        Files.generateMakefileSetup()

    @classmethod
    def printVersion(cls):
        if os.name == 'nt':
            # -- Windows Powershell doesn't support emoticons
            version_string = ''
        else:
            version_string = '🧸 '

        version_string += 'toybox.py v' + __version__
        print(version_string)

    @classmethod
    def printLicense(cls):
        Toybox.printVersion()
        print('')
        print('MIT License')
        print('')
        print('Copyright (c) 2022-present Didier Malenfant')
        print('')
        print('Permission is hereby granted, free of charge, to any person obtaining a copy')
        print('of this software and associated documentation files (the "Software"), to deal')
        print('in the Software without restriction, including without limitation the rights')
        print('to use, copy, modify, merge, publish, distribute, sublicense, and/or sell')
        print('copies of the Software, and to permit persons to whom the Software is')
        print('furnished to do so, subject to the following conditions:')
        print('')
        print('The above copyright notice and this permission notice shall be included in all')
        print('copies or substantial portions of the Software.')
        print('')
        print('THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR')
        print('IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,')
        print('FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE')
        print('AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER')
        print('LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,')
        print('OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE')
        print('SOFTWARE.')
        print('')
        print('Official repo can be found at https://code.malenfant.net/didier/toybox.py')
        print('')

    @classmethod
    def printSetUsage(cls):
        Toybox.printVersion()
        print('')
        print('Usage:')
        print('   toybox set lua_import <value>        - Set the lua filename to import.')
        print('   toybox set assets_sub_folder <value> - Set the subfolder to use for assets.')
        print('   toybox set makefile <value>          - Set the makefile to include for C projects.')
        print('   toybox set include_header <value>    - Set the file to include for C projects.')
        print('')

    @classmethod
    def printStoreUsage(cls):
        Toybox.printVersion()
        print('')
        print('Usage:')
        print('   toybox store content     - List all the toyboxes found in the toystore.')
        print('   toybox store info <name> - Get some info about a given toybox.')
        print('   toybox store repo <name> - Open a browser showing the repo of a given toybox.')
        print('')

    @classmethod
    def printTopics(cls):
        Toybox.printVersion()
        print('')
        print('Usage:')
        print('   toybox help set     - List the names accepted by the set command.')
        print('   toybox help store   - Show subcommands used for the store command.')
        print('   toybox help license - Show the license for the app.')
        print('')

    @classmethod
    def storeContent(cls, argument, force_update=False):
        ToyStore(force_update).content()

    @classmethod
    def storeInfo(cls, argument, force_update=False):
        if argument is None:
            raise ArgumentError('Missing argument for store info command.')

        ToyStore(force_update).info(argument)

    @classmethod
    def storeRepo(cls, argument, force_update=False):
        if argument is None:
            raise ArgumentError('Missing argument for store repo command.')

        ToyStore(force_update).repo(argument)

    @classmethod
    def urlFromArgument(cls, argument, force_update=False):
        if argument.__contains__('/') is False:
            # -- The argument passed looks like a toybox name, let's try to resolve it.
            toystore: ToyStore = ToyStore(force_update)

            url: str = toystore.maybeUrlForName(argument)
            if url is None:
                raise RuntimeError('Could find any toybox named ' + argument + ' in the toystore.')

            return Url(url)

        return Url(argument)

    @classmethod
    def backupToyboxes(cls):
        Utils.backup(Paths.toyboxesFolder(), Paths.toyboxesBackupFolder())

    @classmethod
    def restoreToyboxesBackup(cls):
        Utils.restore(Paths.toyboxesBackupFolder(), Paths.toyboxesFolder())

    @classmethod
    def backupAssets(cls):
        Utils.backup(Paths.assetsFolder(), Paths.assetsBackupFolder())

    @classmethod
    def restoreAssetsBackup(cls):
        Utils.restore(Paths.assetsBackupFolder(), Paths.assetsFolder())

    @classmethod
    def copyToyboxFromBackup(cls, dep: Dependency):
        source_path = dep.toyboxBackupFolder()
        dest_path = dep.toyboxFolder()
        if not os.path.exists(source_path):
            raise RuntimeError('Backup from ' + dep.subFolder() + ' cannot be found.')

        if os.path.exists(dest_path):
            # -- We may have already copied this toybox from another dependency.
            Utils.deleteFolder(dest_path)

        shutil.copytree(source_path, dest_path)

    @classmethod
    def copyAssetsFromBackupIfAny(cls, dep: Dependency):
        maybe_config_asset_folder = Boxfile.boxfileForDependency(dep).maybeAssetsSubFolder()
        source_path = dep.assetsBackupFolder(maybe_config_asset_folder)
        if os.path.exists(source_path):
            shutil.copytree(source_path, dep.assetsFolder(maybe_config_asset_folder))

    @classmethod
    def deleteToyboxesBackup(cls):
        Utils.deleteFolder(Paths.toyboxesBackupFolder())

    @classmethod
    def deleteAssetsBackup(cls):
        Utils.deleteFolder(Paths.assetsBackupFolder())

    @classmethod
    def moveAssetsFromToyboxIfAny(cls, dep: Dependency):
        source_path = os.path.join(dep.toyboxAssetsFolder())
        if not os.path.exists(source_path):
            return

        maybe_config_asset_folder = Boxfile.boxfileForDependency(dep).maybeAssetsSubFolder()
        dest_path = dep.assetsFolder(maybe_config_asset_folder)
        if os.path.exists(dest_path):
            raise RuntimeError('Something already installed assets in \'' + dest_path + '\'')

        os.makedirs(Path(dest_path).parent, exist_ok=True)

        shutil.move(source_path, dest_path)

    @classmethod
    def checkForToyboxPyUpdates(cls, force_check=False):
        try:
            if not force_check and not Utils.fileOlderThan(Paths.appUpdateCheckFile(),
                                                           time_in_seconds=(24 * 60 * 60)):
                return

            latest_version = Git(Url('code.malenfant.net/didier/toybox.py')).getLatestVersion()
            if latest_version is None:
                return

            Files.createAppUpdateCheckFile()

            if latest_version > Version(__version__):
                print('‼️  Version v' + str(latest_version) + ' is available for toybox.py. You have v' + __version__ + ' ‼️')
                print('Please run \'pip install toyboxpy --upgrade\' to upgrade.')
        except Exception:
            pass
