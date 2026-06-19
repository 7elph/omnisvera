"""
Auditor de Formatacao do Vault
Analisa todos os .md e reporta inconsistencias de YAML frontmatter,
NoteIcon, tags, wikilinks, callouts e datacards.
Sem dependencias externas.
"""
import os
import re

VAULT = r'c:\Users\delib\Desktop\OMNISVERA'
IGNORE_DIRS = {'zz_media', '__template', '.git'}

results = {
    'files_scanned': 0,
    'files_with_yaml': 0,
    'files_no_yaml': 0,
    'files_yaml_empty': [],
    'yaml_parse_errors': [],
    'missing_noteicon': [],
    'wrong_tags_format': [],
    'missing_cover': [],
    'old_format_callouts': [],
    'broken_wikilinks': [],
    'missing_territory': [],
    'other_issues': [],
    'summary': {}
}

def parse_yaml_simple(yaml_text):
    """
    Parse YAML frontmatter simples (chave: valor, listas com -)
    Retorna dict com valores string ou list
    """
    data = {}
    current_key = None
    current_list = []
    
    for line in yaml_text.split('\n'):
        # List item
        if line.strip().startswith('- '):
            val = line.strip()[2:].strip()
            if current_key:
                current_list.append(val)
            continue
        
        # Key: value
        match = re.match(r'^(\w+):\s*(.*)', line)
        if match:
            # Save previous list if exists
            if current_key and current_list:
                data[current_key] = current_list
                current_list = []
            
            key = match.group(1).strip()
            val = match.group(2).strip()
            current_key = key
            
            # Remove quotes
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            
            # Remove wikilink brackets for value extraction
            val = val.replace('[[', '').replace(']]', '')
            
            if val:
                data[key] = val
            else:
                # Could be a list start
                current_list = []
                data[key] = []  # placeholder
    
    # Save last list
    if current_key and current_list:
        data[current_key] = current_list
    
    return data


def check_yaml(content, filepath):
    if not content.startswith('---'):
        results['files_no_yaml'] += 1
        results['other_issues'].append(f"{filepath}: Sem frontmatter YAML")
        return None
    
    end_idx = content.find('---', 3)
    if end_idx == -1:
        results['yaml_parse_errors'].append(f"{filepath}: YAML sem fechamento")
        return None
    
    yaml_text = content[3:end_idx].strip()
    if not yaml_text:
        results['files_yaml_empty'].append(filepath)
        return None
    
    data = parse_yaml_simple(yaml_text)
    if not data:
        results['yaml_parse_errors'].append(f"{filepath}: YAML vazio apos parse")
        return None
    
    results['files_with_yaml'] += 1
    return data


def validate_yaml(data, filepath):
    issues = []
    
    # 1. NoteIcon
    noteicon = data.get('NoteIcon', '')
    if not noteicon:
        results['missing_noteicon'].append(filepath)
        issues.append("Sem NoteIcon")
    
    # 2. Tags format
    tags = data.get('tags', [])
    if isinstance(tags, str):
        if ',' in tags:
            results['wrong_tags_format'].append(f"{filepath}: tags como string com virgulas")
            issues.append("tags em string ao inves de lista")
    elif isinstance(tags, list) and len(tags) > 0:
        has_category = any('Category/' in t for t in tags)
        if not has_category and noteicon not in ('home', 'chapter', 'religion', 'audit'):
            results['other_issues'].append(f"{filepath}: tags sem Category/ prefix (NoteIcon: {noteicon})")
            issues.append(f"sem Category/ nas tags")
    
    # 3. Cover
    cover = data.get('cover', '')
    if not cover and noteicon not in ('home', 'chapter', 'audit', 'religion'):
        # Check thumbnail as alternative
        thumb = data.get('thumbnail', '')
        if not thumb:
            results['missing_cover'].append(f"{filepath} (NoteIcon: {noteicon})")
            issues.append("sem cover nem thumbnail")
    
    # 4. Territory for locations/settlements
    if noteicon in ('location', 'settlement'):
        territory = data.get('territory', '')
        if not territory:
            results['missing_territory'].append(filepath)
            issues.append("location/settlement sem territory")
    
    # 5. Check callout format - old style > **text**
    # We check this in the full content later
    
    return issues


