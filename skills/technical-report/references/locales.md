# Locales — labels and typography per report language

The templates are written in English. When the report is in another language, every section
title, field label, and closed vocabulary below is translated **exactly** as in its column, so
the report reads naturally and `scripts/validate_report.py` can recognize it. The labels the
validator checks are marked **(v)**; keep `LOCALES` in that script in sync with this table.

For a language not listed here, translate each label once and use the same translation
throughout. The validator will run only its structural checks for that report (it warns); check
the **(v)** rules by hand.

Never translated, in any language: identifiers, file names, paths, APIs, commands, finding IDs
(`P-01`, `U-03`), task IDs (`T1.1`, `F0`), source IDs (`F1`), effort sizes (`XS / S / M / L`),
backlog types (`Perf`, `UX`, `A11y`), and emojis.

## Contents

- Field labels
- Closed vocabularies
- Section titles — mode A
- Section titles — mode B
- Section titles — mode C
- Sources table
- Typography

## Field labels

| en | pt-BR |
|---|---|
| `**Reproduction:**` **(v)** | `**Reprodução:**` |
| `**Fix:**` **(v)** | `**Correção:**` |
| `**Acceptance criteria:**` **(v)** | `**Critério de aceite:**` |
| `**Verdict:**` **(v)** | `**Veredicto:**` |
| `**Cost [modeled]:**` | `**Custo [modelado]:**` |
| `**Where:**` | `**Onde:**` |
| `**Status**` · `**Coverage**` · `**Effort**` · `**Depends on**` | `**Status**` · `**Cobertura**` · `**Esforço**` · `**Depende de**` |
| `**Blocks**` · `**Shares code with**` · `**Attention**` · `**Closes requirement**` | `**Bloqueia**` · `**Compartilha código com**` · `**Atenção**` · `**Fecha requisito**` |
| `**Delivered scope**` · `**Actual effort**` · `**Base commit**` | `**Escopo entregue**` · `**Esforço real**` · `**Commit base**` |
| `**Date:**` · `**Branch:**` · `**Base commit:**` · `**Scope:**` · `**Sibling report:**` | `**Data:**` · `**Branch:**` · `**Commit base:**` · `**Escopo:**` · `**Relatório irmão:**` |
| `**Minimum viable**` · `**Full scope:**` | `**Mínimo viável**` · `**Escopo completo:**` |
| `**Recommended**` · `Rejected: …` | `**Recomendada**` · `Rejeitada: …` |
| `**new**` · `**deleted**` | `**novo**` · `**apagado**` |
| `**reuse**` · `**diverge, because…**` | `**reutilizar**` · `**divergir, porque…**` |

## Closed vocabularies

| Vocabulary | en | pt-BR |
|---|---|---|
| Estimate marker | `[modeled]` | `[modelado]` |
| Severity **(v)** | **Critical** · **High** · **Medium** · **Low** | **Crítica** · **Alta** · **Média** · **Baixa** |
| Status | ✅ Done · 🟡 Partial · ❌ Not started · ⚠️ Divergence or risk | ✅ Concluído · 🟡 Parcial · ❌ Não iniciado · ⚠️ Divergência ou risco |
| Effort | `5–7 dev-days`, `d` in tables | `5–7 dias-dev`, `d` em tabelas |
| Source type | `Official doc` · `Maintainer example` · `Third-party project` · `Changelog` · `Issue` · `Article` | `Doc oficial` · `Exemplo do mantenedor` · `Projeto de terceiros` · `Changelog` · `Issue` · `Artigo` |
| Backlog type | `Perf` · `UX` · `A11y` · `Fix` · `Quality` · `Architecture` | `Perf` · `UX` · `A11y` · `Correção` · `Qualidade` · `Arquitetura` |
| Zero-result search | `# → 0 results` | `# → 0 resultados` |

## Section titles — mode A

| en | pt-BR |
|---|---|
| `## 1. Current state — evidence` **(v: "Current state")** | `## 1. Estado atual — evidências` |
| `### Precedents in the code` **(v)** | `### Precedentes no código` |
| `### Non-goals` **(v)** | `### Não-objetivos` |
| `### What exists` · `### What does not exist` | `### O que existe` · `### O que não existe` |
| `## 2. Task-by-task analysis` · `## 2. The <N> design decisions` | `## 2. Análise tarefa a tarefa` · `## 2. As <N> decisões de design` |
| `### 2.N What not to do` | `### 2.N O que não fazer` |
| `## 3. Implementation plan` | `## 3. Plano de implementação` |
| `## 4. Pitfalls` | `## 4. Armadilhas` |
| `## 5. Verification` | `## 5. Verificação` |
| `## 6. Risks` | `## 6. Riscos` |
| `## 7. Files touched` | `## 7. Arquivos tocados` |
| `## 8. Sources consulted` **(v)** | `## 8. Fontes consultadas` |

## Section titles — mode B

| en | pt-BR |
|---|---|
| `# Technical Analysis — <scope>` | `# Análise Técnica — <escopo>` |
| `## 1. Executive summary` **(v)** | `## 1. Sumário executivo` |
| `## 2. Methodology and limits` | `## 2. Metodologia e limites` |
| `### 2.1 What was done` · `### 2.2 What was NOT done — limits of this analysis` | `### 2.1 O que foi feito` · `### 2.2 O que NÃO foi feito — limites desta análise` |
| `## 3. Measured evidence` | `## 3. Evidências medidas` |
| `## 4. Performance findings` | `## 4. Achados de performance` |
| `## 5. Usability and accessibility findings` | `## 5. Achados de usabilidade e acessibilidade` |
| `## 6. Prioritized backlog` | `## 6. Backlog priorizado` |
| `## 7. Risks and what remains to verify` | `## 7. Riscos e o que falta verificar` |
| `## N. What is done well` · `## N. Cross-cutting finding: <…>` · `## N. Structural note` | `## N. O que está bem feito` · `## N. Achado transversal: <…>` · `## N. Observação estrutural` |

## Section titles — mode C

| en | pt-BR |
|---|---|
| `## 1. Executive summary` **(v)** | `## 1. Sumário executivo` |
| `## 2. Impacts and gains` | `## 2. Impactos e ganhos` |
| `## 3. Steps executed` | `## 3. Etapas executadas` |
| `## 4. Implementation details` | `## 4. Detalhes de implementação` |
| `## 5. Files touched` | `## 5. Arquivos tocados` |
| `## 6. Verification performed` **(v)** | `## 6. Verificação executada` |
| `## 7. What was not verified` | `## 7. O que não foi verificado` |

## Sources table

| en | pt-BR |
|---|---|
| `\| # \| Source \| Type \| Version \| Consulted on \| Supports \|` | `\| # \| Fonte \| Tipo \| Versão \| Consultada em \| Sustenta \|` |

## Typography

| Rule | en | pt-BR |
|---|---|---|
| Decimal separator | `0.5 d`, `564.55 kB` | `0,5 d`, `564,55 kB` |
| Thousands separator | `2,729 lines` | `2.729 linhas` |
| Percent | `~35% (3 of 8 tasks)` | `~35 % (3 de 8 tarefas)` |
| Foreign technical terms | plain text | *italic* (*tree-shaking*, *lockfile*) |

Shared by every language: `·` as separator · `—` for asides · `×` for versus · `→` for flow ·
`↔` for bidirectional · `–` en-dash in ranges (`5–7`) · `≤ ≥ ≈ ~` as real symbols · ISO dates
(`2026-09-23`) · times always with a time zone (`14:05 UTC`).
