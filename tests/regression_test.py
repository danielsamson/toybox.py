# SPDX-FileCopyrightText: 2026-present the toybox.py community continuation
#
# SPDX-License-Identifier: MIT

import json
import os
import pytest
import stat
import sys

from toybox.boxfile import Boxfile
from toybox.toybox import Toybox
from toybox.files import Files
from toybox.git import Git
from toybox.url import Url
from toybox.utils import Utils
from toybox.version import Version
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


def test_force_delete_removes_readonly_files(tmp_path):
    # -- Exercises the rmtree error handler on whichever path (onexc/onerror) the
    # -- running Python uses; cloned .git folders contain read-only objects.
    folder = tmp_path / 'stubborn'
    folder.mkdir()

    file_path = folder / 'readonly-file'
    file_path.write_text('hands off')
    os.chmod(file_path, stat.S_IRUSR)
    os.chmod(folder, stat.S_IRUSR | stat.S_IXUSR)

    Utils.deleteFolder(str(folder), force_delete=True)

    assert not folder.exists()


def test_url_equality_against_other_types():
    url = Url('someuser/somerepo')

    assert (url == 'someuser/somerepo') is False
    assert url != 42
    assert url == Url('github.com/someuser/somerepo')


@pytest.mark.parametrize('version_string, expected', [
    ('1', ['>=1.0.0', '<2.0.0']),
    ('1.2', ['>=1.2.0', '<1.3.0']),
    ('v1.2', ['>=1.2.0', '<1.3.0']),      # -- leading 'v' used to defeat range expansion
    ('1.2.3', ['1.2.3']),
    ('>1.2', ['>1.2.0']),
    ('develop', ['develop']),
])
def test_incomplete_version_range_expansion(version_string, expected):
    assert Version.maybeRangeFromIncompleteNumericVersion(version_string) == expected


@pytest.mark.parametrize('version_string', ['>', '>=', '<'])
def test_bare_operator_raises_instead_of_index_error(version_string):
    with pytest.raises(SyntaxError):
        Version.maybeRangeFromIncompleteNumericVersion(version_string)


def test_list_refs_parses_sha256_repos(monkeypatch):
    # -- Ref parsing used to take the first 40 characters as the hash; SHA-256 repos
    # -- have 64-character hashes and would have been silently mis-parsed.
    sha256_hash = 'a' * 64
    sha1_hash = 'b' * 40
    canned = (sha256_hash + '\trefs/heads/main\n' + sha1_hash + '\trefs/tags/1.0.0\n')

    git = Git(Url('someuser/somerepo'))
    monkeypatch.setattr(git, 'git', lambda arguments, folder=None: canned)

    assert git.listBranches() == {'main': sha256_hash}
    assert git.listTags() == ['1.0.0']
    assert git.getLatestCommitHashForBranch('main') == sha256_hash


def test_boxfile_save_failure_leaves_the_original_intact(tmp_path, monkeypatch):
    # -- Saves go through a temp file + rename; a failure mid-write must leave the
    # -- existing Boxfile untouched and clean up after itself.
    original = {'toyboxes': {'a/b': '1.0'}}
    (tmp_path / 'Boxfile').write_text(json.dumps(original))

    box_file = Boxfile(str(tmp_path))
    box_file.addDependencyWithURLAt(Url('c/d'), '2.0')

    def explode(*args, **kwargs):
        raise RuntimeError('disk full')

    monkeypatch.setattr(json, 'dump', explode)

    with pytest.raises(RuntimeError):
        box_file.saveIfModified()

    assert json.loads((tmp_path / 'Boxfile').read_text()) == original
    assert [p.name for p in tmp_path.iterdir()] == ['Boxfile']


def test_semver_version_carries_an_optional_ref_hash():
    # -- The installed section records '1.2.3@<hash>' so moved tags can be detected.
    recorded = Version('1.2.3@' + 'a' * 40)

    assert recorded.commit_hash == 'a' * 40
    assert str(recorded) == '1.2.3@' + 'a' * 40
    assert recorded == Version('1.2.3')            # -- the hash is not part of version equality

    # -- A tag merely NAMED like that must keep failing semver parsing as before.
    with pytest.raises(ValueError):
        Version('1.0.0@beta')


def test_git_retries_transient_failures_once(monkeypatch):
    git = Git(Url('someuser/somerepo'))
    attempts = []

    def fake_run(commands, env):
        attempts.append(commands)
        if len(attempts) == 1:
            return (128, '', 'fatal: unable to access \'https://github.com/...\': connection reset')
        return (0, 'all good', '')

    monkeypatch.setattr(git, '_runGitCommand', fake_run)
    monkeypatch.setattr('toybox.git.time.sleep', lambda seconds: None)

    assert git.git('ls-remote --refs') == 'all good'
    assert len(attempts) == 2


