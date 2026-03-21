# KotorBlender

This add-on is a fork of KotORBlender 1.01 by Purifier and Ndix UR, upgraded to support Blender versions 2.80 and above, which are notable by a redesigned user interface and a new real-time render engine. KotORBlender is in turn based on NeverBlender by Symmetric, forked from version 1.23a.

Significant changes have been introduced since KotORBlender 1.01, including, but not limited to, replacing ASCII model import/export with binary format, and ability to import/export layouts and path files.

## Features

- Import & export MDL models, including animations and walkmeshes; import `.wok` / `.pwk` / `.dwk` alone via **File → Import** or drag-and-drop
- Import & export LYT files
- Import & export PTH files
- Lightmap texture baking
- Area minimap rendering
- **Game Installation Browser** - Browse and select KotOR game installations
- **Module Browser** - Browse module resources (Core, Modules, Override, Textures, Saves)
- **Resource Creation** - Create new KotOR resource files (UTC, UTP, UTD, UTI, UTS, UTT, UTM, UTW, UTE, DLG, NSS, TLK, ERF, GFF)
- **Resource Editors** - Edit KotOR resource files with dedicated property panels
- **Module Operations** - Pack/unpack modules, extract resources, extract textures
- **Texture Operations** - Convert TPC/TGA, batch convert textures
- **Toolset Features** - Module Designer, Indoor Map Builder, File Search, KotorDiff, TSLPatchData Editor
- **Save Game Editor** - Edit KotOR save game files
- **PyKotor** - Required for module browser, archives, and most KotOR file tooling; **bundled as wheels** in official release zips (see Installation)

## Compatibility

Current version of KotorBlender is fully compatible with Blender versions 3.6, 4.2, and 5.0.

**Format notes:** TPC and TXI textures are read-only (import only). TGA is supported via Blender. For E2E testing with extracted game assets, see [TESTING.md](TESTING.md) (requires `DATA_DIR`). Blender development moves fast and is known to introduce breaking changes, therefore compatibility with any other version of Blender is not guaranteed.

## Installation

### From DeadlyStream

