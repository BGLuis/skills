---
name: technical-report
description: Produz relatórios técnicos estruturados em docs/reports/, cobrindo impactos, ganhos, resultados, etapas e detalhes de implementação, sempre ancorados em evidência arquivo:linha verificável e fundamentados na documentação oficial da versão instalada, em precedentes do próprio código e em exemplos de referência. Use quando o usuário pedir um relatório técnico, uma análise de viabilidade, uma auditoria de performance ou usabilidade de um módulo, um plano de implementação ou de validação detalhado, ou a documentação de um trabalho recém-concluído. NÃO use para README, documentação de API, changelog, comentários de código, mensagens de commit, descrição de Pull Request, nem para relatórios de negócio sem base em código.
---

# Relatório Técnico

Atue como um engenheiro sênior fazendo revisão crítica. Um relatório só vale se
cada afirmação puder ser conferida no repositório. Prosa sem evidência é ruído.

Escreva sempre em **português do Brasil**, mesmo quando o código ou os relatórios
vizinhos estiverem em português europeu ou inglês.

## 0. Antes de escrever

1. Identifique a raiz do projeto e a pasta `docs/reports/`. Se não existir, crie.
2. Se a pasta já tiver relatórios, leia o índice e um ou dois deles. Convenções
   locais existentes têm precedência sobre os templates desta skill.
3. **Colete evidência real primeiro.** Leia os arquivos citados, rode as buscas,
   confira os números. É proibido descrever código de memória ou supor linhas.
4. **Pesquise e fundamente.** Siga `references/pesquisa.md`: precedentes no próprio
   código, versões fixadas no *lockfile*, documentação oficial dessa versão, exemplos de
   referência e armadilhas conhecidas — na profundidade que o modo pede, e só até cada
   decisão ter base. É o que faz o relatório melhorar a implementação, não só descrevê-la.
5. Só depois comece a escrever.

## 1. Detectar o modo

| Modo | Quando | Template |
|---|---|---|
| **A — Análise/proposta** | Trabalho ainda não feito: "o que falta para", "como implementar X", viabilidade, planejamento | `references/modo-analise.md` |
| **B — Auditoria** | Revisar código existente em busca de defeitos: "analise a performance de", "audite", "que problemas tem" | `references/modo-auditoria.md` |
| **C — Pós-implementação** | O trabalho acabou de ser feito: "documente o que fizemos", "relatório das mudanças" | `references/modo-pos-implementacao.md` |

Se o pedido couber em mais de um modo, **pergunte ao usuário qual deles**. Não
adivinhe: o modo errado produz um relatório que responde à pergunta errada.

## 2. Regras invariáveis

Leia `references/convencoes.md` antes de escrever qualquer seção. São as regras
comuns aos três modos — evidência, fontes externas, marcação de números estimados,
tipografia, emojis, negrito. Nenhuma delas é opcional.

Se o relatório tiver qualquer número de desempenho, memória, bytes ou custo — medido ou
planejado —, leia também `references/medicao-desempenho.md` e siga o protocolo.

## 3. Escrever

Leia o template do modo detectado, em `references/`, e siga o esqueleto de seções
dele. Os templates trazem os títulos literais das seções e a anatomia interna de
cada bloco.

Adapte a profundidade ao escopo: um relatório de seção fica em torno de 120–160
linhas; um relatório de feature ou pedido grande, em torno de 240–320. Passe de
400 apenas quando houver um inventário exaustivo a apresentar.

## 4. Nomear e gravar

Grave em `docs/reports/` com o nome em **MAIÚSCULAS e kebab-case, sem acento e
sem cedilha**, descrevendo o tema — por exemplo `SCREEN-FORMAT-MODAL.md`,
`INPUT-TEXTO-UNIFICADO.md`. Não use data no nome.

Se a pasta tiver um `README.md` servindo de índice, acrescente a linha
correspondente na tabela adequada, respeitando as colunas já existentes.

## 5. Validar antes de entregar

1. Rode o validador de forma que acompanha esta skill (`scripts/validate_report.py`,
   caminho relativo ao diretório da skill), a partir da raiz do projeto:

   ```bash
   python3 <diretório-da-skill>/scripts/validate_report.py docs/reports/<ARQUIVO>.md
   ```

   Corrija todo erro apontado e rode de novo até sair sem erros. Sem Python disponível,
   confira as mesmas regras à mão em `references/convencoes.md` e diga isso ao usuário.
2. Percorra `references/checklist.md` — o que o script não pega: fundamentação,
   protocolo de medição, critérios falsificáveis.

Exemplos completos da forma esperada: `examples/analise-com-pesquisa.md` (modo A) e
`examples/auditoria-desempenho.md` (modo B).

## 6. Relatório ao usuário

Ao terminar, informe:

- o caminho do arquivo gravado, o modo usado e o resultado do validador;
- as afirmações que dependem de medição e ainda não foram medidas;
- as fontes que não puderam ser consultadas e o que ficou `[modelado]` por isso;
- **o que não foi verificado** — explicitamente, sem suavizar.

Nunca declare um relatório "completo" se alguma seção ficou baseada em suposição.
Diga qual, e por quê.
