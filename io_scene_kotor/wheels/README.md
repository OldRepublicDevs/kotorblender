# Bundled Python wheels (PyKotor)

KotorBlender expects **PyKotor** for module browsing, packing, BIF listing, and related tools.

Blender extensions are **not** installed with `pip`, and Blender does **not** hit PyPI when a user
installs your `.zip`. The supported model is: wheels ship **inside** the extension; Blender installs
them when the add-on is enabled. Filenames must be listed in `../blender_manifest.toml` (no globs in
Blender 4.4+).

## Regenerate

From the **repository root**:

```bash
make wheel-download
```

To build a distributable zip (this runs `wheel-download` first unless `SKIP_WHEEL_DOWNLOAD=1`):

```bash
make build
```

This clears any previous `*.whl` here, runs `pip wheel "$(PYKOTOR_SPEC)"` (default **`pykotor==2.3.1`**
from the Makefile), then `helper_scripts/sync_extension_wheels.py` to rewrite `wheels = [...]` in
`blender_manifest.toml`.

On Windows, if `python3` is not on your PATH:

```powershell
make wheel-download PYTHON=python
```

## Git

`*.whl` files in this folder are **gitignored** (large binaries). **CI and release workflows**
download wheels before building the extension zip, so published packages include PyKotor.

For local development with a **symlinked** extension, run `make wheel-download` once after clone.