1. Download latest release of KotorBlender from [Deadly Stream](https://deadlystream.com/files/file/1853-kotorblender-for-blender-293/)
1. Install extension from disk as described in [Blender documentation](https://docs.blender.org/manual/en/4.2/editors/preferences/extensions.html#bpy-ops-extensions-package-install-files)

### From GitHub

1. Clone [GitHub repository](https://github.com/seedhartha/kotorblender)
1. When using Blender 4.2+ (including 5.0), create a symlink to **io_scene_kotor** directory in current user's Blender extensions directory:
    1. Set cloned repository as current directory
    1. Create a symlink on Windows: `mklink /D "%APPDATA%\Blender Foundation\Blender\5.0\extensions\user_default\io_scene_kotor" "%CD%/io_scene_kotor"` (adjust version number as needed)
    1. Create a symlink on Linux: `ln -s $(pwd)/io_scene_kotor ~/.config/blender/5.0/extensions/user_default/io_scene_kotor` (adjust version number as needed)
1. When using Blender 3.6, create a symlink to **io_scene_kotor** directory in current user's Blender addons directory:
    1. Set cloned repository as current directory
    1. Create a symlink on Windows: `mklink /D "%APPDATA%\Blender Foundation\Blender\3.6\scripts\addons\io_scene_kotor" "%CD%/io_scene_kotor"`
    1. Create a symlink on Linux: `ln -s $(pwd)/io_scene_kotor ~/.config/blender/3.6/scripts/addons/io_scene_kotor`

**PyKotor:** Blender extensions are **not** normal Python packages — there is no `pip install` when the user clicks Install. Dependencies must be **wheel files inside the .zip**; Blender installs them when you enable the add-on. Official releases are built with **`make build`**, which downloads PyKotor from PyPI and packs it into the zip. **Symlink from git:** run **`make wheel-download`** once (lighter than a full zip build). On Windows use `PYTHON=python` if `python3` is not on `PATH`. See `io_scene_kotor/wheels/README.md`.

## Usage

### Data Preparation

Extract models, textures, walkmeshes, LYT and PTH files into a working directory, using a tool of your choice, e.g. [reone toolkit](https://deadlystream.com/files/file/1862-reone-toolkit/). Recommended directory structure:

- *data* — extract all BIF archives here without subdirectories
- *texturepacks*
  - *swpc_tex_tpa* — extract swpc_tex_tpa ERF archive here

If you plan to edit textures, batch-convert TPC to TGA / TXI files using **reone toolkit**, although TPC textures are also supported by KotorBlender.

### Model Import and Export

1. Import via File → Import → KotOR Model (.mdl)
1. Select top-level MDL root object to be exported
1. Export via File → Export → KotOR Model (.mdl)

### Editing Animations

To edit list of model animations and corresponding events, select MDL root object and navigate to Object → KotOR Animations. KotorBlender supports both object and armature-based edits. To create an armature from objects, navigate to KotOR Animations → Armature and press Rebuild Armature and Apply Object Keyframes. Before exporting a model, make sure to copy armature keyframes back to objects by pressing Unapply Object Keyframes.

### Lightmapping

1. Select objects for which you want lightmaps to be recreated, or unselect all objects to recreate all lightmaps
1. Press KotOR → Lightmaps → Bake (auto)
1. Open and save each individual lightmap image from UV Editing tab

UV mapping:

1. Select objects having the same lightmap texture and enter Edit mode
1. For every object, ensure that `UVMap_lm` UV layer is active
1. Select all faces and unwrap UVs via UV → Lightmap Pack, increase Margin to avoid face overlapping

Fine-tuning:

1. Increase lightmap image size via UV Editing → Image → Resize
1. Tweak ambient color via Scene → World → Surface → Color
1. Manually toggle rendering of objects in Outliner and press KotOR → Lightmaps → Bake (manual)
1. In Scene → Render, set Device to GPU Compute to improve performance, set Render Engine to Cycles if not already
1. In Scene → Render → Sampling → Render increase Max Samples to improve quality

### Minimap Rendering

1. Press KotOR → Minimap → Render (auto)
1. Open "Render Result" image in UV Editing tab and save it as "lbl_map{modulename}.tga"
1. Open "MinimapCoords" text in Scripting tab and copy-paste generated properties into module .ARE file using any GFF editor

Fine-tuning:

1. Tweak background color via Scene → World → Surface → Color
1. Manually toggle rendering of objects in Outliner and press KotOR → Minimap → Render (manual)

### Connecting Rooms

1. Select a room walkmesh
1. Enter Edit mode and select two vertices adjacent to another room
1. Determine 0-based index of the other room into the LYT file
1. Enter Vertex Paint mode and set brush color to (0.0, G, 0.0), where G = (200 + room index) / 255
1. Ensure that brush blending mode is set to Mix, and brush strength is set to 1.0
1. Paint over the selected vertices

### Editing Paths

1. Extract PTH file from the module's RIM file, e.g. "modules/danm13_s.rim" (Kotor Tool, reone toolkit, etc.)
1. Import PTH into Blender via File → Import → KotOR Path (.pth)
1. Create/move path points, or modify path connections via Object Properties
1. Export PTH via File → Export → KotOR Path (.pth)

### Game Installation and Module Browser

1. Navigate to Scene Properties → KotOR Game Installation
1. Select game type (KotOR 1, KotOR 2, or Custom Path)
1. Click "Refresh Modules" to discover available modules
1. Select a module and click "Open Module" to browse its resources
1. Use the Module Browser panel in the 3D Viewport sidebar to browse resources by type
1. Extract resources or open them in appropriate editors

### Resource Creation and Editing

1. Create new resources via Editor → KotOR → Resources → New
1. Edit existing resources via Editor → KotOR → Editors
1. Resource property panels appear in Object Properties when a resource object is selected
1. Use File → Import → KotOR Module to import entire modules
1. Use File → Import → KotOR Save Game to edit save game files

## Contributing and testing

- **[CONTRIBUTING.md](CONTRIBUTING.md)** — How to contribute, run tests, and submit pull requests.
- **[TESTING.md](TESTING.md)** — E2E testing with game assets. For asset-free tests and Makefile targets, see [AGENTS.md](AGENTS.md).

## License

[GPL 3.0 or later](LICENSE)
