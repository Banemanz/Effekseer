# GTA SA FXS/FXP -> Effekseer EFKPROJ Converter

A standalone Python converter for GTA San Andreas particle definitions (`.fxs`/`.fxp`) to Effekseer project files (`.efkproj`).

## Usage

```bash
python Tools/GTAFxsToEfkproj/convert_fxs_to_efkproj.py <input.fxs> -o <output.efkproj>
```

If `-o` is omitted, output is written beside input with `.efkproj` extension.

## Current mapping

- `FX_PRIM_EMITTER_DATA` -> one Effekseer `Node`
- `NAME` -> node `Name`
- `TEXTURE` -> `RendererCommonValues/ColorTexture`
- `FX_INFO_EMLIFE_DATA/LIFE` -> `CommonValues/Life` (seconds -> 60fps frames)
- `FX_INFO_EMRATE_DATA/RATE` -> `CommonValues/GenerationTime` (derived interval)
- `FX_INFO_SIZE_DATA/SIZEX|SIZEY` -> `ScalingValues/Fixed`

This is intentionally conservative and designed to produce editable starting projects.