def test_git_does_not_retry_permanent_failures_and_names_the_repo(monkeypatch):
    git = Git(Url('someuser/somerepo'))
    attempts = []

    def fake_run(commands, env):
        attempts.append(commands)
        return (128, '', 'fatal: remote error: access denied or repository not exported')

    monkeypatch.setattr(git, '_runGitCommand', fake_run)

    with pytest.raises(RuntimeError) as e:
        git.git('ls-remote --refs')

    assert len(attempts) == 1
    assert 'someuser/somerepo' in str(e.value)


def test_argument_error_exits_nonzero(monkeypatch, capsys):
    # -- An unknown command used to print the error but still exit 0, which lets a
    # -- misspelled command pass silently in CI scripts.
    monkeypatch.setattr(sys, 'argv', ['toybox', 'no-such-command'])

    with pytest.raises(SystemExit) as e:
        main()

    assert e.value.code == 1
    assert 'no-such-command' in capsys.readouterr().out


def test_asset_install_strips_docs_but_keeps_license(tmp_path):
    # -- source/toybox_assets/ is inside source/, so pdc compiles everything in it into
    # -- the .pdx — and pdc copies unrecognised file types by default. A dependency's
    # -- README is not an asset, and it was shipping in every game built with toybox.
    # --
    # -- LICENSE must survive: MIT and BSD require the notice to accompany all copies or
    # -- substantial portions, and a .pdx redistributes the dependency.
    assets = tmp_path / 'toybox_assets'
    (assets / 'nested').mkdir(parents=True)
    for name in ('README.md', 'readme.txt', 'CHANGELOG.md', 'CONTRIBUTING.md',
                 'LICENSE', 'LICENSE.md', 'icons-table-22-22.png', 'dialogue.txt'):
        (assets / name).write_text('x')
    (assets / 'nested' / 'README.rst').write_text('x')

    skipped = Toybox.stripDocsFromAssets(str(assets))

    remaining = sorted(p.name for p in assets.rglob('*') if p.is_file())
    # -- dialogue.txt is the case that makes `pdc -k` the wrong fix: it is an
    # -- unrecognised type AND a real asset, so a blanket skip would drop it silently.
    assert remaining == ['LICENSE', 'LICENSE.md', 'dialogue.txt', 'icons-table-22-22.png']
    assert sorted(skipped) == ['CHANGELOG.md', 'CONTRIBUTING.md', 'README.md',
                               'README.rst', 'readme.txt']


# -- `latest`: move pins to the newest RELEASED version ---------------------------------
#
# The gap it fills: `update` re-resolves the constraint already in the Boxfile, and
# `check` compares what is installed against what that constraint resolves to. Neither
# asks what has been released. So an exact pin — what a generated or carefully pinned
# project has — reports itself up to date forever, and `update` will even downgrade a
# newer install back to the pin. A stale pin has no symptoms: it resolves, builds and
# passes its tests, and simply lacks whatever the newer version added.

def _boxfile(tmp_path, toyboxes):
    (tmp_path / 'Boxfile').write_text(json.dumps({'toyboxes': toyboxes}, indent=4))


def _fake_latest(monkeypatch, available):
    """Pin each repo's newest released tag, without touching the network.

    Git.url is the full clone URL string, not a Url object, so key off its tail.
    """
    def latest(self):
        name = self.url.rsplit('/', 1)[-1].removesuffix('.git')
        return Version(available[name]) if available.get(name) else None

    monkeypatch.setattr(Git, 'getLatestVersion', latest)


def _run_latest(monkeypatch, argv):
    monkeypatch.setattr(sys, 'argv', argv)
    monkeypatch.setattr(Toybox, 'update', lambda self: None)  # no install in a unit test
    main()


