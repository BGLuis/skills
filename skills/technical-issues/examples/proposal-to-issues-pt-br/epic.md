<!-- Exemplo ilustrativo de modo A (proposta) em pt-BR, com uma dependência entre tarefas.
     Caminhos, versões e números são fictícios. -->

**Branch:** `develop` · **Commit base:** `4c1d7e2` · **Escopo:** `src/reader/*`

A lista de capítulos renderiza os 2.400 itens de uma vez (`src/reader/ChapterList.tsx:41-58`). O projeto já tem um hook de janela em `src/shared/virtual-list.tsx:12-88`, mas ele supõe altura fixa, e os títulos de capítulo quebram em uma a três linhas.

| Ordem | Chave | Sub-issue | Esforço |
|---|---|---|---|
| 1 | T1 | Suportar itens de altura variável no hook | 1 d |
| 2 | T2 | Renderizar só a janela visível na lista | 0,5 d |

> T2 depende de T1: sem altura variável, a janela sobrepõe títulos de três linhas.

### Não-objetivos

Não muda o visual da lista nem a ordenação; a busca por capítulo continua fora do escopo.

### Riscos

1. **A restauração de posição pode saltar.** Se a altura medida divergir da estimada, o capítulo restaurado não fica no topo; o critério de aceite de T2 mede isso.

**Não verificado:** nenhuma medição em aparelho real; o custo atual de renderização é `[modelado]` a partir da contagem de nós.
