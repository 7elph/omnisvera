"""Portable production entrypoint; no dependency installation or token disclosure."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parent


def configure(*, init_access=False, environ=None, root=ROOT):
    env = os.environ if environ is None else environ
    config = root / '.env.host'
    if config.exists():
        for line in config.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                key, separator, value = line.partition('=')
                if not separator or not key.strip().replace('_', '').isalnum():
                    raise ValueError('Linha inválida em .env.host')
                env.setdefault(key.strip(), value.strip().strip('\"\''))
    data = root / 'host-data'
    vault = Path(env.setdefault('OMNISVERA_VAULT_PATH', str(data / 'vault'))).resolve()
    database = Path(env.setdefault('OMNISVERA_DB_PATH', str(data / 'state/companion.sqlite3'))).resolve()
    env.setdefault('OMNISVERA_AI_WORKSHOP_DB', str(data / 'state/ai-workshop.sqlite3'))
    tokens = Path(env.get('OMNISVERA_TOKEN_FILE') or data / 'state/access_tokens.json').resolve()
    if not vault.is_dir():
        raise ValueError('Vault ausente; importe o pacote privado ou configure OMNISVERA_VAULT_PATH')
    if not tokens.exists() and init_access:
        tokens.parent.mkdir(parents=True, exist_ok=True)
        value = {'master_token': secrets.token_urlsafe(32), 'player_token': secrets.token_urlsafe(32),
                 'player_profiles': {}}
        with tokens.open('x', encoding='utf-8') as writer:
            os.chmod(tokens, 0o600)
            json.dump(value, writer)
    try:
        access = json.loads(tokens.read_text(encoding='utf-8-sig'))
        if not access.get('master_token') or not access.get('player_token'):
            raise ValueError()
        profiles = access.get('player_profiles') or {}
        if not isinstance(profiles, dict) or any(not isinstance(p, dict) or not p.get('token') for p in profiles.values()):
            raise ValueError()
    except (OSError, ValueError, TypeError, AttributeError):
        raise ValueError('Acessos ausentes/inválidos; importe os originais ou use --init-access somente para instalação nova') from None
    env['OMNISVERA_MASTER_TOKEN'] = access['master_token']
    env['OMNISVERA_ACCESS_TOKEN'] = access['master_token']
    env['OMNISVERA_PLAYER_TOKEN'] = access['player_token']
    env['OMNISVERA_PLAYER_PROFILES_JSON'] = json.dumps({k: v for k, v in profiles.items() if not v.get('gm_controlled')})
    env.setdefault('OMNISVERA_REBUILD_ON_STARTUP', 'false')
    env.setdefault('OMNISVERA_AUTO_REFRESH_INDEX', 'false')
    dist = Path(env.get('OMNISVERA_FRONTEND_DIST') or root / 'frontend/dist')
    if not (dist / 'index.html').is_file() or not (dist / 'assets').is_dir():
        raise ValueError('Frontend não compilado; execute npm ci e npm run build em frontend/')
    database.parent.mkdir(parents=True, exist_ok=True)
    return {'vault': str(vault), 'database_exists': database.is_file(), 'frontend_ready': True,
            'access_ready': True, 'player_profiles': len(profiles)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--init-access', action='store_true')
    args = parser.parse_args()
    try:
        report = configure(init_access=args.init_access)
        if importlib.util.find_spec('uvicorn') is None:
            raise ValueError('Dependências ausentes; instale backend/requirements.txt no ambiente virtual')
    except ValueError as error:
        parser.exit(1, str(error) + '\n')
    if args.check:
        print(json.dumps(report, ensure_ascii=False))
        return
    sys.path.insert(0, str(ROOT / 'backend'))
    import uvicorn
    uvicorn.run('app.main:app', host=args.host, port=args.port, access_log=False)


if __name__ == '__main__':
    main()
