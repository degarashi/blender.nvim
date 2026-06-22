import platform
import sys
from pathlib import Path
from typing import List, Tuple, cast

import addon_utils
import bpy

python_path = Path(sys.executable)
blender_path = Path(cast(str, bpy.app.binary_path))
blender_directory = blender_path.parent

# Test for MacOS app bundles
if platform.system() == "Darwin":
    use_own_python = blender_directory.parent in python_path.parents
else:
    use_own_python = blender_directory in python_path.parents

version = cast(Tuple[int, int, int], bpy.app.version)
scripts_folder = blender_path.parent / f"{version[0]}.{version[1]}" / "scripts"
user_addon_directory = Path(bpy.utils.user_resource("SCRIPTS", path="addons"))
addon_directories = tuple(map(Path, cast(List[str], addon_utils.paths())))


def get_extension_repo_info():
    """Get the local extension repository directory and module name.

    Returns (repo_directory, repo_module) for the first enabled local
    extension repository, or (None, None) if unavailable (Blender < 4.2
    or no local repo found).
    """
    if version < (4, 2, 0):
        return None, None
    try:
        for repo in bpy.context.preferences.extensions.repos:
            if not getattr(repo, "use_remote_url", True) and repo.enabled:
                repo_dir = Path(repo.directory)
                return repo_dir, repo.module
    except (AttributeError, Exception):
        pass
    return None, None
