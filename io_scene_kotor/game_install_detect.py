# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
# ##### END GPL LICENSE BLOCK #####

"""Heuristic KotOR 1 / KotOR 2 install discovery (registry, Steam, common paths).

Used when PyKotor's own discovery returns nothing or is unavailable. All checks
are logged at DEBUG for troubleshooting.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# --- Validation -----------------------------------------------------------------


def _has_chitin_key(path: str) -> bool:
    return os.path.isfile(os.path.join(path, "chitin.key"))


def is_probable_kotor1_install(path: str) -> bool:
    """K1: chitin.key present and not obviously a K2 folder."""
    if not path or not os.path.isdir(path):
        return False
    if not _has_chitin_key(path):
        return False
    if os.path.isfile(os.path.join(path, "swkotor2.exe")):
        return False
    base = os.path.basename(os.path.normpath(path)).lower()
    if "kotor 2" in base or "kotor2" in base or "sith lords" in base:
        return False
    return True


def is_probable_kotor2_install(path: str) -> bool:
    """K2: chitin.key + swkotor2.exe, or path name strongly suggests TSL."""
    if not path or not os.path.isdir(path):
        return False
    if not _has_chitin_key(path):
        return False
    if os.path.isfile(os.path.join(path, "swkotor2.exe")):
        return True
    base = os.path.basename(os.path.normpath(path)).lower()
    return (
        "kotor 2" in base
        or "kotor2" in base
        or "sith lords" in base
        or "tsl" in base
        or path.lower().rstrip("\\/").endswith("knights of the old republic ii")
    )


def explain_k1_rejection(path: str) -> str:
    """Human-readable reason :func:`is_probable_kotor1_install` is false."""
    if not path or not os.path.isdir(path):
        return "not an existing directory"
    if not _has_chitin_key(path):
        return "missing chitin.key at install root"
    if os.path.isfile(os.path.join(path, "swkotor2.exe")):
        return "swkotor2.exe present (looks like KotOR 2)"
    base = os.path.basename(os.path.normpath(path)).lower()
    if "kotor 2" in base or "kotor2" in base or "sith lords" in base:
        return "folder name suggests KotOR 2"
    return "failed internal K1 heuristic"


def explain_k2_rejection(path: str) -> str:
    """Human-readable reason :func:`is_probable_kotor2_install` is false."""
    if not path or not os.path.isdir(path):
        return "not an existing directory"
    if not _has_chitin_key(path):
        return "missing chitin.key at install root"
    base = os.path.basename(os.path.normpath(path)).lower()
    if not (
        "kotor 2" in base
        or "kotor2" in base
        or "sith lords" in base
        or "tsl" in base
        or path.lower().rstrip("\\/").endswith("knights of the old republic ii")
    ):
        return "no swkotor2.exe and folder name does not suggest TSL"
    return "failed internal K2 heuristic"


# --- Windows registry -----------------------------------------------------------


def _winreg_read_install_path(hive: int, subkey: str, value_name: str = "Path") -> str | None:
    try:
        import winreg
    except ImportError:
        return None
    try:
        with winreg.OpenKey(hive, subkey) as key:
            val, _ = winreg.QueryValueEx(key, value_name)
            if isinstance(val, str) and val.strip() and os.path.isdir(val.strip()):
                return os.path.normpath(val.strip())
    except OSError:
        return None
    return None


def _winreg_read_string(hive: int, subkey: str, value_name: str) -> str | None:
    try:
        import winreg
    except ImportError:
        return None
    try:
        with winreg.OpenKey(hive, subkey) as key:
            val, _ = winreg.QueryValueEx(key, value_name)
            if isinstance(val, str) and val.strip():
                return val.strip()
    except OSError:
        return None
    return None


def _windows_registry_candidates_k1(log: logging.Logger) -> list[str]:
    if sys.platform != "win32":
        return []
    try:
        import winreg
    except ImportError:
        return []

    hives_keys: list[tuple[int, str]] = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\BioWare\SWKOTOR"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BioWare\SWKOTOR"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\BioWare\SWKOTOR"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\WOW6432Node\BioWare\SWKOTOR"),
    ]
    out: list[str] = []
    for hive, sub in hives_keys:
        for val_name in ("Path", "InstallPath"):
            p = _winreg_read_install_path(hive, sub, val_name)
            if p:
                log.debug("registry K1 candidate: hive=%s subkey=%s %s=%s", hive, sub, val_name, p)
                if p not in out:
                    out.append(p)
    out.extend(_gog_registry_candidates_k1(log))
    return out


def _gog_registry_candidates_k1(log: logging.Logger) -> list[str]:
    """GOG Galaxy / GOG.com registry entries that look like KotOR 1."""
    if sys.platform != "win32":
        return []
    try:
        import winreg
    except ImportError:
        return []

    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\GOG.com\Games"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GOG.com\Games"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\GOG.com\Games"),
    ]
    # Known GOG product id (region bundles may differ; gameName matching still runs).
    known_k1_ids = frozenset({"1207664663"})
    out: list[str] = []
    for hive, root in roots:
        try:
            with winreg.OpenKey(hive, root) as games:
                i = 0
                while i < 256:
                    try:
                        subname = winreg.EnumKey(games, i)
                    except OSError:
                        break
                    i += 1
                    sub_full = f"{root}\\{subname}"
                    if subname in known_k1_ids:
                        for vn in ("path", "PATH", "workingDir", "installpath", "installDirectory"):
                            p = _winreg_read_install_path(hive, sub_full, vn)
                            if p:
                                log.debug("GOG K1 candidate (known id %s): %s", subname, p)
                                if p not in out:
                                    out.append(p)
                                break
                        continue
                    gname = (
                        _winreg_read_string(hive, sub_full, "gameName")
                        or _winreg_read_string(hive, sub_full, "name")
                        or ""
                    )
                    gl = gname.lower()
                    if "knight" in gl and "old republic" in gl and "ii" not in gl and "2" not in gl:
                        if "sith" in gl:
                            continue
                        for vn in ("path", "PATH", "workingDir", "installpath", "installDirectory"):
                            p = _winreg_read_install_path(hive, sub_full, vn)
                            if p:
                                log.debug("GOG K1 candidate (name %r): %s", gname, p)
                                if p not in out:
                                    out.append(p)
                                break
        except OSError as e:
            log.debug("GOG registry not readable %s %s: %s", hive, root, e)
    return out


def _gog_registry_candidates_k2(log: logging.Logger) -> list[str]:
    if sys.platform != "win32":
        return []
    try:
        import winreg
    except ImportError:
        return []

    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\GOG.com\Games"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GOG.com\Games"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\GOG.com\Games"),
    ]
    known_k2_ids = frozenset({"1421404681"})
    out: list[str] = []
    for hive, root in roots:
        try:
            with winreg.OpenKey(hive, root) as games:
                i = 0
                while i < 256:
                    try:
                        subname = winreg.EnumKey(games, i)
                    except OSError:
                        break
                    i += 1
                    sub_full = f"{root}\\{subname}"
                    if subname in known_k2_ids:
                        for vn in ("path", "PATH", "workingDir", "installpath", "installDirectory"):
                            p = _winreg_read_install_path(hive, sub_full, vn)
                            if p:
                                log.debug("GOG K2 candidate (known id %s): %s", subname, p)
                                if p not in out:
                                    out.append(p)
                                break
                        continue
                    gname = (
                        _winreg_read_string(hive, sub_full, "gameName")
                        or _winreg_read_string(hive, sub_full, "name")
                        or ""
                    )
                    gl = gname.lower()
                    if ("knight" in gl and "old republic" in gl and ("ii" in gl or "2" in gl)) or (
                        "sith lords" in gl
                    ):
                        for vn in ("path", "PATH", "workingDir", "installpath", "installDirectory"):
                            p = _winreg_read_install_path(hive, sub_full, vn)
                            if p:
                                log.debug("GOG K2 candidate (name %r): %s", gname, p)
                                if p not in out:
                                    out.append(p)
                                break
        except OSError as e:
            log.debug("GOG registry not readable %s %s: %s", hive, root, e)
    return out


def _windows_registry_candidates_k2(log: logging.Logger) -> list[str]:
    if sys.platform != "win32":
        return []
    try:
        import winreg as wr
    except ImportError:
        return []

    subs = [
        r"SOFTWARE\WOW6432Node\LucasArts\Star Wars Knights of the Old Republic II\1.0.0",
        r"SOFTWARE\LucasArts\Star Wars Knights of the Old Republic II\1.0.0",
        r"SOFTWARE\WOW6432Node\Obsidian\KotOR2",
        r"SOFTWARE\Obsidian\KotOR2",
    ]
    out: list[str] = []
    for hive in (wr.HKEY_LOCAL_MACHINE, wr.HKEY_CURRENT_USER):
        for sub in subs:
            for val_name in ("Path", "InstallPath"):
                p = _winreg_read_install_path(hive, sub, val_name)
                if p:
                    log.debug("registry K2 candidate: hive=%s sub=%s %s=%s", hive, sub, val_name, p)
                    if p not in out:
                        out.append(p)
    out.extend(_gog_registry_candidates_k2(log))
    return out


# --- Steam / common folders -----------------------------------------------------


def _default_steam_root_candidates() -> list[str]:
    roots: list[str] = []
    if sys.platform == "win32":
        for ev in ("ProgramFiles(x86)", "ProgramFiles", "LocalAppData"):
            base = os.environ.get(ev)
            if base:
                roots.append(os.path.join(base, "Steam"))
        roots.append(r"C:\Program Files (x86)\Steam")
        roots.append(r"C:\Program Files\Steam")
    elif sys.platform == "darwin":
        roots.append(os.path.expanduser("~/Library/Application Support/Steam"))
    else:
        roots.append(os.path.expanduser("~/.steam/steam"))
        roots.append(os.path.expanduser("~/.local/share/Steam"))
    return [os.path.normpath(r) for r in roots if r and os.path.isdir(r)]


def _parse_steam_library_folders(vdf_path: str, log: logging.Logger) -> list[str]:
    steamapps_dirs: list[str] = []
    try:
        with open(vdf_path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as e:
        log.debug("could not read libraryfolders.vdf %s: %s", vdf_path, e)
        return steamapps_dirs
    # Quoted paths in VDF
    for m in re.finditer(r'"path"\s+"([^"]+)"', text):
        raw = m.group(1).replace("\\\\", "\\")
        if os.path.isdir(raw):
            sap = os.path.join(raw, "steamapps")
            if os.path.isdir(sap):
                steamapps_dirs.append(os.path.normpath(sap))
                log.debug("Steam library from VDF: %s", sap)
    return steamapps_dirs


def _iter_steamapps_dirs(log: logging.Logger) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for steam_root in _default_steam_root_candidates():
        vdf = os.path.join(steam_root, "steamapps", "libraryfolders.vdf")
        if os.path.isfile(vdf):
            for sap in _parse_steam_library_folders(vdf, log):
                if sap not in seen:
                    seen.add(sap)
                    out.append(sap)
        sap = os.path.join(steam_root, "steamapps")
        if os.path.isdir(sap) and sap not in seen:
            seen.add(sap)
            out.append(sap)
            log.debug("Steam steamapps: %s", sap)
    return out


def _steam_and_common_folder_candidates_k1(log: logging.Logger) -> list[str]:
    rel_dirs = (
        os.path.join("common", "swkotor"),
        os.path.join("common", "Knights of the Old Republic"),
        os.path.join("common", "Knights Of The Old Republic"),
        os.path.join("common", "Star Wars - Knights of the Old Republic"),
        os.path.join("common", "Star Wars Knights of the Old Republic"),
    )
    candidates: list[str] = []
    for sap in _iter_steamapps_dirs(log):
        for rel in rel_dirs:
            p = os.path.join(sap, rel)
            if os.path.isdir(p):
                log.debug("K1 folder candidate: %s", p)
                candidates.append(os.path.normpath(p))
    return candidates


def _steam_and_common_folder_candidates_k2(log: logging.Logger) -> list[str]:
    rel_dirs = (
        os.path.join("common", "Knights of the Old Republic II"),
        os.path.join("common", "Knights of the Old Republic 2"),
        os.path.join("common", "KOTOR2"),
    )
    candidates: list[str] = []
    for sap in _iter_steamapps_dirs(log):
        for rel in rel_dirs:
            p = os.path.join(sap, rel)
            if os.path.isdir(p):
                log.debug("K2 folder candidate: %s", p)
                candidates.append(os.path.normpath(p))
    return candidates


def _steam_common_deep_scan_chitin(
    log: logging.Logger,
    *,
    maxdirs_per_common: int,
    label: str,
) -> list[str]:
    """List ``steamapps/common/*`` dirs that contain ``chitin.key`` (bounded scan)."""
    found: list[str] = []
    for sap in _iter_steamapps_dirs(log):
        common = os.path.join(sap, "common")
        if not os.path.isdir(common):
            continue
        try:
            names = sorted(os.listdir(common))
        except OSError as e:
            log.debug("listdir failed %s: %s", common, e)
            continue
        for j, name in enumerate(names):
            if j >= maxdirs_per_common:
                log.debug(
                    "%s: capped steam common scan (%s) at %s",
                    label,
                    common,
                    maxdirs_per_common,
                )
                break
            p = os.path.join(common, name)
            if not os.path.isdir(p):
                continue
            if not _has_chitin_key(p):
                continue
            np = os.path.normpath(p)
            log.debug("%s: chitin.key under %s", label, np)
            if np not in found:
                found.append(np)
    return found


# --- Public API -----------------------------------------------------------------


def discover_kotor1_paths(log: logging.Logger) -> list[str]:
    """Ordered candidate paths for KotOR 1 (may be invalid)."""
    cands: list[str] = []
    cands.extend(_windows_registry_candidates_k1(log))
    cands.extend(_steam_and_common_folder_candidates_k1(log))
    cands.extend(_steam_common_deep_scan_chitin(log, maxdirs_per_common=200, label="K1 deep"))
    # Dedupe
    seen: set[str] = set()
    out: list[str] = []
    for p in cands:
        np = os.path.normpath(p)
        if np not in seen:
            seen.add(np)
            out.append(np)
    return out


def discover_kotor2_paths(log: logging.Logger) -> list[str]:
    """Ordered candidate paths for KotOR 2 (may be invalid)."""
    cands: list[str] = []
    cands.extend(_windows_registry_candidates_k2(log))
    cands.extend(_steam_and_common_folder_candidates_k2(log))
    cands.extend(_steam_common_deep_scan_chitin(log, maxdirs_per_common=200, label="K2 deep"))
    seen: set[str] = set()
    out: list[str] = []
    for p in cands:
        np = os.path.normpath(p)
        if np not in seen:
            seen.add(np)
            out.append(np)
    return out


def first_valid_k1(log: logging.Logger) -> str | None:
    for p in discover_kotor1_paths(log):
        ok = is_probable_kotor1_install(p)
        log.debug("K1 validate %s -> %s", p, ok)
        if ok:
            return p
    return None


def first_valid_k2(log: logging.Logger) -> str | None:
    for p in discover_kotor2_paths(log):
        ok = is_probable_kotor2_install(p)
        log.debug("K2 validate %s -> %s", p, ok)
        if ok:
            return p
    return None


def log_install_discovery_summary(
    log: logging.Logger,
    *,
    k1_found: bool,
    k2_found: bool,
) -> None:
    """Log every native candidate path with accept/skip reason (INFO — for support / autodetect)."""
    if not k1_found:
        paths = discover_kotor1_paths(log)
        log.info("KotOR 1: %d native candidate path(s) after dedupe", len(paths))
        for p in paths:
            ok = is_probable_kotor1_install(p)
            if ok:
                log.info("  [accept] %s", p)
            else:
                log.info("  [skip]   %s — %s", p, explain_k1_rejection(p))
        if not paths:
            log.info("  (no paths: registry empty, no Steam libraries, or Steam not found)")
    if not k2_found:
        paths = discover_kotor2_paths(log)
        log.info("KotOR 2: %d native candidate path(s) after dedupe", len(paths))
        for p in paths:
            ok = is_probable_kotor2_install(p)
            if ok:
                log.info("  [accept] %s", p)
            else:
                log.info("  [skip]   %s — %s", p, explain_k2_rejection(p))
        if not paths:
            log.info("  (no paths: registry empty, no Steam libraries, or Steam not found)")
