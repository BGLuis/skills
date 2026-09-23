# Convenções — regras comuns aos três modos

## Sumário

- As sete regras duras
- Forma
- Tipografia PT-BR
- Emojis
- Negrito
- Tom

## As sete regras duras

1. **Toda afirmação sobre código carrega `arquivo:linha`.** Formas aceitas:
   - completa: `chapters.component.ts:293-330`
   - múltiplos locais: `item-book.component.ts:136-147` + `download.service.ts:58-76`
   - linhas soltas: `vr_player_app.cpp:1109-1114,1637`
   - abreviada, quando o arquivo já foi nomeado no parágrafo: `:347-353`
   - símbolo + arquivo: `MediaMetadataReader.parse` (`filebrowser/MediaMetadataReader.kt:70`)

2. **Toda ausência é provada por busca com resultado zero**, mostrando o comando:

   ```bash
   grep -rn "xrCreateHandTrackerEXT\|XR_HAND_JOINT" native/
   # → 0 resultados
   ```

   Nunca escreva "não existe" sem a prova. Uma ausência não provada é um palpite.

3. **Medido não é o mesmo que estimado.** Todo número que não foi medido leva o
   marcador literal `[modelado]` — como rótulo de coluna (`| Impacto [modelado] |`),
   inline (`**Custo [modelado]:** 20 ciclos por segundo`) ou abrindo o parágrafo.
   Números medidos declaram a origem: build real, busca no bundle, trace, teste.

4. **Nenhuma seção termina em resumo.** Termina em recomendação ou consequência.
   Se o último parágrafo apenas repete o que veio acima, apague-o.

5. **Seção obrigatória do que NÃO foi verificado.** O lugar depende do modo: no A é a
   seção 5 (Verificação, toda em `- [ ]`) somada ao blockquote de fechamento; no B, a seção 7
   (Riscos e o que falta verificar); no C, a seção 7 (O que não foi verificado). Hipóteses
   refutadas ficam registradas, não apagadas — para não voltarem a ser levantadas:
   > **Não há duplicação** — a hipótese está refutada e é registada aqui para não
   > voltar a ser levantada.

6. **Blockquote de fechamento**, depois de um `---`, declarando o que não rodou
   em ambiente ou hardware real:
   > Nenhum item deste relatório foi executado no Quest 3. Toda a análise vem da
   > leitura do código no branch `develop` (commit `e0e7406`); a validação em
   > headset está listada na seção 5 como pendente.

7. **Toda afirmação sobre comportamento externo carrega `[Fn]`.** O que uma biblioteca, API,
   ferramenta ou plataforma faz — limites, defaults, custos, *deprecations* — é citado com a
   fonte consultada nesta sessão, na versão instalada. As fontes ficam na última seção numerada,
   `## N. Fontes consultadas`, logo antes do blockquote de fechamento (formato em
   `pesquisa.md`). Comportamento externo sem fonte é `[modelado]`.

## Forma

- Sem frontmatter YAML. A primeira linha é o H1.
- Um único H1. H2 **sempre numerados**: `## 1.`, `## 2.`, contíguos.
- H3 numerados em dot-notation (`### 2.1 …`) ou temáticos (`### O que não existe`).
- **Nunca use H4.**
- `---` entre todas as seções H2 (e entre achados, no modo auditoria). Nunca entre H3.
- Prosa quebrada manualmente em ~100 colunas. Tabelas ficam em linha única.
- Tabela é o instrumento padrão para métrica. Sem gráficos, sem barras ASCII, sem badges.

## Tipografia PT-BR

Vírgula decimal (`0,5 d`, `564,55 kB`, `44,1 kHz`) · ponto de milhar
(`2.729 linhas`) · espaço antes de `%` · `·` como separador · `—` para aposto ·
`×` para versus · `→` para fluxo · `↔` para bidirecional · `–` en-dash em
intervalos (`5–7 dias-dev`, `1,75–3`) · `≤ ≥ ≈ ~` como símbolos reais.

Identificadores, nomes de arquivo, APIs e comandos ficam em inglês, dentro de
crase, **nunca traduzidos**. Termos técnicos estrangeiros em itálico:
*containing block*, *tree-shaking*, *zoneless*.

Percentual sempre aproximado e qualificado: `~35% (3 de 8 tarefas)`.

Esforço em faixa de dias-dev (`5–7 dias-dev`), abreviado `d` dentro de tabelas.

Datas em ISO (`2026-09-23`). Horários sempre com fuso (`14:05 UTC`, `11:05 BRT`).

## Emojis

Conjunto **fechado e semântico**, nunca decorativo:

✅ Concluído · 🟡 Parcial · ❌ Não iniciado · ⚠️ Divergência ou risco

Usados na coluna de status de tabelas, na tabela de metadados e em títulos que
sinalizam um achado (`### ⚠️ Custo estrutural: dois renderizadores`).

**Nada de 🚀, 📊, 🎯, 💡.** Setas e símbolos matemáticos não contam como emoji.

## Negrito

Três papéis, e só eles:

1. Rótulos de campo: `**Status**`, `**Correção:**`, `**Critério de aceite:**`,
   `**Veredicto:**`, `**Custo [modelado]:**`, `**Onde:**`.
2. Identificadores: `**T1.1**`, `**F0**`, `**N2**`, `**P-01**`, `**Alta**`, `**novo**`.
3. A palavra que carrega o juízo na prosa — 1 a 3 por parágrafo, não mais:
   `Não existe **nenhuma** linha de código`, `**dobra** o custo`, `**trunca em silêncio**`.

Itálico fica reservado a termos estrangeiros.

## Tom

Analítico, assertivo, sem hedging. Afirme o mecanismo antes do impacto. Recomende
explicitamente e assuma o custo da recomendação. Corrija o pedido quando o pedido
estiver errado, e diga por quê. Registre defeitos pré-existentes que estejam no
caminho, marcando que não foram causados pelo escopo atual.

Seja franco sobre o que não sabe: *"é uma estimativa que hoje não é verificável"*
vale mais do que um número inventado com duas casas decimais.

Números de desempenho seguem o protocolo de `medicao-desempenho.md` — ambiente, n, estatística
e recurso limitante declarados. Sem isso, o número é `[modelado]`, mesmo que tenha sido rodado.
