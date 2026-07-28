# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import pytest
import sys
import os

# -- We need to import from our parent folder here.
sys.path.append(os.path.join(sys.path[0], '..'))

from toybox.version import Version       # noqa: E402
from toybox.version import VersionIs     # noqa: E402


def test_constructor_invalid_value():
    with pytest.raises(ValueError):
        Version('34.2')


@pytest.mark.parametrize('input, expected_operator, expected_major, expected_minor, expected_patch, expected_string', [
    ('0.0.0', VersionIs.equal, 0, 0, 0, '0.0.0'),
    ('5.12.4', VersionIs.equal, 5, 12, 4, '5.12.4'),
    ('v5.12.4', VersionIs.equal, 5, 12, 4, '5.12.4'),
    ('>5.12.4', VersionIs.greater_than, 5, 12, 4, '>5.12.4'),
    ('>v5.12.4', VersionIs.greater_than, 5, 12, 4, '>5.12.4'),
    ('>=5.12.4', VersionIs.greater_than_or_equal, 5, 12, 4, '>=5.12.4'),
    ('>=v5.12.4', VersionIs.greater_than_or_equal, 5, 12, 4, '>=5.12.4'),
    ('<5.12.4', VersionIs.less_than, 5, 12, 4, '<5.12.4'),
    ('<v5.12.4', VersionIs.less_than, 5, 12, 4, '<5.12.4'),
    ('<=5.12.4', VersionIs.less_than_or_equal, 5, 12, 4, '<=5.12.4'),
    ('<=v5.12.4', VersionIs.less_than_or_equal, 5, 12, 4, '<=5.12.4'),
])

def test_constructor(input, expected_operator, expected_major, expected_minor, expected_patch, expected_string):  # noqa: E304
    version = Version(input)
    assert version.operator == expected_operator
    assert version.asSemVer.major == expected_major
    assert version.asSemVer.minor == expected_minor
    assert version.asSemVer.patch == expected_patch
    assert str(version) == expected_string
    assert version.original_version == input
    assert version.isBranch() is False
    assert version.isLocal() is False


@pytest.mark.parametrize('branch, expected_original_version', [
    ('develop', 'develop'),
    ('main@aaf867d2725ab51a770b036c219e1cfb676e79b7', 'main')
])

def test_constructor_with_branch(branch, expected_original_version):  # noqa: E304
    version = Version(branch)
    assert version.operator == VersionIs.equal
    assert str(version) == branch
    assert version.original_version == expected_original_version
    assert version.isBranch() is True
    assert version.isLocal() is False


@pytest.mark.parametrize('folder, expected_original_version', [
    ('/' + os.path.join('This', 'Is', 'My', 'Folder'), '/' + os.path.join('This', 'Is', 'My', 'Folder')),
    (os.path.join('C:', 'This', 'Is', 'My', 'Folder'), os.path.join('C:', 'This', 'Is', 'My', 'Folder')),
    (os.path.join('~', 'This', 'Is', 'My', 'Folder'), os.path.expanduser(os.path.join('~', 'This', 'Is', 'My', 'Folder')))
])

def test_constructor_with_local_folder(folder, expected_original_version):  # noqa: E304
    version = Version(folder)
    assert version.operator == VersionIs.equal
    assert str(version) == expected_original_version
    assert version.original_version == expected_original_version
    assert version.isLocal() is True
    assert version.isBranch() is False


@pytest.mark.parametrize('version', [
    '5.12.4', '<5.12.4', '<=5.12.4', '>5.12.4', '>=5.12.4',
    'main@aaf867d2725ab51a770b036c219e1cfb676e79b7',
    'very',
    '/' + os.path.join('This', 'Is', 'My', 'Folder'),
    '~', 'This', 'Is', 'My', 'Folder',
    os.path.join('C:', 'This', 'Is', 'My', 'Folder')
])

def test_operator_equal(version):  # noqa: E304
    assert Version(version) == Version(version)


