---
name: github-repo-setup
description: Inicializa e padroniza os arquivos de documentação e comunidade de um repositório GitHub (README em um ou dois idiomas, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, SUPPORT, CHANGELOG, templates de Issue e Pull Request, FUNDING.yml e CODEOWNERS), de forma interativa, com badges e banners exclusivamente do shieldcn.dev. Use quando o usuário pedir para gerar a documentação de um projeto, criar ou traduzir um README, escolher uma licença ou configurar os arquivos da comunidade de um repositório. NÃO use para escrever documentação técnica interna, comentários de código, docstrings, sites de documentação (Docusaurus, MkDocs) ou para configurar workflows de CI/CD.
compatibility: >-
  Requires outbound network access to api.github.com (license text),
  www.contributor-covenant.org (code of conduct) and shieldcn.dev (badge
  validation). Without network, LICENSE and CODE_OF_CONDUCT must be skipped
  rather than written from memory, and validation runs offline only.
---

# GitHub Repository Documentation Setup

Guie o usuário de forma interativa. Tudo o que sai desta skill vem de três
fontes, nesta ordem: **o código do projeto**, **as respostas do usuário** e
**os modelos desta skill**. Nunca invente o motivo do projeto, contatos,
perfis, donos de código nem texto de licença.

## Proibido

- Usar modelos de README ou de arquivos da comunidade de outros lugares
  (readme.so, makeareadme, awesome-readme, "best-README-template" etc.). Só
  os modelos de `templates/`.
- Usar imagens de img.shields.io, badgen, forthebadge, contrib.rocks,
  github-readme-stats, skillicons ou star-history, ou o domínio
  `www.shieldcn.dev`. Badges, banner e contribuidores vêm só de
  `https://shieldcn.dev` (ver `references/shieldcn.md`). A única exceção é
  o banner: um banner próprio do projeto, ou fornecido pelo usuário, pode
  substituir o do shieldcn, mas só quando o usuário escolher isso.
- **Colocar dois idiomas no mesmo README**, seja em seções uma embaixo da
  outra, títulos bilíngues, `<details>` ou colunas. Cada idioma tem o seu
  arquivo (ver `references/idiomas.md`).
- Escrever LICENSE ou CODE_OF_CONDUCT de memória.
- Sobrescrever um arquivo existente sem perguntar.

## Fase 0: Contexto

1. `git remote get-url origin` → extraia `{{OWNER}}` e `{{REPO}}`, mantendo a
   caixa original. Sem remote do GitHub, pergunte ao usuário.
2. Descubra a branch padrão (`git symbolic-ref refs/remotes/origin/HEAD`, ou
   `main` se o usuário confirmar) → `{{DEFAULT_BRANCH}}`.
3. Liste quais destes arquivos já existem: `README*.md`, `LICENSE*`,
   `COPYING`, `CHANGELOG.md` e, na raiz, em `.github/` ou `docs/`,
   `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`,
   `FUNDING.yml`, `CODEOWNERS`, `ISSUE_TEMPLATE/`, `pull_request_template.md`.
4. Procure o logo e um banner próprios do projeto, seguindo "Logo do banner"
   e "Banner próprio do projeto" em `references/shieldcn.md`.

## Fase 1: Coleta

1. Pergunte, em **uma única interação de múltipla escolha**, quais arquivos
   gerar:
   - README
   - LICENSE
   - CONTRIBUTING.md
   - CODE_OF_CONDUCT.md
   - SECURITY.md
   - SUPPORT.md
   - CHANGELOG.md
   - Templates de Issue (bug, feature e `config.yml`) e de Pull Request
   - FUNDING.yml
   - CODEOWNERS
2. Se algum arquivo escolhido já existir, pergunte, arquivo por arquivo:
   **sobrescrever**, **mesclar** (manter o conteúdo e completar com o modelo)
   ou **pular**.
3. Depois, numa **única mensagem**, pergunte só o que os arquivos escolhidos
   exigem, e **espere a resposta** antes de gerar qualquer coisa:

   | Arquivo | Pergunta |
   |---|---|
   | README | Qual foi o motivo da criação do projeto? (é subjetivo, não deduza) |
   | README | Idioma: só PT, só EN ou ambos? Se ambos, qual é o principal (fica no `README.md`)? |
   | README | Banner: o shieldcn do template, o que já existe no projeto (se houver) ou outro que o usuário fornece (caminho ou URL)? A opção de um banner próprio é sempre oferecida. |
   | README | Só se houver mais de um logo candidato, ou variantes de tema: qual arquivo usar e qual é o do tema escuro? |
   | LICENSE | Qual licença (MIT, Apache-2.0, GPL-3.0…)? Quem é o titular do copyright? (sugira `git config user.name`) |
   | CODE_OF_CONDUCT | Qual canal recebe denúncias (e-mail ou link)? |
   | SECURITY | Reporte privado pelo GitHub Security Advisories, ou um e-mail? |
   | FUNDING.yml | Quais plataformas e usuários de patrocínio? |
   | CODEOWNERS | Quem são os donos (`@usuario` ou `@org/time`) e de quais caminhos? |

   Sem README escolhido, o idioma dos outros arquivos também é perguntado
   (PT ou EN).

## Fase 2: README

Leia `references/idiomas.md` e `references/shieldcn.md` antes de começar.

1. Use `templates/<idioma>/README.md` (`pt-BR` ou `en`). Com dois idiomas,
   gere **dois arquivos**: o principal em `README.md` e o outro em
   `README.pt-BR.md` ou `README.en.md`, cada um a partir do modelo do próprio
   idioma, com a linha de troca de idioma. Com um idioma, apague a linha de
   troca.
