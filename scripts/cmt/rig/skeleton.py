"""This module contains methods to export a skeletal transform hierachy to a json-serializable
format.  This is used to export and recreate skeletons on the fly.  A json format allows us
to query what is in a skeleton without actually having to create or import one into Maya.

Example usage:
See test_skeleton.py

import cmt.rig.skeleton as skeleton
skeleton.dump('skeleton_grp', json_file)
cmds.file(new=True, f=True)
skeleton.load(json_file)

# To load the data structure without creating any Maya nodes
data = skeleton.load_data(json_file)
"""
import maya.cmds as cmds
import json


def truncate(value, places=6):
    """Truncates the given float value to the specified number of decimal places.
    :param value: Input float value.
    :param places: Number of decimal places.
    """
    value = round(value, places)
    if abs(value) <= (1.0/pow(10, places)):
        # Prevent -0.0
        value = 0.0
    return value


def get_data(root):
    """Get the data dictionary that makes up a joint/transform hierarchy.  Non-transform
    branches will be skipped.
    :param root: The root node of the hierarchy to export.
    :return: A dictionary containing all data required to rebuild the hierarchy in Maya.
    """
    node_type = cmds.nodeType(root)

    shapes = cmds.listRelatives(root, children=True, shapes=True)
    if node_type not in ['joint', 'transform'] or (shapes and node_type == 'transform'):
        # Skip nodes that are not joints or transforms or if there are shapes below.
        return None
    # Store everything we need to recreate the node
    data = {
        'nodeType': node_type,
        'name': root,
        'translate': [truncate(x) for x in cmds.getAttr('{0}.t'.format(root))[0]],
        'rotate': [truncate(x) for x in cmds.getAttr('{0}.r'.format(root))[0]],
        'scale': [truncate(x) for x in cmds.getAttr('{0}.s'.format(root))[0]],
        'rotateOrder': cmds.getAttr('{0}.rotateOrder'.format(root)),
        'rotateAxis': [truncate(x) for x in cmds.getAttr('{0}.ra'.format(root))[0]],
        'children': [],
    }
    if node_type == 'joint':
        data['jointOrient'] = [truncate(x) for x in cmds.getAttr('{0}.jo'.format(root))[0]]
        data['radius'] = cmds.getAttr('{0}.radius'.format(root))
        data['side'] = cmds.getAttr('{0}.side'.format(root))
        data['type'] = cmds.getAttr('{0}.type'.format(root))
        data['otherType'] = cmds.getAttr('{0}.otherType'.format(root))
        data['jointTypeX'] = cmds.getAttr('{0}.jointTypeX'.format(root))
        data['jointTypeY'] = cmds.getAttr('{0}.jointTypeX'.format(root))
        data['jointTypeZ'] = cmds.getAttr('{0}.jointTypeX'.format(root))

    # Recurse down to all the children
    children = cmds.listRelatives(root, children=True, path=True) or []
    for child in children:
        child_data = get_data(child)
        if child_data:
            data['children'].append(child_data)
    return data


def create_node(node_dictionary, parent=None):
    """Create the Maya node described by the given data dictionary.
    :param node_dictionary: The data dictionary generated by one of the load/get functions.
    :param parent: The node to parent the created node to.
    """
    node = cmds.createNode(node_dictionary['nodeType'], name=node_dictionary['name'])
    if parent:
        cmds.parent(node, parent)
    cmds.setAttr('{0}.t'.format(node), *node_dictionary['translate'])
    cmds.setAttr('{0}.r'.format(node), *node_dictionary['rotate'])
    cmds.setAttr('{0}.s'.format(node), *node_dictionary['scale'])
    cmds.setAttr('{0}.rotateOrder'.format(node), node_dictionary['rotateOrder'])
    cmds.setAttr('{0}.rotateAxis'.format(node), *node_dictionary['rotateAxis'])
    if node_dictionary['nodeType'] == 'joint':
        cmds.setAttr('{0}.jointOrient'.format(node), *node_dictionary['jointOrient'])
        cmds.setAttr('{0}.radius'.format(node), node_dictionary['radius'])
        cmds.setAttr('{0}.side'.format(node), node_dictionary['side'])
        cmds.setAttr('{0}.type'.format(node), node_dictionary['type'])
        cmds.setAttr('{0}.otherType'.format(node), node_dictionary['otherType'], type='string')
        cmds.setAttr('{0}.jointTypeX'.format(node), node_dictionary['jointTypeX'])
        cmds.setAttr('{0}.jointTypeY'.format(node), node_dictionary['jointTypeY'])
        cmds.setAttr('{0}.jointTypeZ'.format(node), node_dictionary['jointTypeZ'])

    for child in node_dictionary.get('children', []):
        create_node(child, node)


def dump(root=None, file_path=None):
    """Dump the hierarchy data starting at root to disk.
    :param root: Root node of the hierarchy.
    :param file_path: Export json path.
    :return: The hierarchy data that was exported.
    """
    if root is None:
        root = cmds.ls(sl=True)
        if root:
            root = root[0]
        else:
            return
    if file_path is None:
        file_path = cmds.fileDialog2(fileFilter='Skeleton Files (*.json)', dialogStyle=2, caption='Export Skeleton',
                                     fileMode=0, returnFilter=False)
        if file_path:
            file_path = file_path[0]
        else:
            return
    data = get_data(root)
    fh = open(file_path, 'w')
    json.dump(data, fh, indent=4)
    fh.close()
    return data, file_path


def load_data(file_path):
    """Load a skeleton hierarchy from the given json data file.  No nodes will be created in Maya.
    :param file_path: Json file on disk.
    :return: The hierarchy data loaded from disk.
    """
    fh = open(file_path, 'r')
    data = json.load(fh)
    fh.close()
    return data


def load(file_path=None):
    """Load a skeleton hierarchy from the given json data file and generates the hierarchy in Maya.
    :param file_path: Json file on disk.
    :return: The hierarchy data loaded from disk.
    """
    if file_path is None:
        file_path = cmds.fileDialog2(fileFilter='Skeleton Files (*.json)', dialogStyle=2, caption='Export Skeleton',
                                     fileMode=1, returnFilter=False)
        if file_path:
            file_path = file_path[0]
        else:
            return
    data = load_data(file_path)
    create_node(data)
    return data





