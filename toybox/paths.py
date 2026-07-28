# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import os
import tempfile


class Paths:
    """Various paths used by toyboxpy."""

    @classmethod
    def escapeOutToyboxPath(cls, path: str) -> str:
        return (path.replace('-dot-', '-dot--dot-')).replace('.', '-dot-')

    @classmethod
    def boxfileFolder(cls) -> str:
        return os.getcwd()

    @classmethod
    def toyboxesFolder(cls) -> str:
        return os.path.join(Paths.boxfileFolder(), 'toyboxes')

    @classmethod
    def toyboxesBackupFolder(cls) -> str:
        return Paths.toyboxesFolder() + '.backup'

    @classmethod
    def assetsFolder(cls) -> str:
        return os.path.join(Paths.boxfileFolder(), 'source', 'toybox_assets')

    @classmethod
    def assetsBackupFolder(cls) -> str:
        return os.path.join(Paths.toyboxesFolder(), 'assets')

    @classmethod
    def preCommitFilePath(cls) -> str:
        return os.path.join('.git', 'hooks', 'pre-commit')

    @classmethod
    def preCommitFileBackupPath(cls) -> str:
        return Paths.preCommitFilePath() + '.toyboxes_backup'

    @classmethod
    def preCommitFileNoBackupPath(cls) -> str:
        return Paths.preCommitFilePath() + '.toyboxes_no_backup'

    @classmethod
    def extensionMakefile(cls) -> str:
        return os.path.join(Paths.boxfileFolder(), 'extension', 'extension.mk')

    @classmethod
    def extensionMainFile(cls) -> str:
        return os.path.join(Paths.boxfileFolder(), 'extension', 'main.c')

    @classmethod
    def projectMakefile(cls) -> str:
        return os.path.join(Paths.boxfileFolder(), 'Makefile')

    @classmethod
    def tempFolder(cls):
        return os.path.join(tempfile.gettempdir(), 'io.toyboxpy')

    @classmethod
    def appUpdateCheckFile(cls):
        return os.path.join(Paths.tempFolder(), 'app-update-check')
