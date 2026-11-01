"""Private, streamed campaign transfer. Never uploads or modifies the source DB."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
import zipfile

SCHEMA_VERSION = 1
EXCLUDED = {'.git', '.obsidian', '.venv', '.venv-observer', 'node_modules', '__pycache__',
            'omnisvera-agent', 'omnisvera-model', 'omnisvera_model', 'scripts', 'tools',
            'backups', 'cache', 'runtime'}
EXTENSIONS = {'.md', '.txt', '.csv', '.json', '.yaml', '.yml', '.png', '.jpg', '.jpeg',
              '.webp', '.avif', '.gif', '.svg', '.bmp', '.ico', '.pdf', '.mp3', '.ogg',
              '.wav', '.mp4', '.webm', '.m4a', '.flac'}
EXTENSIONS.update({'.license', '.xml'})


def _hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(512 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _credentials(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(value, dict) or not value.get('master_token'):
            raise ValueError()
        return value
    except (OSError, ValueError, TypeError):
        raise ValueError('Arquivo de acessos ausente ou inválido; valores não serão exibidos') from None


def _vault_files(root):
    for directory, directories, files in os.walk(root, followlinks=False):
        directories[:] = sorted(d for d in directories if not d.startswith('.')
                                and d.lower() not in EXCLUDED and not (Path(directory) / d).is_symlink()
                                and not getattr(Path(directory) / d, 'is_junction', lambda: False)())
        for name in sorted(files):
            path = Path(directory) / name
            if (not name.startswith('.') and not path.is_symlink()
                    and (path.suffix.lower() in EXTENSIONS or name.lower() in {'license', 'copying', 'notice'})):
                yield path


def _check_database(path):
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
        if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
            raise ValueError('Snapshot SQLite falhou na verificação de integridade')


def export_bundle(vault, database, tokens, output, *, code_ref, workshop=None):
    vault, database, tokens, output = (Path(p).resolve() for p in (vault, database, tokens, output))
    if not vault.is_dir() or not database.is_file():
        raise ValueError('Vault e banco existentes são obrigatórios')
    if output.is_relative_to(vault):
        raise ValueError('O pacote privado precisa ficar fora do Vault/repositório')
    if output.exists():
        raise ValueError('Não sobrescrevo um pacote existente')
    _credentials(tokens)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {'schema_version': SCHEMA_VERSION, 'code_ref': code_ref,
                'created_at': datetime.now(timezone.utc).isoformat(), 'private': True, 'files': {}}
    # The source is opened read-only. sqlite.backup includes committed WAL data.
    with tempfile.TemporaryDirectory(prefix='omni-transfer-') as temp:
        snapshot = Path(temp) / 'companion.sqlite3'
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as source, closing(sqlite3.connect(snapshot)) as target:
            source.backup(target)
        _check_database(snapshot)
        staging = Path(temp) / 'bundle.zip'
        with zipfile.ZipFile(staging, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as archive:
            def add(path, name):
                digest = hashlib.sha256()
                size = 0
                info = zipfile.ZipInfo(name)
                info.compress_type = zipfile.ZIP_DEFLATED if path.suffix.lower() in {'.md', '.txt', '.csv', '.json', '.svg', '.xml', '.yaml', '.yml', '.license'} else zipfile.ZIP_STORED
                with path.open('rb') as reader, archive.open(info, 'w', force_zip64=True) as writer:
                    for chunk in iter(lambda: reader.read(512 * 1024), b''):
                        writer.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
                manifest['files'][name] = {'sha256': digest.hexdigest(), 'bytes': size}
            add(snapshot, 'state/companion.sqlite3')
            add(tokens, 'state/access_tokens.json')
            if workshop is not None:
                workshop = Path(workshop).resolve()
                workshop_snapshot = Path(temp) / 'ai-workshop.sqlite3'
                with closing(sqlite3.connect(workshop.as_uri() + '?mode=ro', uri=True)) as source, closing(sqlite3.connect(workshop_snapshot)) as target:
                    source.backup(target)
                _check_database(workshop_snapshot)
                add(workshop_snapshot, 'state/ai-workshop.sqlite3')
            drafts = database.parent / 'asset_drafts'
            if drafts.is_dir():
                for path in _vault_files(drafts):
                    add(path, 'state/asset_drafts/' + path.relative_to(drafts).as_posix())
            for path in _vault_files(vault):
                add(path, 'vault/' + path.relative_to(vault).as_posix())
            archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        # Exclusive creation avoids replacing another export produced concurrently.
        try:
            with output.open('xb') as writer, staging.open('rb') as reader:
                os.chmod(output, 0o600)
                shutil.copyfileobj(reader, writer, 512 * 1024)
        except FileExistsError:
            raise ValueError('O destino já foi criado por outra exportação') from None
    return {'bundle': str(output), 'files': len(manifest['files']), 'bytes': output.stat().st_size,
            'sha256': _hash(output), 'code_ref': code_ref, 'private': True}


def _safe_name(name):
    path = PurePosixPath(name)
    if (not name or '\\' in name or ':' in name or '\x00' in name or path.is_absolute()
            or str(path) != name or any(part in {'.', '..'} or part.endswith((' ', '.')) for part in path.parts)):
        raise ValueError('Caminho inseguro no pacote')
    if name != 'manifest.json' and path.parts[0] not in {'state', 'vault'}:
        raise ValueError('Conteúdo fora do contrato de transferência')
    return path


def restore_bundle(bundle, destination, *, max_bytes=8 * 1024**3):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError('Restaure em diretório novo; o destino existente foi preservado')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len({name.casefold() for name in names}) != len(names):
            raise ValueError('Entradas duplicadas ou ambíguas no pacote')
        for info in infos:
            _safe_name(info.filename)
            if info.is_dir() or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Links e diretórios explícitos não são aceitos')
        if sum(info.file_size for info in infos) > max_bytes:
            raise ValueError('Pacote excede o limite de extração')
        if 'manifest.json' not in names or archive.getinfo('manifest.json').file_size > 32 * 1024**2:
            raise ValueError('Manifesto ausente ou excessivo')
        manifest = json.loads(archive.read('manifest.json'))
        if manifest.get('schema_version') != SCHEMA_VERSION or manifest.get('private') is not True:
            raise ValueError('Versão de pacote não suportada')
        files = manifest.get('files', {})
        if set(files) != set(names) - {'manifest.json'} or not {'state/companion.sqlite3', 'state/access_tokens.json'} <= set(files):
            raise ValueError('Conteúdo diferente do manifesto')
        with tempfile.TemporaryDirectory(prefix='omni-restore-', dir=destination.parent) as temp:
            staged = Path(temp) / 'data'
            staged.mkdir(mode=0o700)
            for name, record in files.items():
                target = staged.joinpath(*_safe_name(name).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                if archive.getinfo(name).file_size != record['bytes']:
                    raise ValueError('Tamanho diferente do manifesto')
                with archive.open(name) as reader, target.open('xb') as writer:
                    shutil.copyfileobj(reader, writer, 512 * 1024)
                if _hash(target) != record['sha256']:
                    raise ValueError('Checksum inválido; importação cancelada')
            _check_database(staged / 'state/companion.sqlite3')
            if (staged / 'state/ai-workshop.sqlite3').exists():
                _check_database(staged / 'state/ai-workshop.sqlite3')
            _credentials(staged / 'state/access_tokens.json')
            os.chmod(staged / 'state/access_tokens.json', 0o600)
            # rename refuses an existing nonempty destination; no operational files overwritten.
            if destination.exists():
                raise ValueError('Destino criado durante a importação; nada sobrescrito')
            staged.rename(destination)
    return {'destination': str(destination), 'files': len(files), 'code_ref': manifest['code_ref']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    export = commands.add_parser('export')
    for name in ('vault', 'database', 'tokens', 'output', 'code-ref'):
        export.add_argument('--' + name, required=True)
    export.add_argument('--workshop', help='Optional private preparation queue SQLite')
    restore = commands.add_parser('restore')
    restore.add_argument('--bundle', required=True)
    restore.add_argument('--destination', required=True)
    args = vars(parser.parse_args())
    command = args.pop('command')
    try:
        result = export_bundle(**args) if command == 'export' else restore_bundle(**args)
    except (OSError, ValueError, sqlite3.Error, zipfile.BadZipFile, KeyError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
