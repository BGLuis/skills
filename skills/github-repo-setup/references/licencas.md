# Licenças — texto oficial, marcadores certos

## Buscar o texto

```sh
curl -s https://api.github.com/licenses/<chave>
```

- A chave é **minúscula**. Chaves disponíveis: `agpl-3.0`, `apache-2.0`,
  `bsd-2-clause`, `bsd-3-clause`, `bsl-1.0`, `cc0-1.0`, `epl-2.0`, `gpl-2.0`,
  `gpl-3.0`, `lgpl-2.1`, `mit`, `mpl-2.0`, `unlicense` (`curl -s https://api.github.com/licenses` lista todas).
- Use o campo `body` do JSON, sem mexer em nada além dos marcadores da tabela abaixo.
- Sem rede, **não gere a licença**. Avise o usuário. Nunca escreva o texto de memória.

## Marcadores: o que substituir

Substitua **só** o que está na coluna "Substituir". Os marcadores da coluna
"Não tocar" fazem parte das instruções da própria licença (apêndice "How to
apply"), são para o cabeçalho dos arquivos-fonte e têm de ficar como estão.

| Chave | Substituir | Não tocar |
|---|---|---|
| `mit`, `bsd-2-clause`, `bsd-3-clause` | `[year]` → ano atual; `[fullname]` → titular | — |
| `apache-2.0` | nada | `[yyyy]`, `[name of copyright owner]` |
| `gpl-2.0`, `gpl-3.0`, `agpl-3.0`, `lgpl-2.1` | nada | `<year>`, `<name of author>`, `<program>` e demais `<...>` |
| `mpl-2.0`, `epl-2.0`, `bsl-1.0`, `cc0-1.0`, `unlicense` | nada | — |

Para uma chave fora da tabela, abra o `body`, mostre ao usuário os marcadores
encontrados e **pergunte** o que fazer.

O titular (`[fullname]`) é confirmado com o usuário na Fase 1. Sugira
`git config user.name`, mas não use sem confirmação.

## Nome do arquivo

O campo `implementation` do JSON diz o nome convencional. Quase todas sugerem
`LICENSE`; `gpl-3.0` sugere `COPYING`. Nesse caso, pergunte ao usuário se prefere
`COPYING` (convenção GNU) ou `LICENSE` (detectado pelo GitHub nos dois casos).

## Badge e seção no README

O badge `github/license` lê a licença detectada pelo GitHub. A seção
"Licença"/"License" do README cita o nome SPDX e linka o arquivo gerado
(`[MIT](LICENSE)`).
