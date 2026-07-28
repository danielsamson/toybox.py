# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import os
import enum
import string

from semver import VersionInfo
from typing import List


class VersionIs(enum.Enum):
    """The possible outcomes of a comparison."""

    equal = 1
    less_than = 2
    less_than_or_equal = 3
    greater_than = 4
    greater_than_or_equal = 5


class VersionType(enum.Enum):
    """The different types of versions."""

    semver = 1
    branch = 2
    local = 3


class Version:
    """A helper class to compare dependency versions."""

    def __init__(self, version: str):
        """Create a version number from a string."""
        """Format can be simply a full semver version number (i.e. 3.2.5) to point to an exact version,"""
        """or a partial one (i.e. 3 or 3.2) to require any given major or minor version."""
        """It can also have a comparison operator as a prefix (i.e. '>3.0,2' or '<=3.4')."""

        self.operator = VersionIs.equal
        self.commit_hash = None
        self.asSemVer = None

        length = len(version)
        first_character = version[0]
        if length > 1:
            second_character = version[1]
        else:
            second_character = None

        if first_character == '/' or first_character == '~' or (second_character == ':' and first_character in string.ascii_letters):
            if first_character == '~':
                version = os.path.expanduser(version)

            self.original_version = version
            self.type = VersionType.local
        elif first_character == '>' or first_character == '<' or first_character in string.digits or (first_character == 'v' and second_character in string.digits):
            # -- The Boxfile's installed section records semver versions as
            # -- '<version>@<ref-hash>' so a moved tag can be detected later. Only strip
            # -- a suffix that plausibly IS a hash — a tag merely named like
            # -- '1.0.0@beta' must keep failing semver parsing exactly as it used to.
            maybe_version, _, maybe_hash = version.partition('@')
            if Version._looksLikeARefHash(maybe_hash):
                self.commit_hash = maybe_hash
                version = maybe_version

            self.original_version = version

            if first_character == '>':
                if version.startswith('>='):
                    self.operator = VersionIs.greater_than_or_equal
                    version = version[2:]
                else:
                    self.operator = VersionIs.greater_than
                    version = version[1:]
            elif first_character == '<':
                if version.startswith('<='):
                    self.operator = VersionIs.less_than_or_equal
                    version = version[2:]
                else:
                    self.operator = VersionIs.less_than
                    version = version[1:]

            if version[0] == 'v':
                version = version[1:]

            self.asSemVer = VersionInfo.parse(version)
            self.type = VersionType.semver
        else:
            components = version.split('@')
            if len(components) > 2:
                raise SyntaxError('Malformed branch version \'' + version + '\'.')

            if len(components) == 2:
                self.commit_hash = components[1]

            self.original_version = components[0]
            self.type = VersionType.branch

    def __eq__(self, other: 'Version'):
        if self.isBranch():
            return other.isBranch() and self.original_version == other.original_version and self.commit_hash == other.commit_hash
        elif self.isLocal():
            return other.isLocal() and self.original_version == other.original_version

        if other.asSemVer is None or self.asSemVer != other.asSemVer:
            return False

        if self.operator != other.operator:
            return False

        return True

    def __lt__(a: 'Version', b: 'Version'):
        return a.asSemVer < b.asSemVer

    def __gt__(a: 'Version', b: 'Version'):
        return a.asSemVer > b.asSemVer

    def __str__(self):
        if self.isLocal():
            version_string = self.original_version
        elif self.isBranch():
            version_string = self.original_version

            if self.commit_hash is not None:
                version_string += '@' + self.commit_hash
        else:
            switch = {
                VersionIs.equal: '',
                VersionIs.less_than: '<',
                VersionIs.less_than_or_equal: '<=',
                VersionIs.greater_than: '>',
                VersionIs.greater_than_or_equal: '>='
            }

            version_string = switch.get(self.operator) + str(self.asSemVer)

            if self.commit_hash is not None:
                version_string += '@' + self.commit_hash

        return version_string

    @classmethod
    def _looksLikeARefHash(cls, text: str) -> bool:
        # -- Abbreviated through SHA-256 lengths, hex only.
        if len(text) < 7 or len(text) > 64:
            return False

        return all(character in '0123456789abcdef' for character in text)

    def majorVersion(self) -> str:
        if self.asSemVer is None:
            return None

        return self.asSemVer.major

    def isBranch(self) -> bool:
        return self.type == VersionType.branch

    def isLocal(self) -> bool:
        return self.type == VersionType.local

    def includes(self, other: 'Version') -> bool:
        if other.operator != VersionIs.equal:
            raise SyntaxError('Right hand operand must be an exact version number, not a range.')

        other_is_branch = other.isBranch()
        other_is_local = other.isLocal()

        if self.operator is VersionIs.equal:
            self_is_branch = self.isBranch()
            if self_is_branch or other_is_branch:
                return self_is_branch == other_is_branch and self.original_version == other.original_version

            self_is_local = self.isLocal()
            if self_is_local or other_is_local:
                return self_is_local == other_is_local and self.original_version == other.original_version

            return other.asSemVer == self.asSemVer
        elif self.operator is VersionIs.less_than:
            return other_is_branch is False and other_is_local is False and other.asSemVer < self.asSemVer
        elif self.operator is VersionIs.less_than_or_equal:
            return other_is_branch is False and other_is_local is False and other.asSemVer <= self.asSemVer
        elif self.operator is VersionIs.greater_than:
            return other_is_branch is False and other_is_local is False and other.asSemVer > self.asSemVer
        else:
            return other_is_branch is False and other_is_local is False and other.asSemVer >= self.asSemVer

    def includedVersionsIn(self, versions: List['Version']) -> List['Version']:
        result = []

        for version in versions:
            if self.includes(version):
                result.append(version)

        return result

    @classmethod
    def maybeRangeFromIncompleteNumericVersion(cls, version: str) -> str:
        operator = ''
        rest = version

        if rest[0] == '>' or rest[0] == '<':
            if len(rest) > 1 and rest[1] == '=':
                operator = rest[:2]
                rest = rest[2:]
            else:
                operator = rest[:1]
                rest = rest[1:]

            if len(rest) == 0:
                raise SyntaxError('Malformed version \'' + version + '\' (nothing after the operator).')

        # -- Tags commonly carry a leading 'v'; treat 'v1.2' exactly like '1.2'.
        if rest[0] == 'v' and len(rest) > 1 and rest[1] in string.digits:
            rest = rest[1:]

        if rest[0] not in string.digits:
            return [version]

        components = rest.split('.')
        nb_of_components = len(components)
        if nb_of_components > 3:
            raise SyntaxError('Malformed version \'' + version + '\' (too many components).')

        # -- If we're missing any minor or patch numbers, we set them as 0.
        nb_of_components_added = 3 - nb_of_components
        rest += '.0' * nb_of_components_added

        if operator != '':
            # -- An explicit comparison is already a range; just complete the number
            # -- (constructing the Version validates it).
            completed = operator + rest
            Version(completed)
            return [completed]

        if nb_of_components_added == 0:
            Version(rest)
            return [rest]

        # -- A partial number like '1' or '1.2' means 'any version with this prefix'.
        new_version = Version('>=' + rest)
        versions = ['>=' + rest]

        if nb_of_components_added == 1:
            versions.append('<' + str(new_version.asSemVer.bump_minor()))
        else:
            versions.append('<' + str(new_version.asSemVer.bump_major()))

        return versions
