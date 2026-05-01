using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Xml;

namespace GTA_SA_Effect_Editor
{
    public class EfkProjExporter
    {
        public void Export(string path, Effect effect)
        {
            if (effect == null) throw new ArgumentNullException(nameof(effect));

            var settings = new XmlWriterSettings
            {
                Encoding = new UTF8Encoding(false),
                Indent = true,
                IndentChars = "  "
            };

            using (var writer = XmlWriter.Create(path, settings))
            {
                writer.WriteStartDocument();
                writer.WriteStartElement("EffekseerProject");

                writer.WriteStartElement("Root");
                WriteSimpleElement(writer, "Name", effect.Name ?? "ImportedFxs");
                writer.WriteStartElement("Children");

                foreach (var prim in effect.Nodes.OfType<Prim>())
                {
                    WriteNode(writer, prim);
                }

                writer.WriteEndElement(); // Children
                writer.WriteEndElement(); // Root
                writer.WriteEndElement(); // EffekseerProject
                writer.WriteEndDocument();
            }
        }

        private static void WriteNode(XmlWriter writer, Prim prim)
        {
            writer.WriteStartElement("Node");

            writer.WriteStartElement("CommonValues");
            WriteSimpleElement(writer, "MaxGeneration", "1");
            WriteSimpleElement(writer, "GenerationTime", "0");
            WriteSimpleElement(writer, "GenerationTimeOffset", "0");
            writer.WriteEndElement();

            writer.WriteStartElement("RendererCommonValues");
            WriteSimpleElement(writer, "MaterialType", "0");
            writer.WriteEndElement();

            writer.WriteStartElement("RendererValues");
            WriteSimpleElement(writer, "Type", "2");
            writer.WriteStartElement("Sprite");
            var texture = prim.Textures.FirstOrDefault();
            if (!string.IsNullOrWhiteSpace(texture))
            {
                writer.WriteStartElement("ColorTexture");
                WriteSimpleElement(writer, "RelativePath", texture);
                writer.WriteEndElement();
            }
            writer.WriteEndElement(); // Sprite
            writer.WriteEndElement(); // RendererValues

            writer.WriteStartElement("UserData");
            WriteSimpleElement(writer, "FxsInfoCount", prim.Nodes.Count.ToString(CultureInfo.InvariantCulture));
            writer.WriteEndElement();

            writer.WriteEndElement(); // Node
        }

        private static void WriteSimpleElement(XmlWriter writer, string name, string value)
        {
            writer.WriteStartElement(name);
            writer.WriteString(value);
            writer.WriteEndElement();
        }
    }
}
