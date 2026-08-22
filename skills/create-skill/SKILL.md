---
name: create-skill
description: Cria, estrutura, refatora, repara e otimiza Agent Skills (habilidades de agente). Utilize quando o utilizador pedir para criar uma "skill" nova, reparar uma skill existente, otimizar gatilhos (descriptions) que estão a falhar (falsos positivos/negativos), ou desenhar automações reusáveis. NÃO utilize para escrever código de software padrão (apps, sites), scripts soltos, ou quando o utilizador pedir explicações teóricas.
---

# Diretrizes para a Criação e Reparação de Agent Skills

Você atua como um "Agente Construtor" (Skill-Builder) de elite, especializado na especificação aberta agentskills.io. O seu objetivo é projetar skills do zero E atuar como um agente de auto-melhoria (como o EvoSkill) para reparar ou otimizar skills existentes que sofram do "Composition Cliff" ou ineficiência de roteamento.

## 1. Topologia e Escopo

`~/.agents/skills/` é a **fonte única** de todas as skills próprias do utilizador. Crie e edite SEMPRE ali — nunca directamente em `~/.claude/skills/` ou `~/.gemini/skills/`, que contêm apenas symlinks a apontar de volta para o hub. Editar um symlink como se fosse ficheiro real fragmenta a skill em cópias divergentes.

- **Global (fonte única):** `~/.agents/skills/<nome-da-skill>/`
- **Local (workspace):** `./.agents/skills/<nome-da-skill>/`

Depois de criar uma skill nova no hub, ligue-a aos outros agentes:

```sh
ln -s ~/.agents/skills/<nome> ~/.claude/skills/<nome>
ln -s ~/.agents/skills/<nome> ~/.gemini/skills/<nome>
```

O Copilot CLI lê `~/.agents/skills/` nativamente e não precisa de symlink.

## 2. Estrutura Obrigatória do SKILL.md
O ficheiro `SKILL.md` DEVE iniciar obrigatoriamente com o frontmatter YAML (byte 0).

### 2.1. O Frontmatter YAML (Roteamento e Segurança)
*   `name`: Máx 64 caracteres, apenas `a-z`, `0-9`, e `-`. **DEVE coincidir com o nome do diretório pai.**
*   `description`: **O gatilho semântico**. 
    *   **Escopo inegociável:** O que a skill faz.
    *   **Limites Negativos explícitos:** "NÃO utilize para..." (Mitigação crítica contra superativação/falsos positivos e subativação/falsos negativos).
*   **Portabilidade (obrigatório):** estas skills correm em Claude Code, Gemini CLI e Copilot CLI, que têm nomes de ferramentas diferentes. NUNCA escreva nomes de tools específicos (`write_to_file`, `view_file`, `Read`, `Edit`, `Bash`) nem o campo `allowed-tools` — descreva a **acção** ("leia o ficheiro X", "pergunte ao utilizador"), não a ferramenta. Nunca use caminhos absolutos: refira ficheiros de apoio como caminhos relativos ao directório da skill.

### 2.2. Corpo das Instruções em Markdown
*   **Imperativo e Acionável:** Ordens diretas e processuais ("Analise X", "Faça Y"). Evite documentação passiva.
*   **Divulgação Progressiva:** NUNCA sature a janela de contexto. Desloque documentação teórica e heurísticas longas para a pasta `references/`.

## 3. Diretórios de Suporte (Lazy Loading)
*   `scripts/`: Scripts executáveis (`.py`, `.sh`) para lógicas computacionais puras, evitando que o modelo alucine matemática ou processos complexos.
*   `references/`: Regras de estilo, manuais, guias corporativos.
*   `assets/`: Templates estáticos (JSON, YAML).

## Procedimento de Execução

Ao ser invocado, atue silenciosamente aplicando um dos fluxos:

### Cenário A: Criação de Nova Skill
1. **Desenho:** Idealize a topologia e a `description` perfeita.
2. **Instanciação:** Crie a directoria no hub, o `SKILL.md` e as pastas de suporte. Depois crie os symlinks para os outros agentes.

### Cenário B: Reparação ou Otimização de Skill Existente (Modo EvoSkill)
1. **Diagnóstico:** Avalie a queixa do utilizador. A skill não ativa? (Falso negativo). Ativa e interfere noutras tarefas? (Falso positivo/Superativação). Falha a meio do processo? (Sobrecarga cognitiva).
2. **Auditoria:** Leia o `SKILL.md` deficiente e os seus ficheiros de apoio. Confirme que cada ficheiro referenciado em `references/`, `examples/` ou `scripts/` existe mesmo — referências mortas são uma causa comum de falha.
3. **Mutação Estrutural (Refatoração):**
   - **Gatilho:** Reescreva a `description` adicionando limites negativos robustos se o problema for de roteamento.
   - **Cognição:** Se o problema for alucinação devido a um prompt monolítico, particione a skill! Extraia regras longas para `references/` ou operações para `scripts/`.
4. **Aplicação:** Injecte as melhorias no ficheiro, editando cirurgicamente ou reescrevendo-o por inteiro.
5. **Relatório:** Explique ao utilizador qual era a falha arquitetural (ex: gatilho amplo demais) e como a mutação a resolveu.
