using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;

namespace Effekseer.Importer
{
	public static class GtaSaFxImporter
	{
		public class FxEntry
		{
			public string Type;
			public string Name;
			public Dictionary<string, string> Parameters = new Dictionary<string, string>();
		}

		public static List<FxEntry> Parse(string path)
		{
			var entries = new List<FxEntry>();
			FxEntry current = null;
			foreach (var raw in File.ReadLines(path))
			{
				var line = raw.Trim();
				if (string.IsNullOrEmpty(line) || line.StartsWith("#") || line.StartsWith("//")) continue;

				if (line.StartsWith("{") || line.StartsWith("}")) continue;

				if (line.StartsWith("effect", StringComparison.OrdinalIgnoreCase) || line.StartsWith("fx", StringComparison.OrdinalIgnoreCase))
				{
					if (current != null) entries.Add(current);
					var tokens = SplitTokens(line);
					current = new FxEntry();
					current.Type = tokens.Length > 0 ? tokens[0] : "effect";
					current.Name = tokens.Length > 1 ? tokens[1] : $"FX_{entries.Count}";
					continue;
				}

				if (current == null)
				{
					current = new FxEntry() { Type = "effect", Name = $"FX_{entries.Count}" };
				}

				var pair = line.Split(new[] { '=' }, 2);
				if (pair.Length == 2)
				{
					current.Parameters[pair[0].Trim()] = pair[1].Trim().TrimEnd(';');
				}
				else
				{
					var tokens = SplitTokens(line);
					if (tokens.Length >= 2)
					{
						current.Parameters[tokens[0]] = string.Join(" ", tokens.Skip(1));
					}
				}
			}

			if (current != null) entries.Add(current);
			return entries;
		}

		public static Data.NodeRoot ImportToEffekseer(string path)
		{
			var root = new Data.NodeRoot();
			root.SetFullPath(Path.ChangeExtension(path, ".efkefc"));

			var entries = Parse(path);
			if (entries.Count == 0)
			{
				root.AddChild();
				return root;
			}

			foreach (var entry in entries)
			{
				var node = root.AddChild();
				node.Name.SetValueDirectly(entry.Name);
				node.CommonValues.MaxGeneration.SetValue(1);
				node.CommonValues.Life.SetValue(60);
				node.CommonValues.GenerationTime.SetValue(1);

				if (entry.Parameters.TryGetValue("texture", out var tex) || entry.Parameters.TryGetValue("tex", out tex))
				{
					node.RendererCommonValues.ColorTexture.SetAbsolutePath(tex.Trim('"'));
				}

				if (entry.Parameters.TryGetValue("size", out var size))
				{
					var f = ParseFloat(size, 10.0f);
					node.ScalingValues.Fixed.ScaleX.SetValue(f);
					node.ScalingValues.Fixed.ScaleY.SetValue(f);
					node.ScalingValues.Fixed.ScaleZ.SetValue(f);
				}
			}

			return root;
		}

		private static string[] SplitTokens(string line)
		{
			return line.Split(new[] { ' ', '\t', ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
		}

		private static float ParseFloat(string value, float fallback)
		{
			var token = SplitTokens(value).FirstOrDefault() ?? string.Empty;
			if (float.TryParse(token, NumberStyles.Float, CultureInfo.InvariantCulture, out var result))
			{
				return result;
			}
			return fallback;
		}
	}
}
