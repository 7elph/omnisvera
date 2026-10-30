"""Bounded public SRD description enrichment; never replaces combat mechanics."""
from __future__ import annotations
import argparse,hashlib,json,sys,tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
try:
    from .import_old_dragon_srd_monsters import DOMParser
except ImportError:
    from import_old_dragon_srd_monsters import DOMParser

CATALOG=Path(__file__).resolve().parents[1]/'app/data/old_dragon_srd_monsters.json'

def public_description(html: str) -> str | None:
    parser=DOMParser();parser.feed(html)
    values=[node.text() for node in parser.root.descendants('p')
            if 'odo-bk-flavor' in node.attrs.get('class','').split()]
    return values[0] if len(values)==1 and 10<=len(values[0])<=4000 else None

def mechanical_digest(payload):
    records=[{k:v for k,v in m.items() if not k.startswith('description')} for m in payload['monsters']]
    return hashlib.sha256(json.dumps(records,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def fetch(monster):
    url=monster.get('source_url','');parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.netloc!='olddragon.com.br' or not parsed.path.startswith('/monstros/'):
        return monster['id'],None,'invalid_source'
    try:
        with urlopen(Request(url,headers={'User-Agent':'Omnisvera-SRD-Description-Audit/1.0'}),timeout=20) as response:
            if urlsplit(response.url).netloc!='olddragon.com.br':return monster['id'],None,'redirect_rejected'
            raw=response.read(1500001)
            if len(raw)>1500000:return monster['id'],None,'page_too_large'
        text=public_description(raw.decode('utf-8'))
        return monster['id'],text,'found' if text else 'no_public_flavor'
    except Exception as error:return monster['id'],None,type(error).__name__

def main():
    cli=argparse.ArgumentParser();cli.add_argument('--apply',action='store_true');args=cli.parse_args()
    payload=json.loads(CATALOG.read_text(encoding='utf-8'));before=mechanical_digest(payload)
    candidates=[m for m in payload['monsters'] if not m.get('description')]
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(fetch,candidates))
    found={identity:text for identity,text,status in results if text}
    for monster in payload['monsters']:
        if monster['id'] in found:
            monster.update(description=found[monster['id']],description_source_url=monster['source_url'],
                           description_license=payload['catalog']['license'])
    assert mechanical_digest(payload)==before
    report={'retrieved_at':datetime.now(timezone.utc).isoformat(),'applied':args.apply,
            'descriptions_added':len(found),'mechanics_sha256':before,
            'source':'https://olddragon.com.br/livros/srd','license':payload['catalog']['license'],
            'results':[{'id':i,'status':s} for i,t,s in results]}
    folder=Path(tempfile.mkdtemp(prefix='omni-monster-descriptions-'))
    (folder/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if args.apply:
        (folder/'before.json').write_bytes(CATALOG.read_bytes())
        CATALOG.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'added':len(found),'mechanics_unchanged':True,'report':str(folder/'report.json')}))

if __name__=='__main__':main()
