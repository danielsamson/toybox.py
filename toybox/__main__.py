# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT

import sys
import traceback

from .toybox import Toybox
from .exceptions import ArgumentError

# -- This enables more debugging information for exceptions.
_debug_on: bool = False


def main():
    global _debug_on

    try:
        if '--debug' in sys.argv:
            print('Enabling debugging information.')
            _debug_on = True

        # -- Remove the first argument (which is the script filename)
        Toybox(sys.argv[1:]).main()
    except ArgumentError as e:
        print(str(e))
    except Exception as e:
        if _debug_on is True:
            print(traceback.format_exc())
        else:
            print(e)

        sys.exit(1)
    except KeyboardInterrupt:
        print('Execution interrupted by user.')
        pass


if __name__ == '__main__':
    main()
