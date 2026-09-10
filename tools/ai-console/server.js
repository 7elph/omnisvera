import express from "express";
import cors from "cors";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const MCP_URL = process.env.OMNISVERA_MCP_URL || "http://127.0.0.1:8765/mcp";
const OLLAMA_URL = process.env.OLLAMA_URL || "http://127.0.0.1:11434";
const PORT = parseInt(process.env.AI_CONSOLE_PORT || process.env.CONSOLE_PORT || "8787", 10);
const HOST = process.env.CONSOLE_HOST || process.env.AI_CONSOLE_HOST || "127.0.0.1";
const DEFAULT_MODEL = process.env.OLLAMA_MODEL || process.env.DEFAULT_MODEL || "gpt-oss:20b-cloud";

// Internal console token: never sent to browser/model/trace. Loaded from env or fallback file.
function _loadConsoleToken() {
  // Deployment choice only; never read from browser requests or tool arguments.
  if (process.env.OMNISVERA_AI_CONSOLE_PROFILE === "crypto") {
    const secret = process.env.OMNISVERA_AI_CONSOLE_CRYPTO_TOKEN;
    if (secret && secret.trim()) return secret.trim();
    return fs.readFileSync(path.resolve(__dirname, "..", "..", ".assistant-runtime", "omnisvera-mcp", "ai-console-crypto-token"), "utf-8").trim();
  }
  const envTok = process.env.OMNISVERA_AI_CONSOLE_TOKEN;
  if (envTok && envTok.trim()) return envTok.trim();
  try {
    const p = path.resolve(__dirname, "..", "..", ".assistant-runtime", "omnisvera-mcp", "ai-console-token");
    if (fs.existsSync(p)) return fs.readFileSync(p, "utf-8").trim();
  } catch {}
  // Also try .local-tools parent relative
  try {
    const p2 = path.resolve(process.cwd(), ".assistant-runtime", "omnisvera-mcp", "ai-console-token");
    if (fs.existsSync(p2)) return fs.readFileSync(p2, "utf-8").trim();
  } catch {}
  return null;
}
const CONSOLE_TOKEN = _loadConsoleToken();

function _mcpAuthHeaders() {
  const h = {};
  if (CONSOLE_TOKEN) {
    h["X-Omnisvera-Caller"] = "omnisvera-ai-console";
    h["X-Omnisvera-Console-Token"] = CONSOLE_TOKEN;
  }
  return h;
}

const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" }));
app.use(express.static(path.join(__dirname, "public")));

// --- MCP helpers (Streamable HTTP) ---
async function mcpCall(method, params = {}) {
  const body = JSON.stringify({ jsonrpc: "2.0", id: 1, method, params });
  const res = await fetch(MCP_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
      ..._mcpAuthHeaders(),
    },
    body,
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`MCP ${method} HTTP ${res.status}: ${txt.slice(0, 500)}`);
  }
  const text = await res.text();
  // SSE style: lines starting with data:
  const lines = text.split("\n");
  let dataLine = lines.find((l) => l.startsWith("data: "));
  if (!dataLine) {
    // fallback: try to parse whole text as json
    try {
      const j = JSON.parse(text);
      if (j.result !== undefined) return j.result;
      if (j.error) throw new Error(j.error.message || JSON.stringify(j.error));
      return j;
    } catch {
      throw new Error(`MCP ${method} no data line: ${text.slice(0, 500)}`);
    }
  }
  const jsonStr = dataLine.slice(6).trim();
  const payload = JSON.parse(jsonStr);
  if (payload.error) throw new Error(payload.error.message || JSON.stringify(payload.error));
  return payload.result;
}

async function mcpToolsList() {
  // Use tools/list via mcpCall
  const result = await mcpCall("tools/list", {});
  // result may be {tools: [...]} or directly tools array
  if (Array.isArray(result)) return result;
  if (result && Array.isArray(result.tools)) return result.tools;
  return [];
}

function mcpToOllamaTools(mcpTools) {
  return mcpTools.map((t) => ({
    type: "function",
    function: {
      name: t.name,
      description: t.description || t.name,
      parameters: t.inputSchema || { type: "object", properties: {} },
    },
  }));
}

