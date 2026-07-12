import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getAccessMode, mediaUrlFromVaultPath, resolveNote } from "../api";

type RenderedNoteProps = {
  content: string;
  onOpenNote?: (id: number) => void;
  onUnknownNote?: (target: string) => void;
};

function normalizeMediaTarget(target: string) {
  const clean = target
    .split("|")[0]
    .trim()
    .replace(/^\/media\//, "")
    .split("?")[0];
  if (clean.startsWith("zz_media/")) return clean;
  return `zz_media/${clean}`;
}

function prettifyWikilink(target: string) {
  const [path, label] = target.split("|");
  return (label || path.split("/").pop() || path).replace(/\.md$/i, "");
}

function noteHrefFromTarget(target: string) {
  return `#/note/${encodeURIComponent(target)}`;
}

function noteTargetFromHref(href?: string) {
  if (!href) return null;
  const legacyPrefix = "omnisvera://note/";
  if (href.startsWith(legacyPrefix)) {
    return decodeURIComponent(href.slice(legacyPrefix.length));
  }

  const hashPrefix = "#/note/";
  const hashIndex = href.indexOf(hashPrefix);
  if (hashIndex >= 0) {
    return decodeURIComponent(href.slice(hashIndex + hashPrefix.length));
  }

  return null;
}

function stripInlineHtml(value: string) {
  return value.replace(/<[^>]+>/g, "").trim();
}

function parseMediaTarget(target: string, fallbackAlt = "imagem") {
  const clean = target.trim().replace(/^\/media\//, "").split("?")[0];
  const [rawPath, ...rawModifiers] = clean.split("|").map((part) => part.trim()).filter(Boolean);
  const modifier = rawModifiers[0] || "";
  const width = modifier.match(/^\d+$/) ? modifier : "";
  const alt = width ? fallbackAlt : modifier || fallbackAlt;
  return {
    path: normalizeMediaTarget(rawPath || clean),
    alt,
    width,
  };
}

function mediaMarkdownFromTarget(target: string, alt = "imagem") {
  const parsed = parseMediaTarget(target, alt);
  const url = mediaUrlFromVaultPath(parsed.path);
  const safeAlt = parsed.alt || parsed.path.split("/").pop() || "imagem";
  return parsed.width ? `![${safeAlt}](${url} "w:${parsed.width}")` : `![${safeAlt}](${url})`;
}

function displayCalloutKind(kind: string) {
  const normalized = kind.toLowerCase();
  const labels: Record<string, string> = {
    abstract: "Resumo",
    attention: "Atenção",
    bug: "Problema",
    cards: "Cards",
    caution: "Cuidado",
    danger: "Perigo",
    error: "Erro",
    example: "Exemplo",
    failure: "Falha",
    faq: "Pergunta",
    help: "Ajuda",
    hint: "Dica",
    important: "Importante",
    info: "Info",
    infobox: "Ficha visual",
    map: "Mapa",
    note: "Nota",
    query: "Consulta",
    question: "Pergunta",
    quote: "Citação",
    success: "Sucesso",
    summary: "Resumo",
    tip: "Dica",
    todo: "A fazer",
    warning: "Aviso",
    world: "Mundo",
  };
  return labels[normalized] || kind;
}

function stripCalloutBlocksByTitle(content: string, blockedTitles: RegExp[]) {
  const lines = content.split("\n");
  const kept: string[] = [];
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const callout = line.match(/^>\s*\[!([^\]\|\s]+)(?:\|[^\]]+)?\]([+-])?\s*(.*)$/i);
    const title = callout?.[3] || "";
    if (callout && blockedTitles.some((pattern) => pattern.test(title))) {
      while (index + 1 < lines.length && (lines[index + 1].startsWith(">") || lines[index + 1].trim() === "")) {
        index += 1;
        if (lines[index].trim() === "") break;
      }
      continue;
    }
    kept.push(line);
  }
  return kept.join("\n");
}

