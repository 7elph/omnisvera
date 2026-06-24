#!/usr/bin/env python3
"""
Auditoria completa do vault Obsidian Omnisvera.

Executa todos os validadores e gera relatório consolidado em Markdown.
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict

import validate_frontmatter
import validate_links
import validate_media


def get_git_info(vault_path: Path) -> Dict:
    """Obtém informações do Git."""
    info = {
        'branch': 'unknown',
        'commit': 'unknown',
        'status': 'unknown'
    }
    
    try:
        # Obter branch atual
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=vault_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            info['branch'] = result.stdout.strip()
        
        # Obter commit atual
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=vault_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            info['commit'] = result.stdout.strip()[:8]
        
        # Obter status
        result = subprocess.run(
            ['git', 'status', '--short'],
            cwd=vault_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            if result.stdout.strip():
                info['status'] = 'dirty'
            else:
                info['status'] = 'clean'
    except Exception as e:
        print(f"Erro ao obter informações do Git: {e}")
    
    return info


def generate_report(vault_path: str, ignore_legacy: bool = False) -> str:
    """
    Gera relatório completo de auditoria.
    
    Returns:
        String com o relatório em Markdown
    """
    vault = Path(vault_path)
    
    # Executar validadores
    fm_results = validate_frontmatter.validate_frontmatter(vault_path, ignore_legacy)
    links_results = validate_links.validate_links(vault_path, ignore_legacy)
    media_results = validate_media.validate_media(vault_path, ignore_legacy)
    
    # Obter informações do Git
    git_info = get_git_info(vault)
    
    # Data/hora
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Construir relatório
    report = f"""# Relatório de Auditoria do Vault

**Data/Hora:** {now}
**Branch:** {git_info['branch']}
**Commit:** {git_info['commit']}
**Status Git:** {git_info['status']}

---

## Resumo Git

- **Branch atual:** {git_info['branch']}
- **Commit:** {git_info['commit']}
- **Status:** {git_info['status']}

---

## Validação de Frontmatter

- **Total de notas analisadas:** {fm_results['total_notes']}
- **Notas sem frontmatter:** {len(fm_results['notes_without_frontmatter'])}
- **Notas com frontmatter inválido:** {len(fm_results['notes_invalid_frontmatter'])}
- **Notas com campos vazios importantes:** {len(fm_results['notes_empty_fields'])}

