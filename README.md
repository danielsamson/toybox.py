# toybox.py

[![MIT License](https://img.shields.io/badge/license-MIT-orange)](https://spdx.org/licenses/MIT.html)

A **Lua**, **C** and asset dependency manager for the [**Playdate**](https://play.date) **SDK**.

> **This is a community continuation.** The original **toybox.py** by
> [Didier Malenfant](https://pypi.org/project/toyboxpy/) was discontinued in 2025 and its
> repositories deleted; only the PyPI package and a
> [Software Heritage snapshot](https://archive.softwareheritage.org/browse/origin/directory/?origin_url=https://codeberg.org/DidierMalenfant/toybox.py.git)
> remained. This repo continues the project from those two sources under the same MIT
> license — see the first two commits for full provenance. The original commit history
> could not be recovered. The **toystore** (the author-hosted name registry) is gone, so
> the `store` command is retired and toyboxes are added by `<username>/<repo>`; everything
> else works as it always did. Moving a repo off the dead upstream? See
> [MIGRATING.md](MIGRATING.md) — a step-by-step playbook an agent can work through.

**toybox.py** is a Python port of [Jeremy McAnally](https://github.com/jm)'s toybox app. **toybox.py** lets you easily use, create and share third party libraries, called **toyboxes**, for any **Playdate** project. It handles all dependencies between **toyboxes** automatically and provides precise versioning for each **toybox**.

Some **toyboxes** may provide **C** code, some may provide **Lua** code or **Lua** extensions written in **C** and some may provide just assets. Some **toyboxes** may provide all three or only two of these, it's completely up to the **toybox** creator and maintainer.

Playdate is a registered trademark of [**Panic**](https://panic.com).

-----

**Table of Contents**

- [Installation](#installation)
- [Usage](#usage)
- [Using Lua toyboxes](#using-lua-toyboxes)
- [Using C toyboxes](#using-c-toyboxes)
- [Creating your own toyboxes](#creating-your-own-toyboxes)
- [License](#license)

### Installation

**toybox.py** is a pure Python project. It requires at least [Python](https://python.org) 3.9 and access to the [git](https://git-scm.com) command line tool.

You can install **toybox.py** by typing the following in a terminal window:

```console
pip install git+https://github.com/danielsamson/toybox.py
```

(The original author's final release is still on PyPI as
[toyboxpy](https://pypi.org/project/toyboxpy/) 1.4.0, but it is unmaintained and points
at servers that no longer exist — prefer this repo.)

### Usage

**toybox.py** supports various commands, sometimes with one or two extra arguments:

```console
toybox <options> <command> <arguments>
```

The following commands are supported:

```console
help <topic>             - Show a help message. topic is optional (use 'help topics' for a list).
version                  - Get the current version.
license                  - Show the license for the app.
info                     - List your current dependencies.
add <name/url> <version> - Add a new dependency (version is optional).
remove <name/url>        - Remove a dependency.
update <name/url>        - Update a dependency or all dependencies if no argument is provided.
check                    - Check for updated toyboxes.
store <subcommand>       - Retired: the toystore went away with the original project.
set <name> <value>       - Set a configuration value for this toybox.
setupMakefile            - Setup a basic makefile project for using C toyboxes.
```

The following options are supported:

```console
--help/-h                - Show a help message.
--force/-f               - Forces the execution of some commands, even if things seem up to date.
--local/-l <folder>      - Update the dependencies as local, if found in this folder.
--debug                  - Enable extra debugging information.
```

**toybox.py** should always be run from your project's root folder. Although it doesn't use and `git` commands directly on your project folder, some `git` commands that **toybox.py** uses do require that your project folder already be a `git` repo. A simple `git init` suffices. This also makes it easy for you to back-track any unwanted changes.

**toybox.py** creates and uses a local file at the root of your project's folder named `Boxfile`. You can use the `add` and `remove` commands to modify it.

#### Adding dependencies

The `add` command takes up to two arguments:

```console
toybox add <name/url> <version>
```

The first argument is the **git** repository which contains the **toybox** you would like to add, as a full url or a `username/repo` shorthand. All of the forms below point to the same repository:

``` console
toybox add https://github.com/ebeneliason/easy-pattern
toybox add github.com/ebeneliason/easy-pattern
toybox add ebeneliason/easy-pattern
```

(Bare names like `toybox add easy-pattern` used to be resolved through the **toystore**, an author-hosted registry that went away with the original project — use the `username/repo` form instead.)

**toyboxes** do not need to be hosted on [Github](https://github.com) but, as shown above, if the server url is omitted then Github is assumed.

Adding a dependency with a `name` or `url` which already exists for your project will replace the `version` used for that dependency.

The `version` parameter is optional and allows you to select a specific or a range of versions for the **toybox** such as `1.4.12`. If no `version` argument is provided then the lastest version of the latest major version of the **toybox**'s repo, if available, is used.

You can also require a specific minor version with `1.4` or a specific major version with `1`. In that case, the latest version with the given minor or major version numbers will be used which allows a developer using your **toybox** to stay up to date with bug fixes or new features without risking an API change from breaking your project.

If you would like to fine tune your version requirement even more, you can instead use up to two comparaison operators in the `version` argument. For example `'>1.2.3 <=3.0.0'`. Keep in mind that, here too, valid [semver](https://semver.org) version numbers should be used. Major or minor versions can be still used in combination with comparaisons. For example, a version requirement like `'3 <3.9.0'` results in all versions higher or equal to `3.0.0` but less than `3.9.0`. Supported comparaison operators are `>`, `<`, `>=`, `<=`.

You can also specify the name of a branch when, for example, using a development version of a given **toybox**. In that case, the latest commit from that branch is used when updating.

``` console
toybox add modplayer develop
```

There may be times, like during development of a **toybox**, when you'll want to use a local version of a **toybox** instead of one found on a server. In order to do that, just replace `version` by the path to the local folder that contains your **toybox** and then use the `update` command. This path need to start with either `~` or `/`. In order to prevent you from committing files that come from a local **toybox** by mistake, using local **toyboxes** will also create a pre-commit hook that will prevent you from making any commits while local **toyboxes** are used.

Note that you can do this temporarily by using the `-l` option together with the `update` command described below.

On **macOS** and **linux**, the content of a local **toybox** is be soft-linked inside your project instead of copied. This way, any modifications you make during development will modify the actual local **toybox** directly. On **Windows**, the files from the local **toybox** are just copied over.

In order to restore everything after using local **toyboxes**, just add the regular version back and use the `update` command again.

#### Removing dependencies

You can remove a **toybox** with the remove command:

```console
toybox remove <name/url>
```

#### Updating dependencies

Once you've added or modified a dependency, you can update its content within your project by using the `update` command:

```console
toybox update <name/url>
```

If no `dependency` argument is used then all dependencies are updated.

**toybox** records the current version of any dependency installed in your project so keep in mind that this may modify the `Boxfile` for your project.

If you already have all your dependencies up to date then `update` will have no effect. If you need to force your dependencies to update, you can use the `-f` option.

```console
toybox -f update <name/url>
```

If you have local versions of **toyboxes** that you want to use instead of the ones found at the URL provided in the Boxfile, for example when you are testing changes on those **toyboxes** locally, you could modify each **toybox** entry separately but you can also use the `-l` option:

```console
toybox -l <folder> update
```

This will update all your dependencies and for any of those, if the **toybox** is found inside `folder` then this local version will be used instead. You can then simply use a regular `toybox update` to put everything back in place and use the online content of the repos again.

#### Checking for updates

You can check to see if any of the **toyboxes** you use have been updated by using the `check` command:

```console
toybox check
```

This will not modify anything within your project, it will just let you know if anything new is available for you.

### Using Lua toyboxes

Any **toybox** will be installed in a subfolder named `toyboxes` at the root folder of your project. If any of the **toyboxes** provides **Lua** code, a file named `toyboxes.lua` will be created in that folder. All you need to do to start using your **toyboxes** is import that file anywhere in your project.

Assuming you are using the standard [project structure](https://sdk.play.date/1.12.2/Inside%20Playdate.html#_structuring_your_project) suggested by the **Playdate SDK** and have your **Lua** source files in a subfolder named `source` then you can do this by adding this import statement in any file that uses the **toyboxes**:

```lua
import '../toyboxes/toyboxes.lua'
```

Note that due to a bug in the `pdc` app used by the **Playdate SDK** to process source files, the `.lua` extension is required here. Once this bug is fixed, this will no longer be needed.

### Using C toyboxes

Any **toybox** will be installed in a subfolder named `toyboxes` at the root folder of your project. If any of the **toyboxes** provides **C** code, a file named `toyboxes.mk` and a file named `toyboxes.h` will be created in that folder.

Assuming your makefile is in your project's root folder, you will need to include this makefile in your own before you include the **Playdate** SDK's common makefile:

```make
include toyboxes/toyboxes.mk

...

include $(SDK)/C_API/buildsupport/common.mk
```

You will then need to call the **toyboxes** init macro `REGISTER_TOYBOXES` during the `kEventInitLua` event and pass it a `PlaydateAPI*`:

```c
#include "toyboxes.h"

#include "pd_api.h"

int eventHandler(PlaydateAPI* playdate, PDSystemEvent event, uint32_t arg)
{
    if(event == kEventInitLua) {
        REGISTER_TOYBOXES(playdate)
    }
    
    return 0;
}
```

If you don't know how to or your project doesn't already use **C** extensions, you can use the `setupMakefile` command to create a bare bones makefile project, like the one above, in the current folder. Remember that makefile projects need to be built with `make` and not `pdc`.

### Using assets from toyboxes

If you want, or need, to access a **toybox**'s assets directly they will, if any, be located in a folder named `toybox_assets` inside the `source` folder of your project. The folder is organised by **toybox** URLs so, for example, an asset named `MyPic` in a **toybox** named `MyRepo` from user `Usernmame` on `github` will be located at
```
source/toybox_assets/github.com/Username/MyRepo/MyPic
```
Usually **toyboxes** should provide **Lua** methods to access their assets so you shouldn't need to do this.

### Using luacheck

If any of the **toyboxes** provide [`luacheck`](https://github.com/lunarmodules/luacheck) configuration in a [supported format](#adding-luacheck-globals), then **toybox.py** will generate a file named `luacheck.lua` inside the `toyboxes` folder. This file can be used to import this `luacheck` configuration in your project's `.luacheckrc`, for example, like this:

```lua
require "toyboxes/luacheck" (stds, files)

std = "lua54+playdate+toyboxes"

operators = {"+=", "-=", "*=", "/="}
```

Make sure to always run `luacheck` from the root folder of your project in order for these definitions to work correctly. (The original author's Luacheck fork with compound-operator support went away with the rest of his repos.)

### The toystore (retired)

The **toystore** was an online registry of known **toyboxes** so that they could be referred to by only their names. It was hosted by the original author and was deleted when the project was discontinued, so the `store` subcommands are retired and bare names can no longer be resolved — refer to **toyboxes** by their `username/repo` form or full url instead. (Some library READMEs written in the toystore era still show bare-name commands like `toybox add somelib`; mentally substitute the `username/repo` form.)

### Finding toyboxes

Discovery now happens where the code lives:

- The [`playdate` topic on GitHub](https://github.com/topics/playdate) and a search for the "Toybox Compatible" badge surface most libraries.
- [awesome-playdate](https://github.com/sayhiben/awesome-playdate) and the [Playdate community wiki](https://playdate-wiki.com/wiki/SDK_Resources) are the curated lists.
- New libraries are usually announced on the [Playdate Developer Forum](https://devforum.play.date).

Known **toyboxes**, verified alive as of July 2026 — PRs adding entries are welcome:

<!-- BEGIN store table (generated by tools/gen_store_table.py) -->

| Toybox | Add with | Provides |
|---|---|---|
| [acetate](https://github.com/ebeneliason/acetate) | `toybox add ebeneliason/acetate` | Visual sprite-debugging overlay for the Simulator — pins easy-pattern "1"; add easy-pattern as `1` or the two collide |
| [animatedsprite](https://github.com/whitebrim/animatedsprite) | `toybox add whitebrim/animatedsprite` | Sprite class with imagetable animation and a state machine |
| [bump.lua](https://github.com/kikito/bump.lua) | `toybox add kikito/bump.lua` | Collision detection for axis-aligned rectangles (AABB only) — imported as `bump` |
| [classic](https://github.com/rxi/classic) | `toybox add rxi/classic` | A tiny class module — minimal alternative to middleclass — imported as `Object` |
| [deep](https://github.com/nikaoto/deep) | `toybox add nikaoto/deep` | Draw layers and a Z axis, via a schedule instead of z-sorting — imported as `deep` |
| [easy-pattern](https://github.com/ebeneliason/easy-pattern) | `toybox add ebeneliason/easy-pattern` | Animated 8x8 patterns with easing — add as `1` if you also use acetate, which pins the 1.x line |
| [gfxp](https://github.com/ivansergeev/gfxp) | `toybox add ivansergeev/gfxp` | A library of fill patterns, published as the GFXP global — its only tag, v2.0, is not valid semver, so it can only track master |
| [json.lua](https://github.com/rxi/json.lua) | `toybox add rxi/json.lua` | Lightweight JSON encode/decode — imported as `json`; overlaps the SDK's built-in json |
| [librif](https://github.com/risolvipro/librif) | `toybox add risolvipro/librif` | Grayscale image encoding/reading with RLE compression — **C toybox** |
| [lua-star](https://github.com/wesleywerner/lua-star) | `toybox add wesleywerner/lua-star` | A* pathfinding, pure Lua — imported as `luastar` |
| [lume](https://github.com/rxi/lume) | `toybox add rxi/lume` | Utility functions geared towards game development — imported as `lume` |
| [middleclass](https://github.com/kikito/middleclass) | `toybox add kikito/middleclass` | OOP: inheritance, metamethods, class variables, mixins — imported as `middleclass` |
| [pd-options](https://github.com/macvogelsang/pd-options) | `toybox add macvogelsang/pd-options` | Options/settings menu with saved preferences — its Boxfile lua_import says "options.lua" but the file is at source/options.lua, so no import is generated — import it yourself |
| [pddialogue](https://github.com/playdatesquad/pddialogue) | `toybox add playdatesquad/pddialogue` | Dialogue system |
| [pdparticles](https://github.com/possiblyaxolotl/pdparticles) | `toybox add possiblyaxolotl/pdparticles` | Particle effects — GitHub repo frozen Aug 2025; development moved to Codeberg |
| [playbit](https://github.com/gamesrightmeow/playbit) | `toybox add gamesrightmeow/playbit` | Game framework: its own graphics, timer, vector and geometry modules — imported as `playbit` |
| [playbox2d](https://github.com/mierau/playbox2d) | `toybox add mierau/playbox2d` | Port of box2d-lite physics to C for the Playdate — **C toybox** |
| [playdate-keyboard-based-menu-ui](https://github.com/aavagames/playdate-keyboard-based-menu-ui) | `toybox add aavagames/playdate-keyboard-based-menu-ui` | Menu navigated with the on-screen keyboard, roguelike in style — imported as `Menu` |
| [playdateldtkimporter](https://github.com/nicmagnier/playdateldtkimporter) | `toybox add nicmagnier/playdateldtkimporter` | Import LDtk level-editor tilemaps |
| [playdatesequence](https://github.com/nicmagnier/playdatesequence) | `toybox add nicmagnier/playdatesequence` | Animation sequences built from easing functions |
| [playout](https://github.com/potch/playout) | `toybox add potch/playout` | UI layout / box-model library |
| [pp-lib](https://github.com/robertcurry0216/pp-lib) | `toybox add robertcurry0216/pp-lib` | Platformer building blocks |
| [robkohr-mono-5x8-font-for-playdate](https://github.com/robkohr/robkohr-mono-5x8-font-for-playdate) | `toybox add robkohr/robkohr-mono-5x8-font-for-playdate` | Readable 5x8 monospaced font |
| [roomy-playdate](https://github.com/robertcurry0216/roomy-playdate) | `toybox add robertcurry0216/roomy-playdate` | Stack-based scene management |
| [shash](https://github.com/rxi/shash) | `toybox add rxi/shash` | Spatial hash, for when pairwise collision checks get too slow — imported as `shash` |
| [tick](https://github.com/rxi/tick) | `toybox add rxi/tick` | Call a function after a delay or on an interval — imported as `tick`; overlaps the SDK's playdate.timer |
| [tiny-ecs](https://github.com/bakpakin/tiny-ecs) | `toybox add bakpakin/tiny-ecs` | Entity-component-system — imported as `tiny` |
| [vector.lua](https://github.com/themousery/vector.lua) | `toybox add themousery/vector.lua` | 2D vectors, modelled on Processing's PVector — imported as `vector`; overlaps the SDK's playdate.geometry.vector2D |

Browse the same data from the command line with `toybox store content`, and get
the detail for one entry — including how it is imported — with `toybox store info
<name>`.

<details>
<summary>Checked and <b>not</b> usable as toyboxes (5)</summary>

Recorded so the reasoning is not re-derived. See `toybox store info <name>`.

- **[drawdate](https://github.com/neil-morrison44/drawdate)** — a JavaScript project, not a Lua library.
- **[nobleengine](https://github.com/noblerobot/nobleengine)** — Noble.lua imports its own modules by project-root-relative path ("libraries/noble/modules/..."), which cannot resolve from inside toyboxes/. Needs an upstream change or a vendored copy.
- **[memory](https://github.com/pictogrammers/memory)** — an icon set, not a Lua library.
- **[prismatic-engine](https://github.com/sheep42/prismatic-engine)** — resolves to a CMake/C tree with no importable Lua entry.
- **[jumper](https://github.com/yonaba/jumper)** — ships only examples/ and specs/ on its default branch — no library tree.

</details>

<!-- END store table -->

Three entries need a small workaround, summarised in the table above and spelled out here.
All three are in the **toyboxes** themselves, not in **toybox.py**, and all were found by
installing every listed toybox into one project and building it.

**`acetate` and `easy-pattern` cannot both be added with default versions.**
`acetate`'s own `Boxfile` pins `easy-pattern` to `"1"`, but `easy-pattern` has since
released `2.0.0`, so a bare add of the latter picks `2` and resolution stops:

```console
Can't resolve version with '>=1.0.0 <2.0.0 >=2.0.0 <3.0.0' for 'github.com/ebeneliason/easy-pattern'.
```

Pin the major version explicitly and both install:

```console
toybox add ebeneliason/easy-pattern 1
```

**`pd-options` installs but generates no import.** Its `Boxfile` declares
`"lua_import": "options.lua"` while the file ships at `source/options.lua`, and
`lua_import` is resolved from the repo root without searching subfolders:

```console
Warning: Could not find file 'options.lua' to import in 'pd-options'.
```

Until upstream changes that value to `source/options.lua`, import it yourself. `import`
resolves relative to the importing file, so from `source/main.lua` that is:

```lua
import '../toyboxes/toyboxes.lua'
import '../toyboxes/github-dot-com/macvogelsang/pd-options/source/options.lua'
```

**`GFXP` can only track `master` for now.** Its sole tag is `v2.0`, which is not
valid [semver](https://semver.org) (three components are required), so it cannot be
resolved as a version — `toybox add ivansergeev/gfxp 2` fails with
`Can't resolve version with '>=2.0.0 <3.0.0'`. A bare add correctly falls back to the
`master` branch and works; a `v2.0.0` tag upstream would make it pinnable.

### A note for toybox authors

Playdate's `import` is not Lua's `require`, and the difference decides whether a library
can be a **toybox** at all. Per *Inside Playdate*: `import` returns the file's value, but
**runs each file only once — a second `import` of the same file returns `nil`**. The SDK's
own example:

```lua
-- a.lua
return "hello"
-- b.lua
print("b says " .. (import "a" or "nil"))
-- main.lua
print(import "a" or "nil")
import "b"
--> hello
--> b says nil
```

That matters here because **toybox.py** generates an import line for every resolved
dependency, and *that* line is the first import. Its return value goes nowhere. So a
library written in the usual `local M = {} … return M` style installs correctly, is
imported correctly, and still leaves the game with nothing — by the time your code runs
`local M = import "thatlib"`, it returns `nil`.

A toybox should therefore publish a **global**:

```lua
GFXP = {}          -- reachable by any file after the generated import
-- return M        -- consumed by the generated import; your game sees nil
```

(Verified on the Simulator, not just read: a file that imports a `return M` module *first*
receives the value, and a later `import` of the same file receives `nil`.)

This is why many otherwise-excellent Lua libraries listed in
[awesome-playdate](https://github.com/sayhiben/awesome-playdate) are not in the table
above. They are good code; they just cannot be dropped in as **toyboxes** unmodified.

**Adopting one anyway.** Because **toybox.py** writes that first import, it can write a
*capturing* one instead, and the value is kept rather than dropped:

```lua
middleclass = import 'github-dot-com/kikito/middleclass/middleclass.lua'
```

No shim repo, no vendored copy, no patch, and nothing needed from upstream. Two things
are required that cannot be guessed — which file is the entry point, and what to call the
value — so they are declared.

**In your own `Boxfile`**, which always wins:

```json
{
    "toyboxes": { "github.com/kikito/middleclass": "4" },
    "config": {
        "imports": {
            "kikito/middleclass": "middleclass",
            "GamesRightMeow/playbit": { "entry": "playbit/playbit", "global": "playbit" }
        }
    }
}
```

The string form is shorthand for just the global. `"global": null` suppresses capturing
for a library that publishes its own global.

**Or from the bundled registry**, [`toybox/registry.py`](toybox/registry.py) — a curated
table of libraries already known to work this way, so a project (or an automated build)
gets them with no configuration at all. It is the successor to the toystore: where that
mapped names to URLs and died with the server hosting it, this maps repos to the packaging
knowledge you would otherwise have to rediscover, and ships inside the tool. Every entry
is verified by resolving it and compiling a `.pdx`; PRs are welcome on the same terms.

**What this cannot fix.** A library whose *internal* imports are project-root-relative
still will not work from inside `toyboxes/`. NobleEngine is the example: `Noble.lua` does
`import "libraries/noble/modules/..."`, which has no meaning from a dependency folder. An
entry point and a global are not enough; that needs an upstream change or a vendored copy.
`registry.py` records the cases like this that were checked and rejected, so nobody has to
work it out twice.

This table folds in every surviving entry of the original **toystore** registry, whose
final state (crawled 2024-05-15) is preserved verbatim in
[docs/toystore-2024-05.toml](docs/toystore-2024-05.toml). Not everything survived: the
original author's own libraries — **Aspen** (platformer engine), **modplayer** (Amiga
module player), **pdbase** (SDK utilities), **Plupdate** (update manager), **Signal**
(pub/sub), **TileMap**, and **TiledUp** (Tiled importer) — were deleted with his
accounts. At least Signal, TileMap, and TiledUp have
[Software Heritage](https://archive.softwareheritage.org) snapshots and could be revived
by a willing maintainer, the same way this repo was.

Remember that a **toybox** does not have to be listed anywhere, or even know about **toybox.py**, to be usable: any git repo that follows the usual **Playdate** source layout can be added by its `username/repo` or url.

### Adding the toybox powered badge

If your projects use **toyboxes**, you can let others know that they are [![Toybox Powered](https://img.shields.io/badge/toybox.py-powered-orange)](https://github.com/danielsamson/toybox.py) by adding this badge to your `README.md` file:

```
[![Toybox Powered](https://img.shields.io/badge/toybox.py-powered-orange)](https://github.com/danielsamson/toybox.py)
```

### Creating your own toyboxes

Of course the best part of **toybox.py** is that anyone can create, distribute and maintain their own **toyboxes** for others to use. All you need it a **git** repo (which can be located anywhere on the internet) and to make sure that some of your code is laid out in a way that **toybox** can process and understand.

For starters, the name of your **git** repo will be the name **toybox** uses for a lot of things. It's better not to use the name of an existing **toybox** as this could cause clashes with other **toyboxes**.

**toyboxes** can provide **Lua** methods, either written in **Lua** or in **C** as extensions to the **Lua** language, or **C** methods that can be used by others when writing their own **C** code for the **Playdate**. Your **toybox** can provide just one, two or all three of these types of extensions.

Versionning for **toyboxes** is done via tags in the git repo for your **toybox**. Those tags should be a valid [semver](https://semver.org) version and can optionally be prefixed by a `v`. For example `v2.3.0` is correct, `v2.3` is not. The most important part for users of your **toybox** is to make sure that you only fix issues when incrementing a patch version, that you only add new functionality when incrementing a minor version and that you always increment the major version when adding things to your **toybox** that may break things for your users (removing deprecated methods or changing the API for example).

It's usually a good idea, rather than provide a swiss-army knife type of **toybox**, to try and make sure your **toyboxes** provide just one service and do it well. Split different functionality into separate **toyboxes** so developers can only add the ones they need.

**toyboxes** can depend on other **toyboxes**. All you need is to add a `Boxfile` in the root folder of your **toybox** and it will be taken care of automatically when resolving dependencies. Be careful, during development for example, to not resolve that dependency directly in your project folder. You could end up committing the resulting **toyboxes** folder which would be redundant when others use your **toybox**. Instead you can use it as a local **toybox** in a test project.

A **Lua** **toybox** can depend on a **C** **toybox** and a **C** **toybox** can depend on another **C** **toybox**. You don't even need any extra import statements because any **Lua** **toyboxes** your **toybox** depends on should already be imported before your **toyboxe**'s import file is imported.

Try to make sure that **toyboxes** don't cross-depend on each other (**A** require **B** and **B** also requires **A**) as this is usually a sign of some API design issues and can complicate things in the long run.

#### Creating a Lua toybox

Creating a **Lua** **toybox** is as simple as adding one **Lua** file at the root to your project's repo or in a subfolder named `source` or `Source`. That file can be named `import.lua` or the same as your project and must contain all the import statements required to use your **toybox**. For example, the fictional `MyPdPi` **toybox**, if written in **Lua**, would contain one file named `MyPdPi.lua` which would look like this:

```lua
--
--  MyPdPi - Calculate Pi to an infinite number of decimals.
--

import "math"
import "picalc"
import "utils"
```

The source code itself in your **toybox** can be laid out any way you want (additional `Source` subfolder, etc...) as long as this file imports all the other files correctly.

If you wish to use a completely custom name or location for the **Lua** file **toybox** will import for your project, you can use the `set lua_import` command:

```console
toybox set lua_import mycustomfile.lua
```

This will create a `Boxfile` in your project, if one didn't already exist, and will set a configuration parameter for **toybox** to use that **Lua** file when importing your **toybox** instead of the default.

#### Creating a C toybox

Creating a **C** **toybox** is almost as simple and requires three things. First you need to create a makefile for your **toybox** in the root folder of your project and name it after your project. Once again, if the fictional `MyPdPi` **toybox** was written in **C**, it would contain one file named `MyPdPi.mk` which would look like this:

```make
#
#  MyPdPi - Calculate Pi to an infinite number of decimals.
#

# -- Find out more about where this file is relative to the Makefile including it
_RELATIVE_FILE_PATH := $(lastword $(MAKEFILE_LIST))
_RELATIVE_DIR := $(subst /$(notdir $(_RELATIVE_FILE_PATH)),,$(_RELATIVE_FILE_PATH))

# -- Add us as an include search folder only if it's not already there
uniq = $(if $1,$(firstword $1) $(call uniq,$(filter-out $(firstword $1),$1)))
UINCDIR := $(call uniq, $(UINCDIR) $(_RELATIVE_DIR))

# -- Add our source files.
SRC := $(SRC) \
       $(_RELATIVE_DIR)/MyPdPi/MyPdPi.c
```

The first section is very important and makes sure that the makefile is relocatable, i.e. can work no matter where the includer's makefile is located. The second part adds the root folder of your **toybox** as an include path. The last section adds the source files that need to be compiled for your **toybox**. Don't forget the `$(SRC)` on the first line to make sure that any previous sources files from other **toyboxes** are included.

The use of `:=` instead of `=` is also very important here as it forces make to resolve the value right here and there, instead of when it is used because it could have been overwritten by another **toybox** at that point.

If you wish to use a completely custom name or location for the makefile **toybox** will import for your project, you can use the `set makefile` command:

```console
toybox set makefile subfolder/OtherMakefile
```

This will create a `Boxfile` in your project, if one didn't already exist, and will set a configuration parameter for **toybox** to use that **Lua** file when importing your **toybox** instead of the default.

Header files for your project should be located in a subfolder named after your project, in our case `MyPdPi` and it should contain at least an include header named after your project, i.e. `MyPdPi.h` which, at a minimum, looks like this:

```c
/*
*  MyPdPi - Calculate Pi to an infinite number of decimals.
*/

#ifndef MYPDPI_H
#define MYPDPI_H

#include "pd_api.h"

// -- Globals
extern PlaydateAPI* pd;

// -- toybox registration function
void register_MyPdPi(PlaydateAPI* playdate);

#endif
```

If you wish to use a completely custom name or location for the include file **toybox** will import for your project, you can use the `set include_header` command:

```console
toybox set include_header Folder/OtherHeader.h
```

This will create a `Boxfile` in your project, if one didn't already exist, and will set a configuration parameter for **toybox** to use that **Lua** file when importing your **toybox** instead of the default.

As shown above, your **toybox** header file needs to declare at least one function and that's the function called during the `kEventInitLua` event. The name of that function needs to be `register_<toybox_name>` and take a `PlaydateAPI* playdate` as an argument. If you're registering extensions to the **Lua** language this is where that would take place.

You can also declare any other functions your **toybox** exposes or include any other header files that may be needed. If your **toybox** is just providing **C** code for other projects and doesn't require any particular initialisation you can leave this method empty or just grab the `PlaydateAPI*` for future use elsewhere in your code, like so:

```c
/*
 *  MyPdPi - Calculate Pi to an infinite number of decimals.
 */
 
#include "MyPdPi/MyPdPi.h"

// -- Globals
PlaydateAPI* pd = NULL;

// -- toybox registration function
void register_MyPdPi(PlaydateAPI* playdate)
{
    pd = playdate;
}
```

#### Providing assets in your toybox

If your **toybox** uses or provides assets, they should be located in a folder named `assets` at the root of your **toybox** folder. This folder will be moved into the end-user's `source` folder during installation so that it can be accessible by `pdc` during compilation of the project. You will therefore need to use a specific path in order to reach those assets from your code.

For example, if our `MyPdPi` **toybox** contained an image named `MyPic.png` in `assets/images` and was available via a `github` repo named `MyRepo` from user `MyUsername` then accessing the asset can be done as follows:
```
image = playdate.graphics.image.new(`toybox_assets/github.com/MyUsername/MyRepo/images/MyPic`)
```
While this works when the code is internal to your **toybox**, when you need to provide assets to the end-user of your **toybox**, it is much more elegant to provide utility methods in order to access your assets, like this:
```
function MyPdPi.getMyPic()
    return playdate.graphics.image.new(`toybox_assets/github.com/MyUsername/MyRepo/images/MyPic`)
end
```
That way they do not have to deal with the path to your asset.

You can override the subfolder used for your **toybox**'s assets by using the `set assets_sub_folder` command:

```console
toybox set assets_sub_folder My/Custom/Path
```

This will create a `Boxfile` in your project, if one didn't already exist, and will set a configuration parameter for **toybox** to use that subfolder inside the **toybox_assets** folder. This is **not recommended** to use for production **toyboxes** as is could cause name collisions. It can still be useful if you forked a **toybox** repo for development but want to still keep the assets' path the same as the original repo.

### Adding luacheck globals

You can provide [`luacheck`](https://github.com/lunarmodules/luacheck) configuration info in your **toybox** that others using it can automatically benefit from. It needs to be in a supported format for **toybox.py** to detect and use it.

Just create a file named `Luacheck.lua` and place it in a folder named 'luacheck' in your project's root folder. This file will contain list of     `globals` or `read_globals` provided by your **toybox**:

```lua
-- Globals provided by MyPdPi.

return {
    globals = {
        MyPdPi = {
            fields = {
                super = {
                    fields = {
                        className = {},
                        init = {}
                    }
                },
                className = {},
                init = {},
                calculatePi = {}
            }
        }
    }
}
```

The format of this file follows similar rules to `luacheck`'s `.luacheckrc` [config file](https://luacheck.readthedocs.io/en/stable/config.html).

You can also still use this file for your **toybox**'s itself by creating a `.luacheckrc` like this one in your **toybox**:

```lua
stds.MyPdPi = require "luacheck/Luacheck"

std = "lua54+playdate+MyPdPi"

operators = {"+=", "-=", "*=", "/="}
```

#### Letting others know about your toybox

It's not required, but it's always a good idea, to add a word about **toybox.py** in the README.md of your **toybox** repo so developers know what it contains and how to use it:

```console
**MyPdPi** is a [**Playdate**](https://play.date) **toybox** which lets you calculate Pi to an infinite number of decimals.

You can add it to your **Playdate** project by installing [**toybox.py**](https://github.com/danielsamson/toybox.py), going to your project folder in a Terminal window and typing:

    toybox add MyGitHubUsername/MyPdPi
    toybox update

This **toybox** contains both **Lua** and **C** toys for you to play with.
```
You can also add a nice [![Toybox Compatible](https://img.shields.io/badge/toybox.py-compatible-brightgreen)](https://github.com/danielsamson/toybox.py) badge like this:

```
[![Toybox Compatible](https://img.shields.io/badge/toybox.py-compatible-brightgreen)](https://github.com/danielsamson/toybox.py)
```

### License

**toybox.py** is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
