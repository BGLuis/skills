---
name: github-repo-setup
description: Inicializa e padroniza os arquivos de documentação de um repositório GitHub (README, LICENSE, CONTRIBUTING, SECURITY, CHANGELOG, templates de Issue e Pull Request), de forma interativa. Use quando o usuário pedir para gerar a documentação de um projeto, criar um README, escolher uma licença ou configurar os arquivos da comunidade de um repositório. NÃO use para escrever documentação técnica interna, comentários de código, docstrings, sites de documentação (Docusaurus, MkDocs) ou para configurar workflows de CI/CD.
compatibility: >-
  Requires outbound network access to https://api.github.com to fetch official
  license text in Fase 3. Without internet access, license generation must be
  skipped rather than guessed from memory.
---

# GitHub Repository Documentation Setup

Quando esta skill for ativada, você é **obrigado** a guiar o usuário na criação da documentação de forma interativa. Nunca invente ou alucine o **motivo** do projeto. Siga rigorosamente o fluxo abaixo:

## Fase 1: Coleta de Preferências
1. Pergunte ao usuário, em uma única interação de múltipla escolha, quais arquivos ele deseja gerar:
   - `README`
   - `LICENSE`
   - `CONTRIBUTING.md`
   - `CODE_OF_CONDUCT.md`
   - `SECURITY.md`
   - `SUPPORT.md`
   - `CHANGELOG.md`
   - `Templates de Issue e Pull Request`
2. **SE o usuário marcou `README`:** Você **não pode prosseguir e criar o arquivo ainda**. Você DEVE escrever uma mensagem no chat (texto normal) perguntando ao usuário APENAS os seguintes itens e **aguardar a resposta dele**:
   - Qual foi o motivo da criação deste projeto? (Pois isso é subjetivo)
   - Qual o idioma desejado? (Apenas PT, Apenas EN, ou Ambos)

## Fase 2: Geração do README
Leia e utilize o template base em `templates/bgluis-template.md`, relativo ao diretório desta skill. Preste extrema atenção para garantir que o resultado fique perfeito:

1. **Título e Badges:** Substitua as tags `{{PROJECT_NAME}}` e `{{PROJECT_TITLE}}` pelo nome real do projeto. Inspecione o código (ex: package.json) para colocar as shields das linguagens usadas, mantendo o padrão `shieldcn.dev`.
2. **Sobre e Motivo:** Preencha a seção "📖 Sobre" lendo o código. Na seção "📋 Motivo", cole a explicação que o usuário te deu na Fase 1. NUNCA invente o motivo.
3. **Requisitos com Links:** Na seção de requisitos, SEMPRE adicione o link oficial para download ao lado da ferramenta. Ex: `[Docker](https://docs.docker.com/get-docker/)`, `[Node.js](https://nodejs.org/)`. Leia o `package.json` ou `.nvmrc` para sugerir a versão exata do Node recomendada.
4. **Instalação Abrangente (Múltiplos Métodos):** Se o projeto suportar Docker (`docker-compose.yml`) E execução nativa/manual (ex: node, npm start), você **DEVE** criar duas subseções e documentar os **DOIS** métodos, para que o leitor possa escolher.
5. **Variáveis de Ambiente:** Leia o arquivo `.env.example`. Se ele existir, crie uma tabela Markdown na seção `⚙️ Variáveis de Ambiente`. Se não existir, APAGUE essa seção do template.
6. **Subtítulo (A Descrição Curta):** Por último, após ter analisado todo o código do repositório para preencher as seções acima, crie você mesmo uma breve descrição inteligente e precisa de apenas 1 linha. Localize a frase exata `"Uma breve descrição de uma linha sobre o projeto."` (abaixo do título no template) e substitua por essa descrição curta que você gerou.

## Fase 3: Licença e Automações da Comunidade
- **Licença**: Se selecionada, pergunte ao usuário qual ele quer (MIT, Apache-2.0, GPL-3.0, etc). DEPOIS, busque `https://api.github.com/licenses/<sigla>` e pegue o campo `body` do JSON. Substitua o ano e nome. **NUNCA** adivinhe o texto da licença da sua memória.
- **Templates**: Se selecionado, crie `bug_report.yml` e `feature_request.yml` em `.github/ISSUE_TEMPLATE/` e crie um `.github/pull_request_template.md` robusto.

## Fase 4: Finalização
Grave os arquivos no disco. Quando tudo terminar, informe o usuário com uma mensagem simpática!
