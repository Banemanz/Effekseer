# GTA SA FXS/FXP -> Effekseer EFKPROJ Converter

Converts GTA SA `.fxs/.fxp` files into `.efkproj` as a fully self-contained script (no external template file dependency).

## Usage

```bash
python Tools/GTAFxsToEfkproj/convert_fxs_to_efkproj.py <input.fxs> -o <output.efkproj>
```

If `-o` is omitted, output is `<input_basename>.efkproj`.

## Approach

The script embeds an internal editor-safe node XML template and clones it per emitter, then applies GTA values. This keeps required Effekseer fields present while avoiding runtime dependency on another `.efkproj` file.

## Current mapping

- `FX_PRIM_EMITTER_DATA` -> one Effekseer `Node`
- `NAME` -> node `Name`
- `TEXTURE` -> `RendererCommonValues/ColorTexture`
- `FX_INFO_EMLIFE_DATA/LIFE` -> `CommonValues/Life` (seconds -> frames)
- `FX_INFO_EMRATE_DATA/RATE` -> `CommonValues/GenerationTime`
- `FX_INFO_SIZE_DATA/SIZEX|SIZEY` -> `ScalingValues/Fixed`
