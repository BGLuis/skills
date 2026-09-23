# Análise Técnica — `src/api/export`

<!-- Exemplo ilustrativo do modo B. Caminhos, versões e números são fictícios; num relatório
     real cada um vem da leitura do repositório, de medição nesta sessão ou de fonte citada. -->

**Data:** 2026-09-23 · **Branch:** `main` · **Commit base:** `9f3e21a`
**Escopo:** `src/api/export/*` (exportação de relatórios em CSV)

---

## 1. Sumário executivo

A rota `GET /export` gera o CSV de um mês de pedidos. Com 180 mil linhas, cada exportação segura
~1,1 GB de memória e uma conexão do *pool* por 9 s. O tempo não é o problema principal: a memória
é — duas exportações simultâneas já derrubam o *container* de 2 GB.

| # | Problema | Alcance | Severidade |
|---|---|---|---|
| P-01 | Resultado inteiro carregado em memória antes de escrever | Toda exportação | Crítica |
| P-02 | Consulta N+1 para o nome do cliente | Toda exportação | Alta |

**Veredicto:** correto nos dados, mas o custo de memória cresce linearmente com o mês e limita a
rota a uma exportação por vez.

---

## 2. Metodologia e limites

### 2.1 O que foi feito

Leitura de `src/api/export/*` e medição local com o protocolo abaixo.

**Protocolo** (`medicao-desempenho.md` §2): notebook de 8 núcleos, Node 22.4, *build* de produção,
Postgres 16 local com a base de testes de 180 mil pedidos · `hyperfine --warmup 2 --runs 10` sobre
`curl` da rota · estado quente (*buffer* do Postgres aquecido pelas execuções de aquecimento) ·
memória pelo pico de RSS em `/proc/<pid>/status` · ruído não controlado: *turbo boost* ligado.

### 2.2 O que NÃO foi feito — limites desta análise

> Nenhuma medição em produção nem com concorrência real. O limite de 2 GB vem do manifesto de
> *deploy* (`deploy/api.yaml:31`), não de um teste de carga.

| Métrica | Limiar "Bom" | Fonte |
|---|---|---|
| Pico de memória por exportação | ≤ 100 MB | orçamento do time (`docs/SLO.md:12`) |
| Conexões do *pool* por requisição | 1, liberada ao fim | `src/db/pool.ts:8` (`max: 10`) |

---

## 3. Evidências medidas

### 3.1 A memória, não a CPU, é o recurso limitante

| Métrica (n = 10) | Mediana | p95 |
|---|---|---|
| Tempo total | 9,2 s | 9,8 s |
| Pico de RSS | 1,12 GB | 1,15 GB |
| CPU do processo | 1,4 núcleo | — |

Durante a exportação a CPU fica em ~1,4 de 8 núcleos; o RSS cresce até o fim e só cai depois do
envio. Dobrar a CPU não muda o resultado — o que limita é a memória do *container*.

### 3.2 Verificação negativa: não há vazamento entre requisições

Depois de 10 exportações seguidas o RSS volta a ~140 MB. A memória é do pico, não acumulada — a
hipótese de vazamento está refutada e é registrada aqui para não voltar a ser levantada.

---

## 4. Achados de performance

### P-01 · Resultado inteiro carregado em memória antes de escrever — **Crítica**

`src/api/export/handler.ts:22-40`

```ts
const rows = await db.query(sql, [month]); // linha 24 — 180 mil objetos
res.send(toCsv(rows.rows));                 // linha 39 — string de ~95 MB
```

O `query` materializa todas as linhas como objetos JS e `toCsv` monta uma única *string*; os dois
coexistem no pico. O custo cresce linearmente com o mês exportado.

**Reprodução:** com a base de testes, `curl -o /dev/null localhost:3000/export?month=2026-08`
enquanto observa `VmHWM` em `/proc/<pid>/status`; o pico passa de 1 GB.

**Correção:** trocar por *cursor* + *stream* (`pg-query-stream` [F1]) encadeado a um *transform* CSV,
como já faz a exportação de auditoria em `src/api/audit/stream.ts:15-48`.
**Critério de aceite:** pico de RSS ≤ 100 MB na mesma reprodução, n = 10, mediana.

---

### P-02 · Consulta N+1 para o nome do cliente — **Alta**

`src/api/export/handler.ts:31-35`

Cada linha chama `getCustomerName(id)`, uma consulta por pedido: 180 mil *round-trips* seguram a
conexão do *pool* pelos 9 s da exportação.

**Reprodução:** ligar `log_statement = 'all'` no Postgres local e exportar um mês; o log mostra
uma consulta `SELECT name FROM customers` por pedido.

**Correção:** `JOIN` com `customers` na consulta principal.
**Critério de aceite:** o mesmo log mostra **uma** consulta por exportação.

---

## 5. Achados de usabilidade e acessibilidade

Fora do escopo desta análise — a rota não tem interface.

---

## 6. Backlog priorizado

> Ordenado por (impacto no usuário × alcance) ÷ esforço.

| Pri | Item | Esforço | Alcance | Tipo |
|---|---|---|---|---|
| 1 | **P-02** — `JOIN` no lugar do N+1 | XS | Toda exportação | Perf |
| 2 | **P-01** — *cursor* + *stream* | S | Toda exportação | Perf/Arquitetura |

Aplicar um por vez e medir de novo entre eles com o protocolo da seção 2 — o P-02 muda o tempo, o
P-01 muda a memória, e medir os dois juntos esconde qual resolveu o quê.

---

## 7. Riscos e o que falta verificar

1. **Nenhuma medição foi feita com concorrência.** Antes de liberar exportações simultâneas,
   rodar 5 requisições paralelas e confirmar o pico total ≤ 500 MB.
2. **O *stream* muda o erro no meio da exportação.** Hoje falha antes de enviar o primeiro byte;
   com *stream* o cliente recebe um CSV truncado. Precisa de um marcador de fim de arquivo.

---

## 8. Fontes consultadas

| # | Fonte | Tipo | Versão | Consultada em | Sustenta |
|---|---|---|---|---|---|
| F1 | [`pg-query-stream` — README](https://github.com/brianc/node-postgres/tree/master/packages/pg-query-stream) | Doc oficial | 4.7.0 | 2026-09-23 | Correção de P-01 |

---

> Nada foi medido em produção. Os números vêm de 10 execuções locais no branch `main` (commit
> `9f3e21a`), com o protocolo da seção 2; o teste com concorrência está pendente na seção 7.