@pytest.mark.parametrize('version, different_version', [
    ('5.12.4', '5.13.4'),
    ('>=5.12.4', '<5.13.4'),
    ('5.12.4', '>5.12.4'),
    ('>=5.12.4', '5.12.4'),
    ('5.12.4', 'main'),
    ('5.12.4', 'main@aaf867d2725ab51a770b036c219e1cfb676e79b7'),
    ('5.12.4', '/' + os.path.join('This', 'Is', 'My', 'Folder')),
    ('5.12.4', os.path.join('C:', 'This', 'Is', 'My', 'Folder')),

    ('develop', 'main'),
    ('main@aaf867d2725ab51a770b026c219e1cfb676e79b7', 'main@aaf867d2725ab51a770b036c219e1cfb676e79b7'),
    ('main', '/' + os.path.join('This', 'Is', 'My', 'Folder')),
    ('main@aaf867d2725ab51a770b036c219e1cfb676e79b7', os.path.join('C:', 'This', 'Is', 'My', 'Folder')),
    ('main', '/' + os.path.join('This', 'Is', 'My', 'Folder')),
    ('main@aaf867d2725ab51a770b036c219e1cfb676e79b7', os.path.join('C:', 'This', 'Is', 'My', 'Folder')),

    ('/' + os.path.join('This', 'Is', 'Not', 'My', 'Folder'), '/' + os.path.join('This', 'Is', 'My', 'Folder')),
    (os.path.join('C:', 'This', 'Is', 'Not', 'My', 'Folder'), os.path.join('C:', 'This', 'Is', 'My', 'Folder')),
    ('/' + os.path.join('This', 'Is', 'My', 'Folder'), os.path.join('C:', 'This', 'Is', 'My', 'Folder'))
])

def test_operator_not_equal(version, different_version):  # noqa: E304
    assert Version(version) != Version(different_version)


@pytest.mark.parametrize('version, expected_result', [
    ('5.2.1', 5),
    ('>=4.8.4', 4),
    ('<3.0.0', 3),
    ('<6.8.4', 6),
    ('main', None),
    ('main@aaf867d2725ab51a770b036c219e1cfb676e79b7', None),
    ('/' + os.path.join('This', 'Is', 'Not', 'My', 'Folder'), None),
    (os.path.join('C:', 'This', 'Is', 'Not', 'My', 'Folder'), None)
])

def test_majorVersion(version, expected_result):  # noqa: E304
    assert Version(version).majorVersion() == expected_result


@pytest.mark.parametrize('input, expected_result', [
    ('3.4.2', ['3.4.2']),
    ('2', ['>=2.0.0', '<3.0.0']),
    ('1.4', ['>=1.4.0', '<1.5.0']),
    ('>10.2.9', ['>10.2.9']),
    ('<=5.5', ['<=5.5.0']),
    ('develop', ['develop']),
    ('/' + os.path.join('This', 'Is', 'My', 'Folder'), ['/' + os.path.join('This', 'Is', 'My', 'Folder')]),
    (os.path.join('d:', 'This', 'Is', 'My', 'Folder'), [os.path.join('d:', 'This', 'Is', 'My', 'Folder')]),
])

def test_maybeRangeFromIncompleteNumericVersion(input, expected_result):  # noqa: E304
    versions = Version.maybeRangeFromIncompleteNumericVersion(input)
    assert versions == expected_result


def test_maybeRangeFromIncompleteNumericVersion_invalid_inpu():
    with pytest.raises(ValueError):
        Version.maybeRangeFromIncompleteNumericVersion('<3.4.2 >3 <5')


@pytest.mark.parametrize('rule, includes_version', [
    ('3.4.2', '3.4.2'),
    ('>3.4.2', '3.40.2'),
    ('<3.4.2', '3.3.2'),
    ('>=3.4.2', '3.4.2'),
    ('>=3.4.2', '3.40.2'),
    ('<=3.4.2', '3.4.2'),
    ('<=3.4.2', '3.3.2'),
    ('main', 'main'),
    ('/' + os.path.join('This', 'Is', 'My', 'Folder'), '/' + os.path.join('This', 'Is', 'My', 'Folder')),
    (os.path.join('z:', 'This', 'Is', 'My', 'Folder'), os.path.join('z:', 'This', 'Is', 'My', 'Folder'))
])

