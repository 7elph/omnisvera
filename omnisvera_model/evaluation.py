from __future__ import annotations

import json
import re
import statistics
import time
import urllib.request
from pathlib import Path
from typing import Any

from .io import normalized_text, read_json, write_json
from .paths import MODEL_ROOT


def _chat(base_url: str, model: str, case: dict[str, Any], timeout: int) -> tuple[str, float, dict[str, Any]]:
    prompt = "Contexto autorizado:\n- " + "\n- ".join(case.get("context") or []) + f"\n\nPergunta: {case['question']}"
    payload = {"model":model,"stream":False,"messages":[
        {"role":"system","content":"Use apenas o contexto. Não invente. Responda em português."},
        {"role":"user","content":prompt}],"options":{"temperature":0.0,"num_predict":180,"num_ctx":2048}}
    request=urllib.request.Request(base_url.rstrip("/")+"/api/chat",data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),headers={"Content-Type":"application/json"},method="POST")
    started=time.perf_counter()
    with urllib.request.urlopen(request,timeout=timeout) as response: result=json.load(response)
    usage={key:result.get(key) for key in ("prompt_eval_count","eval_count","load_duration","prompt_eval_duration","eval_duration")}
    eval_seconds=(float(result.get("eval_duration") or 0)/1_000_000_000)
    usage["tokens_per_second"]=round(float(result.get("eval_count") or 0)/eval_seconds,2) if eval_seconds else None
    return str((result.get("message") or {}).get("content") or "").strip(), time.perf_counter()-started, usage


def _invented_proper_nouns(answer: str, case: dict[str, Any]) -> list[str]:
    authorized=normalized_text(" ".join([case.get("question") or "",*(case.get("context") or [])]))
    candidates=[value.strip(" .,!?:;") for value in re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ.']+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ.']+)+",answer)]
    return sorted({value for value in candidates if normalized_text(value) not in authorized})


def evaluate_models(models: list[str], base_url: str = "http://localhost:11434",
                    cases_path: Path | None = None, output: Path | None = None,
                    timeout: int = 120, validate_only: bool = False, limit: int | None = None) -> dict[str, Any]:
    payload=read_json(cases_path or MODEL_ROOT / "evaluation" / "frozen_eval_v1.json")
    cases=payload.get("cases") or []
    if limit: cases=cases[:max(1,limit)]
    report: dict[str,Any]={"frozen_eval_version":payload.get("version"),"cases":len(cases),"models":{}}
    for model in models:
        results=[]
        for case in cases:
            if validate_only: answer=""; elapsed=0.0; passed=None; failures=[]; usage={}
            else:
                try: answer,elapsed,usage=_chat(base_url,model,case,timeout)
                except Exception as exc: answer="";elapsed=0.0;usage={};failures=[f"runtime: {type(exc).__name__}"];passed=False
                else:
                    normalized=normalized_text(answer); failures=[]
                    for value in case.get("must_contain") or []:
                        if normalized_text(str(value)) not in normalized: failures.append(f"ausente: {value}")
                    for value in case.get("must_not_contain") or []:
                        if normalized_text(str(value)) in normalized: failures.append(f"proibido: {value}")
                    for value in _invented_proper_nouns(answer,case): failures.append(f"nome sem contexto: {value}")
                    passed=not failures
            results.append({"id":case["id"],"category":case["category"],"passed":passed,"failures":failures,"seconds":round(elapsed,3),"usage":usage,"answer":answer,"human_review":None})
        times=[row["seconds"] for row in results if row["seconds"]>0]
        report["models"][model]={"executed":not validate_only,
            "passed":sum(row["passed"] is True for row in results) if not validate_only else None,"total":len(results),
            "average_seconds":round(statistics.mean(times),3) if times else 0,"max_seconds":max(times,default=0),
            "average_tokens_per_second":round(statistics.mean([row["usage"]["tokens_per_second"] for row in results if row["usage"].get("tokens_per_second")]),2) if any(row["usage"].get("tokens_per_second") for row in results) else None,
            "human_review_required_for":["naturalidade","coerência","persona","factualidade sem correspondência lexical"],"results":results}
    if output: write_json(output,report)
    return report
