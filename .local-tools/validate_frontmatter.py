#!/usr/bin/env python3
"""
Validador de frontmatter YAML para notas Markdown do vault Obsidian.

Verifica:
- Presença de frontmatter YAML
- Frontmatter bem formado (aberto e fechado corretamente)
- Campos vazios importantes
- Não modifica arquivos, apenas relata problemas.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


def is_ignored_dir(path: Path) -> bool:
    """Verifica se o diretório deve ser ignorado."""
    ignored = {
        '.git',
        '.obsidian',
        '.trash',
        'node_modules',
        '.venv',
        '.local-tools',
        '.omnisvera-tools',
        '.codex-tools',
    }
    return any(part in ignored for part in path.parts)


def is_ignored_when_operational(path: Path) -> bool:
    """Ignora documentação interna no modo --ignore-legacy."""
    return 'Workflow' in path.parts


def has_frontmatter(content: str) -> bool:
    """Verifica se o conteúdo começa com frontmatter YAML."""
    return content.lstrip('\ufeff').startswith('---')


def is_frontmatter_well_formed(content: str) -> bool:
    """Verifica se o frontmatter está bem formado (aberto e fechado)."""
    content = content.lstrip('\ufeff')
    if not has_frontmatter(content):
        return False
    
    lines = content.split('\n')
    if not lines or lines[0].strip() != '---':
        return False

    for line in lines[1:300]:
        if line.strip() == '---':
            return True
    return False


def extract_frontmatter(content: str) -> str:
    """Extrai o conteúdo do frontmatter YAML."""
    content = content.lstrip('\ufeff')
    if not is_frontmatter_well_formed(content):
        return ""
    
    lines = content.split('\n')
    start = 1  # Após o primeiro ---
    end = 0
    
    for i in range(1, min(300, len(lines))):
        if lines[i].strip() == '---':
            end = i
            break
    
    if end == 0:
        return ""
    
    return '\n'.join(lines[start:end])


def parse_yaml_like(frontmatter: str) -> Dict[str, str]:
    """Parse simples de YAML (não é um parser completo, apenas extrai campos)."""
    result = {}
    for line in frontmatter.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            result[key.strip()] = value.strip()
    return result


def check_empty_important_fields(frontmatter_dict: Dict[str, str]) -> List[str]:
    """Verifica campos importantes que estão vazios."""
    important_fields = ['title', 'name', 'type', 'category']
    empty_fields = []
    
    for field in important_fields:
        if field in frontmatter_dict and not frontmatter_dict[field]:
            empty_fields.append(field)
    
    return empty_fields


def validate_frontmatter(vault_path: str, ignore_legacy: bool = False) -> Dict:
    """
    Valida frontmatter de todas as notas .md no vault.
    
    Args:
        vault_path: Caminho para o diretório raiz do vault
        ignore_legacy: Se True, ignora Workflow/Legacy/
    
    Returns:
        Dicionário com resultados da validação
    """
    vault = Path(vault_path)
    
    results = {
        'total_notes': 0,
        'notes_without_frontmatter': [],
        'notes_invalid_frontmatter': [],
        'notes_empty_fields': [],
        'fields_by_category': {}
    }
    
    for md_file in vault.rglob('*.md'):
        # Ignorar diretórios específicos
        if is_ignored_dir(md_file):
            continue
        
        if ignore_legacy and is_ignored_when_operational(md_file):
            continue
        
        results['total_notes'] += 1
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Erro ao ler {md_file}: {e}")
            continue
        
        # Verificar se tem frontmatter
        if not has_frontmatter(content):
            results['notes_without_frontmatter'].append(str(md_file.relative_to(vault)))
            continue
        
        # Verificar se está bem formado
        if not is_frontmatter_well_formed(content):
            results['notes_invalid_frontmatter'].append(str(md_file.relative_to(vault)))
            continue
        
        # Extrair e verificar campos vazios
        fm = extract_frontmatter(content)
        fm_dict = parse_yaml_like(fm)
        empty = [] if 'Templates' in md_file.parts else check_empty_important_fields(fm_dict)
        
        if empty:
            results['notes_empty_fields'].append({
                'file': str(md_file.relative_to(vault)),
                'empty_fields': empty
            })
    
    return results


def print_results(results: Dict):
    """Imprime resultados da validação."""
    print(f"\n=== VALIDAÇÃO DE FRONTMATTER ===")
    print(f"Total de notas analisadas: {results['total_notes']}")
    print(f"Notas sem frontmatter: {len(results['notes_without_frontmatter'])}")
    print(f"Notas com frontmatter inválido: {len(results['notes_invalid_frontmatter'])}")
    print(f"Notas com campos vazios importantes: {len(results['notes_empty_fields'])}")
    
    if results['notes_without_frontmatter']:
        print(f"\n--- Notas sem frontmatter ({len(results['notes_without_frontmatter'])}) ---")
        for note in results['notes_without_frontmatter']:
            print(f"  - {note}")
    
    if results['notes_invalid_frontmatter']:
        print(f"\n--- Notas com frontmatter inválido ({len(results['notes_invalid_frontmatter'])}) ---")
        for note in results['notes_invalid_frontmatter']:
            print(f"  - {note}")
    
    if results['notes_empty_fields']:
        print(f"\n--- Notas com campos vazios ({len(results['notes_empty_fields'])}) ---")
        for item in results['notes_empty_fields']:
            print(f"  - {item['file']}: {', '.join(item['empty_fields'])}")


if __name__ == '__main__':
    import sys
    
    vault_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    ignore_legacy = '--ignore-legacy' in sys.argv
    
    results = validate_frontmatter(vault_path, ignore_legacy)
    print_results(results)