### Notas sem frontmatter
"""
    
    if fm_results['notes_without_frontmatter']:
        for note in fm_results['notes_without_frontmatter']:
            report += f"- {note}\n"
    else:
        report += "Nenhuma\n"
    
    report += "\n### Notas com frontmatter inválido\n"
    
    if fm_results['notes_invalid_frontmatter']:
        for note in fm_results['notes_invalid_frontmatter']:
            report += f"- {note}\n"
    else:
        report += "Nenhuma\n"
    
    report += "\n### Notas com campos vazios importantes\n"
    
    if fm_results['notes_empty_fields']:
        for item in fm_results['notes_empty_fields']:
            report += f"- {item['file']}: {', '.join(item['empty_fields'])}\n"
    else:
        report += "Nenhuma\n"
    
    report += "\n---\n\n## Validação de Wikilinks\n\n"
    report += f"- **Total de wikilinks encontrados:** {links_results['total_links']}\n"
    report += f"- **Links resolvidos:** {links_results['resolved_links']}\n"
    report += f"- **Links quebrados:** {len(links_results['broken_links'])}\n"
    
    report += "\n### Links quebrados\n"
    
    if links_results['broken_links']:
        for item in links_results['broken_links']:
            report += f"- [[{item['link']}]] em {item['file']}:{item['line']}\n"
    else:
        report += "Nenhum\n"
    
    report += "\n---\n\n## Validação de Mídia\n\n"
    report += f"- **Total de referências de mídia:** {media_results['total_references']}\n"
    report += f"- **Referências válidas:** {media_results['valid_references']}\n"
    report += f"- **Referências quebradas (ativas):** {len(media_results['broken_references_active'])}\n"
    report += f"- **Referências quebradas (legacy):** {len(media_results['broken_references_legacy'])}\n"
    report += f"- **Imagens órfãs:** {len(media_results['orphaned_media'])}\n"
    
    report += "\n### Referências quebradas em notas ativas\n"
    
    if media_results['broken_references_active']:
        for item in media_results['broken_references_active']:
            report += f"- {item['reference']} em {item['file']}\n"
    else:
        report += "Nenhuma\n"
    
    report += "\n### Referências quebradas em legacy\n"
    
    if media_results['broken_references_legacy']:
        for item in media_results['broken_references_legacy']:
            report += f"- {item['reference']} em {item['file']}\n"
    else:
        report += "Nenhuma\n"
    
    report += "\n### Imagens órfãs\n"
    
    if media_results['orphaned_media']:
        for media in media_results['orphaned_media'][:20]:
            report += f"- {media}\n"
        if len(media_results['orphaned_media']) > 20:
            report += f"- ... e mais {len(media_results['orphaned_media']) - 20} arquivos\n"
    else:
        report += "Nenhuma\n"
    
    report += "\n---\n\n## Riscos Críticos\n\n"
    
    critical_risks = []
    
    if len(fm_results['notes_without_frontmatter']) > 10:
        critical_risks.append(f"Muitas notas ({len(fm_results['notes_without_frontmatter'])}) sem frontmatter")
    
    if len(links_results['broken_links']) > 5:
        critical_risks.append(f"Muitos links quebrados ({len(links_results['broken_links'])})")
    
    if len(media_results['broken_references_active']) > 5:
        critical_risks.append(f"Muitas referências de mídia quebradas em notas ativas ({len(media_results['broken_references_active'])})")
    
    if critical_risks:
        for risk in critical_risks:
            report += f"- {risk}\n"
    else:
        report += "Nenhum risco crítico identificado\n"
    
    report += "\n## Riscos Médios\n\n"
    
    medium_risks = []
    
    if len(fm_results['notes_invalid_frontmatter']) > 0:
        medium_risks.append(f"Notas com frontmatter inválido ({len(fm_results['notes_invalid_frontmatter'])})")
    
    if len(media_results['orphaned_media']) > 10:
        medium_risks.append(f"Muitas imagens órfãs ({len(media_results['orphaned_media'])})")
    
    if medium_risks:
        for risk in medium_risks:
            report += f"- {risk}\n"
    else:
        report += "Nenhum risco médio identificado\n"
    
    report += "\n## Pendências\n\n"
    
    pending = []
    
    if fm_results['notes_empty_fields']:
        pending.append("Revisar campos vazios importantes em frontmatter")
    
    if media_results['broken_references_legacy']:
        pending.append("Revisar referências quebradas em Workflow/Legacy")
    
    if pending:
        for item in pending:
            report += f"- {item}\n"
    else:
        report += "Nenhuma pendência\n"
    
    report += "\n---\n\n## Recomendação Final\n\n"
    
    # Determinar recomendação
    if not critical_risks and not medium_risks:
        recommendation = "Seguro"
    elif not critical_risks:
        recommendation = "Seguro com ressalvas"
    else:
        recommendation = "Não seguro"
    
    report += f"**Status:** {recommendation}\n\n"
    
    if recommendation == "Seguro":
        report += "O vault está em bom estado. Não há riscos críticos ou médios identificados.\n"
    elif recommendation == "Seguro com ressalvas":
        report += "O vault está geralmente seguro, mas há riscos médios que devem ser revisados.\n"
    else:
        report += "O vault não está seguro. Há riscos críticos que precisam ser resolvidos antes de operações importantes.\n"
    
    return report


def save_report(report: str, vault_path: str):
    """Salva o relatório em Workflow/Reports/latest_vault_audit.md."""
    vault = Path(vault_path)
    reports_dir = vault / 'Workflow' / 'Reports'
    
    # Criar diretório se não existir
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Salvar relatório
    report_file = reports_dir / 'latest_vault_audit.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Relatório salvo em: {report_file}")


if __name__ == '__main__':
    import sys
    
    vault_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    ignore_legacy = '--ignore-legacy' in sys.argv
    
    report = generate_report(vault_path, ignore_legacy)
    save_report(report, vault_path)
    
    print("\n" + "="*50)
    print("Auditoria concluída!")
    print("="*50)