function normalizeArgsForKey(args) {
  if (args == null) return "null";
  if (typeof args !== "object") return JSON.stringify(args);
  function sorted(v) {
    if (Array.isArray(v)) return v.map(sorted);
    if (v && typeof v === "object") {
      const out = {};
      Object.keys(v).sort().forEach((k) => { out[k] = sorted(v[k]); });
      return out;
    }
    return v;
  }
  try {
    return JSON.stringify(sorted(args));
  } catch {
    try { return JSON.stringify(args); } catch { return String(args); }
  }
}

async function mcpToolsCall(name, args) {
  const body = JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name, arguments: args || {} } });
  const res = await fetch(MCP_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
      ..._mcpAuthHeaders(),
    },
    body,
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`MCP tools/call HTTP ${res.status}: ${txt.slice(0, 500)}`);
  }
  const text = await res.text();
  const lines = text.split("\n");
  let dataLine = lines.find((l) => l.startsWith("data: "));
  let payload;
  if (!dataLine) {
    try {
      payload = JSON.parse(text);
    } catch {
      throw new Error(`MCP tools/call no data line: ${text.slice(0, 500)}`);
    }
  } else {
    const jsonStr = dataLine.slice(6).trim();
    payload = JSON.parse(jsonStr);
  }
  if (payload.error) throw new Error(payload.error.message || JSON.stringify(payload.error));
  const result = payload.result;
  // Preserve isError from MCP (check payload.isError or result.isError)
  const isError = !!(payload.isError || (result && result.isError));
  let contentText = "";
  if (typeof result === "string") contentText = result;
  else if (result && Array.isArray(result.content)) {
    contentText = result.content.map((c) => c.text ?? JSON.stringify(c)).join("\n");
  } else if (result && result.content) contentText = JSON.stringify(result);
  else contentText = JSON.stringify(result);
  return { content: contentText, isError, rawResult: result, payload };
}

// --- Status ---
app.get("/api/status", async (req, res) => {
  const status = { ollama: "unknown", mcp: "unknown", tools: 0, toolsList: [], error: null };
  // Ollama
  try {
    const r = await fetch(`${OLLAMA_URL}/api/tags`, { method: "GET" });
    if (r.ok) status.ollama = "connected";
    else status.ollama = `http ${r.status}`;
  } catch (e) {
    status.ollama = `error: ${e.message}`;
  }
  // MCP
  try {
    const tools = await mcpToolsList();
    status.mcp = "connected";
    status.tools = tools.length;
    status.toolsList = tools.map((t) => t.name);
  } catch (e) {
    status.mcp = `error: ${e.message}`;
  }
  res.json(status);
});

