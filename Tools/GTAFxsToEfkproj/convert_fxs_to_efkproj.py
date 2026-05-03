#!/usr/bin/env python3
import argparse
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom


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
            cur = {
                'name': 'GTA_FX',
                'texture': '',
                'life': 1.0,
                'emit_rate': 30.0,
                'size_x': 1.0,
                'size_y': 1.0,
            }
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
            cur['name'] = line.split(':', 1)[1].strip() or cur['name']
        elif line.startswith('TEXTURE:'):
            tex = line.split(':', 1)[1].strip()
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
                    cur[key] = max(0.01, float(line.split(':', 1)[1].strip()))
                except ValueError:
                    pass
                pending = None

    if cur is not None:
        prims.append(cur)

    return system_name, prims


def add_text(parent, name, text):
    e = ET.SubElement(parent, name)
    e.text = str(text)
    return e


def add_range(parent, name, value):
    e = ET.SubElement(parent, name)
    add_text(e, 'Center', value)
    add_text(e, 'Max', value)
    add_text(e, 'Min', value)


def build_efkproj(system_name, prims):
    root = ET.Element('EffekseerProject')
    root_node = ET.SubElement(root, 'Root')
    add_text(root_node, 'Name', system_name)
    children = ET.SubElement(root_node, 'Children')

    for prim in prims:
        node = ET.SubElement(children, 'Node')

        common = ET.SubElement(node, 'CommonValues')
        max_gen = ET.SubElement(common, 'MaxGeneration')
        add_text(max_gen, 'Infinite', 'True')

        life_frames = int(max(1.0, prim['life'] * 60.0))
        add_range(common, 'Life', life_frames)

        gen = int(max(1.0, 60.0 / max(1.0, prim['emit_rate'])))
        add_range(common, 'GenerationTime', gen)

        scaling = ET.SubElement(node, 'ScalingValues')
        add_text(scaling, 'Type', 0)
        fixed = ET.SubElement(scaling, 'Fixed')
        add_text(fixed, 'ScaleX', prim['size_x'])
        add_text(fixed, 'ScaleY', prim['size_y'])
        add_text(fixed, 'ScaleZ', 1)

        renderer = ET.SubElement(node, 'RendererCommonValues')
        if prim['texture']:
            add_text(renderer, 'ColorTexture', prim['texture'])

        name = ET.SubElement(node, 'Name')
        name.text = prim['name']

    return root


def save_pretty_xml(root, output_path):
    xml_bytes = ET.tostring(root, encoding='utf-8')
    pretty = minidom.parseString(xml_bytes).toprettyxml(indent='  ', encoding='utf-8')
    with open(output_path, 'wb') as f:
        f.write(pretty)


def main():
    parser = argparse.ArgumentParser(description='Convert GTA SA .fxs/.fxp into Effekseer .efkproj')
    parser.add_argument('input', help='Input .fxs/.fxp file')
    parser.add_argument('-o', '--output', help='Output .efkproj path')
    args = parser.parse_args()

    output = args.output
    if not output:
        output = os.path.splitext(args.input)[0] + '.efkproj'

    system_name, prims = parse_fxs(args.input)
    if not prims:
        raise SystemExit('No FX_PRIM_EMITTER_DATA entries found in input.')

    root = build_efkproj(system_name, prims)
    save_pretty_xml(root, output)
    print(f'Converted {args.input} -> {output} ({len(prims)} emitters)')


if __name__ == '__main__':
    main()
