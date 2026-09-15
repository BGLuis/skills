# Modo A — Análise / proposta

Relatório escrito **antes** de implementar. O eixo não é "antes × depois", é
**"o que existe" × "o que falta"**. Nada aqui foi executado — e o relatório
precisa dizer isso.

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
`| Opção | O que é | Custo | Veredito |`, com `**Recomendada**` / `Rejeitada: …`.

## Seção 3 — Plano

Lista numerada com o esforço dentro do negrito do passo:

```markdown
1. **Fundação de cena (3–4 d)** — `EnvironmentAsset` em C++: struct, carregamento
   via `AAssetManager`, ciclo de vida.
```

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

Duas regras:
- **Nenhum checkbox nasce marcado.** Use `- [ ]` sempre — nada foi executado.
- O item declara **o invariante que o teste guarda**, não o passo do teste.
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
