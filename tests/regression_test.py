# SPDX-FileCopyrightText: 2026-present the toybox.py community continuation
#
# SPDX-License-Identifier: MIT

import os
import pytest
import sys

from toybox.boxfile import Boxfile
from toybox.files import Files
from toybox.git import Git
from toybox.url import Url
from toybox.__main__ import main


def test_list_tag_versions_skips_non_semver_tags(monkeypatch):
    # -- A repo tag like 'latest' parses as a branch-type Version with no semver value;
    # -- it used to end up in the list and make the sort throw a TypeError.
    git = Git(Url('someuser/somerepo'))
    monkeypatch.setattr(git, 'listTags', lambda: ['latest', 'release-2024', 'v1.2.3', '1.0.0', 'not@a@version'])

    versions = git.listTagVersions()

    assert [str(version) for version in versions] == ['1.0.0', '1.2.3']


def test_old_boxfile_conversion_keeps_each_version(monkeypatch):
    # -- Each migrated entry used to receive the value of whichever key a stale loop
    # -- variable happened to hold, instead of its own.
    content = {'a/b': '1.0', 'c/d': '2.0'}

    assert Boxfile.maybeConvertOldBoxfile(content) is True
    assert content == {'toyboxes': {'a/b': '1.0', 'c/d': '2.0'}}


def test_pre_commit_hook_backup_and_restore(tmp_path, monkeypatch):
    # -- Backing up an existing pre-commit hook used to call a misnamed Paths method
    # -- and crash with an AttributeError.
    monkeypatch.chdir(tmp_path)
    hooks_folder = os.path.join('.git', 'hooks')
    os.makedirs(hooks_folder)

    hook_path = os.path.join(hooks_folder, 'pre-commit')
    with open(hook_path, 'w') as file:
        file.write('#!/bin/sh\necho original hook\n')

    Files.generatePreCommitFile()

    with open(hook_path, 'r') as file:
        assert 'local' in file.read()

    Files.restorePreCommitFileIfAny()

    with open(hook_path, 'r') as file:
        assert 'original hook' in file.read()


def test_argument_error_exits_nonzero(monkeypatch, capsys):
    # -- An unknown command used to print the error but still exit 0, which lets a
    # -- misspelled command pass silently in CI scripts.
    monkeypatch.setattr(sys, 'argv', ['toybox', 'no-such-command'])

    with pytest.raises(SystemExit) as e:
        main()

    assert e.value.code == 1
    assert 'no-such-command' in capsys.readouterr().out
