# Checklist de entrega

Percorra na ordem, depois de rodar `scripts/validate_report.py`. O script confere a forma; esta
lista confere o que só uma leitura crítica pega. Um item que não passa volta para o texto — não
para a seção de limites.

## 1. Fundamentação
- [ ] A pesquisa seguiu a proporção do modo (`pesquisa.md`): completa em A, média em B, mínima em C?
- [ ] Cada decisão ou correção tem uma base de nível 1 a 3 — precedente `arquivo:linha`, doc oficial
      ou exemplo do mantenedor — ou está marcada `[modelado]` com a razão?
- [ ] Os precedentes internos foram procurados pelo padrão e pelo sintoma, não só pelo nome do módulo?
- [ ] Toda divergência de um precedente tem justificativa escrita?
- [ ] A versão de cada dependência foi lida no *lockfile*, e a doc consultada é dessa versão?
- [ ] Nenhuma afirmação sobre API externa vem da memória do modelo?

## 2. Evidência
- [ ] Toda afirmação sobre código tem `arquivo:linha`, e as linhas foram abertas nesta sessão?
- [ ] Toda ausência tem a busca de resultado zero com o comando?
- [ ] Todo número está medido (com origem) ou marcado `[modelado]`?
- [ ] Todo número de desempenho declara ambiente, ferramenta, n, estatística e recurso limitante
      (`medicao-desempenho.md`)?
- [ ] Antes e depois foram medidos com o mesmo protocolo?

## 3. Acionabilidade
- [ ] Todo critério de aceite é falsificável — um comando, uma asserção, uma observação de trace?
- [ ] Todo achado do modo B tem `**Reprodução:**` que outra pessoa consegue seguir?
- [ ] Cada item de verificação do modo A aponta a decisão ou fonte que valida?
- [ ] Nenhuma seção termina em resumo?
- [ ] Os não-objetivos (modo A) e os desvios do plano (modo C) estão escritos, não implícitos?

## 4. Honestidade
- [ ] A seção do que não foi verificado lista tudo o que ficou em suposição, incluindo fontes que
      não puderam ser consultadas?
- [ ] Nenhum checkbox está marcado `[x]` sem ter rodado nesta sessão?
- [ ] Hipóteses refutadas continuam registradas?

## Ao entregar
Informe o caminho, o modo, o resultado do validador, as fontes que não puderam ser consultadas e o
que ficou sem verificar — sem suavizar.
