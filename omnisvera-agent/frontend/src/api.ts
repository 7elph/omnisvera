const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  `${window.location.protocol}//${window.location.hostname}:8787`;

export type NoteSummary = {
  id: number;
  path: string;
  title: string;
  aliases: string[];
  type?: string | null;
  visibility?: string | null;
  tags: string[];
  updated_at: string;
};

export type NoteDetail = NoteSummary & {
  content: string;
  frontmatter: Record<string, unknown>;
};

export type SearchResult = NoteSummary & {
  score: number;
  excerpt: string;
};

export async function health() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error("Falha ao consultar /health");
  return response.json();
}

export async function rebuildIndex() {
  const response = await fetch(`${API_BASE}/index/rebuild`, { method: "POST" });
  if (!response.ok) throw new Error("Falha ao reconstruir índice");
  return response.json();
}

export async function listNotes(): Promise<NoteSummary[]> {
  const response = await fetch(`${API_BASE}/notes`);
  if (!response.ok) throw new Error("Falha ao listar notas");
  return response.json();
}

export async function getNote(id: number): Promise<NoteDetail> {
  const response = await fetch(`${API_BASE}/notes/${id}`);
  if (!response.ok) throw new Error("Nota não encontrada");
  return response.json();
}

export async function searchNotes(query: string, limit = 10): Promise<SearchResult[]> {
  const response = await fetch(`${API_BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
  });
  if (!response.ok) throw new Error("Falha na busca");
  return response.json();
}

export async function chatVault(question: string, limit = 6) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, limit }),
  });
  if (!response.ok) throw new Error("Falha no chat");
  return response.json();
}
