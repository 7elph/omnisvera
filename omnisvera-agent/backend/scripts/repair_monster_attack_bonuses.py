"""Recover missing BA only from explicit public attack dice, never infer from HD."""
import argparse,json,re,sys,tempfile,unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
try:from .enrich_monster_descriptions import CATALOG,DOMParser
except ImportError:from enrich_monster_descriptions import CATALOG,DOMParser

def key(value):return ''.join(c for c in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(c)).strip()

def source_attack_bonuses(html):
    parser=DOMParser();parser.feed(html);result={}
    for node in parser.root.descendants('span'):
        attrs=node.attrs
        if attrs.get('data-dice-bar-attack-param')!='true':continue
        formula=attrs.get('data-dice-bar-instruction-param','')
        match=re.fullmatch(r'1d20\s*([+-]\s*\d+)?',formula,re.I)
        label=attrs.get('aria-label','')
        if not match or not label.startswith('Ataque: '):continue
        bonus=int(re.sub(r'\s','',match.group(1) or '0'))
        name=key(label.removeprefix('Ataque: '))
        result.setdefault(name,set()).add(bonus)
    return {name:next(iter(values)) for name,values in result.items() if len(values)==1}

def fetch(monster):
    url=monster['source_url'];parts=urlsplit(url)
    assert parts.scheme=='https' and parts.netloc=='olddragon.com.br' and parts.path.startswith('/monstros/')
    try:
        with urlopen(Request(url,headers={'User-Agent':'Omnisvera-SRD-Attack-Audit/1.0'}),timeout=20) as response:
            if urlsplit(response.url).netloc!='olddragon.com.br':return monster['id'],{}
            data=response.read(1500001)
        return monster['id'],source_attack_bonuses(data.decode('utf-8')) if len(data)<=1500000 else {}
    except Exception:return monster['id'],{}

def main():
    cli=argparse.ArgumentParser();cli.add_argument('--apply',action='store_true');args=cli.parse_args()
    original=CATALOG.read_bytes();payload=json.loads(original)
    candidates=[m for m in payload['monsters'] if any(a.get('bonus') is None for a in m.get('attacks',[]))]
    with ThreadPoolExecutor(max_workers=2) as pool:found=dict(pool.map(fetch,candidates))
    changes=[]
    for monster in candidates:
        for index,attack in enumerate(monster['attacks']):
            name=key(attack['name']);bonus=found[monster['id']].get(name)
            if attack.get('bonus') is None and bonus is not None:
                attack['bonus']=bonus
                changes.append({'id':monster['id'],'attack_index':index,'bonus':bonus,'source_url':monster['source_url']})
    folder=Path(tempfile.mkdtemp(prefix='omni-monster-attack-bonuses-'))
    (folder/'before.json').write_bytes(original)
    (folder/'report.json').write_text(json.dumps({'applied':args.apply,'changes':changes},indent=2),encoding='utf-8')
    if args.apply:CATALOG.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'recovered_attacks':len(changes),'report':str(folder/'report.json')}))

if __name__=='__main__':main()
