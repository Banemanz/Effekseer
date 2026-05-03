#!/usr/bin/env python3
import argparse
import copy
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

NODE_TEMPLATE_XML = r'''
<Node><CommonValues><MaxGeneration><Infinite>True</Infinite></MaxGeneration><Life><Center>50</Center><Max>50</Max><Min>50</Min></Life><GenerationTime><Center>3</Center><Max>3</Max><Min>3</Min></GenerationTime></CommonValues><RotationValues><Type>1</Type><PVA><Rotation><X><Center>-90</Center><Min>-180</Min></X><Y><Max>90</Max><Min>-90</Min></Y><Z><Max>180</Max><Min>-180</Min></Z></Rotation></PVA></RotationValues><ScalingValues><Type>3</Type><SinglePVA><Scale><Center>0.3</Center><Max>0.6</Max><Min>0</Min><DrawnAs>0</DrawnAs></Scale><Velocity><Center>0.001</Center><Max>0.001</Max><Min>0.001</Min></Velocity></SinglePVA><SingleEasing><Start><Center>0.2</Center><Max>0.2</Max><Min>0.2</Min></Start><End><Center>2</Center><Max>2</Max><Min>2</Min></End><StartSpeed>10</StartSpeed><EndSpeed>-30</EndSpeed></SingleEasing></ScalingValues><RendererCommonValues><ColorTexture>Texture/aura3_type2.png</ColorTexture><AlphaBlend>2</AlphaBlend><FadeInType>1</FadeInType><FadeIn><Frame>8</Frame></FadeIn><FadeOutType>1</FadeOutType><FadeOut><Frame>8</Frame></FadeOut><UV>3</UV><UVScroll><Size><X>2048</X><Y>2048</Y></Size><Speed><X>10</X><Y>20</Y></Speed></UVScroll></RendererCommonValues><DrawingValues><Type>4</Type><Ring><VertexCount>36</VertexCount><Inner_Fixed><Location><X>0</X></Location></Inner_Fixed><OuterColor>1</OuterColor><OuterColor_Fixed><R>17</R><G>221</G><B>238</B></OuterColor_Fixed><OuterColor_Random><R><Center>98</Center><Max>98</Max><Min>98</Min></R><G><Center>123</Center><Max>123</Max><Min>123</Min></G><B><Center>223</Center><Max>223</Max><Min>223</Min></B></OuterColor_Random><CenterColor_Fixed><R>0</R><G>58</G><B>117</B></CenterColor_Fixed><CenterColor_Random><R><Center>21</Center><Max>42</Max><Min>0</Min></R><G><Center>95</Center><Max>125</Max><Min>65</Min></G><B><Center>116</Center><Max>146</Max><Min>86</Min></B><A><Center>240</Center><Min>225</Min></A></CenterColor_Random><CenterColor_Easing><Start><R><Center>73</Center><Max>146</Max><Min>0</Min></R><G><Center>127</Center><Min>0</Min></G><ColorSpace>1</ColorSpace></Start><End><R><Center>65</Center><Max>131</Max><Min>0</Min></R><G><Center>120</Center><Max>240</Max><Min>0</Min></G><B><Center>241</Center><Max>241</Max><Min>241</Min></B><ColorSpace>1</ColorSpace></End></CenterColor_Easing><InnerColor_Fixed><R>40</R><G>6</G><B>200</B></InnerColor_Fixed><InnerColor_Random><R><Center>77</Center><Max>107</Max><Min>47</Min></R><G><Center>209</Center><Max>239</Max><Min>179</Min></G><B><Center>194</Center><Min>133</Min></B></InnerColor_Random></Ring></DrawingValues><Name>FlareMini</Name><Children /></Node>
'''

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

def build_project(system_name, prims):
    project = ET.Element('EffekseerProject')
    root = ET.SubElement(project, 'Root')
    ET.SubElement(root, 'Name').text = system_name
    children = ET.SubElement(root, 'Children')
    template_node = ET.fromstring(NODE_TEMPLATE_XML)
    for prim in prims:
        node = copy.deepcopy(template_node)
        apply_prim(node, prim)
        children.append(node)
    return project

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
    root = build_project(name, prims)
    save_pretty_xml(root, output)
    print(f'Converted {args.input} -> {output} ({len(prims)} emitters)')

if __name__ == '__main__':
    main()
