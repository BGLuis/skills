# Medição de desempenho — protocolo para qualquer número

Vale para todo número de tempo, memória, CPU, bytes ou custo que entra num relatório: evidências
do modo B, tabela antes/depois do modo C e plano de validação do modo A. Um número sem protocolo
declarado não é evidência — é `[modelado]`.

Não se aplica a **Esforço** e **Cobertura** dos metadados: são estimativas de trabalho humano,
regidas pela tipografia de `convencoes.md` (`5–7 dias-dev`, `~35 % (3 de 8 tarefas)`).

## Sumário

- 1. Gargalo primeiro
- 2. O que declarar em toda medição
- 3. Estatística mínima
- 4. Explicar o número — *active benchmarking*
- 5. Eficiência por unidade de trabalho
- 6. Uma mudança por vez
- 7. As sete perguntas antes de publicar um número
- 8. Antimétodos
- 9. Ferramentas por stack
- Fontes

## 1. Gargalo primeiro

Antes de propor otimização, nomeie o recurso que limita. Para cada recurso (CPU, memória, disco,
rede, pool de conexões, *locks*), verifique **Utilização, Saturação e Erros** — o método USE. Para
serviços movidos a requisição, meça **Taxa, Erros e Duração** juntos — o método RED; latência sem
taxa de erro engana, porque erro rápido baixa a média.

Otimizar o que não é gargalo não muda o resultado (lei de Amdahl): se a rede é 80 % do tempo,
dividir a CPU por dois ganha no máximo 10 %.

## 2. O que declarar em toda medição

Em coluna da tabela ou no parágrafo logo abaixo dela:

- **Ambiente** — máquina ou tipo de *runner*, SO, versão do *runtime*, *build* de produção ou não,
  *throttling* aplicado (p.ex. CPU 4×, rede 4G).
- **Ferramenta e comando exato** — reproduzível por outra pessoa.
- **n** — número de execuções por configuração. Mínimo **10**; abaixo disso, diga o n e trate a
  diferença como indicativa.
- **Aquecimento** — quantas execuções foram descartadas e por quê (JIT, cache de disco, frequência
  da CPU subindo).
- **Estado** — quente ou frio (cache limpo, primeira carga, *container* recém-iniciado).
- **Ruído** — o que foi controlado (governador de CPU, *turbo boost*, outros processos, vizinhos
  de *container*) e o que **não** foi. Não controlado também se declara.

## 3. Estatística mínima

- Latência que o usuário sente: **mediana e p95** (p99 quando houver n suficiente). Throughput e
  CPU: média ± desvio padrão.
- Diferença entre antes e depois só é afirmada com dispersão ou intervalo de confiança, ou com o
  veredito estatístico da ferramenta (p-valor de `benchstat`, mudança de `criterion`).
- **Não repita a medição até "dar significativo"**: rodar de novo até o resultado agradar é teste
  múltiplo e invalida o p-valor. Defina n antes, rode uma vez.
- *Outliers*: exclua só por regra declarada (p.ex. cercas IQR) e diga quantos saíram.
- Variação menor que o ruído medido entre duas execuções do **mesmo** código é "sem mudança".

## 4. Explicar o número — *active benchmarking*

Todo número relevante vem com a resposta a **"por que é este valor e não o dobro?"**: qual recurso
chegou ao limite durante a medição. Isso exige observar o sistema *enquanto* a medição roda (uso
de CPU por núcleo, GC, *syscalls*, I/O, *long tasks*), não só ler o resultado final.

Afirmação sobre **por que** algo é lento exige um artefato de *profiling* — *flame graph*, `perf`,
`pprof`, trace do navegador — e aponta o *frame* ou trecho específico, não o gráfico inteiro:
*"`JSON.parse` em `parseChapter` ocupa 41 % das amostras de CPU (trace `scroll-5s.json`)"*.

## 5. Eficiência por unidade de trabalho

O ganho que importa é o **por unidade de trabalho entregue**, não o absoluto — o absoluto mistura
escala com eficiência. Inclua ao menos uma linha normalizada na tabela:

