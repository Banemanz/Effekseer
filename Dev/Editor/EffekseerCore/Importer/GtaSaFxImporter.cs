using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;

namespace Effekseer.Importer
{
	public static class GtaSaFxImporter
	{
		private class PrimData
		{
			public string Name = string.Empty;
			public string Texture = string.Empty;
			public float Life = 1.0f;
			public float EmitRate = 30.0f;
			public float SizeX = 1.0f;
			public float SizeY = 1.0f;
			public float Alpha = 255.0f;
		}

		public static Data.NodeRoot ImportToEffekseer(string path)
		{
			var lines = File.ReadAllLines(path);
			var prims = ParsePrims(lines);

			var root = new Data.NodeRoot();
			root.SetFullPath(Path.ChangeExtension(path, ".efkefc"));

			if (prims.Count == 0)
			{
				root.AddChild();
				return root;
			}

			foreach (var prim in prims)
			{
				var node = root.AddChild();
				node.Name.SetValueDirectly(string.IsNullOrEmpty(prim.Name) ? "GTA_FX" : prim.Name);
				node.CommonValues.MaxGeneration.SetValue(1);
				node.CommonValues.Life.SetValue((int)Math.Max(1.0f, prim.Life * 60.0f));
				node.CommonValues.GenerationTime.SetValue(Math.Max(1, (int)(60.0f / Math.Max(1.0f, prim.EmitRate))));
				node.ScalingValues.Fixed.ScaleX.SetValue(prim.SizeX);
				node.ScalingValues.Fixed.ScaleY.SetValue(prim.SizeY);
				node.ScalingValues.Fixed.ScaleZ.SetValue(1.0f);
				node.RendererCommonValues.ColorTexture.SetAbsolutePath(prim.Texture);
			}

			return root;
		}

		private static List<PrimData> ParsePrims(string[] lines)
		{
			var prims = new List<PrimData>();
			PrimData current = null;
			string currentInfo = string.Empty;
			string currentChannel = string.Empty;
			bool nextValIsRate = false;
			bool nextValIsLife = false;
			bool nextValIsAlpha = false;
			bool nextValIsSizeX = false;
			bool nextValIsSizeY = false;

			for (int i = 0; i < lines.Length; i++)
			{
				var line = lines[i].Trim();
				if (string.IsNullOrEmpty(line)) continue;

				if (line.StartsWith("FX_PRIM_EMITTER_DATA", StringComparison.OrdinalIgnoreCase))
				{
					if (current != null) prims.Add(current);
					current = new PrimData();
					currentInfo = string.Empty;
					currentChannel = string.Empty;
					continue;
				}

				if (current == null) continue;

				if (line.StartsWith("FX_INFO_", StringComparison.OrdinalIgnoreCase))
				{
					currentInfo = line;
					currentChannel = string.Empty;
					continue;
				}

				if (line.StartsWith("RATE:", StringComparison.OrdinalIgnoreCase)) nextValIsRate = true;
				if (line.StartsWith("LIFE:", StringComparison.OrdinalIgnoreCase)) nextValIsLife = true;
				if (line.StartsWith("ALPHA:", StringComparison.OrdinalIgnoreCase)) { currentChannel = "ALPHA"; nextValIsAlpha = true; }
				if (line.StartsWith("SIZEX:", StringComparison.OrdinalIgnoreCase)) { currentChannel = "SIZEX"; nextValIsSizeX = true; }
				if (line.StartsWith("SIZEY:", StringComparison.OrdinalIgnoreCase)) { currentChannel = "SIZEY"; nextValIsSizeY = true; }

				if (TryGetKeyValue(line, out var key, out var value))
				{
					if (key == "NAME") current.Name = value;
					if (key == "TEXTURE" && value != "NULL") current.Texture = value;

					if (key == "VAL")
					{
						var f = ParseFloat(value, 0.0f);
						if (nextValIsRate && currentInfo.StartsWith("FX_INFO_EMRATE")) { current.EmitRate = Math.Max(1.0f, f); nextValIsRate = false; }
						if (nextValIsLife && currentInfo.StartsWith("FX_INFO_EMLIFE")) { current.Life = Math.Max(0.016f, f); nextValIsLife = false; }
						if (nextValIsAlpha && currentInfo.StartsWith("FX_INFO_COLOUR") && currentChannel == "ALPHA") { current.Alpha = f; nextValIsAlpha = false; }
						if (nextValIsSizeX && currentInfo.StartsWith("FX_INFO_SIZE") && currentChannel == "SIZEX") { current.SizeX = Math.Max(0.01f, f); nextValIsSizeX = false; }
						if (nextValIsSizeY && currentInfo.StartsWith("FX_INFO_SIZE") && currentChannel == "SIZEY") { current.SizeY = Math.Max(0.01f, f); nextValIsSizeY = false; }
					}
				}
			}

			if (current != null) prims.Add(current);
			return prims;
		}

		private static bool TryGetKeyValue(string line, out string key, out string value)
		{
			key = null;
			value = null;
			var index = line.IndexOf(':');
			if (index <= 0) return false;
			key = line.Substring(0, index).Trim();
			value = line.Substring(index + 1).Trim();
			return true;
		}

		private static float ParseFloat(string value, float fallback)
		{
			if (float.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out var result)) return result;
			return fallback;
		}
	}
}
