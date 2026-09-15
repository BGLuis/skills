<div align="center">

<!-- Badges de Status do GitHub -->
![GitHub Stars](https://www.shieldcn.dev/github/stars/bgluis/skills.svg?variant=secondary&size=sm)
![GitHub Forks](https://www.shieldcn.dev/github/forks/bgluis/skills.svg?variant=secondary&size=sm)
![Watchers](https://www.shieldcn.dev/github/watchers/bgluis/skills.svg?variant=secondary&size=sm)
![License](https://www.shieldcn.dev/github/license/bgluis/skills.svg?variant=ghost&size=sm)

<br/>

<!-- Badges das Tecnologias Utilizadas -->
![Agentskills](https://img.shields.io/badge/Standard-agentskills.io-blue?style=flat-square)
![Claude Code](https://img.shields.io/badge/Agent-Claude_Code-D97706?style=flat-square)
![Gemini CLI](https://img.shields.io/badge/Agent-Gemini_CLI-4285F4?style=flat-square)
![GitHub Copilot](https://img.shields.io/badge/Agent-GitHub_Copilot-181717?style=flat-square)
![Cursor](https://img.shields.io/badge/Agent-Cursor-000000?style=flat-square)

  <h3>Agent Skills Hub</h3>
  Coleção de habilidades modulares e portáteis para agentes de inteligência artificial.
</div>

---

# 📖 Sobre

Este repositório é um **Hub Central de Agent Skills** projetado sob a especificação aberta [agentskills.io](https://agentskills.io). Ele oferece um conjunto robusto de procedimentos, diretrizes e heurísticas projetadas para elevar a precisão de agentes de codificação como **Claude Code**, **Gemini CLI / Antigravity**, **GitHub Copilot**, **Cursor** e outros.

As habilidades seguem três princípios estruturais inegociáveis:
1. **Portabilidade Universal:** Sem acoplamento a nomes de ferramentas de agentes específicos (ex: `read_file` vs `view_file`).
2. **Divulgação Progressiva:** O `SKILL.md` principal carrega apenas a cognição imediata; guias e heurísticas extensas são isolados na pasta `references/`.
3. **Limites Negativos Estritos:** Cada gatilho semântico (`description`) define explicitamente quando a skill **NÃO** deve ser acionada, eliminando falsos positivos e superativações.

---

# 📋 Motivo

O projeto nasceu da necessidade de unificar e versionar as habilidades dos agentes em uma única fonte da verdade (`Single Source of Truth`). Em vez de manter cópias divergentes em diretórios de cada agente (`~/.claude/skills`, `~/.gemini/skills`, `.copilot/skills`), este hub centraliza o ciclo de vida das skills e permite distribuição transparente via links simbólicos ou comandos simples de ecossistema.

---

# 💻 Como Instalar e Usar

Você pode instalar as skills no seu computador ou projeto através de dois métodos simples:

### Método 1: Via CLI Oficial da Comunidade (`npx skills`)

Compatível automaticamente com Claude, Gemini, Copilot, Cursor, Zed, Amp, Cline e outros:

```sh
# Instalar interativamente (escolha quais agentes e quais skills ativar):
npx skills add BGLuis/skills

# Ou instalar apenas uma skill específica (ex: docker-optimizer):
npx skills add BGLuis/skills --skill docker-optimizer
```

---

### Método 2: Via Script Instalador Universal (`install.sh`)

Ideal para ambientes Linux e macOS com automação de links simbólicos:

```sh
# Instalação rápida via curl (detecta seus agentes automaticamente):
curl -fsSL https://raw.githubusercontent.com/BGLuis/skills/main/install.sh | bash

# Ou instale apenas o pacote autoral core (@BGLuis):
curl -fsSL https://raw.githubusercontent.com/BGLuis/skills/main/install.sh | bash -s -- --core
```

#### Instalação Manual via Git Clone:
```sh
git clone https://github.com/BGLuis/skills.git ~/.agents
cd ~/.agents
./install.sh
```

---

# 📦 Catálogo de Skills

### 🚀 Skills Autorais Core (@BGLuis)

| Skill | Descrição & Gatilho Principal | Foco & Recursos |
| :--- | :--- | :--- |
| [`create-skill`](./skills/create-skill/SKILL.md) | Cria, audita, padroniza e repara Agent Skills contra o *composition cliff*. | Meta-skill, arquitetura hub+symlink, portabilidade entre Claude/Gemini/Copilot. |
| [`docker-optimizer`](./skills/docker-optimizer/SKILL.md) | Otimiza `Dockerfile` e `docker-compose.yml` para alta performance e segurança. | Multi-stage builds, cache mounts, redução drástica de imagem e relatórios antes/depois. |
| [`find-docs`](./skills/find-docs/SKILL.md) | Consulta documentações, APIs e SDKs atualizados em tempo real via Context7. | Evita alucinações de bibliotecas modernas, com limites negativos rigorosos. |
| [`github-actions`](./skills/github-actions/SKILL.md) | Constrói e audita pipelines de CI/CD em `.github/workflows/`. | Segurança (permissões mínimas, pinned hashes), cache de dependências e paralelismo. |
| [`github-repo-setup`](./skills/github-repo-setup/SKILL.md) | Padronização interativa da documentação de repositórios (README, LICENSE, etc.). | Baseado no padrão de excelência `bgluis-template` e badges `shieldcn.dev`. |
| [`technical-report`](./skills/technical-report/SKILL.md) | Elabora relatórios técnicos estruturados em `docs/reports/`. | Análise, auditoria e pós-implementação 100% ancorados em evidências `arquivo:linha`. |
| [`testing-strategy`](./skills/testing-strategy/SKILL.md) | Cria e audita suítes de teste para verificação de intenção real de regras de negócio. | Doutrina agnóstica de testes com referências para JS/TS, Python, Go e Rust. |

### 🌐 Ferramentas Curadas da Comunidade

O hub também inclui ferramentas essenciais curadas do ecossistema:
- [`impeccable`](./skills/impeccable/SKILL.md): Design system e polimento de interfaces frontend.
- [`systematic-debugging`](./skills/systematic-debugging/SKILL.md): Metodologia estrita para descoberta de causa-raiz antes de propor correções.
- [`grill-me`](./skills/grill-me/SKILL.md): Entrevista implacável para refinar ideias e arquiteturas.
- [`triage`](./skills/triage/SKILL.md): Máquina de estados para triagem de issues e PRs.
- [`microsoft-foundry`](./skills/microsoft-foundry/SKILL.md): Suite avançada para desenvolvimento de agentes Microsoft Foundry.
- [`find-skills`](./skills/find-skills/SKILL.md): Descoberta de novas skills no ecossistema aberto.

---

# 🤝 Contribuidores

<a href="https://github.com/bgluis/skills/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=bgluis/skills"/>
</a>

---

# 📄 Licença

Distribuído sob a licença [MIT](./LICENSE).
