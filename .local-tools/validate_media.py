#!/usr/bin/env python3
"""
Validador de referências de mídia para notas Markdown do vault Obsidian.

Verifica:
- Referências a arquivos em zz_media
- Se os arquivos existem
- Referências quebradas em notas ativas vs legacy
- Imagens órfãs não referenciadas
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set


def is_ignored_dir(path: Path) -> bool:
    """Verifica se o diretório deve ser ignorado."""
    ignored = {'.git', '.obsidian', '.trash', 'node_modules', '.venv', '.local-tools'}
    return any(part in ignored for part in path.parts)


def extract_media_references(content: str, file_path: Path) -> List[str]:
    """
    Extrai referências de mídia do conteúdo.
    
    Padrões suportados:
    - ![[...]] (embed)
    - [](zz_media/...) (markdown link)
    - src="zz_media/..." (HTML)
    """
    references = []
    
    # Padrão para embeds Obsidian: ![[...]]
    embed_pattern = r'!\[\[([^\]]+)\]\]'
    for match in re.finditer(embed_pattern, content):
        ref = match.group(1)
        if 'zz_media' in ref or ref.startswith('zz_media/'):
            references.append(ref)
    
    # Padrão para markdown links: [](zz_media/...)
    md_link_pattern = r'\]\(([^)]*zz_media[^)]*)\)'
    for match in re.finditer(md_link_pattern, content):
        references.append(match.group(1))
    
    # Padrão para HTML: src="zz_media/..."
    html_pattern = r'src="([^"]*zz_media[^"]*)"'
    for match in re.finditer(html_pattern, content):
        references.append(match.group(1))
    
    # Padrão simples para zz_media/... no texto
    simple_pattern = r'zz_media/[^\s\)\]]+'
    for match in re.finditer(simple_pattern, content):
        ref = match.group(0)
        # Evitar duplicatas
        if ref not in references:
            references.append(ref)
    
    return references


def get_all_media_files(vault_path: Path) -> Set[str]:
    """Retorna conjunto de todos os arquivos em zz_media."""
    media_dir = vault_path / 'zz_media'
    media_files = set()
    
    if not media_dir.exists():
        return media_files
    
    for media_file in media_dir.rglob('*'):
        if media_file.is_file():
            # Caminho relativo a partir do vault
            rel_path = str(media_file.relative_to(vault_path))
            media_files.add(rel_path)
            # Também adicionar sem prefixo zz_media/ para compatibilidade
            media_files.add(str(media_file.relative_to(media_dir)))
    
    return media_files


def is_in_legacy(file_path: str) -> bool:
    """Verifica se o arquivo está em Workflow/Legacy."""
    return 'Workflow/Legacy' in file_path


def validate_media(vault_path: str, ignore_legacy: bool = False) -> Dict:
    """
    Valida referências de mídia de todas as notas .md no vault.
    
    Args:
        vault_path: Caminho para o diretório raiz do vault
        ignore_legacy: Se True, ignora Workflow/Legacy/ na análise de referências
    
    Returns:
        Dicionário com resultados da validação
    """
    vault = Path(vault_path)
    
    results = {
        'total_references': 0,
        'valid_references': 0,
        'broken_references_active': [],
        'broken_references_legacy': [],
        'orphaned_media': [],
        'referenced_media': set()
    }
    
    # Obter todos os arquivos de mídia
    media_files = get_all_media_files(vault)
    
    # Extrair todas as referências de mídia
    all_references = []
    
    for md_file in vault.rglob('*.md'):
        if is_ignored_dir(md_file):
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Erro ao ler {md_file}: {e}")
            continue
        
        refs = extract_media_references(content, md_file)
        file_path = str(md_file.relative_to(vault))
        
        for ref in refs:
            all_references.append({
                'reference': ref,
                'file': file_path,
                'is_legacy': is_in_legacy(file_path)
            })
    
    results['total_references'] = len(all_references)
    
    # Verificar cada referência
    for ref_item in all_references:
        ref = ref_item['reference']
        file_path = ref_item['file']
        is_legacy = ref_item['is_legacy']
        
        # Normalizar a referência
        ref_normalized = ref
        if not ref.startswith('zz_media/'):
            ref_normalized = f'zz_media/{ref}'
        
        # Verificar se o arquivo existe
        exists = ref_normalized in media_files or ref in media_files
        
        if exists:
            results['valid_references'] += 1
            results['referenced_media'].add(ref_normalized)
            results['referenced_media'].add(ref)
        else:
            if is_legacy and not ignore_legacy:
                results['broken_references_legacy'].append({
                    'reference': ref,
                    'file': file_path
                })
            elif not is_legacy:
                results['broken_references_active'].append({
                    'reference': ref,
                    'file': file_path
                })
    
    # Encontrar mídias órfãs
    for media_file in media_files:
        # Verificar se é referenciada
        is_referenced = False
        for ref in results['referenced_media']:
            if media_file in ref or ref in media_file:
                is_referenced = True
                break
        
        if not is_referenced:
            results['orphaned_media'].append(media_file)
    
    return results


def print_results(results: Dict):
    """Imprime resultados da validação."""
    print(f"\n=== VALIDAÇÃO DE MÍDIA ===")
    print(f"Total de referências de mídia: {results['total_references']}")
    print(f"Referências válidas: {results['valid_references']}")
    print(f"Referências quebradas (ativas): {len(results['broken_references_active'])}")
    print(f"Referências quebradas (legacy): {len(results['broken_references_legacy'])}")
    print(f"Imagens órfãs: {len(results['orphaned_media'])}")
    
    if results['broken_references_active']:
        print(f"\n--- Referências quebradas em notas ativas ({len(results['broken_references_active'])}) ---")
        for item in results['broken_references_active']:
            print(f"  - {item['reference']} em {item['file']}")
    
    if results['broken_references_legacy']:
        print(f"\n--- Referências quebradas em legacy ({len(results['broken_references_legacy'])}) ---")
        for item in results['broken_references_legacy']:
            print(f"  - {item['reference']} em {item['file']}")
    
    if results['orphaned_media']:
        print(f"\n--- Imagens órfãs ({len(results['orphaned_media'])}) ---")
        for media in results['orphaned_media'][:20]:  # Limitar a 20 para não poluir
            print(f"  - {media}")
        if len(results['orphaned_media']) > 20:
            print(f"  ... e mais {len(results['orphaned_media']) - 20} arquivos")


if __name__ == '__main__':
    import sys
    
    vault_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    ignore_legacy = '--ignore-legacy' in sys.argv
    
    results = validate_media(vault_path, ignore_legacy)
    print_results(results)
