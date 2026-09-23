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

  <h3>BGLuis Agent Skills</h3>
  Coleção de habilidades autorais, modulares e portáteis para agentes de inteligência artificial.
</div>

---

# 📖 Sobre

Este repositório reúne as **Agent Skills autorais criadas e mantidas por [@BGLuis](https://github.com/BGLuis)**, projetadas sob a especificação aberta [agentskills.io](https://agentskills.io). 

Cada habilidade foi desenvolvida para solucionar gargalos frequentes de precisão, contextualização e autonomia em agentes de codificação como **Claude Code**, **Gemini CLI / Antigravity**, **GitHub Copilot**, **Cursor** e outros.

### Pilares de Design:
1. **Portabilidade Universal:** Descreve ações sem acoplar a nomes específicos de ferramentas de uma IA proprietária.
2. **Divulgação Progressiva:** Mantém o `SKILL.md` enxuto; heurísticas e referências longas são carregadas sob demanda a partir de `references/`.
3. **Limites Negativos Estritos:** Cada gatilho semântico define expressamente o que a skill **NÃO** deve fazer, prevenindo superativações e falsos positivos.

---

# 📋 Motivo

O projeto nasceu da necessidade de centralizar, versionar e compartilhar procedimentos de engenharia de alta qualidade para assistentes de IA em uma única fonte da verdade (`Single Source of Truth`).

---

# 💻 Como Instalar e Usar

### Método 1: Via CLI Oficial da Comunidade (`npx skills`)

Compatível automaticamente com Claude Code, Gemini CLI, Copilot, Cursor, Zed, Amp, Cline, etc.:

```sh
# Instalar interativamente (escolha quais agentes e quais skills ativar):
npx skills add BGLuis/skills

# Ou instalar apenas uma skill específica (ex: docker-optimizer):
npx skills add BGLuis/skills --skill docker-optimizer
```

---

### Método 2: Via Script Instalador Universal (`install.sh`)

Ideal para ambientes Linux e macOS com criação e atualização automática de links simbólicos:

```sh
# Instalação rápida via curl:
curl -fsSL https://raw.githubusercontent.com/BGLuis/skills/main/install.sh | bash

# Ou instalação local após clonar o repositório:
git clone https://github.com/BGLuis/skills.git
cd skills
./install.sh
```

---

# 📦 Catálogo de Skills

| Skill | Descrição & Gatilho Principal | Foco & Recursos |
| :--- | :--- | :--- |
| [`create-skill`](./skills/create-skill/SKILL.md) | Cria, audita, padroniza e repara Agent Skills contra o *composition cliff*. | Meta-skill, arquitetura hub+symlink, portabilidade entre Claude/Gemini/Copilot. |
| [`docker-optimizer`](./skills/docker-optimizer/SKILL.md) | Gera, revisa e ajusta `Dockerfile` e `compose.yaml`: imagens mínimas, builds com cache, containers endurecidos e máxima performance com poucos recursos. | Exemplos validados (Node, Python/uv, Go, Rust, Java) com números medidos, tuning de runtime sob limites (heap, workers, GOMAXPROCS), hardening de compose e cache em CI. |
| [`find-docs`](./skills/find-docs/SKILL.md) | Consulta documentações, APIs e SDKs atualizados em tempo real via Context7. | Evita alucinações de bibliotecas modernas, com limites negativos rigorosos. |
| [`github-actions`](./skills/github-actions/SKILL.md) | Constrói e audita pipelines de CI/CD em `.github/workflows/`. | Segurança (permissões mínimas, pinned hashes), cache de dependências e paralelismo. |
| [`github-repo-setup`](./skills/github-repo-setup/SKILL.md) | Padronização interativa da documentação de repositórios (README, LICENSE, etc.). | Baseado no padrão de excelência `bgluis-template` e badges `shieldcn.dev`. |
| [`technical-report`](./skills/technical-report/SKILL.md) | Elabora relatórios técnicos estruturados em `docs/reports/`. | Análise, auditoria e pós-implementação 100% ancorados em evidências `arquivo:linha`. |
| [`testing-strategy`](./skills/testing-strategy/SKILL.md) | Cria e audita suítes de teste para verificação de intenção real de regras de negócio. | Doutrina agnóstica de testes com referências para JS/TS, Python, Go e Rust. |

---

# 🤝 Contribuidores

<a href="https://github.com/bgluis/skills/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=bgluis/skills"/>
</a>

---

# 📄 Licença

Distribuído sob a licença [MIT](./LICENSE).
