# shieldcn — única fonte de imagens do README

Todo badge, banner e grade de contribuidores vem de `https://shieldcn.dev`.
Documentação oficial: <https://shieldcn.dev/docs> · repositório `jal-co/shieldcn`.

## Proibido

| Não use | Use no lugar |
|---|---|
| `img.shields.io`, `badgen.net`, `forthebadge.com`, `badge.fury.io` | `shieldcn.dev/badge/...` ou o provedor shieldcn equivalente |
| `contrib.rocks`, `contributors-img.web.app` | `shieldcn.dev/contributors/{owner}/{repo}.svg` |
| `github-readme-stats`, `skillicons.dev`, `star-history.com`, `api.star-history.com` | nada: fora do padrão desta skill |
| `www.shieldcn.dev` | `shieldcn.dev` (o `www` responde 308) |
| Modelos de README de readme.so, makeareadme.com, awesome-readme, "best-README-template" | `templates/<idioma>/README.md` desta skill |

Imagens próprias do projeto (screenshots, logo) podem ficar em caminho relativo
no repositório ou em anexos do GitHub (`github.com/user-attachments/...`).
Um banner alternativo escolhido pelo usuário também é permitido; veja "Banner
próprio do projeto".

## Formatos de URL

```text
https://shieldcn.dev/github/{metrica}/{owner}/{repo}.svg   badge do GitHub
https://shieldcn.dev/badge/{label}-{mensagem}-{hex}.svg    badge estático
https://shieldcn.dev/header/{preset}.svg?title=...         banner
https://shieldcn.dev/contributors/{owner}/{repo}.svg       grade de contribuidores
```

Métricas do GitHub usadas no template: `stars`, `forks`, `watchers`,
`contributors`, `license`. Existem também `release`, `ci`, `issues`,
`open-prs`, `last-commit` (a doc aceita também a ordem `/github/{owner}/{repo}/{metrica}`,
mas o template usa sempre a ordem acima).

Texto do badge estático: `-` separa os campos, `_` ou `%20` viram espaço, `--`
é um hífen literal e `__` é um underscore literal. Exemplo: `Claude_Code` →
"Claude Code".

## Parâmetros

| Parâmetro | Valores | Uso no template |
|---|---|---|
| `variant` | `default`, `secondary`, `outline`, `ghost`, `destructive`, `branded` | `secondary` nas métricas, `ghost` na licença, `branded` nas tecnologias |
| `size` | `xs`, `sm`, `default`, `lg` | `sm` |
| `mode` | `light`, `dark` | um de cada dentro de `<picture>` |
| `theme` | `zinc`, `slate`, `blue`, `green`, `rose`, `orange`, `violet`, `purple`, `cyan`, `emerald` | `emerald` em contributors |
| `logo` | slug do Simple Icons, `ri:Nome`, `lu:Nome`, `false` | slug da tecnologia |

## Claro/escuro com `<picture>`

O `mode` só muda badges cujas cores vêm do tema (`default`, `secondary`,
`outline`, `ghost`, `branded` **sem** cor fixa). Esses vão em `<picture>`: o
`<source>` recebe `mode=dark`, o `<img>` de fallback recebe `mode=light`.

```html
<picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/github/stars/OWNER/REPO.svg?variant=secondary&size=sm&mode=dark" /><img alt="GitHub Stars" src="https://shieldcn.dev/github/stars/OWNER/REPO.svg?variant=secondary&size=sm&mode=light" /></picture>
```

Badge com cor fixa (os de tecnologia, `Language-Nome-HEX`) é igual nos dois
modos: fica como `![alt](url)` simples, sem `<picture>`.

Dentro de HTML, `&` pode ficar literal; o GitHub aceita as duas formas.

## Banner (header)

```text
https://shieldcn.dev/header/graph.svg?title=Nome+Do+Projeto&subtitle=Descrição+de+uma+linha&align=left&font=geist-mono&mode=dark
```

- Espaço vira `+` em `title` e `subtitle`; acentos podem ir literais ou em `%XX`.
  **Vírgula vira `%2C`:** dentro de `srcset`, uma vírgula solta separa imagens
  alternativas e corta a URL.
- Presets: `surface`, `gradient`, `dots`, `grid`, `graph`, `glow`, `transparent`.
  O template usa `graph`, como o README do próprio shieldcn.

### Logo do banner

O logo é decidido nesta ordem:

1. **Logo próprio do projeto.** Procure arquivos de imagem com `logo` ou `icon`
   no nome (`.svg`, `.png`, `.webp`, `.jpg`) na raiz, em `assets/`, `docs/`,
   `public/`, `static/`, `images/`, `img/` e `.github/`, ignorando
   `node_modules/`, `vendor/` e pastas de build. Com mais de um candidato,
   pergunte qual usar. Favicon não conta como logo.
