# Modo B — Auditoria

Revisão crítica de código existente em busca de defeitos. Cada defeito vira um
**achado** com identificador, severidade, correção e critério de aceite.

## Esqueleto

```markdown
# Análise Técnica — `src/app/pages/chapters`

**Data:** 2026-08-23 · **Branch:** `developer` · **Commit base:** `912fc3d`
**Escopo:** `src/app/pages/chapters/*` (host da experiência de leitura)
**Relatório irmão:** [`OUTRO-RELATORIO.md`](./OUTRO-RELATORIO.md)

---

## 1. Sumário executivo

---

## 2. Metodologia e limites

---

## 3. Evidências medidas

---

## 4. Achados de performance

---

## 5. Achados de usabilidade e acessibilidade

---

## 6. Backlog priorizado

---

## 7. Riscos e o que falta verificar
```

Os metadados são um **bloco em negrito separado por `·`**, não uma tabela — é o
que distingue visualmente a auditoria da análise. Campos: Data, Branch, Commit
base, Escopo, e Relatório(s) irmão(s) quando houver.

Seções opcionais, quando o material pedir: `## N. O que está bem feito` (tabela
`| Local | Decisão |`, registrando decisões que devem sobreviver a um refactor),
`## N. Achado transversal: <…>` (causa-raiz comum a vários achados, colocada
antes do backlog) e `## N. Observação estrutural`.

## Seção 1 — Sumário executivo

Um a dois parágrafos situando o módulo, seguidos da tabela dos problemas que
dominam o resultado:

```markdown
| # | Problema | Alcance | Severidade |
|---|---|---|---|
| P-01 | `cdr.detectChanges()` síncrono em cada tick de scroll (20 Hz) | Celular | Alta |
| U-01 | Retomada de leitura **sempre descartada** em texto e documento | Todas | Crítica |
```

Fecha obrigatoriamente com um veredito de uma a três frases:

```markdown
**Veredicto:** funcionalmente rico, mas com um pipeline de scroll que gasta
orçamento de frame sem contrapartida.
```

## Seção 2 — Metodologia e limites

Subseções: `### 2.1 O que foi feito`, `### 2.2 O que NÃO foi feito — limites
desta análise`, e as métricas de referência com a fonte de cada limiar:

```markdown
| Métrica | Limiar "Bom" | Fonte |
|---|---|---|
| LCP (p75) | ≤ 2,5 s | Core Web Vitals |
| Alvo de toque | ≥ 24 × 24 px CSS | WCAG 2.2 SC 2.5.8 (AA) |
| Bundle inicial | 750 kB aviso / 1,5 MB erro | `angular.json:66-70` |
```

A subseção de limites é obrigatória e vai num blockquote quando for crítica. Se
nenhum tempo foi medido, diga isso aqui, não só no fim.

## Seção 3 — Evidências medidas

Só o que foi de fato medido: saída de build, busca no bundle, contagem de bytes.
Cada subseção tem título específico e afirmativo — `### 3.2 O import dinâmico do
PDF está bem feito`, `### 3.4 Verificação negativa: estilos NÃO estão duplicados`.

## Seções 4 e 5 — Achados

Heading, formato literal:

```markdown
### P-01 · `detectChanges()` síncrono a 20 Hz durante o scroll — **Alta**
### U-03 · Barra de progresso: 4 px de alvo, sem teclado — **Alta** (WCAG 2.5.8)
### P-07 · `PreloadAllModules` compete com o conteúdo — **Baixa** (fora de escopo, registado)
```

`P-NN` para performance, `U-NN` para usabilidade e acessibilidade, com zero à
esquerda · separador ` · ` · severidade em negrito após ` — ` · sufixo opcional
entre parênteses para norma ou ressalva de escopo.

Severidade em vocabulário **fechado**: **Crítica** · **Alta** · **Média** · **Baixa**.

Quando o relatório cobre vários componentes, prefixe o título com o componente:
`### P-05 · `document-reader`: a virtualização desalinha após duas páginas — **Crítica**`.

### Anatomia de um achado

````markdown
### P-01 · <título> — **<Severidade>**

`arquivo.ts:293-330`

```ts
this.showScrollToTopButton.set(isScrolledDown && isScrollingUp);
this.cdr.detectChanges(); // linha 323
```

<parágrafo explicando o mecanismo — o porquê técnico do custo, não só o sintoma>

| Alcance | Impacto |
|---|---|
| Celular | Alto. Com 4× de throttling, cada ciclo compete com o orçamento de 10 ms/frame. |
| Desktop | Baixo — mascarado pela CPU. |

**Custo [modelado]:** 20 ciclos de detecção por segundo × 340 componentes.

**Correção:** remover a chamada e deixar o signal propagar.
**Critério de aceite:** um trace de 5 s de scroll mostra zero long tasks acima de 50 ms.

---
````

Regras do bloco final:
- `**Correção:**` e `**Critério de aceite:**` ficam em **linhas consecutivas**,
  sem linha em branco entre elas.
- O critério é sempre **falsificável**: um comando, uma asserção de teste, uma
  observação de trace. Nunca "melhorar a performance".
- Cada achado fecha com `---`.

Exemplos de critérios bem formados:

```markdown
**Critério de aceite:** `grep -l "app-text-reader" dist/browser/*.js` devolve um
chunk diferente do `chapters-component`.
**Critério de aceite:** três testes, um por tipo de conteúdo, que guardam progresso
a 50 %, remontam o componente e afirmam que a posição restaurada é 50 % e não 0.
```

Use blockquote dentro de um achado apenas para ressalvas de peso:

> **Precisa de medição.** O custo real varia por motor — mas a correção é barata
> e correta independentemente do resultado da medição.

## Seção 6 — Backlog priorizado

Declare o critério de ordenação **antes** da tabela:

> Ordenado por (impacto no usuário × alcance) ÷ esforço.

```markdown
| Pri | Item | Esforço | Alcance | Tipo |
|---|---|---|---|---|
| 1 | **U-01 + U-02** — retomada de leitura (unidade única) | M | Todas | Correção |
| 2 | **P-01** — remover `detectChanges()` do scroll | XS | Celular | Perf |
```

Esforço na escala fechada **XS / S / M / L**. Tipo: `Perf`, `UX`, `A11y`,
`Correção`, `Qualidade`, `Arquitetura`, ou híbridos (`A11y/UX`).

Itens podem agrupar achados acoplados (`**U-01 + U-02**`) — e quando agrupam, o
texto explica por que são uma unidade só.

Feche com um parágrafo de quick wins: *"Os itens 2, 3 e 7 somam menos de uma hora
de trabalho e cobrem os dois maiores custos de runtime identificados."*

## Seção 7 — Riscos e o que falta verificar

Lista numerada, cada item abrindo com tese em negrito e continuando com a ação
de verificação:

```markdown
1. **Nenhum número de tempo neste relatório foi medido.** Antes de aceitar as
   correções de performance, executar um trace sobre um capítulo de 40 páginas.
4. **U-01 tem de ser corrigido junto com U-02.** Corrigir só o primeiro expõe o segundo.
```
