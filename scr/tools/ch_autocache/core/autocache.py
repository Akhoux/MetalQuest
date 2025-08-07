from __future__ import annotations

import hou
from PySide2 import QtWidgets


def get_user_input(prompt: str = "Enter a name:") -> str | None:
    QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    text, ok = QtWidgets.QInputDialog.getText(
        None, "Name your output !", prompt
    )
    if ok and text:
        return text
    return None


def create_node_cache(node: hou.node) -> None:
    if node.type().name() != "null":
        tmp_ctx = node.parent()
        null = tmp_ctx.createNode("null")
        pos = node.position()
        null.setPosition((pos[0], pos[1] - 1))
        null.setInput(0, node)
        node = null

    if "OUT" in node.name():
        name = node.name()
        name_read = f"IN_{'_'.join(name.split('_')[1:])}"
    else:
        name = get_user_input()
        name_read = f"IN_{name}"
        node_name = f"OUT_{name}"
        node.setName(node_name)
        name = f"OUT_{name}"

    parm_template_group = node.parmTemplateGroup()
    string_parm = hou.StringParmTemplate(
        name="version",
        label="version",
        num_components=1,
        default_value=("v001",),
    )

    parm_template_group.addParmTemplate(string_parm)
    node.setParmTemplateGroup(parm_template_group)

    node.setColor(hou.Color(0.14, 0.42, 0.26))
    node.setUserData("nodeshape", "circle")
    node_ctx = node.parent()
    rop_ctx = hou.node("/out")
    ropout = rop_ctx.createNode("geometry", name)
    ropout.parm("soppath").set(node.path())
    file_path = (  # noqa: UP032
        '$JOB/geo/{}/`chs("{}/version")`/'
        '{}_`chs("{}/version")`_cache.$F4.bgeo.sc'
    ).format(name, node.path(), name, node.path())
    ropout.parm("sopoutput").set(file_path)

    file_read = node_ctx.createNode("file", name_read)
    file_read.parm("file").set(ropout.parm("sopoutput"))
    file_read.setInput(0, node)
    pos = node.position()
    file_read.setPosition((pos[0], pos[1] - 1))
