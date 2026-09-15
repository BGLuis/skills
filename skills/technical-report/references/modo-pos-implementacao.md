# Modo C — Pós-implementação

Relatório de trabalho **já concluído**. É o único modo em que o eixo é
"antes × depois" — e por isso o único em que os números precisam vir de medição
real, não de projeção.

## Esqueleto

```markdown
# <Nome curto> — <o que foi entregue>

| Campo | Valor |
|-------|-------|
| **Status** | ✅ Concluído |
| **Escopo entregue** | <o que foi feito, em uma frase> |
| **Esforço real** | 2,5 d |
| **Commit base** | `abc1234` → `def5678` |

---

## 1. Sumário executivo

---

## 2. Impactos e ganhos

---

## 3. Etapas executadas

---

## 4. Detalhes de implementação

---

## 5. Arquivos tocados

---

## 6. Verificação executada

---

## 7. O que não foi verificado

---

> <o que não rodou em ambiente ou hardware real>
```

Se o escopo entregue divergiu do planejado, o Status vira `🟡 Parcial` e a linha
`**Escopo entregue**` diz o que ficou de fora. Não marque ✅ um trabalho parcial.

## Seção 1 — Sumário executivo

O que mudou e por quê, em um a três parágrafos. Fecha com `**Veredicto:**` — uma
frase sobre o estado em que o módulo ficou, não sobre o esforço gasto.

## Seção 2 — Impactos e ganhos

O núcleo do relatório. Tabela antes/depois:

```markdown
| Métrica | Antes | Depois | Variação |
|---|---|---|---|
| Bundle inicial (transferido) | 152,54 kB | 98,20 kB | **−35,6 %** |
| Long tasks em 5 s de scroll | 14 | 0 | **−14** |
```

Regras desta seção, sem exceção:

- Cada linha declara **como foi medido** — na própria tabela, em coluna `Fonte`,
  ou num parágrafo logo abaixo. Sem origem, o número não entra.
- Ganho não medido leva `[modelado]` e a tabela diz explicitamente que é
  estimativa. Uma tabela mista precisa separar as duas coisas visualmente.
- Se nada foi medido, **a seção diz isso na primeira linha** em vez de exibir
  números inventados: *"Nenhum ganho foi medido; os valores abaixo são
  `[modelado]` a partir de <base>."*
- Ganhos qualitativos (acessibilidade, manutenção) vão em prosa, não em tabela
  com percentual falso.

## Seção 3 — Etapas executadas

Lista numerada na **ordem real** em que aconteceram, não na ordem planejada.
Onde a execução divergiu do plano, registre o desvio e a razão:

```markdown
3. **Migração dos call sites (1 d)** — 15 dos 21 campos. Os 6 restantes ficaram
   para depois: dependem do `NgControl`, e mexer neles agora exigiria remover o
   provider `NG_VALUE_ACCESSOR` no mesmo commit.
```

Desvio silenciado é o defeito mais comum deste tipo de relatório. Se algo foi
pulado, esta seção é o lugar de dizer.

## Seção 4 — Detalhes de implementação

Organizada **por decisão**, não por arquivo. Cada bloco: a decisão, o
`arquivo:linha` onde ela vive, o trecho relevante, e a alternativa descartada.

````markdown
### 4.2 A serialização virou struct, não string plana

`native/src/debug_stats.h:12-38` + `app/.../DebugStatsParser.kt:20-44`

```cpp
struct DebugStats { float fps; uint32_t triangles; /* … */ };
```

A string plana teria evitado o header compartilhado, mas quebra em silêncio a
cada campo novo — e o parser Kotlin não tem como detectar a quebra.
````

## Seção 5 — Arquivos tocados

Tabela `| Arquivo | Mudança |`, com `**novo**`, `**apagado**`, ou a descrição da
alteração. Inclua testes, recursos e documentação atualizada.

## Seção 6 — Verificação executada

**Esta é a única seção, nos três modos, em que checkboxes podem nascer marcados**
— e apenas para o que foi realmente executado nesta sessão:

```markdown
**Rodado e passando (`npm test`):**
- [x] `chapters.spec.ts` — 3 testes de retomada de leitura, um por tipo de conteúdo.

**Não executado:**
- [ ] Trace de scroll no perfil Celular — depende de dispositivo físico.
```

Marcar `[x]` algo que não rodou invalida o relatório inteiro. Na dúvida, deixe
`- [ ]` e explique na seção 7.

## Seção 7 — O que não foi verificado

Riscos residuais e lacunas de verificação, em lista numerada, cada item abrindo
com tese em negrito. Inclua o que a implementação deixou em aberto de propósito
e o que só apareceria em produção.
