# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import pytest
import sys
import os

# -- We need to import from our parent folder here.
sys.path.append(os.path.join(sys.path[0], '..'))

from toybox.boxfile import Boxfile       # noqa: E402
from toybox.version import Version       # noqa: E402
from toybox.url import Url       # noqa: E402


def test_constructor_old_format():
    boxfile = Boxfile(os.path.join('tests', 'data', 'boxfile_old'))
    urls = boxfile.urls()
    assert len(urls) == 1
    url = urls[0]
    assert url.as_string == 'code.malenfant.net/didier/pdbase'
    assert boxfile.versionsForUrl(url) == [Version('>=1.0.0'), Version('<2.0.0')]
    assert boxfile.maybeInstalledVersionForUrl(url) is None
    assert boxfile.maybeLuaImportFile() is None


def test_constructor_current_format():
    boxfile = Boxfile(os.path.join('tests', 'data', 'boxfile_current'))
    urls = boxfile.urls()
    assert len(urls) == 1
    url = urls[0]
    assert url.as_string == 'code.malenfant.net/didier/pdbase'
    assert boxfile.versionsForUrl(url) == [Version('>=1.0.0'), Version('<2.0.0')]
    assert boxfile.maybeInstalledVersionForUrl(url) == Version('1.2.3')
    assert boxfile.maybeLuaImportFile() == 'source/main.lua'


def test_constructor_incorrect_format():
    folder = os.path.join('tests', 'data', 'boxfile_future')

    with pytest.raises(SyntaxError) as e:
        Boxfile(folder)

    test = 'Incorrect format for Boxfile \'' + os.path.join(folder, 'Boxfile') + '\'.\nMaybe you need to upgrade toybox?'
    assert str(e.value) == test


def test_constructor_invalid_filename():
    folder = os.path.join('tests', 'data', 'boxfile_which_does_not_exist')

    with pytest.raises(RuntimeError) as e:
        Boxfile(folder)

    test = 'No Boxfile found in \'' + folder + '\'.'
    assert str(e.value) == test


def test_constructor_invalid_filename_but_told_to_ignore_it():
    boxfile = Boxfile(os.path.join('tests', 'data', 'boxfile_which_does_not_exist'), empty_if_does_not_exist=True)
    urls = boxfile.urls()
    assert len(urls) == 0


def test_constructor_malformed_file():
    folder = os.path.join('tests', 'data', 'boxfile_invalid')

    with pytest.raises(SyntaxError) as e:
        Boxfile(folder)

    test = 'Malformed JSON in Boxfile \'' + os.path.join(folder, 'Boxfile') + '\'.\nExpecting \',\' delimiter: line 3 column 5 (char 40).'
    assert str(e.value) == test


@pytest.mark.parametrize('version_string, expected_results', [
    ('develop', [Version('develop')]),
    ('>1.0 <3 <2.5', [Version('>1.0.0'), Version('<3.0.0'), Version('<2.5.0')]),
    ('<3 <2.5 <3', [Version('<3.0.0'), Version('<2.5.0')]),
    ('/' + os.path.join('My', 'Local', 'Folder'), [Version('/' + os.path.join('My', 'Local', 'Folder'))]),
    (os.path.join('J:', 'My', 'Local', 'Folder'), [Version(os.path.join('J:', 'My', 'Local', 'Folder'))])
])

def test_versionsForUrl(version_string, expected_results):  # noqa: E304
    boxfile = Boxfile(os.path.join('tests', 'data', 'boxfile_current'))
    url = Url('didier/pdbase')
    boxfile.addDependencyWithURLAt(url, version_string)
    assert boxfile.versionsForUrl(url) == expected_results


def test_versionsForUrl_incorrect_versions():
    boxfile = Boxfile(os.path.join('tests', 'data', 'boxfile_current'))
    url = Url('didier/pdbase')
    boxfile.addDependencyWithURLAt(url, '>1 <=4.5 >4 <6')
    with pytest.raises(SyntaxError):
        boxfile.versionsForUrl(url)