def check_callouts(content, filepath):
    """Check for old-style callouts without [!NOTE]"""
    if '> [!NOTE' not in content:
        # Check for old style: > **text**
        old_style = re.findall(r'> \*\*[^*]+\*\*', content)
        if old_style:
            results['old_format_callouts'].append(f"{filepath}: {len(old_style)} callouts antigos (> **texto**) sem [!NOTE]")
            return True
    return False


def check_wikilinks(content, filepath):
    """Find broken wikilinks by checking if target file exists"""
    wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)
    broken = []
    for link in wikilinks:
        link_clean = link.split('|')[0].split('#')[0]
        if link_clean.startswith('http'):
            continue
        
        # Normalize path separators
        link_path = link_clean.replace('/', '\\')
        
        # Try absolute from vault root
        full_path = os.path.join(VAULT, link_path + '.md')
        if os.path.isfile(full_path):
            continue
        
        # Try relative to file's directory
        filedir = os.path.dirname(filepath)
        rel_path = os.path.join(filedir, link_path + '.md')
        if os.path.isfile(rel_path):
            continue
        
        # Try with partial path (e.g. [[Factions/X]] with file at Factions/X.md)
        # Already tried above
        
        # Try nested path search
        # e.g. [[Locations/Oakvale]] -> Locations/Oakvale.md
        if not link_clean.startswith('zz_media'):
            found = False
            for root, dirs, files in os.walk(VAULT):
                if any(ig in root for ig in IGNORE_DIRS):
                    continue
                for f in files:
                    if f == link_clean + '.md':
                        found = True
                        break
                if found:
                    break
            if not found:
                broken.append(link_clean)
    
    if broken:
        results['broken_wikilinks'].append(f"{filepath}: {broken}")


