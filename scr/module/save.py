import os
import re

import hou

_VERSION_RE = re.compile(r"^(?P<base>.+)_v(?P<ver>\d{3,})\.hip$", re.IGNORECASE)


def _job_dir() -> str:
    return hou.expandString("$JOB").rstrip("/\\")


def _project_name() -> str:
    base = os.path.basename(_job_dir())
    return base or "project"


def _workscenes_dir() -> str:
    return os.path.join(_job_dir(), "hip", "workscenes")


def _ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def _sanitize_label(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", label.strip())


def _is_initial_scene() -> bool:
    name = hou.hipFile.name()
    return (
        (not name)
        or (os.path.basename(name).lower() in {"untitled.hip", "newfile.hip"})
        or (not os.path.isabs(name))
    )


def save_hip() -> None:
    """Save the current hip file. If the file is unsaved, prompt for a label."""
    if _is_initial_scene():
        label, result = hou.ui.readInput(
            "Enter a label for the file",
            buttons=("OK", "Cancel"),
            close_choice=1,
            title="New Hip File",
            initial_contents="",
        )
        if result == 1:
            return

        label = _sanitize_label(label)
        if not label:
            hou.ui.displayMessage("Empty label is not allowed.")
            return

        _ensure_dir(_workscenes_dir())
        filename = f"{_project_name()}_{label}_v001.hip"
        path = os.path.join(_workscenes_dir(), filename)
        hou.hipFile.save(file_name=path, save_to_recent_files=True)
        return

    hou.hipFile.save(save_to_recent_files=True)


def increment_hip_version() -> None:
    """Increment the hip file version (v001 → v002)."""
    current = hou.hipFile.name()
    if not current or not os.path.isabs(current):
        save_hip()
        return

    folder = os.path.dirname(current)
    name = os.path.basename(current)

    match = _VERSION_RE.match(name)
    if not match:
        base = os.path.splitext(name)[0]
        new_name = f"{base}_v001.hip"
    else:
        base = match.group("base")
        version = int(match.group("ver")) + 1
        new_name = f"{base}_v{version:03d}.hip"

    new_path = os.path.join(folder, new_name)
    hou.hipFile.save(file_name=new_path, save_to_recent_files=True)


def save_or_increment(increment: bool = False) -> None:
    """Save or increment the hip file version based on the flag."""
    if increment:
        increment_hip_version()
    else:
        save_hip()