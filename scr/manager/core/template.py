import datetime
import json
import os
import re

import hou

INDEX_FILENAME = "templates.json"
TEMPLATE_DIRNAME = "template"


def _job_root() -> str:
    j = hou.getenv("JOB")
    if not j:
        raise RuntimeError("$JOB non défini")
    return j


def _template_dir() -> str:
    d = os.path.join(_job_root(), TEMPLATE_DIRNAME)
    os.makedirs(d, exist_ok=True)
    return d


def _index_path() -> str:
    return os.path.join(_template_dir(), INDEX_FILENAME)


def _timestamp() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _load_index() -> list:
    p = _index_path()
    if not os.path.isfile(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_index(data: list) -> None:
    with open(_index_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _job_basename() -> str:
    return os.path.basename(os.path.normpath(_job_root()))


def _format_name(label: str, version: int) -> str:
    job = _job_basename()
    return f"{job}_{label}_v{version:03d}"


def _next_version(label: str, ext: str) -> int:
    base = re.escape(f"{_job_basename()}_{label}_v")
    pat = re.compile(rf"^{base}(\d+)\{re.escape(ext)}$")
    mx = 0
    for f in os.listdir(_template_dir()):
        m = pat.match(f)
        if m:
            try:
                v = int(m.group(1))
                if v > mx:
                    mx = v
            except Exception:
                pass
    return mx + 1


def _mwrite_copy(path: str) -> None:
    hou.hscript(f"mwrite -n \"{path}\"")


def save_scene_template(label: str, description: str = "", version: int | None = None) -> str:
    ext = ".hip"
    if version is None:
        version = _next_version(label, ext)
    name = _format_name(label, version) + ext
    path = os.path.join(_template_dir(), name)
    _mwrite_copy(path)
    idx = _load_index()
    idx.append({
        "name": os.path.splitext(name)[0],
        "type": "scene",
        "path": path,
        "date": _timestamp(),
        "label": label,
        "version": version,
        "description": description,
    })
    _save_index(idx)
    return path


def save_scene_increment(label: str, description: str = "") -> str:
    return save_scene_template(label=label, description=description, version=None)


def _ensure_library(path: str) -> None:
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    if not os.path.exists(path):
        open(path, "wb").close()


def _copy_or_create_hda(node: hou.Node, library_path: str, op_label_prefix: str) -> str:
    d = node.type().definition()
    if d:
        d.copyToHDAFile(library_path)
        return d.nodeTypeName()
    op_type_name = re.sub(r"[^A-Za-z0-9_]+", "_", f"{op_label_prefix}_{node.name()}")
    node.createDigitalAsset(name=op_type_name, hda_file_name=library_path, description=op_type_name)
    return op_type_name


def save_nodes_as_otl(label: str, nodes: list[hou.Node] | None = None, description: str = "", version: int | None = None) -> str:
    if nodes is None:
        nodes = hou.selectedNodes()
    if not nodes:
        raise RuntimeError("Aucun node sélectionné")
    ext = ".hda"
    if version is None:
        version = _next_version(label, ext)
    name = _format_name(label, version) + ext
    lib_path = os.path.join(_template_dir(), name)
    _ensure_library(lib_path)
    saved_types = []
    for n in nodes:
        tname = _copy_or_create_hda(n, lib_path, _format_name(label, version))
        saved_types.append(tname)
    idx = _load_index()
    idx.append({
        "name": os.path.splitext(name)[0],
        "type": "otl",
        "path": lib_path,
        "date": _timestamp(),
        "label": label,
        "version": version,
        "description": description,
        "operators": saved_types,
    })
    _save_index(idx)
    return lib_path


def save_nodes_as_otl_increment(label: str, nodes: list[hou.Node] | None = None, description: str = "") -> str:
    return save_nodes_as_otl(label=label, nodes=nodes, description=description, version=None)


def list_templates(kind: str | None = None) -> list:
    data = _load_index()
    if kind:
        return [d for d in data if d.get("type") == kind]
    return data


def find_templates(label: str | None = None, kind: str | None = None) -> list:
    data = _load_index()
    out = []
    for d in data:
        if label and d.get("label") != label:
            continue
        if kind and d.get("type") != kind:
            continue
        out.append(d)
    return out
