# Lista de capítulos — virtualização com altura variável

<!-- Exemplo ilustrativo do modo A. Caminhos, versões e números são fictícios; num relatório
     real cada um vem da leitura do repositório e das fontes consultadas na sessão. -->

| Campo | Valor |
|-------|-------|
| **Status** | ❌ Não iniciado — a lista renderiza os 2.400 itens de uma vez |
| **Cobertura** | ~0 % (0 de 5 tarefas) · ~40 % reaproveitável de `virtual-list.tsx` |
| **Esforço** | 2–3 dias-dev no escopo completo; 1 d no mínimo viável |
| **Depende de** | Nada (pode começar já) |

---

## 1. Estado atual — evidências

`ChapterList` monta um `<li>` por capítulo, sem janela (`src/reader/ChapterList.tsx:41-58`). Um
livro de referência abre 2.400 capítulos; o componente não tem `key` estável por capítulo —
usa o índice (`:47`).

### Precedentes no código

- `src/shared/virtual-list.tsx:12-88` — já virtualiza a estante de livros com
  `@tanstack/react-virtual`. **Reutilizar** o *hook* e o contêiner de rolagem; **divergir** na
  altura: a estante usa `estimateSize` fixo (`:30`), e aqui os títulos quebram em 1–3 linhas, o que
  exige medição dinâmica com `measureElement` [F1] [F2].
- `src/shared/virtual-list.test.tsx:8-40` — teste com `ResizeObserver` falso; serve de molde para
  os testes da seção 5.

### Não-objetivos

- Busca dentro da lista de capítulos — continua como está.
- Rolagem horizontal ou grade.
- Trocar a biblioteca de virtualização.

### O que não existe

Nenhum outro uso de `measureElement` no repositório:

```bash
grep -rn "measureElement" src/
# → 0 resultados
```

---

## 2. As 3 decisões de design

### 2.1 Medição de altura

| Opção | O que é | Custo | Base | Veredito |
|---|---|---|---|---|
| `estimateSize` fixo | Igual à estante | 0,5 d | `virtual-list.tsx:30` | Rejeitada: títulos de 3 linhas se sobrepõem |
| `measureElement` + `ResizeObserver` | Mede cada item ao montar | 1 d | [F1] [F2] | **Recomendada** |

### 2.2 Versão da biblioteca

`package-lock.json:2210` fixa `@tanstack/react-virtual` em `3.10.8`. `measureElement` existe nessa
versão [F1]; não há motivo para atualizar dentro deste escopo.

### 2.3 O que não fazer

Não criar um segundo componente de lista virtual: estender `virtual-list.tsx` com a opção
`dynamicHeight` mantém um só lugar para corrigir defeitos de rolagem.

---

## 3. Plano de implementação

1. **Opção `dynamicHeight` em `virtual-list.tsx` (0,5 d)** — liga `measureElement` no *ref* do
   item, como no exemplo do mantenedor [F2]. Reusa o contêiner de `:52-70`.
2. **Migrar `ChapterList` (0,5 d)** — trocar o `map` por `VirtualList` e a `key` por `chapter.id`.
3. **Restaurar a posição de leitura (0,5–1 d)** — `scrollToIndex` com `align: 'start'` [F1].

**Mínimo viável** (só o que foi pedido literalmente): passos 1 e 2 ≈ 1 d.
**Escopo completo:** passos 1–3 ≈ 1,5–2 d, mais 0,5 d de testes.

Ordem importa: o passo 1 primeiro deixa a estante como teste de regressão da mudança no
componente compartilhado.

---

## 4. Armadilhas

| Armadilha | Mitigação |
|---|---|
| `scrollToIndex` antes da medição cai na posição estimada | Chamar depois do primeiro `measure`, como documentado [F1] |
| Oscilação de altura com fonte ainda carregando | Medir de novo no `document.fonts.ready` |
| Issue aberta sobre salto de rolagem com `smooth` e altura dinâmica [F3] | Usar `behavior: 'auto'` na restauração |

---

## 5. Verificação

**Automatizável no host (`npm test`):**
- [ ] `virtual-list.test.tsx`: com `dynamicHeight`, itens de 1 e 3 linhas não se sobrepõem — guarda
      a decisão 2.1.
- [ ] A estante continua renderizando no máximo 20 itens montados — guarda o precedente.
- [ ] Restaurar o capítulo 1.800 deixa o item 1.800 no topo — guarda a armadilha 1 [F1].

**Desempenho (protocolo de `medicao-desempenho.md`):**
- [ ] Abrir a lista de 2.400 capítulos, `hyperfine --warmup 3 --runs 10` sobre o teste de
      montagem: mediana ≤ 50 ms (hoje sem medição — o valor atual é o primeiro passo).
- [ ] Trace de 5 s de rolagem com CPU 4×: zero *long tasks* > 50 ms.

---

## 6. Riscos

1. **O ganho depende do tamanho real dos livros.** Com menos de ~200 capítulos a virtualização
   não muda nada perceptível; o esforço só se paga no catálogo de referência.
2. **Mudar um componente compartilhado afeta a estante.** Mitigado pela ordem do plano.

---

## 7. Arquivos tocados

| Arquivo | Mudança |
|---|---|
| `src/shared/virtual-list.tsx` | opção `dynamicHeight` |
| `src/shared/virtual-list.test.tsx` | 2 testes novos |
| `src/reader/ChapterList.tsx` | migra para `VirtualList`; `key` por `chapter.id` |
| `src/reader/ChapterList.test.tsx` | **novo** — restauração de posição |

---

## 8. Fontes consultadas

| # | Fonte | Tipo | Versão | Consultada em | Sustenta |
|---|---|---|---|---|---|
| F1 | [TanStack Virtual — Virtualizer API](https://tanstack.com/virtual/latest/docs/api/virtualizer) | Doc oficial | 3.10.8 | 2026-09-23 | 2.1, 2.2, passo 3, armadilha 1 |
| F2 | `TanStack/virtual` — `examples/react/dynamic` | Exemplo do mantenedor | 3.10.8 | 2026-09-23 | 2.1, passo 1 |
| F3 | `TanStack/virtual` — issue sobre `smooth` com altura dinâmica | Issue | 3.x | 2026-09-23 | Armadilha 3 |

---

> Nenhum item deste relatório foi executado. Toda a análise vem da leitura do código no branch
> `main` (commit `a1b2c3d`) e das fontes da seção 8; a medição de base está pendente na seção 5.
