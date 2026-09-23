# Pesquisa e fundamentação — antes de escrever

Um relatório que só descreve o código diz **o que existe**. Para dizer **o que fazer**, precisa de
base: o que o próprio repositório já resolveu, o que a documentação oficial da versão instalada
garante e como projetos maduros fazem a mesma coisa. Sem essa base, o plano reinventa o que já
existe, usa API da versão errada ou repete um erro conhecido — e a implementação herda tudo isso.

## Sumário

- Proporção por modo
- Os seis passos
- Hierarquia de evidência
- Orçamento de pesquisa
- Como registrar no relatório

## Proporção por modo

| Modo | Profundidade | Passos obrigatórios |
|---|---|---|
| **A — Análise/proposta** | Completa | 1 a 6 |
| **B — Auditoria** | Média — só para sustentar cada `**Correção:**` | 1, 2, 3 e 5 |
| **C — Pós-implementação** | Mínima — confirmar que o entregue segue a doc | 2 e 3, e só onde o relatório afirma algo sobre API externa |

## Os seis passos

Em ordem de custo crescente. Não pule para o 4 sem ter feito o 1.

1. **Precedentes internos.** Procure no repositório o que já resolve um problema parecido: a
   mesma biblioteca usada em outro módulo, o mesmo padrão (cache, fila, retry, virtualização),
   uma feature irmã, os testes da área, e as convenções escritas (ADRs, `CONTRIBUTING`, configs
   de lint). Busque pelo nome da API, pelo padrão e pelo sintoma — não só pelo nome do módulo.
   Registre cada precedente com `arquivo:linha` e decida explicitamente:
   - **reutilizar** — o plano chama ou estende o que existe;
   - **divergir** — e diga por quê (o precedente tem defeito, a versão é outra, o requisito
     difere). Divergência sem justificativa vira inconsistência no código.

   Se não houver precedente, prove com a busca de resultado zero (regra 2 de `convencoes.md`).

2. **Fixar versões.** Leia o manifesto e o *lockfile* (`package-lock.json`, `pnpm-lock.yaml`,
   `poetry.lock`, `go.sum`, `Cargo.lock`, `build.gradle`…) e anote a versão **instalada** de cada
   dependência envolvida. Toda consulta dos passos 3 a 5 é feita contra essa versão. Se a versão
   atual da biblioteca for outra, registre as *deprecations* e o guia de migração entre as duas —
   é frequente a solução recomendada hoje não existir na versão instalada.

3. **Documentação oficial.** Consulte a documentação da versão fixada: use uma ferramenta de
   consulta de documentação atualizada quando o ambiente oferecer (p.ex. Context7), ou o site
   oficial do projeto. Procure a página do recurso usado, os limites documentados (tamanho,
   concorrência, *timeouts*) e as notas de desempenho. **Nunca cite a memória do modelo como
   fonte**: comportamento de API que não foi conferido nesta sessão é `[modelado]`.

4. **Implementações de referência.** Busque código em repositórios maduros que usam a mesma API:
   primeiro os exemplos mantidos pelos autores da biblioteca, depois projetos amplamente usados e
   ativos. Extraia o **padrão** (a ordem das chamadas, o tratamento de erro, a configuração), não
   cole o código. Se algum trecho for copiado, anote a licença.

5. **Armadilhas conhecidas.** Leia o *changelog* e as *release notes* da versão fixada e procure
   *issues* abertas sobre o recurso. Um bug aberto que afeta o plano entra em Armadilhas (modo A)
   ou em Riscos, com a fonte.

6. **Derivar a validação.** Para cada decisão do relatório, feche a cadeia:

   ```text
   decisão → fonte que a sustenta ([Fn] ou arquivo:linha) → verificação que a confirma
   ```

   A verificação vem da própria fonte sempre que possível: o limite documentado vira o caso de
   teste, o exemplo do mantenedor vira o comportamento esperado, o precedente interno vira o teste
   de regressão. Números de desempenho seguem `medicao-desempenho.md`.

## Hierarquia de evidência

Quando duas fontes discordam, vale a mais alta — e a discordância é registrada como ⚠️:

1. Código do repositório (`arquivo:linha`) e medições feitas nesta sessão.
2. Documentação oficial da versão instalada.
3. Exemplos e código mantidos pelos autores da biblioteca.
4. Projetos maduros de terceiros.
5. Artigos, respostas de fórum, posts — só como pista para achar uma fonte de nível 1 a 4.
   Nunca sustentam sozinhos uma recomendação.

## Orçamento de pesquisa

O objetivo é o máximo de fundamentação com o mínimo de leitura. **Pare quando cada decisão do
relatório tiver uma base de nível 1 a 3.** Limites indicativos por decisão:

| Passo | Limite indicativo |
|---|---|
| Precedentes internos | até 3 locais — os mais parecidos, não todos |
| Documentação oficial | 2–4 páginas |
| Implementações de referência | até 2 projetos |
| Armadilhas | *changelog* da versão + 1 busca de *issues* |

Passar do limite é permitido quando a decisão continua sem base — e isso vira uma frase no
relatório. Pesquisa que não sustenta nenhuma decisão não entra no relatório.

Se uma fonte não puder ser consultada (sem rede, doc privada, versão sem documentação), diga isso
na seção de fontes e marque como `[modelado]` as afirmações que dependiam dela.

## Como registrar no relatório

Precedentes internos entram no corpo, com `arquivo:linha` (modo A: `### Precedentes no código`, na
seção 1). Fontes externas são citadas inline como `[F1]`, `[F2]`… e listadas na **última seção
numerada**, `## N. Fontes consultadas`, antes do blockquote de fechamento:

```markdown
| # | Fonte | Tipo | Versão | Consultada em | Sustenta |
|---|---|---|---|---|---|
| F1 | [TanStack Virtual — `useVirtualizer`](https://tanstack.com/virtual/latest/docs/api/virtualizer) | Doc oficial | 3.10.8 | 2026-09-23 | Decisão 2.1; verificação 5.2 |
| F2 | `TanStack/virtual` — `examples/react/dynamic` | Exemplo do mantenedor | 3.10.8 | 2026-09-23 | Medição dinâmica de altura |
```

`Tipo` usa o vocabulário da hierarquia: `Doc oficial`, `Exemplo do mantenedor`, `Projeto de
terceiros`, `Changelog`, `Issue`, `Artigo`. Toda fonte listada é citada ao menos uma vez no texto,
e toda citação aponta para uma linha da tabela.
