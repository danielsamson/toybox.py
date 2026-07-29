# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

class ArgumentError(Exception):
    """Error caused when command line arguments have something wrong in them."""
    pass


class DependencyError(Exception):
    """Error caused when a dependency cannot be resolved."""
    pass


class VersionsAreBehind(Exception):
    """`toybox latest --check` found pins behind their newest release.

    Its own type, not an ArgumentError: nothing is wrong with the command or the
    project — this is a reportable RESULT, and a caller (a CI gate, a pre-release
    script) needs to tell it apart from a genuine failure. Carries the count.
    """

    def __init__(self, count: int):
        self.count = count
        super().__init__(str(count) + ' pin(s) behind their latest release.')
