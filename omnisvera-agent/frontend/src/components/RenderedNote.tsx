import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getAccessToken } from "../api";

type RenderedNoteProps = {
  content: string;
};

function encodeMediaPath(path: string) {
  return path
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
}

function mediaUrl(path: string) {
  const cleanPath = path.replace(/^\/+/, "");
  const token = getAccessToken();
  const query = token ? `?token=${encodeURIComponent(token)}` : "";
  return `/media/${encodeMediaPath(cleanPath)}${query}`;
}

function normalizeMediaTarget(target: string) {
  const clean = target.split("|")[0].trim();
  if (clean.startsWith("zz_media/")) return clean;
  return `zz_media/${clean}`;
}

function prettifyWikilink(target: string) {
  const [path, label] = target.split("|");
  return (label || path.split("/").pop() || path).replace(/\.md$/i, "");
}

function transformObsidianMarkdown(content: string) {
  let transformed = content;

  transformed = transformed.replace(/```(dataview|datacards|leaflet)([\s\S]*?)```/gi, (_match, kind) => {
    const label = String(kind).toLowerCase();
    if (label === "leaflet") return "\n\n> [!map] Mapa Leaflet disponível no Obsidian.\n\n";
    if (label === "datacards") return "\n\n> [!cards] DataCards disponível no Obsidian.\n\n";
    return "\n\n> [!query] Consulta Dataview disponível no Obsidian.\n\n";
  });

  transformed = transformed.replace(/^>\s*\[!(\w+)\]([+-])?\s*(.*)$/gim, (_match, kind, collapse, title) => {
    const marker = collapse ? " recolhido" : "";
    return `> **${String(kind).toUpperCase()}${marker}${title ? ` — ${title}` : ""}**`;
  });

  transformed = transformed.replace(/!\[\[([^\]]+)\]\]/g, (_match, target) => {
    const raw = String(target);
    const [path, pipe] = raw.split("|");
    const mediaPath = normalizeMediaTarget(path);
    const alt = path.split("/").pop() || "imagem";
    const size = pipe && /^\d+$/.test(pipe.trim()) ? ` width="${pipe.trim()}"` : "";
    return `<img src="${mediaUrl(mediaPath)}" alt="${alt}"${size} />`;
  });

  transformed = transformed.replace(/\[\[([^\]]+)\]\]/g, (_match, target) => {
    const label = prettifyWikilink(String(target));
    return `**${label}**`;
  });

  return transformed;
}

export default function RenderedNote({ content }: RenderedNoteProps) {
  return (
    <div className="rendered-note">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          img: ({ ...props }) => <img loading="lazy" {...props} />,
          a: ({ children, ...props }) => (
            <a target="_blank" rel="noreferrer" {...props}>
              {children}
            </a>
          ),
        }}
      >
        {transformObsidianMarkdown(content)}
      </ReactMarkdown>
    </div>
  );
}
