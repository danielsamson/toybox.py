# SPDX-FileCopyrightText: 2026-present the toybox.py community continuation
#
# SPDX-License-Identifier: MIT
#
# Hermetic end-to-end tests: the real add/update/check/remove cycle against real git
# repos, served by a local `git daemon` — no network, no third-party repos to flake.
#
# The trick that makes this work: toybox always builds https://<server>/<user>/<repo>.git
# URLs, and git's url.<base>.insteadOf rewriting (injected via GIT_CONFIG_* environment
# variables, appended after any rules the host environment already sets) points
# https://127.0.0.1:<port>/ at the daemon's git:// endpoint.

import json
import os
import socket
import subprocess
import time

import pytest

from toybox.toybox import Toybox

# -- The fixture layout puts the server:port in a folder name, and ':' is not a legal
# -- path character on Windows.
pytestmark = pytest.mark.skipif(os.name == 'nt', reason="fixture paths contain ':'")


class Forge:
    """Builds toybox repos on disk and serves them over a local git daemon."""

    def __init__(self, base_path):
        self.src_root = base_path / 'src'
        self.serve_root = base_path / 'serve'
        (self.serve_root / 'testuser').mkdir(parents=True)
        self.src_root.mkdir(parents=True)

        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            self.port = probe.getsockname()[1]

        self.server = '127.0.0.1:' + str(self.port)
        self.daemon = subprocess.Popen(
            ['git', 'daemon', '--reuseaddr', '--port=' + str(self.port),
             '--base-path=' + str(self.serve_root), '--export-all'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for _ in range(100):
            try:
                with socket.create_connection(('127.0.0.1', self.port), timeout=0.2):
                    return
            except OSError:
                time.sleep(0.1)

        raise RuntimeError('git daemon never came up')

    def stop(self):
        self.daemon.terminate()
        self.daemon.wait()

    def _git(self, arguments, folder):
        subprocess.run(['git', '-c', 'user.name=e2e', '-c', 'user.email=e2e@test',
                        '-c', 'protocol.file.allow=always'] + arguments,
                       cwd=folder, check=True, capture_output=True)

    def _write(self, folder, files):
        for relative_path, content in files.items():
            path = folder / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def make_repo(self, name, files, tags=()):
        """Create a repo with one commit and the given tags; return its toybox spec."""
        src = self.src_root / name
        src.mkdir()
        self._git(['init', '-q', '-b', 'main'], src)
        self._write(src, files)
        self._git(['add', '-A'], src)
        self._git(['commit', '-q', '-m', 'init'], src)
        for tag in tags:
            self._git(['tag', tag], src)

        bare = self.serve_root / 'testuser' / (name + '.git')
        subprocess.run(['git', 'clone', '-q', '--bare', str(src), str(bare)],
                       check=True, capture_output=True)

        return self.server + '/testuser/' + name

    def push_update(self, name, files, tags=()):
        """Add a commit (and optional tags) to an existing repo and publish it."""
        src = self.src_root / name
        self._write(src, files)
        self._git(['add', '-A'], src)
        self._git(['commit', '-q', '-m', 'update'], src)
        for tag in tags:
            self._git(['tag', tag], src)

        bare = self.serve_root / 'testuser' / (name + '.git')
        self._git(['push', '-q', str(bare), 'main'], src)
        self._git(['push', '-q', '--tags', str(bare)], src)


@pytest.fixture(scope='module')
def forge(tmp_path_factory):
    forge = Forge(tmp_path_factory.mktemp('forge'))
    yield forge
    forge.stop()


@pytest.fixture
def project(forge, tmp_path, monkeypatch):
    """A fresh project folder, with the https->git:// rewrite for the forge in place."""
    # -- Append our rewrite AFTER any GIT_CONFIG_* entries the host environment already
    # -- injects (CI runners have none; development sandboxes may have several).
    count = int(os.environ.get('GIT_CONFIG_COUNT', '0'))
    monkeypatch.setenv('GIT_CONFIG_KEY_' + str(count), 'url.git://' + forge.server + '/.insteadOf')
    monkeypatch.setenv('GIT_CONFIG_VALUE_' + str(count), 'https://' + forge.server + '/')
    monkeypatch.setenv('GIT_CONFIG_COUNT', str(count + 1))

    monkeypatch.chdir(tmp_path)
    subprocess.run(['git', 'init', '-q'], check=True)
    return tmp_path


def write_boxfile(project, deps):
    (project / 'Boxfile').write_text(json.dumps({'toyboxes': deps}, indent=4))


def read_boxfile(project):
    return json.loads((project / 'Boxfile').read_text())


def toybox_folder(project, spec):
    server, username, repo = spec.split('/')
    return project / 'toyboxes' / server.replace('.', '-dot-') / username / repo


def test_update_installs_resolves_range_and_moves_assets(forge, project):
    spec = forge.make_repo('simple', files={'simple.lua': 'print("hi")',
                                            'assets/logo.txt': 'logo'},
                           tags=('1.0.0', '1.1.0', '2.0.0'))
    write_boxfile(project, {spec: '1'})

    Toybox(['update']).update()

    installed = toybox_folder(project, spec)
    assert (installed / 'simple.lua').exists()
    assert not (installed / '.git').exists()

    # -- '1' must resolve to the highest 1.x, not 2.0.0.
    assert read_boxfile(project)['installed'] == {spec: '1.1.0'}

    imports = (project / 'toyboxes' / 'toyboxes.lua').read_text()
    assert "/simple.lua'" in imports

    # -- The assets folder is moved out of the toybox and into the project's source.
    moved_assets = project / 'source' / 'toybox_assets' / (forge.server.replace('.', '-dot-')) / 'testuser' / 'simple'
    assert (moved_assets / 'logo.txt').exists()
    assert not (installed / 'assets').exists()


def test_update_installs_transitive_dependencies(forge, project):
    leaf_spec = forge.make_repo('leaf', files={'leaf.lua': 'print("leaf")'}, tags=('1.0.0',))
    app_spec = forge.make_repo('app', files={
        'app.lua': 'print("app")',
        'Boxfile': json.dumps({'toyboxes': {leaf_spec: '1'}}),
    }, tags=('1.0.0',))
    write_boxfile(project, {app_spec: '1'})

    Toybox(['update']).update()

    assert (toybox_folder(project, app_spec) / 'app.lua').exists()
    assert (toybox_folder(project, leaf_spec) / 'leaf.lua').exists()

    imports = (project / 'toyboxes' / 'toyboxes.lua').read_text()
    assert "/app.lua'" in imports
    assert "/leaf.lua'" in imports


def test_branch_pin_installs_and_check_sees_new_commits(forge, project):
    spec = forge.make_repo('dev', files={'dev.lua': 'print(1)'})
    write_boxfile(project, {spec: 'main'})

    Toybox(['update']).update()

    installed_version = read_boxfile(project)['installed'][spec]
    assert installed_version.startswith('main@')

    assert Toybox(['check']).checkForUpdates() is False

    forge.push_update('dev', files={'dev.lua': 'print(2)'})

    assert Toybox(['check']).checkForUpdates() is True


def test_c_toybox_generates_makefile_and_header(forge, project):
    spec = forge.make_repo('clib', files={'clib.mk': '# makefile',
                                          'clib/clib.h': '// header'},
                           tags=('1.0.0',))
    write_boxfile(project, {spec: '1'})

    Toybox(['update']).update()

    makefile = (project / 'toyboxes' / 'toyboxes.mk').read_text()
    assert 'CLIB_MAKEFILE' in makefile

    header = (project / 'toyboxes' / 'toyboxes.h').read_text()
    assert '/clib/clib.h"' in header
    assert 'REGISTER_TOYBOXES' in header


def test_add_then_remove_round_trip(forge, project):
    spec = forge.make_repo('addme', files={'addme.lua': 'print(1)'}, tags=('1.0.0',))

    Toybox(['add', spec, '1']).addDependency()
    assert read_boxfile(project)['toyboxes'] == {spec: '1'}

    Toybox(['update']).update()
    assert toybox_folder(project, spec).exists()

    Toybox(['remove', spec]).removeDependency()
    assert read_boxfile(project)['toyboxes'] == {}
    assert not toybox_folder(project, spec).exists()


def test_failed_update_restores_the_previous_install(forge, project):
    good_spec = forge.make_repo('good', files={'good.lua': 'print(1)'}, tags=('1.0.0',))
    write_boxfile(project, {good_spec: '1'})
    Toybox(['update']).update()

    ghost_spec = forge.server + '/testuser/ghost'
    write_boxfile(project, {good_spec: '1', ghost_spec: '1'})

    with pytest.raises(RuntimeError):
        Toybox(['update']).update()

    # -- The failed run must leave the previous good install in place, with no
    # -- stranded backup folder.
    assert (toybox_folder(project, good_spec) / 'good.lua').exists()
    assert not (project / 'toyboxes.backup').exists()


def test_circular_dependency_is_reported_not_a_stack_overflow(forge, project):
    a_spec = forge.server + '/testuser/cyc-a'
    b_spec = forge.server + '/testuser/cyc-b'
    forge.make_repo('cyc-a', files={'cyc-a.lua': 'print(1)',
                                    'Boxfile': json.dumps({'toyboxes': {b_spec: 'main'}})})
    forge.make_repo('cyc-b', files={'cyc-b.lua': 'print(1)',
                                    'Boxfile': json.dumps({'toyboxes': {a_spec: 'main'}})})
    write_boxfile(project, {a_spec: 'main'})

    with pytest.raises(RuntimeError, match='Circular toybox dependency'):
        Toybox(['update']).update()


def test_interrupted_update_restores_the_previous_install(forge, project, monkeypatch):
    spec = forge.make_repo('steady', files={'steady.lua': 'print(1)'}, tags=('1.0.0',))
    write_boxfile(project, {spec: '1'})
    Toybox(['update']).update()

    def boom(self, dep, force_install=False):
        raise KeyboardInterrupt

    monkeypatch.setattr(Toybox, 'installDependency', boom)

    with pytest.raises(KeyboardInterrupt):
        Toybox(['update']).update()

    assert (toybox_folder(project, spec) / 'steady.lua').exists()
    assert not (project / 'toyboxes.backup').exists()
