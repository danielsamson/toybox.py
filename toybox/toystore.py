# SPDX-FileCopyrightText: toybox.py contributors
#
# SPDX-License-Identifier: MIT

"""The toystore — a local, curated index of libraries you can use with toybox.py.

The original toystore was an online registry that mapped short names to repository
URLs. It was hosted by the original author and went away with him, taking every name
with it. This is its successor, and it is deliberately not a service: it is data that
ships inside the tool, so it cannot go offline, and it is version-controlled, so a fix
is a pull request rather than a request to someone.

It also does more than the original. The old registry answered "where does this name
live?"; this one answers "how do I actually use this?", which is the question that
turns out to matter, because a great many useful Lua libraries cannot be dropped into
a Playdate project unmodified.

WHY AN ADAPTATION IS SOMETIMES NEEDED. Playdate's `import` returns a file's value but
runs each file only once, so the FIRST import receives the value and every later one
receives nil. toybox generates that first import. A library written in the ordinary Lua
style — `local M = {} … return M` — therefore installs correctly, imports correctly, and
still leaves the game with nothing, because the value went into the generated line and
was dropped. Since we write that line, we can write a capturing one instead:

    middleclass = import 'github-dot-com/kikito/middleclass/middleclass.lua'

That needs two facts nothing can infer: which file is the entry point, and what to call
the value. Those are the `entry` and `global` fields below.

FIELDS

    provides   one line on what the library is. Shown by `toybox store content`.
    kind       'lua' (default) or 'c'.
    entry      entry file relative to the repo root, WITHOUT the .lua extension. Only
               needed when toybox's own discovery finds nothing — no `lua_import` in the
               library's Boxfile and no <repo>.lua / import.lua at the root or in source/.
    global     name to bind the imported value to. Omit for libraries that publish their
               own global; setting it there would shadow their API with whatever the file
               returns (usually nil).
    libpath    for a library that imports its OWN files by a path relative to the PROJECT
               root (rather than to itself), a map of {expected path: subfolder in the
               repo}. toybox builds a search root under toyboxes/.libpath/ containing
               those paths, and you compile with `pdc -I toyboxes/.libpath`. This is what
               makes an engine written to be copied into source/ usable as a dependency.
    note       a caveat a user needs before adding it.

A consuming project always overrides this table — see `config.imports` in the Boxfile —
so a stale entry is an inconvenience, never a wall.

ADDING AN ENTRY. Please verify before submitting: resolve the dependency, build a .pdx
that actually calls into the library, and say so in the pull request. Entries here are
meant to be trustworthy; a hopeful one is worse than an absent one.
"""

# key: 'owner/repo', lowercased for matching.
KNOWN = {
    # ── Playdate libraries that package themselves properly ──────────────────
    'ebeneliason/acetate': {
        'provides': 'Visual sprite-debugging overlay for the Simulator',
        'note': 'pins easy-pattern "1"; add easy-pattern as `1` or the two collide',
    },
    'whitebrim/animatedsprite': {
        'provides': 'Sprite class with imagetable animation and a state machine',
    },
    'ebeneliason/easy-pattern': {
        'provides': 'Animated 8x8 patterns with easing',
        'note': 'add as `1` if you also use acetate, which pins the 1.x line',
    },
    'ivansergeev/gfxp': {
        'provides': 'A library of fill patterns, published as the GFXP global',
        'note': 'its only tag, v2.0, is not valid semver, so it can only track master',
    },
    'nicmagnier/playdateldtkimporter': {
        'provides': 'Import LDtk level-editor tilemaps',
    },
    'risolvipro/librif': {
        'provides': 'Grayscale image encoding/reading with RLE compression',
        'kind': 'c',
    },
    'macvogelsang/pd-options': {
        'provides': 'Options/settings menu with saved preferences',
        'note': 'its Boxfile lua_import says "options.lua" but the file is at '
                'source/options.lua, so no import is generated — import it yourself',
    },
    'playdatesquad/pddialogue': {
        'provides': 'Dialogue system',
    },
    'possiblyaxolotl/pdparticles': {
        'provides': 'Particle effects',
        'note': 'GitHub repo frozen Aug 2025; development moved to Codeberg',
    },
    'mierau/playbox2d': {
        'provides': 'Port of box2d-lite physics to C for the Playdate',
        'kind': 'c',
    },
    'potch/playout': {
        'provides': 'UI layout / box-model library',
    },
    'nicmagnier/playdatesequence': {
        'provides': 'Animation sequences built from easing functions',
    },
    'robertcurry0216/pp-lib': {
        'provides': 'Platformer building blocks',
    },
    'robkohr/robkohr-mono-5x8-font-for-playdate': {
        'provides': 'Readable 5x8 monospaced font',
    },
    'robertcurry0216/roomy-playdate': {
        'provides': 'Stack-based scene management',
    },

    # ── Playdate frameworks that need an adaptation ──────────────────────────
    'noblerobot/nobleengine': {
        'provides': 'Game engine: scenes, transitions, input, settings, save data',
        'entry': 'Noble',
        'libpath': {'libraries/noble': ''},
        'note': 'compile with `pdc -I toyboxes/.libpath` — it imports its own modules by '
                'project-root path. No global: Noble.lua publishes its own',
    },
    'gamesrightmeow/playbit': {
        'provides': 'Game framework: its own graphics, timer, vector and geometry modules',
        'entry': 'playbit/playbit', 'global': 'playbit',
    },
    'aavagames/playdate-keyboard-based-menu-ui': {
        'provides': 'Menu navigated with the on-screen keyboard, roguelike in style',
        'entry': 'keyboard-based-menu/Menu', 'global': 'Menu',
    },

    # ── general Lua libraries, adapted ───────────────────────────────────────
    # Not written for Playdate, but widely used in Playdate games. Each needs a global
    # or the generated import swallows its return value. Note that the SDK already
    # covers some of this ground (playdate.timer, json, playdate.geometry.vector2D).
    'kikito/middleclass': {
        'provides': 'OOP: inheritance, metamethods, class variables, mixins',
        'global': 'middleclass',
    },
    'rxi/classic': {
        'provides': 'A tiny class module — minimal alternative to middleclass',
        'global': 'Object',
    },
    'rxi/lume': {
        'provides': 'Utility functions geared towards game development',
        'global': 'lume',
    },
    'rxi/tick': {
        'provides': 'Call a function after a delay or on an interval',
        'global': 'tick',
        'note': 'overlaps the SDK\'s playdate.timer',
    },
    'rxi/shash': {
        'provides': 'Spatial hash, for when pairwise collision checks get too slow',
        'global': 'shash',
    },
    'rxi/json.lua': {
        'provides': 'Lightweight JSON encode/decode',
        'entry': 'json', 'global': 'json',
        'note': 'overlaps the SDK\'s built-in json',
    },
    'nikaoto/deep': {
        'provides': 'Draw layers and a Z axis, via a schedule instead of z-sorting',
        'global': 'deep',
    },
    'kikito/bump.lua': {
        'provides': 'Collision detection for axis-aligned rectangles (AABB only)',
        'entry': 'bump', 'global': 'bump',
    },
    'bakpakin/tiny-ecs': {
        'provides': 'Entity-component-system',
        'global': 'tiny', 'entry': 'tiny',
    },
    'themousery/vector.lua': {
        'provides': '2D vectors, modelled on Processing\'s PVector',
        'entry': 'vector', 'global': 'vector',
        'note': 'overlaps the SDK\'s playdate.geometry.vector2D',
    },
    'wesleywerner/lua-star': {
        'provides': 'A* pathfinding, pure Lua',
        'entry': 'src/lua-star', 'global': 'luastar',
    },
}

