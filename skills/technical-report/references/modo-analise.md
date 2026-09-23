# Modo A — Análise / proposta

Relatório escrito **antes** de implementar. O eixo não é "antes × depois", é
**"o que existe" × "o que falta"**. Nada aqui foi executado — e o relatório
precisa dizer isso.

É o modo que mais depende de `pesquisa.md`: faça os seis passos antes de escrever a seção 2.
Um plano sem precedentes e sem fontes é uma opinião.

## Sumário

- Esqueleto
- Seção 1 — Estado atual (inclui precedentes e não-objetivos)
- Seção 2 — Tarefas ou decisões de design
- Seção 3 — Plano
- Seção 4 — Armadilhas
- Seção 5 — Verificação
- Seção 6 — Riscos
- Seção 7 — Arquivos tocados
- Seção 8 — Fontes consultadas

## Esqueleto

```markdown
# <Nome curto> — <o que o relatório propõe, em minúsculas>

| Campo | Valor |
|-------|-------|
| **Status** | 🟡 Parcial — <razão em uma frase> |
| **Cobertura** | ~35% (3 de 8 tarefas) |
| **Esforço** | 5–7 dias-dev no escopo completo; 1–1,5 d no mínimo viável |
| **Depende de** | Nada (pode começar já) |

---

## 1. Estado atual — evidências

---

## 2. Análise tarefa a tarefa        |  ## 2. As <N> decisões de design

---

## 3. Plano de implementação

---

## 4. Armadilhas

---

## 5. Verificação

---

## 6. Riscos

---

## 7. Arquivos tocados

---

## 8. Fontes consultadas

---

> Nenhum item deste relatório foi executado em <ambiente/hardware>. Toda a
> análise vem da leitura do código no branch `<branch>` (commit `<sha>`); a
> validação está listada na seção 5 como pendente.
```

Campos de metadados adicionais, conforme o caso: `**Bloqueia**`,
`**Compartilha código com**`, `**Atenção**`, `**Fecha requisito**`. O núcleo fixo
é Status / Cobertura / Esforço / Depende de.

## Seção 1 — Estado atual

Prosa ancorada em `arquivo:linha`, blocos de código curtos (3–8 linhas) com
comentário de origem na primeira linha, e provas de ausência por busca.

Subseções úteis: `### O que existe`, `### O que não existe`,
`### ⚠️ Defeito encontrado: <…>`, `### 1.4 Cinco defeitos já presentes no código atual`.

Duas subseções são **obrigatórias**:

- `### Precedentes no código` — o que o repositório já resolve de forma parecida (passo 1 de
  `pesquisa.md`), com `arquivo:linha` e o veredito **reutilizar** ou **divergir, porque…**. Se não
  houver precedente, a busca de resultado zero fica aqui.

  ```markdown
  - `src/shared/virtual-list.ts:12-88` — já virtualiza a lista de livros com altura fixa.
    **Reutilizar** a API; **divergir** na medição de altura, que aqui é variável [F1].
  ```

- `### Não-objetivos` — o que o plano deliberadamente **não** resolve, em lista curta. Evita que
  a implementação cresça em silêncio e que o revisor cobre o que ficou fora de propósito.

Ao listar defeitos pré-existentes, deixe claro que não foram causados pelo pedido:

> Nenhum deles é causado pelo pedido — mas todos passam pelo mesmo código que
> será reescrito, e o custo de corrigi-los agora é próximo de zero.

## Seção 2 — duas formas

**Tarefa a tarefa** (quando há uma spec com tarefas numeradas):

```markdown
| Tarefa | Status | Observações |
|---|---|---|
| **T1.1** Pipeline de loading de ambientes | ❌ | Nenhuma estrutura de diretórios, nenhum `config.json`. |
```

**Decisões de design** (quando o pedido é uma feature): H3 numerados `### 2.1`…,
sendo o último `### 2.N O que não fazer`. Trade-offs em tabela
`| Opção | O que é | Custo | Base | Veredito |`, com `**Recomendada**` / `Rejeitada: …`.

