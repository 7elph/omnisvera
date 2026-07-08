import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { mediaUrlFromVaultPath, resolveNote } from "../api";

type RenderedNoteProps = {
  content: string;
  onOpenNote?: (id: number) => void;
};

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
    return `<img src="${mediaUrlFromVaultPath(mediaPath)}" alt="${alt}"${size} />`;
  });

  transformed = transformed.replace(/\[\[([^\]]+)\]\]/g, (_match, target) => {
    const label = prettifyWikilink(String(target));
    const encodedTarget = encodeURIComponent(String(target));
    return `[${label}](omnisvera://note/${encodedTarget})`;
  });

  return transformed;
}

export default function RenderedNote({ content, onOpenNote }: RenderedNoteProps) {
  async function handleLink(event: React.MouseEvent<HTMLAnchorElement>, href?: string) {
    if (!href?.startsWith("omnisvera://note/")) return;
    event.preventDefault();
    if (!onOpenNote) return;
    const target = decodeURIComponent(href.replace("omnisvera://note/", ""));
    const note = await resolveNote(target);
    if (note) onOpenNote(note.id);
  }

  return (
    <div className="rendered-note">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          img: ({ ...props }) => <img loading="lazy" {...props} />,
          a: ({ children, href, ...props }) => (
            <a
              href={href}
              onClick={(event) => handleLink(event, href)}
              target={href?.startsWith("omnisvera://note/") ? undefined : "_blank"}
              rel={href?.startsWith("omnisvera://note/") ? undefined : "noreferrer"}
              {...props}
            >
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