def test_includes_is_true(rule, includes_version):  # noqa: E304
    assert Version(rule).includes(Version(includes_version)) is True


@pytest.mark.parametrize('rule, does_not_include_version', [
    ('3.4.2', '3.40.2'),
    ('>3.4.2', '3.3.2'),
    ('<3.4.2', '3.4.2'),
    ('>=3.4.2', '3.3.2'),
    ('<=3.4.2', '5.4.1'),
    ('main', 'test'),
    ('main', '3.4.2'),
    ('/' + os.path.join('This', 'Is', 'My', 'Folder'), '/' + os.path.join('This', 'Is', 'My', 'Other')),
    ('/' + os.path.join('This', 'Is', 'My', 'Folder'), '3.4.2'),
    (os.path.join('z:', 'This', 'Is', 'My', 'Folder'), os.path.join('D:', 'This', 'Is', 'My', 'Other')),
    (os.path.join('z:', 'This', 'Is', 'My', 'Folder'), '3.4.2')
])

def test_includes_is_false(rule, does_not_include_version):  # noqa: E304
    assert Version(rule).includes(Version(does_not_include_version)) is False


def test_includes_invalid_input():
    with pytest.raises(SyntaxError):
        Version('<3.4.2').includes(Version('>3.4.2'))


@pytest.fixture
def included_versions_input():
    return [Version('3.2.1'), Version('4.2.1'), Version('5.0.0'), Version('5.2.1')]


@pytest.mark.parametrize('rule, expected_result', [
    ('<5.0.0', [Version('3.2.1'), Version('4.2.1')]),
    ('<3.0.0', []),
    ('<=5.0.0', [Version('3.2.1'), Version('4.2.1'), Version('5.0.0')]),
    ('<=2.8.4', []),
    ('4.2.1', [Version('4.2.1')]),
    ('4.3.1', []),
    ('>4.3.0', [Version('5.0.0'), Version('5.2.1')]),
    ('>6.0.0', []),
    ('>=5.0.0', [Version('5.0.0'), Version('5.2.1')]),
    ('>=5.8.4', [])
])

def test_includedVersionsIn(rule, expected_result, included_versions_input):  # noqa: E304
    assert Version(rule).includedVersionsIn(included_versions_input) == expected_result


@pytest.fixture
def some_versions():
    return [Version('3.2.1'), Version('4.2.1'), Version('5.0.0'), Version('5.2.1')]


@pytest.fixture
def branch_version():
    return Version('develop')


@pytest.fixture
def unix_folder_version():
    return Version('/' + os.path.join('This', 'Is', 'My', 'Folder'))


@pytest.fixture
def windows_folder_version():
    return Version(os.path.join('S:', 'This', 'Is', 'My', 'Folder'))


def test_includedVersionsIn_same_thing(some_versions, branch_version, unix_folder_version, windows_folder_version):  # noqa: E304
    assert branch_version.includedVersionsIn(some_versions + [branch_version]) == [branch_version]
    assert unix_folder_version.includedVersionsIn(some_versions + [unix_folder_version]) == [unix_folder_version]
    assert windows_folder_version.includedVersionsIn(some_versions + [windows_folder_version]) == [windows_folder_version]


@pytest.mark.parametrize('rule, expected_result', [
    ('5.2.1', [Version('5.2.1')]),
    ('>=4.8.4', [Version('5.0.0'), Version('5.2.1')]),
    ('<5.0.0', [Version('3.2.1'), Version('4.2.1')]),
    ('<6.8.4', [Version('3.2.1'), Version('4.2.1'), Version('5.0.0'), Version('5.2.1')])
])

def test_includedVersionsIn_with_branch_and_folder(rule, expected_result, some_versions, branch_version, unix_folder_version, windows_folder_version):  # noqa: E304
    assert Version(rule).includedVersionsIn(some_versions + [branch_version]) == expected_result
    assert Version(rule).includedVersionsIn(some_versions + [unix_folder_version]) == expected_result
    assert Version(rule).includedVersionsIn(some_versions + [unix_folder_version]) == expected_result
