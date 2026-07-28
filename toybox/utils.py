# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import os
import shutil
import errno
import stat
import glob
import time

from typing import List


def _handleRemoveReadonly(func, path, exc):
    excvalue = exc[1]
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # -- 0777
        func(path)
    else:
        raise


class Utils:
    """Utility methods used by toyboxpy."""

    @classmethod
    def lookInFolderFor(cls, folder: str, wildcard: str) -> List[str]:
        # -- We use this here instead of just simply os.path.exists()
        # -- because we want the test to be case-sensitive on all platforms,
        # -- so we list what the match are and let glob give us the paths.
        paths_found = []
        looking_in = os.path.join(folder, wildcard)

        for p in glob.glob(looking_in, recursive=True):
            as_string = str(p)
            if len(as_string) > 4:
                as_string = as_string[len(folder) + 1:]
                paths_found.append(as_string)

        return paths_found

    @classmethod
    def backup(cls, from_folder: str, to_folder: str):
        if os.path.exists(from_folder):
            shutil.move(from_folder, to_folder)

    @classmethod
    def restore(cls, from_folder: str, to_folder: str):
        Utils.deleteFolder(to_folder)

        if os.path.exists(from_folder):
            shutil.move(from_folder, to_folder)

    @classmethod
    def deleteFolder(cls, folder: str, force_delete: bool = False):
        if os.path.exists(folder):
            if force_delete is True:
                ignore_errors = False
                on_error = _handleRemoveReadonly
            else:
                ignore_errors = True
                on_error = None

            shutil.rmtree(folder, ignore_errors=ignore_errors, onerror=on_error)

    @classmethod
    def softlinkFromTo(cls, source: str, dest: str):
        if not os.path.exists(source):
            raise RuntimeError('Local toybox folder ' + source + ' cannot be found.')

        os.makedirs(dest, exist_ok=True)

        for file_or_dir in os.listdir(source):
            if file_or_dir[0] == '.':
                continue

            os.symlink(os.path.join(source, file_or_dir), os.path.join(dest, file_or_dir))

    @classmethod
    def copyFromTo(cls, source: str, dest: str):
        if not os.path.exists(source):
            raise RuntimeError('Local toybox folder ' + source + ' cannot be found.')

        shutil.copytree(source, os.path.join(dest, ''))

    @classmethod
    def fileOlderThan(cls, path: str, time_in_seconds: int):
        if not os.path.exists(path):
            return True

        return (time.time() - os.path.getmtime(path)) > time_in_seconds
