import os
import sys
import traceback

import bpy

from .environment import addon_directories, user_addon_directory, get_extension_repo_info
from .rpc import NvimRpc


def setup_addon_links(addons_to_load):
    if not os.path.exists(user_addon_directory):
        os.makedirs(user_addon_directory)

    if str(user_addon_directory) not in sys.path:
        sys.path.append(str(user_addon_directory))

    path_mappings = []

    for source_path, module_name, addon_type in addons_to_load:
        if addon_type == "extension":
            ext_dir, repo_module = get_extension_repo_info()
            if ext_dir is None:
                print(
                    "[Blender.nvim] ERROR: Could not find local extension repository. "
                    "Falling back to legacy addon loading."
                )
                # Fall back to legacy behavior
                load_path, blender_module = _setup_legacy_link(
                    source_path, module_name
                )
            else:
                load_path = ext_dir / module_name
                if not _is_in_directory(source_path, ext_dir):
                    os.makedirs(ext_dir, exist_ok=True)
                    _create_link(source_path, load_path)
                blender_module = f"bl_ext.{repo_module}.{module_name}"
        else:
            load_path, blender_module = _setup_legacy_link(
                source_path, module_name
            )

        path_mappings.append(
            {
                "src": str(source_path),
                "load": str(load_path),
                "blender_module": blender_module,
            }
        )

    return path_mappings


def _setup_legacy_link(source_path, module_name):
    """Set up a legacy addon symlink and return (load_path, blender_module)."""
    if is_in_any_addon_directory(source_path):
        load_path = source_path
    else:
        load_path = os.path.join(user_addon_directory, module_name)
        _create_link(source_path, load_path)
    return load_path, module_name


def load_addons(addons_to_load, path_mappings):
    for mapping in path_mappings:
        blender_module = mapping["blender_module"]
        try:
            bpy.ops.preferences.addon_enable(module=blender_module)
        except Exception:
            traceback.print_exc()
            NvimRpc.get_instance().send(
                {"type": "enable_failure", "message": traceback.format_exc()}
            )


def _create_link(source, link_path):
    """Create a symlink or junction from source to link_path."""
    link_path = str(link_path)
    if os.path.lexists(link_path):
        os.remove(link_path)

    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(source), link_path)
    else:
        os.symlink(str(source), link_path, target_is_directory=True)


def _is_in_directory(path, directory):
    """Check if path is directly inside directory."""
    try:
        return path.parent == directory
    except (AttributeError, TypeError):
        return False


def is_in_any_addon_directory(module_path):
    for path in addon_directories:
        if path == module_path.parent:
            return True
    return False
