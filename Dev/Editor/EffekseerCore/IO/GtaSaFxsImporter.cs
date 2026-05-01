using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Xml;

namespace Effekseer.IO
{
    /// <summary>
    /// Imports GTA SA *.fxs files and exports an Effekseer *.efkproj file.
    /// </summary>
    public static class GtaSaFxsImporter
    {
        private sealed class ParsedEffect
        {
            public string Name;
            public List<ParsedPrim> Prims = new List<ParsedPrim>();
        }

        private sealed class ParsedPrim
        {
            public List<string> Textures = new List<string>();
            public int InfoCount;
        }

        public static void ConvertToEfkProj(string inputFxsPath, string outputEfkProjPath)
        {
            if (string.IsNullOrEmpty(inputFxsPath)) throw new ArgumentException("inputFxsPath is empty.");
            if (string.IsNullOrEmpty(outputEfkProjPath)) throw new ArgumentException("outputEfkProjPath is empty.");

            var lines = File.ReadAllLines(inputFxsPath, Encoding.GetEncoding(1251));
            var effect = Parse(lines);
            WriteProject(outputEfkProjPath, effect);
        }

        private static ParsedEffect Parse(string[] lines)
        {
            var effect = new ParsedEffect();
            int currentPrim = -1;

            for (int i = 0; i < lines.Length; i++)
            {
                var line = (lines[i] ?? string.Empty).Trim();

                if (line.StartsWith("FILENAME:", StringComparison.OrdinalIgnoreCase))
                {
                    var fileName = line.Substring("FILENAME:".Length).Trim();
                    effect.Name = Path.GetFileNameWithoutExtension(fileName);
                    continue;
                }

                if (line.StartsWith("FX_PRIM_EMITTER_DATA", StringComparison.OrdinalIgnoreCase))
                {
                    effect.Prims.Add(new ParsedPrim());
                    currentPrim = effect.Prims.Count - 1;
                    continue;
                }

                if (currentPrim >= 0 && line.StartsWith("TEXTURE", StringComparison.OrdinalIgnoreCase))
                {
                    var split = line.Split(':');
                    if (split.Length > 1)
                    {
                        var texture = split[1].Trim();
                        if (!string.IsNullOrEmpty(texture))
                        {
                            effect.Prims[currentPrim].Textures.Add(texture);
                        }
                    }
                    continue;
                }

                if (currentPrim >= 0 && line.StartsWith("NUM_INFOS", StringComparison.OrdinalIgnoreCase))
                {
                    var split = line.Split(':');
                    if (split.Length > 1)
                    {
                        int count;
                        if (int.TryParse(split[1].Trim(), NumberStyles.Integer, CultureInfo.InvariantCulture, out count))
                        {
                            effect.Prims[currentPrim].InfoCount = count;
                        }
                    }
                }
            }

            if (string.IsNullOrEmpty(effect.Name))
            {
                effect.Name = "ImportedFxs";
            }

            return effect;
        }

        private static void WriteProject(string outputPath, ParsedEffect effect)
        {
            var settings = new XmlWriterSettings();
            settings.Encoding = new UTF8Encoding(false);
            settings.Indent = true;
            settings.IndentChars = "  ";

            using (var writer = XmlWriter.Create(outputPath, settings))
            {
                writer.WriteStartDocument();
                writer.WriteStartElement("EffekseerProject");
                writer.WriteStartElement("Root");
                Write(writer, "Name", effect.Name);
                writer.WriteStartElement("Children");

                foreach (var prim in effect.Prims)
                {
                    writer.WriteStartElement("Node");

                    writer.WriteStartElement("CommonValues");
                    Write(writer, "MaxGeneration", "1");
                    Write(writer, "GenerationTime", "0");
                    Write(writer, "GenerationTimeOffset", "0");
                    writer.WriteEndElement();

                    writer.WriteStartElement("RendererCommonValues");
                    Write(writer, "MaterialType", "0");
                    writer.WriteEndElement();

                    writer.WriteStartElement("RendererValues");
                    Write(writer, "Type", "2");
                    writer.WriteStartElement("Sprite");
                    if (prim.Textures.Count > 0)
                    {
                        writer.WriteStartElement("ColorTexture");
                        Write(writer, "RelativePath", prim.Textures[0]);
                        writer.WriteEndElement();
                    }
                    writer.WriteEndElement();
                    writer.WriteEndElement();

                    writer.WriteStartElement("UserData");
                    Write(writer, "GtaNumInfos", prim.InfoCount.ToString(CultureInfo.InvariantCulture));
                    writer.WriteEndElement();

                    writer.WriteEndElement();
                }

                writer.WriteEndElement();
                writer.WriteEndElement();
                writer.WriteEndElement();
                writer.WriteEndDocument();
            }
        }

        private static void Write(XmlWriter writer, string name, string value)
        {
            writer.WriteStartElement(name);
            writer.WriteString(value);
            writer.WriteEndElement();
        }
    }
}