A coluna `Base` diz o que sustenta a opção: um precedente (`virtual-list.ts:12`), uma fonte
(`[F1]`) ou `[modelado]`. Opção recomendada com base `[modelado]` precisa de uma frase dizendo
por que nenhuma fonte foi encontrada.

## Seção 3 — Plano

Lista numerada com o esforço dentro do negrito do passo:

```markdown
1. **Fundação de cena (3–4 d)** — `EnvironmentAsset` em C++: struct, carregamento
   via `AAssetManager`, ciclo de vida. Reusa o *loader* de `texture_cache.cpp:40-95`.
```

Quando o passo reutiliza um precedente ou segue um exemplo de referência, diga qual — é isso que
impede a implementação de criar uma segunda versão do que já existe.

Ou tabela de fases, quando há sequenciamento: `| Fase | Conteúdo | Esforço |`,
com linhas `| **F0** | … | 0,5 d |`.

Feche sempre com os dois totais e a ordem:

```markdown
**Mínimo viável** (só o que foi pedido literalmente): F1 + F2 ≈ 1,5–2 d.
**Escopo completo:** F0–F6 ≈ 5,5–7 d.

Ordem importa: fazer F3 antes de F4 evita refazer a formatação a cada campo novo.
```

## Seção 4 — Armadilhas

Tabela `| Armadilha | Mitigação |` — granular e acionável. É seção **distinta**
de Riscos: armadilha é técnica e imediata, risco é de cronograma e estratégia.

Variantes de título: `## 4. Armadilhas confirmadas`,
`## 4. Armadilhas da spec × situação real`.

## Seção 5 — Verificação

Checkboxes agrupados por **onde o teste roda**, com rótulo em negrito:

```markdown
**Automatizável no host (`./gradlew testDebugUnitTest`):**
- [ ] `FeatureFlags`: `DEBUG_STATS_PANEL` com default `false` (o teste falha se
      alguém ligar por engano — é isso que o teste está guardando).

**Só no Quest 3 (declarar explicitamente como não verificado até rodar):**
- [ ] O modal abre a 1,64 m sem clipping do quad da UI.
```

Regras:
- **Nenhum checkbox nasce marcado.** Use `- [ ]` sempre — nada foi executado.
- O item declara **o invariante que o teste guarda**, não o passo do teste.
- Cada item aponta a decisão ou fonte que valida (passo 6 de `pesquisa.md`): um limite
  documentado vira caso de teste — *"lista com 10.000 itens rola sem* long task *> 50 ms [F1]"*.
- Item de desempenho declara o protocolo de `medicao-desempenho.md`: ferramenta, n, métrica
  (mediana/p95) e o limiar que aprova — *"`hyperfine --runs 10`, mediana ≤ 120 ms"*.
- Continuação de item indentada com 6 espaços, alinhada sob o texto.

Se a seção for pouco automatizável, abra com a frase franca:
*"Automatizável em CI/host: **quase nada** — esta seção é essencialmente gráfica."*

## Seção 6 — Riscos

Lista numerada, cada item abrindo com uma **tese em negrito** seguida da consequência:

```markdown
1. **Assets 3D são o caminho crítico, não o código.** Se depender de modelagem
   própria, esta seção sozinha pode consumir metade do cronograma da fase.
```

## Seção 7 — Arquivos tocados

Tabela `| Arquivo | Mudança |`, com marcadores em negrito na segunda coluna:
`**novo**`, `**apagado** ao fim de F2`, `idem, caminho Vulkan`. Inclua arquivos
de teste, recursos e documentação a atualizar.

## Seção 8 — Fontes consultadas

Tabela de fontes no formato de `pesquisa.md`. Se alguma fonte necessária não pôde ser consultada,
diga qual numa frase abaixo da tabela e quais afirmações ficaram `[modelado]` por isso. Se o
relatório não usou nenhuma fonte externa, a seção diz isso em uma linha e por quê.