# Checked and NOT usable, recorded so nobody re-derives it.
REJECTED = {
    'yonaba/jumper': 'ships only examples/ and specs/ on its default branch — no library tree.',
    'neil-morrison44/drawdate': 'a JavaScript project, not a Lua library.',
    'pictogrammers/memory': 'an icon set, not a Lua library.',
    'sheep42/prismatic-engine': 'resolves to a CMake/C tree with no importable Lua entry.',
}

ADAPTATION_FIELDS = ('entry', 'global')


def libPathsFor(url) -> dict:
    """{path to create: subfolder of the repo it points at}, or None."""
    return KNOWN.get(_key(url), {}).get('libpath')


def _key(url) -> str:
    """A Url object, or an 'owner/repo'-ish string, -> the lowercase match key.

    Url has no useful __str__ (it would give an object repr), so read its fields when
    they are there and fall back to text for Boxfile override keys and CLI arguments.
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
    """How to import a dependency: {'entry': ..., 'global': ...}, or None.

    `overrides` is the consuming project's `config.imports`, which always wins: this
    table is a default, not a decree. An override may set only `global` (keeping the
    entry) or only `entry`, so the two merge rather than replace.
    """
    key = _key(url)
    entry = KNOWN.get(key, {})
    found = {f: entry[f] for f in ADAPTATION_FIELDS if f in entry}

    if overrides:
        for raw_key, value in overrides.items():
            if _key(raw_key) != key:
                continue
            if isinstance(value, str):
                found['global'] = value            # shorthand: just the global
            elif isinstance(value, dict):
                for field in ADAPTATION_FIELDS:
                    if value.get(field):
                        found[field] = value[field]
                if 'global' in value and value['global'] is None:
                    found.pop('global', None)      # explicit null clears it
            break

    return found or None


def rejectionFor(name: str) -> str:
    """Why a library was checked and found unusable, or None.

    Matches a bare repo name too: someone asking about 'NobleEngine' deserves the
    reason, not a generic miss — that reason is the whole point of recording it.
    """
    key = _key(name)
    if key in REJECTED:
        return REJECTED[key]

    bare = name.strip().lower().split('/')[-1]
    for rejected_key, reason in REJECTED.items():
        if rejected_key.split('/')[-1] == bare:
            return reason

    return None


def find(name: str):
    """Look a toybox up by 'owner/repo', or by bare repo name if unambiguous.

    Returns (key, entry) or (None, [close matches]) so the caller can be helpful about
    a near miss rather than just failing.
    """
    key = _key(name)
    if key in KNOWN:
        return key, KNOWN[key]

    bare = name.strip().lower().split('/')[-1]
    matches = [k for k in KNOWN if k.split('/')[-1] == bare]
    if len(matches) == 1:
        return matches[0], KNOWN[matches[0]]
    if matches:
        return None, matches

    partial = sorted(k for k in KNOWN if bare and bare in k)
    return None, partial