function removeEmptySections(content: string) {
  const lines = content.split("\n");
  const kept: string[] = [];
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const heading = line.match(/^(#{2,6})\s+(.+?)\s*$/);
    if (!heading) {
      kept.push(line);
      continue;
    }

    let cursor = index + 1;
    const sectionLines: string[] = [];
    while (cursor < lines.length && !/^#{1,6}\s+/.test(lines[cursor])) {
      sectionLines.push(lines[cursor]);
      cursor += 1;
    }

    const meaningful = sectionLines.some((sectionLine) => {
      const clean = sectionLine.trim();
      return clean && clean !== "---" && !/^>\s*$/.test(clean);
    });

    if (!meaningful) {
      index = cursor - 1;
      continue;
    }

    kept.push(line, ...sectionLines);
    index = cursor - 1;
  }
  return kept.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

function stripSectionsByTitle(content: string, blockedTitles: RegExp[]) {
  const lines = content.split("\n");
  const kept: string[] = [];
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const heading = line.match(/^(#{2,6})\s+(.+?)\s*$/);
    if (!heading) {
      kept.push(line);
      continue;
    }

    const level = heading[1].length;
    const title = heading[2].trim();
    if (!blockedTitles.some((pattern) => pattern.test(title))) {
      kept.push(line);
      continue;
    }

    index += 1;
    while (index < lines.length) {
      const nextHeading = lines[index].match(/^(#{2,6})\s+(.+?)\s*$/);
      if (nextHeading && nextHeading[1].length <= level) {
        index -= 1;
        break;
      }
      index += 1;
    }
  }
  return kept.join("\n");
}

function normalizeMarkdownImageSrc(src?: string) {
  if (!src) return src;
  if (/^(https?:|data:|blob:)/i.test(src)) return src;
  if (src.startsWith("/media/")) return src;
  if (src.startsWith("zz_media/")) return mediaUrlFromVaultPath(src);
  if (/\.(png|jpe?g|gif|webp|svg)$/i.test(src)) return mediaUrlFromVaultPath(src);
  return src;
}

function transformObsidianMarkdown(content: string) {
  const isPlayerMode = getAccessMode() === "player";
  let transformed = content;

  transformed = stripCalloutBlocksByTitle(transformed, [/template aplicado/i]);
  if (isPlayerMode) {
    transformed = stripSectionsByTitle(transformed, [
      /^pend[eê]ncias?/i,
      /^pendencias?/i,
      /^uso em mesa/i,
      /^como usar/i,
      /^como apresentar/i,
      /^fun[cç][aã]o em jogo/i,
      /^ganchos?/i,
      /^poss[ií]veis ganchos/i,
      /^templates?/i,
      /^template aplicado/i,
      /^notas t[eé]cnicas?/i,
    ]);
  }

  transformed = transformed.replace(/<h([1-6])[^>]*>([\s\S]*?)<\/h\1>/gi, (_match, level, inner) => {
    const hashes = "#".repeat(Number(level));
    return `\n\n${hashes} ${stripInlineHtml(String(inner))}\n\n`;
  });

  transformed = transformed.replace(/<br\s*\/?>/gi, "\n");
  transformed = transformed.replace(/<hr\s*\/?>/gi, "\n\n---\n\n");
  transformed = transformed.replace(/<\/?(div|center|span)[^>]*>/gi, "\n");

  transformed = transformed.replace(/<img\b[^>]*\bsrc=["']([^"']+)["'][^>]*>/gi, (match, src) => {
    const altMatch = String(match).match(/\balt=["']([^"']*)["']/i);
    const alt = altMatch?.[1] || String(src).split("/").pop()?.split("?")[0] || "imagem";
    return `\n\n${mediaMarkdownFromTarget(String(src), alt)}\n\n`;
  });

  transformed = transformed.replace(/```(dataview|datacards|leaflet)([\s\S]*?)```/gi, (_match, kind) => {
    if (isPlayerMode) return "\n\n";
    const label = String(kind).toLowerCase();
    if (label === "leaflet") return "\n\n> [!map] Mapa Leaflet disponível no Obsidian.\n\n";
    if (label === "datacards") return "\n\n> [!cards] DataCards disponível no Obsidian.\n\n";
    return "\n\n> [!query] Consulta Dataview disponível no Obsidian.\n\n";
  });

  transformed = transformed.replace(/^>\s*\[!([^\]\|\s]+)(?:\|([^\]]+))?\]([+-])?\s*(.*)$/gim, (_match, kind, classes, collapse, title) => {
    const marker = collapse === "-" ? " recolhido" : "";
    const rawKind = String(kind);
    const classText = String(classes || "");
    const label = rawKind.toLowerCase() === "note" && /clean|right|infobox/i.test(classText)
      ? "Retrato"
      : displayCalloutKind(rawKind);
    return `> **${label}${marker}${title ? ` — ${title}` : ""}**`;
  });

  transformed = transformed.replace(/!\[\[([^\]]+)\]\]/g, (_match, target) => {
    const raw = String(target);
    const [path] = raw.split("|");
    const alt = path.split("/").pop() || "imagem";
    return mediaMarkdownFromTarget(raw, alt);
  });

  transformed = transformed.replace(/\[\[([^\]]+)\]\]/g, (_match, target) => {
    const label = prettifyWikilink(String(target));
    return `[${label}](${noteHrefFromTarget(String(target))})`;
  });

  transformed = transformed.replace(/^(\*\*[^*\n]+:\*\*\s*.+)$/gm, "- $1");

  return removeEmptySections(transformed);
}

export default function RenderedNote({ content, onOpenNote, onUnknownNote }: RenderedNoteProps) {
  async function handleLink(event: React.MouseEvent<HTMLAnchorElement>, href?: string) {
    const target = noteTargetFromHref(href);
    if (!target) return;
    event.preventDefault();
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
    if (!onOpenNote) {
      onUnknownNote?.(target);
      return;
    }
    try {
      const note = await resolveNote(target);
      if (note) {
        onOpenNote(note.id);
        return;
      }
      onUnknownNote?.(target);
    } catch {
      onUnknownNote?.(target);
      return;
    }
  }

  return (
    <div className="rendered-note">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          img: ({ ...props }) => {
            const widthMatch = typeof props.title === "string" ? props.title.match(/^w:(\d+)$/) : null;
            const width = widthMatch ? Number(widthMatch[1]) : undefined;
            const src = normalizeMarkdownImageSrc(typeof props.src === "string" ? props.src : undefined);
            return (
              <img
                loading="lazy"
                {...props}
                src={src}
                title={width ? undefined : props.title}
                style={width ? { maxWidth: `${width}px`, width: "100%" } : props.style}
              />
            );
          },
          a: ({ children, href, ...props }) => (
            <a
              href={href}
              onClick={(event) => handleLink(event, href)}
              target={noteTargetFromHref(href) ? undefined : "_blank"}
              rel={noteTargetFromHref(href) ? undefined : "noreferrer"}
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
