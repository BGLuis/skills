<div align="center">

<!-- Badges de Status do GitHub -->
![GitHub Stars](https://shieldcn.dev/github/stars/BGLuis/skills.svg?variant=secondary&size=sm)
![GitHub Forks](https://shieldcn.dev/github/forks/BGLuis/skills.svg?variant=secondary&size=sm)
![Watchers](https://shieldcn.dev/github/watchers/BGLuis/skills.svg?variant=secondary&size=sm)
![License](https://shieldcn.dev/github/license/BGLuis/skills.svg?variant=ghost&size=sm)

<br/>

<!-- Badges das Tecnologias Utilizadas -->
![Agentskills](https://shieldcn.dev/badge/Standard-agentskills.io-blue.svg?logo=false&variant=secondary&size=sm)
![Claude Code](https://shieldcn.dev/badge/Agent-Claude_Code-D97706.svg?logo=claude&variant=branded&size=sm)
![Gemini CLI](https://shieldcn.dev/badge/Agent-Gemini_CLI-4285F4.svg?logo=googlegemini&variant=branded&size=sm)
![GitHub Copilot](https://shieldcn.dev/badge/Agent-GitHub_Copilot-181717.svg?logo=githubcopilot&variant=branded&size=sm)
![Cursor](https://shieldcn.dev/badge/Agent-Cursor-000000.svg?logo=cursor&variant=branded&size=sm)

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

### Método 3: Baixar o ZIP da Release

Cada [release](https://github.com/BGLuis/skills/releases/latest) traz `all-skills.zip` (todas as skills) e um `<skill>.zip` por skill, sem precisar de git, Node ou `curl | bash`. Os nomes não levam versão, então o link `latest/download` é estável:

```sh
# Todas as skills (cada uma vira uma pasta em ~/.claude/skills):
curl -fsSLO https://github.com/BGLuis/skills/releases/latest/download/all-skills.zip
unzip all-skills.zip -d ~/.claude/skills

# Ou só uma skill (ex: docker-optimizer):
curl -fsSLO https://github.com/BGLuis/skills/releases/latest/download/docker-optimizer.zip
unzip docker-optimizer.zip -d ~/.claude/skills
```

> A `technical-issues` depende da `technical-report`: instale as duas juntas ao usar ZIPs individuais.

---

# 📦 Catálogo de Skills

| Skill | Descrição & Gatilho Principal | Foco & Recursos |
| :--- | :--- | :--- |
| [`create-skill`](./skills/create-skill/SKILL.md) | Cria, audita, padroniza e repara Agent Skills contra o *composition cliff*. | Meta-skill, arquitetura hub+symlink, portabilidade entre Claude/Gemini/Copilot. |
| [`docker-optimizer`](./skills/docker-optimizer/SKILL.md) | Gera, revisa e ajusta `Dockerfile` e `compose.yaml`: imagens mínimas, builds com cache, containers endurecidos e máxima performance com poucos recursos. | Exemplos validados (Node, Python/uv, Go, Rust, Java) com números medidos, tuning de runtime sob limites (heap, workers, GOMAXPROCS), hardening de compose e cache em CI. |
| [`find-docs`](./skills/find-docs/SKILL.md) | Consulta documentações, APIs e SDKs atualizados em tempo real via Context7. | Evita alucinações de bibliotecas modernas, com limites negativos rigorosos. |
| [`github-actions`](./skills/github-actions/SKILL.md) | Constrói, audita e otimiza pipelines de CI/CD em `.github/workflows/`. | Segurança (permissões mínimas, SHA pins, OIDC, `cache-mode`), máximo desempenho com o mínimo de minutos (menos jobs, cache correto, runners certos), exemplos medidos em runners reais. |
| [`github-repo-setup`](./skills/github-repo-setup/SKILL.md) | Gera e padroniza, de forma interativa, README (um arquivo por idioma), LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, SUPPORT, CHANGELOG, templates de Issue/PR, FUNDING e CODEOWNERS. | Modelos próprios em pt-BR e en, imagens só do `shieldcn.dev` (banner, badges claro/escuro, contribuidores), licença pela API do GitHub e validador de README (`scripts/validate_readme.py`). |
| [`technical-issues`](./skills/technical-issues/SKILL.md) | Transforma uma análise ou auditoria técnica em issues do GitHub (uma issue ou epic + sub-issues) em vez de um relatório. Depende da `technical-report`. | Mesma fundamentação da `technical-report`, rascunhos validados (`scripts/validate_issues.py`), deduplicação, prévia com confirmação antes de criar e sub-issues nativas via `gh`. |
| [`technical-report`](./skills/technical-report/SKILL.md) | Elabora relatórios técnicos estruturados em `docs/reports/`, fundamentados em documentação oficial e precedentes do código, no idioma definido pelo repositório ou escolhido pelo usuário. | Análise, auditoria e pós-implementação ancorados em `arquivo:linha` e fontes `[Fn]`, com protocolo de medição de desempenho, rótulos em en/pt-BR e validador de forma (`scripts/validate_report.py`). |
| [`testing-strategy`](./skills/testing-strategy/SKILL.md) | Cria e audita suítes de teste para verificação de intenção real de regras de negócio e torna-as rápidas e baratas de executar. | Doutrina agnóstica de testes (falsificabilidade, mutation e property-based testing, orçamento de desempenho) com referências para JS/TS, Python, Go e Rust. |
| [`ui-design-system`](./skills/ui-design-system/SKILL.md) | Aplica regras numéricas e fundamentadas para consistência visual de UI: escalas de cor e tokens semânticos, grades de espaçamento, proporção de `border-radius` e escala tipográfica. | Fontes nomeadas (Tailwind, Radix Colors, Material Design 3, WCAG, Apple HIG, *Refactoring UI*), checklist de revisão e exemplos antes/depois. |
| [`web-performance-optimizer`](./skills/web-performance-optimizer/SKILL.md) | Audita e otimiza a performance real de sites com limiares de Core Web Vitals e benchmarks públicos (CrUX, HTTP Archive, Lighthouse, WebPageTest). | Depuração por navegador e dispositivo (HAR, Firefox Profiler, particularidades do Safari/iOS), formatos de imagem, lazy-loading e resource hints. |
| [`webxr-optimizer`](./skills/webxr-optimizer/SKILL.md) | Otimiza, revisa e depura sites WebXR (VR/AR) em three.js, React Three Fiber/`@react-three/xr` ou WebXR puro para Meta Quest, Apple Vision Pro, Android XR e celulares ARCore. | Budgets de frame e fluxo de profiling da Meta, matriz de recursos por dispositivo verificada em fonte primária, armadilhas de input (pinça do Vision Pro), testes com IWER e scanner de APIs depreciadas (`scripts/scan_deprecated.py`). |

---

# 🔄 Como Atualizar

### Via `npx skills`

```sh
# Atualiza todas as skills instaladas:
npx skills update

# Ou apenas uma skill específica:
npx skills update docker-optimizer
```

### Via `install.sh`

Com links simbólicos (padrão), um `git pull` no repositório já atualiza as skills existentes. Execute o `install.sh` novamente para vincular skills novas e para refazer as cópias caso tenha usado `--copy`:

```sh
# Instalação via curl (hub em ~/.agents):
git -C ~/.agents pull
~/.agents/install.sh

# Instalação a partir de um clone local:
cd skills
git pull
./install.sh
```

---

# 🤝 Contribuidores

<a href="https://github.com/BGLuis/skills/graphs/contributors">
  <img alt="Contribuidores" src="https://shieldcn.dev/contributors/BGLuis/skills.svg?title=false&preset=transparent&border=false&mode=light"/>
</a>

---

# 📄 Licença

Distribuído sob a licença [MIT](./LICENSE).