def scan_vault():
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        
        for f in files:
            if not f.endswith('.md'):
                continue
            
            filepath = os.path.join(root, f)
            results['files_scanned'] += 1
            
            try:
                with open(filepath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
            except Exception as e:
                results['other_issues'].append(f"{filepath}: Erro lendo - {e}")
                continue
            
            # Check YAML
            data = check_yaml(content, filepath)
            if data:
                issues = validate_yaml(data, filepath)
            
            # Check callouts (always)
            check_callouts(content, filepath)
            
            # Check wikilinks (always, even without YAML)
            check_wikilinks(content, filepath)
    
    # Summary
    total_issues = (
        results['files_no_yaml'] +
        len(results['files_yaml_empty']) +
        len(results['yaml_parse_errors']) +
        len(results['missing_noteicon']) +
        len(results['wrong_tags_format']) +
        len(results['missing_cover']) +
        len(results['old_format_callouts']) +
        len(results['broken_wikilinks']) +
        len(results['missing_territory']) +
        len(results['other_issues'])
    )
    
    results['summary'] = {
        'Arquivos escaneados': results['files_scanned'],
        'Com YAML frontmatter': results['files_with_yaml'],
        'Sem YAML': results['files_no_yaml'],
        'YAML vazio': len(results['files_yaml_empty']),
        'Erros de parse YAML': len(results['yaml_parse_errors']),
        'Sem NoteIcon': len(results['missing_noteicon']),
        'Tags em formato string': len(results['wrong_tags_format']),
        'Sem cover/thumbnail': len(results['missing_cover']),
        'Callouts antigos (sem [!NOTE])': len(results['old_format_callouts']),
        'Wikilinks quebrados': len(results['broken_wikilinks']),
        'Location sem territory': len(results['missing_territory']),
        'Outras inconsistencias': len(results['other_issues']),
        'TOTAL DE PROBLEMAS': total_issues
    }


def print_report():
    print("=" * 70)
    print("RELATORIO DE AUDITORIA DE FORMATACAO - OMNISVERA VAULT")
    print("=" * 70)
    print()
    
    print("--- RESUMO ---")
    for k, v in results['summary'].items():
        print(f"  {k}: {v}")
    print()
    
    if results['files_no_yaml'] > 0:
        print("--- ARQUIVOS SEM YAML ---")
        for item in results['other_issues']:
            if 'Sem frontmatter' in item:
                print(f"  {item}")
    
    if results['files_yaml_empty']:
        print("\n--- YAML VAZIO ---")
        for f in results['files_yaml_empty']:
            rel = os.path.relpath(f, VAULT)
            print(f"  {rel}")
    
    if results['yaml_parse_errors']:
        print("\n--- ERROS DE PARSE YAML ---")
        for item in results['yaml_parse_errors']:
            print(f"  {item}")
    
    if results['missing_noteicon']:
        print("\n--- SEM NOTEICON ---")
        for f in results['missing_noteicon']:
            rel = os.path.relpath(f, VAULT)
            print(f"  {rel}")
    
    if results['wrong_tags_format']:
        print("\n--- TAGS EM FORMATO STRING ---")
        for item in results['wrong_tags_format'][:15]:
            print(f"  {item}")
    
    if results['missing_cover']:
        print("\n--- SEM COVER / THUMBNAIL ---")
        for item in results['missing_cover'][:15]:
            print(f"  {item}")
    
    if results['old_format_callouts']:
        print("\n--- CALLOUTS ANTIGOS (sem [!NOTE]) ---")
        for item in results['old_format_callouts'][:10]:
            print(f"  {item}")
    
    if results['missing_territory']:
        print("\n--- LOCATION/SETTLEMENT SEM TERRITORY ---")
        for f in results['missing_territory']:
            rel = os.path.relpath(f, VAULT)
            print(f"  {rel}")
    
    if results['broken_wikilinks']:
        print("\n--- WIKILINKS QUEBRADOS ---")
        for item in results['broken_wikilinks'][:20]:
            print(f"  {item}")
    
    if results['other_issues']:
        print("\n--- OUTRAS INCONSISTENCIAS ---")
        for item in results['other_issues'][:10]:
            if 'Sem frontmatter' not in item:
                print(f"  {item}")
    
    # Save full report
    report_path = os.path.join(VAULT, 'Workflow', 'Format Audit Report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Format Audit Report\n\n")
        f.write(f"_Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n")
        f.write("## Summary\n\n")
        for k, v in results['summary'].items():
            f.write(f"- **{k}:** {v}\n")
        f.write("\n---\n\n")
        
        sections = [
            ('Files without YAML', results['other_issues'], 'Sem frontmatter'),
            ('Empty YAML', results['files_yaml_empty'], None),
            ('YAML Parse Errors', results['yaml_parse_errors'], None),
            ('Missing NoteIcon', results['missing_noteicon'], None),
            ('Tags as String (should be list)', results['wrong_tags_format'], None),
            ('Missing Cover/Thumbnail', results['missing_cover'], None),
            ('Old Callouts (no [!NOTE])', results['old_format_callouts'], None),
            ('Location without territory', results['missing_territory'], None),
            ('Broken Wikilinks', results['broken_wikilinks'], None),
            ('Other Issues', results['other_issues'], None),
        ]
        
        for title, items, filter_str in sections:
            if not items:
                continue
            f.write(f"## {title}\n\n")
            for item in items:
                if filter_str:
                    if filter_str in str(item):
                        f.write(f"- {item}\n")
                else:
                    rel = os.path.relpath(item, VAULT) if isinstance(item, str) and os.path.exists(item) else item
                    f.write(f"- {rel}\n")
            f.write("\n---\n\n")
    
    print(f"\nRelatorio completo: Workflow/Format Audit Report.md")


if __name__ == '__main__':
    scan_vault()
    print_report()