| Recurso | Unidade normalizada |
|---|---|
| CPU | requisições/s por núcleo · ms de CPU por requisição |
| Memória | MB por requisição ou por conexão · pico de *heap* por documento aberto |
| Rede/bundle | kB transferidos por navegação · kB de JS por rota |
| CI | minutos de *runner* por *build* · custo por execução do *pipeline* |
| Nuvem | custo por mil requisições · custo por usuário ativo |

Recomendação que reduz recurso sem piorar a métrica do usuário é ganho mesmo sem ganho de tempo:
registre-a como tal.

## 6. Uma mudança por vez

Meça → identifique o gargalo → mude **uma** coisa → meça de novo com o mesmo protocolo. Duas
mudanças na mesma medição tornam o ganho inatribuível: o relatório não pode dizer qual das duas
funcionou, e uma delas pode estar piorando. No backlog, correções acopladas são uma unidade só e
são medidas juntas — e o texto diz isso.

## 7. As sete perguntas antes de publicar um número

1. Por que não o dobro? — qual o recurso limitante (§4).
2. Foi configurado como em produção? — *build*, *flags*, tamanho de dados.
3. Passou de algum limite? — memória esgotada, *swap*, fila cheia distorcem tudo.
4. Houve erros? — conte-os junto com o tempo.
5. Reproduz? — outra execução independente dá o mesmo resultado dentro da dispersão.
6. Importa? — a carga medida representa uso real, não o melhor caso sintético.
7. Aconteceu de fato? — o caminho de código afirmado foi exercitado (sem cache curto-circuitando,
   sem código eliminado pelo compilador).

## 8. Antimétodos

- **Poste de luz** — medir o que é fácil de medir, não o que limita.
- **Culpar outro** — atribuir o custo a um componente sem USE/RED apontando para ele.
- **Mudança aleatória** — trocar configurações até o número melhorar, sem hipótese.
- **Benchmark passivo** — publicar o número da ferramenta sem observar o sistema durante a execução.

## 9. Ferramentas por stack

| Stack | Ferramenta | Uso mínimo correto |
|---|---|---|
| Qualquer comando | `hyperfine` | `--warmup 3 --runs 10 --export-json out.json`; `--prepare` para estado frio |
| Go | `go test -bench` + `benchstat` | `-count=10` em antes e depois; `benchstat old.txt new.txt` dá o p-valor |
| Rust | `criterion` | relatório de mudança com intervalo de confiança; ruído abaixo do limiar = sem mudança |
| Python | `pyperf` | `python -m pyperf system tune` antes; `pyperf compare_to` para o veredito |
| C++ | `google/benchmark` | `--benchmark_repetitions=10 --benchmark_report_aggregates_only=true`; atenção ao aviso de *CPU scaling* |
| Navegador | trace do DevTools / Lighthouse | perfil com *throttling* declarado; *long tasks* > 50 ms; mediana de ≥ 5 execuções do Lighthouse |
| Sistema | `perf`, `pprof`, *flame graphs* | anexar o arquivo e citar o *frame* |

Anexe a saída bruta (JSON, `.txt` do benchmark, arquivo de trace) ou o caminho onde ela está.
Tabela resumida sem a saída bruta não é reproduzível.

## Fontes

- Brendan Gregg — The USE Method: https://www.brendangregg.com/usemethod.html
- Brendan Gregg — Active Benchmarking: https://www.brendangregg.com/activebenchmarking.html
- Brendan Gregg — Benchmarking Checklist: https://www.brendangregg.com/blog/2018-06-30/benchmarking-checklist.html
- Tom Wilkie — The RED Method: https://grafana.com/blog/the-red-method-how-to-instrument-your-services/
- hyperfine: https://github.com/sharkdp/hyperfine
- benchstat: https://pkg.go.dev/golang.org/x/perf/cmd/benchstat
- criterion.rs — análise: https://bheisler.github.io/criterion.rs/book/analysis.html
- pyperf — ajuste do sistema: https://pyperf.readthedocs.io/en/latest/system.html
- google/benchmark — redução de variância: https://github.com/google/benchmark/blob/main/docs/reducing_variance.md
- Green Software Foundation — SCI (custo por unidade funcional): https://github.com/Green-Software-Foundation/sci