app.get("/api/tools", async (req, res) => {
  try {
    const tools = await mcpToolsList();
    res.json({ count: tools.length, tools });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// --- Chat (agent loop) ---
app.post("/api/chat", async (req, res) => {
  const { messages, model, stream } = req.body || {};
  if (!Array.isArray(messages) || messages.length === 0) {
    return res.status(400).json({ error: "messages required" });
  }
  const useModel = model || DEFAULT_MODEL;

  let ollamaTools = [];
  let mcpTools = [];
  try {
    mcpTools = await mcpToolsList();
    ollamaTools = mcpToOllamaTools(mcpTools);
  } catch (e) {
    return res.status(500).json({ error: `MCP tools/list failed: ${e.message}` });
  }

  // Agent loop
  let loopMessages = [...messages];
  const toolCallsLog = [];
  let finalContent = "";
  let iterations = 0;
  const maxIter = 12;
  // repetition tracking: key = name::normalizedArgs::error
  const failureCounts = new Map();

  try {
    while (iterations < maxIter) {
      iterations++;
      const ollamaBody = {
        model: useModel,
        messages: loopMessages,
        tools: ollamaTools,
        stream: false,
      };

      const r = await fetch(`${OLLAMA_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(ollamaBody),
      });

      if (!r.ok) {
        const txt = await r.text().catch(() => "");
        throw new Error(`Ollama /api/chat HTTP ${r.status}: ${txt.slice(0, 800)}`);
      }

      const data = await r.json();
      const msg = data.message || {};

      // If no tool calls, we're done
      const toolCalls = msg.tool_calls || [];
      if (toolCalls.length === 0) {
        finalContent = msg.content || "";
        break;
      }

      // Record assistant tool call intent
      loopMessages.push(msg);

      // Execute each tool call sequentially
      for (const tc of toolCalls) {
        const fname = tc.function?.name || tc.name;
        let fargs = tc.function?.arguments || tc.arguments || {};
        // Ollama may send arguments as JSON string
        if (typeof fargs === "string") {
          try {
            fargs = JSON.parse(fargs);
          } catch {
            fargs = {};
          }
        }
        const normalized = normalizeArgsForKey(fargs);
        // Check repetition before execution: if same tool+args already failed twice with same error, short-circuit
        let repeated = null;
        for (const [key, count] of failureCounts.entries()) {
          if (count >= 2 && key.startsWith(fname + "::" + normalized + "::")) {
            const errPart = key.slice((fname + "::" + normalized + "::").length);
            repeated = errPart;
            break;
          }
        }
        const started_at = new Date().toISOString();
        const startedMs = Date.now();
        let toolResultText = "";
        let toolError = null;
        let isMcpError = false;
        let duration_ms = 0;

        if (repeated !== null) {
          // Do not execute third time - repeated failure guard
          toolError = `Repetição detectada: a ferramenta '${fname}' com os mesmos argumentos falhou 2 vezes com o erro '${repeated}'. Escolha outra estratégia em vez de repetir a chamada. (Repeated failure: choose another strategy instead of repeating the same tool call.)`;
          toolResultText = `Erro de repetição: ${toolError} (args: ${normalized}) - Repeated failure, choose another strategy.`;
          isMcpError = true;
          duration_ms = Date.now() - startedMs;
          // do not increment failureCounts further for synthetic? keep as is
        } else {
          try {
            const callRes = await mcpToolsCall(fname, fargs);
            toolResultText = callRes.content;
            isMcpError = !!callRes.isError;
            if (isMcpError) {
              toolError = callRes.content.slice(0, 800);
              // track failure for repetition
              const key = fname + "::" + normalized + "::" + toolError;
              failureCounts.set(key, (failureCounts.get(key) || 0) + 1);
            }
          } catch (e) {
            toolError = e.message;
            toolResultText = `Error calling ${fname}: ${e.message}`;
            isMcpError = true;
            const key = fname + "::" + normalized + "::" + toolError;
            failureCounts.set(key, (failureCounts.get(key) || 0) + 1);
          }
          duration_ms = Date.now() - startedMs;
        }

        const status = (toolError || isMcpError) ? "error" : "success";
        toolCallsLog.push({
          id: tc.id || `${fname}-${Date.now()}-${Math.random().toString(36).slice(2,6)}`,
          name: fname,
          arguments: fargs,
          result: toolResultText.slice(0, 8000),
          error: toolError,
          started_at,
          duration_ms,
          status,
          isError: isMcpError,
        });
        // Append tool result as role=tool
        loopMessages.push({
          role: "tool",
          content: toolResultText,
          tool_name: fname,
        });
      }

      // If Ollama returned tool_calls but also content, keep content
      if (msg.content) {
        finalContent = msg.content;
      }
    }

    // --- Trace experimental (outside Core, not Memory) ---
    let proofFields = { experience: null, validation: null, commit: null, prediction_persisted: null };
    let _userPrompt = "";
    try { _userPrompt = (messages.find(m=>m.role==="user")||messages[0]||{}).content || ""; } catch {}
    try {
      for (const tc of toolCallsLog) {
        let parsed = null;
        try { parsed = JSON.parse(tc.result); } catch {}
        // experience from bootstrap or experience.latest
        if (tc.name === "system.bootstrap" && parsed) {
          const exps = parsed.experiences || (parsed.experience && parsed.experience.per_world && Object.values(parsed.experience.per_world).flat()) || [];
          if (Array.isArray(exps) && exps.length) {
            const profileWorld = process.env.OMNISVERA_AI_CONSOLE_PROFILE === "crypto" ? "crypto" : "football";
            const e = exps.find(x=>x.world_id===profileWorld) || exps[0];
            if (e && !proofFields.experience) proofFields.experience = {
              experience_id: e.experience_id || e.latest_experience_id,
              state_version: e.state_version ?? e.latest_state_version,
              learned_state_schema: e.learned_state_schema,
              learned_state_hash: e.learned_state_hash,
              integrity_ok: e.integrity_ok,
              world_id: e.world_id, predictor_id: e.predictor_id, predictor_version: e.predictor_version
            };
          }
        }
        if (tc.name === "experience.latest" && parsed && !proofFields.experience) {
          if (parsed.experience_id) proofFields.experience = {
            experience_id: parsed.experience_id,
            state_version: parsed.state_version,
            learned_state_schema: parsed.learned_state_schema,
            learned_state_hash: parsed.learned_state_hash,
            integrity_ok: parsed.integrity_ok,
            world_id: parsed.world_id, predictor_id: parsed.predictor_id, predictor_version: parsed.predictor_version
          };
        }
        if (tc.name === "epistemic.validate_candidate" && parsed && typeof parsed.valid === "boolean") {
          proofFields.validation = {
            valid: parsed.valid, errors: parsed.errors, warnings: parsed.warnings,
            experience: parsed.experience || null
          };
        }
        if (tc.name === "epistemic.commit_candidate" && parsed) {
          proofFields.commit = {
            called: true, status: parsed.status, prediction_id: parsed.prediction_id || null,
            candidate_hash: parsed.candidate_hash || null, raw: parsed
          };
          // try to fetch persisted prediction for proof (best-effort, no error propagation)
          if (parsed.prediction_id) {
            try {
              const persisted = await mcpToolsCall("epistemic.get_prediction", { prediction_id: parsed.prediction_id });
              let p = null; try { p = JSON.parse(persisted.content); } catch {}
              if (p) proofFields.prediction_persisted = {
                id: p.id ?? parsed.prediction_id,
                experience_id: p.experience_id ?? null,
                experience_state_version: p.experience_state_version ?? null,
                experience_state_hash: p.experience_state_hash ?? null,
                snapshot_memory_id: p.snapshot_memory_id || p.snapshot_ref || null,
                domain: p.domain, predictor_id: p.predictor_id, predictor_version: p.predictor_version
              };
            } catch {}
          }
        }
      }
    } catch {}

    // Write artifact (never includes token)
    let artifactPath = null;
    try {
      const expDir = path.resolve(__dirname, "..", "..", ".assistant-runtime", "experiments");
      // also ensure absolute from cwd fallback
      const altDir = path.resolve(process.cwd(), ".assistant-runtime", "experiments");
      const dir = fs.existsSync(expDir) ? expDir : altDir;
      fs.mkdirSync(dir, { recursive: true });
      const ts = new Date().toISOString().replace(/[:.]/g,"-");
      const safeModel = useModel.replace(/[^a-zA-Z0-9._-]/g,"-");
      const sid = Math.random().toString(36).slice(2,7);
      const fname = `handoff-${ts}-${safeModel}-${sid}.json`;
      artifactPath = path.join(dir, fname);
      const artifact = {
        experiment: "cold_handoff",
        timestamp: new Date().toISOString(),
        caller_class: "external-ai",
        provider: "ollama",
        model: useModel,
        user_prompt: _userPrompt,
        tool_sequence: toolCallsLog.map((tc,i)=>({seq:i+1,name:tc.name,arguments:tc.arguments,started_at:tc.started_at,duration_ms:tc.duration_ms,status:tc.status,isError:tc.isError,result:tc.result})),
        validation: proofFields.validation,
        commit: proofFields.commit,
        proof_fields: proofFields,
        iterations,
        final_response: finalContent,
        mcpTools: mcpTools.map((t)=>t.name),
      };
      fs.writeFileSync(artifactPath, JSON.stringify(artifact, null, 2), "utf-8");
    } catch (e) {
      console.error("trace artifact write failed:", e.message);
    }

    res.json({
      model: useModel,
      content: finalContent,
      toolCalls: toolCallsLog,
      iterations,
      mcpTools: mcpTools.map((t) => t.name),
      proof_fields: proofFields,
      trace_artifact: artifactPath,
    });
  } catch (e) {
    res.status(500).json({ error: e.message, toolCalls: toolCallsLog, mcpTools: mcpTools.map((t) => t.name) });
  }
});

app.listen(PORT, HOST, () => {
  console.log(`Omnisvera AI Console v0.1 listening on http://${HOST}:${PORT}`);
  console.log(`MCP: ${MCP_URL} (127.0.0.1 only)  Ollama: ${OLLAMA_URL} (127.0.0.1 only)  default model: ${DEFAULT_MODEL}`);
  console.log(`Remote: use Tailscale Serve -> http://${HOST}:${PORT}  (do NOT expose 8765/11434)`);
});
