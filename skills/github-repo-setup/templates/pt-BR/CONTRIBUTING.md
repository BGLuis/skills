# Contribuindo com o {{PROJECT_TITLE}}

Obrigado pelo interesse em contribuir! Este guia explica como propor mudanças.

## Código de conduta

<!-- TEMPLATE: só se CODE_OF_CONDUCT.md for gerado ou já existir; senão apague a seção. -->
Ao participar, você concorda em seguir o nosso [Código de Conduta](CODE_OF_CONDUCT.md).

## Reportando bugs e sugerindo melhorias

- Procure nas [issues](https://github.com/{{OWNER}}/{{REPO}}/issues) se o assunto já foi aberto.
- Se não foi, abra uma issue usando o modelo adequado (bug ou sugestão).
<!-- TEMPLATE: só se SECURITY.md for gerado ou já existir; senão apague o item abaixo. -->
- Vulnerabilidades de segurança **não** devem ser abertas como issue: veja a [Política de Segurança](SECURITY.md).

## Preparando o ambiente

Siga a seção "Como iniciar" do [README](../README.md) para instalar e rodar o projeto.

## Fluxo de contribuição

1. Faça um fork do repositório e crie uma branch a partir de `{{DEFAULT_BRANCH}}`.
2. Faça as mudanças em commits pequenos e com mensagens claras.
3. Rode as verificações abaixo antes de abrir o Pull Request.
4. Abra o Pull Request para `{{DEFAULT_BRANCH}}` preenchendo o modelo.

<!-- TEMPLATE: mantenha se houver configuração de Conventional Commits (commitlint, commit-check.toml, cz). Se só o histórico de commits seguir o formato, pergunte ao usuário. Senão apague a seção. -->
## Padrão de commits

Este projeto usa [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/): `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

<!-- TEMPLATE: só comandos que existem no projeto (scripts do package.json, Makefile, justfile, pyproject etc.). Sem comando encontrado, apague a linha; sem nenhum, apague a seção. -->
## Verificações

```sh
{{LINT_COMMAND}}
{{TEST_COMMAND}}
```