2. Substitua todos os `{{...}}`. Siga cada comentário `<!-- TEMPLATE: ... -->`
   e **apague o comentário** depois.
3. **Sobre:** descreva o projeto a partir do código lido: o que é, o que
   resolve e as ferramentas principais.
4. **Motivo:** o texto do usuário, literal no idioma dele e fielmente
   traduzido no outro. Nunca invente.
5. **Badges de tecnologia:** só tecnologias presentes no código, de 3 a 6,
   no formato de `references/shieldcn.md`.
6. **Requisitos:** cada ferramenta com o link oficial de download e a versão
   lida do projeto (`.nvmrc`/`engines`, `.python-version`/`requires-python`,
   diretiva `go` do `go.mod`, `rust-toolchain.toml`, `.tool-versions`, ou a
   tag de imagem em `compose.yaml`/`Dockerfile`, como `postgres:17`). Sem
   versão declarada, não chute uma. Ferramenta necessária só para um dos
   métodos de instalação leva a indicação `(opção Docker)` ou
   `(execução local)` / `(Docker option)` ou `(local execution)`.
7. **Instalação:** se houver Docker (`Dockerfile`/`compose.yaml`) **e**
   execução nativa, documente os dois métodos. Os comandos saem dos scripts
   reais do projeto.
8. **Variáveis de ambiente:** leia `.env.example`, `.env.sample` ou
   `.env.template` e monte a tabela. Sem nenhum deles, apague a seção.
9. **Licença:** cite o nome e linke o arquivo. Sem licença no repositório,
   pergunte se a seção fica ou sai.
10. **Banner, por último:** depois de ler o projeto inteiro, escreva uma
    descrição de uma linha e use-a como `subtitle` do banner (`{{TAGLINE_URL}}`,
    com espaços como `+`). `{{PROJECT_TITLE}}` é o nome legível do projeto.
    - **Logo próprio:** vai dentro do banner pela URL raw, se ela responder
      200 sem login. Senão (repositório privado, ou arquivo ainda não enviado),
      o banner sai sem logo e o logo aparece como imagem relativa logo abaixo
      dele. Veja "Logo do banner" em `references/shieldcn.md`.
    - **Banner do projeto ou do usuário:** substitui o bloco do banner
      shieldcn. Badges e contribuidores continuam no shieldcn.

## Fase 3: LICENSE

Siga `references/licencas.md`: texto do campo `body` de
`https://api.github.com/licenses/<chave-minúscula>`, substituindo **só** os
marcadores da tabela daquela licença. Em Apache-2.0 e GPL, os marcadores do
apêndice **ficam intactos**.

## Fase 4: Arquivos da comunidade

Só o README é duplicado por idioma. Os demais vêm **uma vez**, de
`templates/<idioma principal>/`.

| Arquivo | Fonte | Destino |
|---|---|---|
| CONTRIBUTING.md, SECURITY.md, SUPPORT.md | `templates/<idioma>/` | `.github/` |
| CHANGELOG.md | `templates/<idioma>/` (Keep a Changelog 1.1.0) | raiz |
| Templates de issue | `templates/<idioma>/ISSUE_TEMPLATE/*.yml` | `.github/ISSUE_TEMPLATE/` |
| Template de PR | `templates/<idioma>/pull_request_template.md` | `.github/` |
| FUNDING.yml, CODEOWNERS | `templates/` | `.github/` |
| CODE_OF_CONDUCT.md | `https://www.contributor-covenant.org/version/3/0/code_of_conduct/code_of_conduct.md` | `.github/` |

- **CODE_OF_CONDUCT:** baixe o texto oficial do Contributor Covenant 3.0
  (sempre em inglês; as traduções oficiais ficam em
  `https://www.contributor-covenant.org/translations`). Substitua só o
  `**[NOTE: describe your means of reporting here.]**` pelo canal informado.
  Mantenha o outro `[NOTE: ...]` (processo de aplicação) e avise o usuário
  para revisá-lo.
- **Opcional nos modelos:** trechos condicionais estão marcados com
  `TEMPLATE:`. Mantenha-os só quando a condição for verdadeira no projeto
  (Discussions habilitado, Conventional Commits em uso, comando de teste
  existente…). Na dúvida, pergunte.
- **Links entre arquivos:** um link para CONTRIBUTING, CODE_OF_CONDUCT ou
  SECURITY só fica se esse arquivo for gerado agora ou já existir no
  repositório. Com um subconjunto de arquivos, apague os itens que apontam
  para os que faltam.
- **Labels:** os templates de issue usam `bug` e `enhancement`, que são
  labels padrão do GitHub. Se o repositório não tiver essas labels
  (`gh label list`, quando disponível), avise o usuário.
- **CHANGELOG:** sem tags/releases, deixe só `[Unreleased]`. Não invente
  histórico.

## Fase 5: Validação e entrega

1. Grave os arquivos.
2. Na raiz do projeto, rode o validador desta skill sobre os Markdown gerados:

   ```sh
   python3 <diretório-desta-skill>/scripts/validate_readme.py --online README*.md <demais .md gerados>
   ```

   Passe só os `.md` que foram gerados nesta execução (por exemplo,
   `.github/*.md` e `CHANGELOG.md`, quando existirem). Se o usuário escolheu
   um banner hospedado fora do shieldcn e do GitHub, acrescente
   `--allow-host <host-do-banner>`.

   Sem rede, rode sem `--online` e avise que os badges não foram conferidos.
3. Corrija cada linha apontada e rode de novo até sair sem erros.
4. Encerre com uma mensagem simpática, listando os arquivos criados e o que
   o usuário ainda precisa revisar (por exemplo, o processo de aplicação do
   CODE_OF_CONDUCT).
