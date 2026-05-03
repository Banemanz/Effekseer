#!/usr/bin/env python3
import argparse
import copy
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

TEMPLATE_PATH = "Release/Sample/01_Suzuki01/001_magma_effect/aura.efkproj"


def parse_fxs(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [l.strip() for l in f.readlines()]

    system_name = os.path.splitext(os.path.basename(path))[0]
    prims = []
    cur = None
    current_info = ''
    pending = None

    for line in lines:
        if not line:
            continue
        if line.startswith('NAME:') and cur is None:
            system_name = line.split(':', 1)[1].strip() or system_name
        if line.startswith('FX_PRIM_EMITTER_DATA'):
            if cur is not None:
                prims.append(cur)
            cur = {'name':'GTA_FX','texture':'','life':1.0,'emit_rate':30.0,'size_x':1.0,'size_y':1.0}
            current_info = ''
            pending = None
            continue
        if cur is None:
            continue
        if line.startswith('FX_INFO_'):
            current_info = line
            pending = None
            continue
        if line.startswith('NAME:'):
            cur['name'] = line.split(':',1)[1].strip() or cur['name']
        elif line.startswith('TEXTURE:'):
            tex = line.split(':',1)[1].strip()
            if tex.upper() != 'NULL':
                cur['texture'] = tex
        elif line.startswith('RATE:'):
            pending = ('emit_rate', 'FX_INFO_EMRATE_DATA')
        elif line.startswith('LIFE:'):
            pending = ('life', 'FX_INFO_EMLIFE_DATA')
        elif line.startswith('SIZEX:'):
            pending = ('size_x', 'FX_INFO_SIZE_DATA')
        elif line.startswith('SIZEY:'):
            pending = ('size_y', 'FX_INFO_SIZE_DATA')
        elif line.startswith('VAL:') and pending is not None:
            key, expected = pending
            if current_info.startswith(expected):
                try:
                    cur[key] = max(0.01, float(line.split(':',1)[1].strip()))
                except ValueError:
                    pass
                pending = None

    if cur is not None:
        prims.append(cur)
    return system_name, prims


def set_text(node, path, value):
    t = node.find(path)
    if t is not None:
        t.text = str(value)


def apply_prim(node, prim):
    set_text(node, 'Name', prim['name'])
    if prim['texture']:
        set_text(node, 'RendererCommonValues/ColorTexture', prim['texture'])

    life_frames = int(max(1.0, prim['life'] * 60.0))
    for p in ['CommonValues/Life/Center','CommonValues/Life/Max','CommonValues/Life/Min']:
        set_text(node, p, life_frames)

    gen = int(max(1.0, 60.0 / max(1.0, prim['emit_rate'])))
    for p in ['CommonValues/GenerationTime/Center','CommonValues/GenerationTime/Max','CommonValues/GenerationTime/Min']:
        set_text(node, p, gen)

    set_text(node, 'ScalingValues/Type', 0)
    set_text(node, 'ScalingValues/Fixed/ScaleX', prim['size_x'])
    set_text(node, 'ScalingValues/Fixed/ScaleY', prim['size_y'])
    set_text(node, 'ScalingValues/Fixed/ScaleZ', 1)


def build_from_template(system_name, prims):
    tree = ET.parse(TEMPLATE_PATH)
    root = tree.getroot()
    root_name = root.find('Root/Name')
    if root_name is not None:
        root_name.text = system_name

    children = root.find('Root/Children')
    if children is None:
        raise RuntimeError('Invalid template: missing Root/Children')

    first_node = children.find('Node')
    if first_node is None:
        raise RuntimeError('Invalid template: missing node template')

    for c in list(children):
        children.remove(c)

    for prim in prims:
        node = copy.deepcopy(first_node)
        apply_prim(node, prim)
        children.append(node)

    return root


def save_pretty_xml(root, output_path):
    xml_bytes = ET.tostring(root, encoding='utf-8')
    pretty = minidom.parseString(xml_bytes).toprettyxml(indent='  ', encoding='utf-8')
    with open(output_path, 'wb') as f:
        f.write(pretty)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()

    output = args.output or os.path.splitext(args.input)[0] + '.efkproj'
    name, prims = parse_fxs(args.input)
    if not prims:
        raise SystemExit('No FX_PRIM_EMITTER_DATA found')
    root = build_from_template(name, prims)
    save_pretty_xml(root, output)
    print(f'Converted {args.input} -> {output} ({len(prims)} emitters)')


if __name__ == '__main__':
    main()
