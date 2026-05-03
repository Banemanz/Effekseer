# GTA SA FXS/FXP -> Effekseer EFKPROJ Converter

Converts GTA SA `.fxs/.fxp` files into `.efkproj` using a **known-good Effekseer project template node** so generated files remain editor-compatible.

## Usage

```bash
python Tools/GTAFxsToEfkproj/convert_fxs_to_efkproj.py <input.fxs> -o <output.efkproj>
```

If `-o` is omitted, output is `<input_basename>.efkproj`.

## Why template-based

Effekseer project XML contains many fields that are easy to miss when writing from scratch and can cause null-reference errors in the editor. This converter clones a valid node from:

`Release/Sample/01_Suzuki01/001_magma_effect/aura.efkproj`

Then overrides only selected values from GTA data.

## Current mapping

- `FX_PRIM_EMITTER_DATA` -> one Effekseer `Node`
- `NAME` -> node `Name`
- `TEXTURE` -> `RendererCommonValues/ColorTexture`
- `FX_INFO_EMLIFE_DATA/LIFE` -> `CommonValues/Life` (seconds -> frames)
- `FX_INFO_EMRATE_DATA/RATE` -> `CommonValues/GenerationTime`
- `FX_INFO_SIZE_DATA/SIZEX|SIZEY` -> `ScalingValues/Fixed`
