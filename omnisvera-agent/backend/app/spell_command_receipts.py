"""Generic spell retry receipts in the existing command table, not a second store."""
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path


def command_receipt(request_id, namespace, intent):
    if request_id is None:
        return None
    if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9._:-]{1,120}', request_id):
        raise ValueError('Informe uma chave de comando válida, com até 120 caracteres')
    fingerprint = json.dumps(['master', 'spell-engine:v1', namespace, intent],
                             sort_keys=True, separators=(',', ':'), allow_nan=False)
    return request_id, fingerprint


def read_receipt(connection, receipt):
    if receipt is None:
        return None
    if not connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='combat_effect_commands'").fetchone():
        return None
    row = connection.execute('SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?',
                             (receipt[0],)).fetchone()
    if row is None:
        return None
    if row[0] != receipt[1]:
        raise ValueError('Esta chave pertence a outro comando ou outra intenção')
    return json.loads(row[1])


def replay_before_resolution(database_path, receipt):
    if receipt is None:
        return None
    path = Path(database_path).resolve()
    if not path.is_file():
        return None
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=30)) as connection:
        return read_receipt(connection, receipt)


def save_receipt(connection, receipt, result):
    if receipt is not None:
        connection.execute('INSERT INTO combat_effect_commands(request_id,fingerprint,response_json) VALUES(?,?,?)',
                           (*receipt, json.dumps(result, ensure_ascii=False, allow_nan=False)))
