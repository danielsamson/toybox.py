# SPDX-FileCopyrightText: toybox.py contributors
#
# SPDX-License-Identifier: MIT

"""The adaptation registry — how to consume libraries that aren't packaged as toyboxes.

WHY THIS EXISTS. Playdate's `import` returns a file's value but runs each file only
once, so the FIRST import gets the value and every later one gets nil. toybox generates
the first import, which means a library written in the ordinary Lua style —
`local M = {} … return M` — installs correctly, imports correctly, and still leaves the
game with nothing. The value went into the generated line and was discarded.

That is fixable from here, because we WRITE that line. Given a global name we can emit

    Noble = import 'github-dot-com/NobleRobot/NobleEngine/Noble.lua'

and the value is captured instead of dropped. No shim repo, no vendored copy, no patch,
and no cooperation needed from upstream.

This table is the curated knowledge of how to do that per library — the successor to the
original toystore, which mapped names to URLs and died with the server that hosted it.
This one maps repos to the two facts you cannot guess (which file is the entry point, and
what to call the value) and ships inside the tool, so it cannot go offline.

    ENTRY  the file to import, relative to the repo root, WITHOUT the .lua extension.
           Needed when toybox's own discovery finds nothing — no `lua_import` in the
           library's Boxfile and no <repo>.lua / import.lua at the root or in source/.
    GLOBAL the name to bind the imported value to. Omit for libraries that already
           publish their own global; setting it then would shadow their API with
           whatever the file happens to return (usually nil).

A consuming project always wins over this table — see `config.imports` in the Boxfile —
so a wrong or stale entry here is an inconvenience, never a wall.

PRs adding entries are welcome. Please verify before submitting: resolve the dependency,
build a .pdx that actually calls into the library, and say so in the PR.
"""

# key: 'owner/repo' exactly as it appears in a Boxfile url, lowercased for matching.
REGISTRY = {
    # ── Playdate frameworks ──────────────────────────────────────────────────
    'gamesrightmeow/playbit':      {'entry': 'playbit/playbit',  'global': 'playbit'},
    'aavagames/playdate-keyboard-based-menu-ui':
                                   {'entry': 'keyboard-based-menu/Menu', 'global': 'Menu'},

    # ── general Lua libraries commonly used in Playdate games ────────────────
    # toybox already finds the entry file for most of these (the filename matches the
    # repo), so only the global is needed — without it the generated import consumes
    # the return value and the game sees nothing.
    'kikito/middleclass':          {'global': 'middleclass'},
    'rxi/classic':                 {'global': 'Object'},
    'rxi/lume':                    {'global': 'lume'},
    'rxi/tick':                    {'global': 'tick'},
    'rxi/shash':                   {'global': 'shash'},
    'rxi/json.lua':                {'entry': 'json',             'global': 'json'},
    'nikaoto/deep':                {'global': 'deep'},
    'kikito/bump.lua':             {'entry': 'bump',             'global': 'bump'},
    'bakpakin/tiny-ecs':           {'entry': 'tiny',             'global': 'tiny'},
    'themousery/vector.lua':       {'entry': 'vector',           'global': 'vector'},
    'wesleywerner/lua-star':       {'entry': 'src/lua-star',     'global': 'luastar'},
}

# NOT adaptable, recorded so nobody re-derives it:
#
#   NobleRobot/NobleEngine   Noble.lua imports its own modules by PROJECT-root-relative
#                            path ("libraries/noble/modules/..."), which cannot resolve
#                            from inside toyboxes/. An entry point and a global are not
#                            enough; this needs an upstream change or a vendored copy.
#   Yonaba/Jumper            ships only examples/ and specs/ at its default branch —
#                            no library tree to import.
#   neil-morrison44/drawdate a JavaScript project, not a Lua library.
#   Pictogrammers/Memory     an icon set, not a Lua library.
#   Sheep42/prismatic-engine resolves to a CMake/C tree with no importable Lua entry.


def _key(url) -> str:
    """A Url object, or an 'owner/repo'-ish string, -> the lowercase match key.

    Url has no useful __str__ (it would give an object repr), so read its fields when
    they are there and fall back to text for Boxfile override keys.
    """
    username = getattr(url, 'username', None)
    repo_name = getattr(url, 'repo_name', None)
    if username and repo_name:
        return (username + '/' + repo_name).lower()

    text = str(getattr(url, 'as_string', url)).strip().lower()
    if text.endswith('.git'):
        text = text[:-4]
    parts = [p for p in text.replace(':', '/').split('/') if p]
    return '/'.join(parts[-2:]) if len(parts) >= 2 else text


def adaptationFor(url, overrides=None) -> dict:
    """The adaptation for a dependency, or None.

    `overrides` is the consuming project's `config.imports`, which always wins: this
    table is a default, not a decree. An override may set only `global` (keeping the
    registry's entry) or only `entry`, so they merge rather than replace.
    """
    key = _key(url)
    found = dict(REGISTRY.get(key, {}))

    if overrides:
        for raw_key, value in overrides.items():
            if _key(raw_key) != key:
                continue
            if isinstance(value, str):
                # shorthand: "owner/repo": "GlobalName"
                found['global'] = value
            elif isinstance(value, dict):
                for field in ('entry', 'global'):
                    if value.get(field):
                        found[field] = value[field]
                # an explicit null clears the registry's suggestion
                if 'global' in value and value['global'] is None:
                    found.pop('global', None)
            break

    return found or None