2. **Sem logo próprio:** um slug do Simple Icons só se houver um ícone óbvio
   (a linguagem principal, por exemplo). Nunca invente um slug. Na dúvida,
   deixe o banner sem logo.

Com logo próprio, teste se a versão *raw* dele está acessível sem login:

```sh
curl -s -o /dev/null -w '%{http_code}' https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{caminho}
```

| Resultado | O que fazer |
|---|---|
| `200` (repositório público, arquivo já no GitHub) | `logo=` com essa URL raw, codificada (`%3A`, `%2F`…), dentro do banner |
| Qualquer outro (privado, ou arquivo ainda não enviado) | banner **sem** `logo=` e o logo como imagem relativa logo abaixo dele (bloco abaixo) |

```html
<p align="center"><img alt="{{PROJECT_TITLE}} logo" src="{{LOGO_PATH}}" width="96" /></p>
```

- Use sempre a URL `raw.githubusercontent.com`. Com o link `github.com/.../blob/...`
  o logo some sem erro. O validador pega isso pelo `"hasLogo": false`.
- Com variantes de tema (`logo-dark.svg`/`logo-light.svg`, `logo-white.svg`),
  pergunte ao usuário qual arquivo é para o tema escuro. O nome é ambíguo:
  `logo-dark` pode ser "logo escuro" ou "logo para tema escuro". O `<source>`
  (`mode=dark`) recebe o arquivo do tema escuro, e o `<img>` (`mode=light`)
  recebe o outro.
- Não use `data:` URI com o logo embutido: um SVG de 11 KB vira uma URL de
  cerca de 15 mil caracteres.
- O shieldcn encaixa o logo num quadrado. Com um logo largo (proporção acima
  de 2:1, como um logotipo com o nome escrito), avise o usuário que ele vai
  ficar pequeno no banner.

### Banner próprio do projeto

Se o projeto já tiver uma imagem de capa (arquivo com `banner`, `cover`,
`hero`, `header` ou `social-preview` no nome, ou uma imagem grande no topo do
README atual), **pergunte ao usuário** qual banner usar:

1. o banner shieldcn deste template;
2. o banner que já existe no projeto;
3. outro banner, que o usuário fornece (caminho no repositório ou URL).

Mesmo sem banner no projeto, a pergunta da Fase 1 oferece a opção 3. Com a
opção 2 ou 3, o banner fica **no lugar** do `<p>` do header shieldcn, com
`<img alt="{{PROJECT_TITLE}}" src="..." />` centralizado. Badges e
contribuidores continuam vindo do shieldcn.

Se o banner escolhido for uma URL fora do shieldcn e do GitHub, rode o
validador com `--allow-host <host>` para esse host. Nunca libere hosts
proibidos por conta própria: é o usuário quem escolhe esse banner.

## Badges de tecnologia

Um badge por linguagem, framework ou ferramenta **detectada nos arquivos do
projeto** (lockfiles, `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`,
`Dockerfile` etc.). Nunca inclua tecnologia que não aparece no código.

```text
https://shieldcn.dev/badge/Language-TypeScript-3178C6.svg?logo=typescript&variant=branded&size=sm
```

- `{label}`: categoria (`Language`, `Framework`, `Runtime`, `Database`, `Tool`).
- `{hex}` e `logo`: cor e slug oficiais do [Simple Icons](https://simpleicons.org).
  Não chute: um slug inexistente não dá erro, só some o ícone (o validador pega).
- Mantenha a linha de badges enxuta: de 3 a 6 tecnologias de maior sinal.

Se o projeto tiver Node disponível, `npx shieldcn-cli --format json` detecta a
stack e já devolve URLs shieldcn. Use a saída como insumo, depois ajuste ao
formato do template (`size=sm`, `<picture>` nos badges do GitHub).

## Como o shieldcn sinaliza erro

Tudo responde HTTP 200, até com repositório inexistente. Por isso a checagem é
pelo conteúdo, e é o que `scripts/validate_readme.py --online` faz:

| Caso | Sinal |
|---|---|
| Badge com repositório ou pacote inválido | `.json` do mesmo caminho devolve `"error": true` |
| `logo=` inexistente em badge | o SVG é idêntico, byte a byte, ao mesmo badge com `logo=false` |
| `logo=` inexistente em header | `.json` do header devolve `"hasLogo": false` |
| Contributors de repositório inexistente | HTTP 404 |