def test_latest_moves_an_exact_pin_that_is_behind(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _boxfile(tmp_path, {'someuser/alpha': '0.4.8', 'someuser/beta': '0.1.0'})
    _fake_latest(monkeypatch, {'alpha': 'v0.6.0', 'beta': '0.1.0'})

    _run_latest(monkeypatch, ['toybox', 'latest'])

    written = json.loads((tmp_path / 'Boxfile').read_text())['toyboxes']
    # -- The 'v' prefix the tag carried is dropped: both parse, but a Boxfile that
    # -- reads "0.1.0" for one dep and "v0.6.0" for another invites someone to wonder
    # -- whether the difference means something.
    assert written == {'someuser/alpha': '0.6.0', 'someuser/beta': '0.1.0'}


def test_latest_leaves_a_branch_pin_alone(tmp_path, monkeypatch, capsys):
    # -- A branch is not a version and already tracks its own tip. Moving it because
    # -- it is "behind" would be a change nobody asked for — but skipping it in
    # -- SILENCE is how a dependency gets quietly left out of an update-everything.
    monkeypatch.chdir(tmp_path)
    _boxfile(tmp_path, {'someuser/alpha': 'main'})
    _fake_latest(monkeypatch, {'alpha': '0.6.0'})

    _run_latest(monkeypatch, ['toybox', 'latest'])

    assert json.loads((tmp_path / 'Boxfile').read_text())['toyboxes'] == {'someuser/alpha': 'main'}
    assert 'not a released version' in capsys.readouterr().out


def test_latest_check_reports_without_changing_anything(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _boxfile(tmp_path, {'someuser/alpha': '0.4.8'})
    _fake_latest(monkeypatch, {'alpha': '0.6.0'})
    monkeypatch.setattr(sys, 'argv', ['toybox', 'latest', '--check'])

    # -- Non-zero so it works as a CI gate, the same way a failing test does.
    with pytest.raises(SystemExit) as e:
        main()

    assert e.value.code == 1
    assert '0.4.8 is behind 0.6.0' in capsys.readouterr().out
    assert json.loads((tmp_path / 'Boxfile').read_text())['toyboxes'] == {'someuser/alpha': '0.4.8'}


def test_latest_check_is_quiet_and_zero_when_current(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _boxfile(tmp_path, {'someuser/alpha': '0.6.0'})
    _fake_latest(monkeypatch, {'alpha': '0.6.0'})
    monkeypatch.setattr(sys, 'argv', ['toybox', 'latest', '--check'])

    main()   # -- no SystemExit: nothing is behind


def test_latest_never_moves_a_pin_backwards(tmp_path, monkeypatch):
    # -- A pin ahead of the newest visible tag is not "behind". Rewriting it would be
    # -- a silent downgrade, which is exactly what `update` already does to a newer
    # -- install and the reason this command exists.
    monkeypatch.chdir(tmp_path)
    _boxfile(tmp_path, {'someuser/alpha': '0.7.0'})
    _fake_latest(monkeypatch, {'alpha': '0.6.0'})

    _run_latest(monkeypatch, ['toybox', 'latest'])

    assert json.loads((tmp_path / 'Boxfile').read_text())['toyboxes'] == {'someuser/alpha': '0.7.0'}


def test_latest_can_target_one_dependency(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _boxfile(tmp_path, {'someuser/alpha': '0.4.8', 'someuser/beta': '0.1.0'})
    _fake_latest(monkeypatch, {'alpha': '0.6.0', 'beta': '0.9.0'})

    _run_latest(monkeypatch, ['toybox', 'latest', 'someuser/alpha'])

    written = json.loads((tmp_path / 'Boxfile').read_text())['toyboxes']
    assert written == {'someuser/alpha': '0.6.0', 'someuser/beta': '0.1.0'}


def test_latest_on_a_dependency_not_in_the_boxfile_says_so(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _boxfile(tmp_path, {'someuser/alpha': '0.4.8'})
    _fake_latest(monkeypatch, {'alpha': '0.6.0'})
    monkeypatch.setattr(sys, 'argv', ['toybox', 'latest', 'someuser/nope'])

    with pytest.raises(SystemExit) as e:
        main()

    assert e.value.code == 1
    assert 'No dependency on' in capsys.readouterr().out


def test_repinning_replaces_the_entry_rather_than_adding_a_second(tmp_path, monkeypatch):
    # -- A Boxfile may spell an entry short while Url.as_string is always canonical, so
    # -- keying off as_string added a SECOND entry for the same dependency. Both then
    # -- resolved, and re-pinning looked like it had simply not taken. Affects `add
    # -- <existing-dep> <version>` too, not just `latest`.
    monkeypatch.chdir(tmp_path)
    _boxfile(tmp_path, {'someuser/alpha': '0.4.8'})

    box = Boxfile(str(tmp_path))
    box.addDependencyWithURLAt(Url('someuser/alpha'), '0.6.0')
    box.saveIfModified()

    assert json.loads((tmp_path / 'Boxfile').read_text())['toyboxes'] == {'someuser/alpha': '0.6.0'}
