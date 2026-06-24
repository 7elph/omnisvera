#!/usr/bin/env python3
"""
Validador de wikilinks para notas Markdown do vault Obsidian.

Verifica:
- Wikilinks [[...]]
- Links com aliases [[Nota|Texto]]
- Se o destino existe como nota .md
- Não corrige automaticamente, apenas relata problemas.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


def is_ignored_dir(path: Path) -> bool:
    """Verifica se o diretório deve ser ignorado."""
    ignored = {'.git', '.obsidian', '.trash', 'node_modules', '.venv', '.local-tools'}
    return any(part in ignored for part in path.parts)


def extract_wikilinks(content: str, file_path: Path) -> List[Tuple[str, int, str]]:
    """
    Extrai wikilinks do conteúdo.
    
    Returns:
        Lista de tuplas (link, linha, arquivo_origem)
    """
    links = []
    lines = content.split('\n')
    
    # Padrão para wikilinks: [[...]] ou [[...|...]]
    pattern = r'\[\[([^\]]+)\]\]'
    
    for line_num, line in enumerate(lines, 1):
        matches = re.finditer(pattern, line)
        for match in matches:
            full_match = match.group(1)
            # Extrair o link real (antes do | se houver alias)
            link = full_match.split('|')[0].strip()
            links.append((link, line_num, str(file_path)))
    
    return links


def get_all_md_files(vault_path: Path, ignore_legacy: bool = False) -> set:
    """Retorna conjunto de todos os arquivos .md do vault."""
    md_files = set()
    
    for md_file in vault_path.rglob('*.md'):
        if is_ignored_dir(md_file):
            continue
        
        if ignore_legacy and 'Workflow/Legacy' in str(md_file):
            continue
        
        # Nome do arquivo sem extensão
        md_files.add(md_file.stem)
        md_files.add(str(md_file.relative_to(vault_path).with_suffix('')))
    
    return md_files


def resolve_link(link: str, md_files: set, vault_path: Path) -> bool:
    """
    Verifica se um link pode ser resolvido.
    
    Considera:
    - Nome do arquivo exato
    - Caminho relativo
    """
    # Tentar match exato
    if link in md_files:
        return True
    
    # Tentar como caminho relativo
    link_path = vault_path / (link + '.md')
    if link_path.exists():
        return True
    
    return False


def validate_links(vault_path: str, ignore_legacy: bool = False) -> Dict:
    """
    Valida wikilinks de todas as notas .md no vault.
    
    Args:
        vault_path: Caminho para o diretório raiz do vault
        ignore_legacy: Se True, ignora Workflow/Legacy/
    
    Returns:
        Dicionário com resultados da validação
    """
    vault = Path(vault_path)
    
    results = {
        'total_links': 0,
        'resolved_links': 0,
        'broken_links': [],
        'links_by_file': {}
    }
    
    # Obter todos os arquivos .md disponíveis
    md_files = get_all_md_files(vault, ignore_legacy)
    
    # Extrair todos os links de todas as notas
    all_links = []
    
    for md_file in vault.rglob('*.md'):
        if is_ignored_dir(md_file):
            continue
        
        if ignore_legacy and 'Workflow/Legacy' in str(md_file):
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Erro ao ler {md_file}: {e}")
            continue
        
        links = extract_wikilinks(content, md_file)
        all_links.extend(links)
    
    results['total_links'] = len(all_links)
    
    # Verificar cada link
    for link, line_num, source_file in all_links:
        if resolve_link(link, md_files, vault):
            results['resolved_links'] += 1
        else:
            results['broken_links'].append({
                'link': link,
                'line': line_num,
                'file': source_file
            })
    
    # Agrupar links por arquivo
    for link, line_num, source_file in all_links:
        if source_file not in results['links_by_file']:
            results['links_by_file'][source_file] = []
        results['links_by_file'][source_file].append(link)
    
    return results


def print_results(results: Dict):
    """Imprime resultados da validação."""
    print(f"\n=== VALIDAÇÃO DE WIKILINKS ===")
    print(f"Total de wikilinks encontrados: {results['total_links']}")
    print(f"Links resolvidos: {results['resolved_links']}")
    print(f"Links quebrados: {len(results['broken_links'])}")
    
    if results['broken_links']:
        print(f"\n--- Links quebrados ({len(results['broken_links'])}) ---")
        for item in results['broken_links']:
            print(f"  - [[{item['link']}]] em {item['file']}:{item['line']}")


if __name__ == '__main__':
    import sys
    
    vault_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    ignore_legacy = '--ignore-legacy' in sys.argv
    
    results = validate_links(vault_path, ignore_legacy)
    print_results(results)
