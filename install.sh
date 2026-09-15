#!/usr/bin/env bash
# ==============================================================================
# Installer for BGLuis Agent Skills Hub
# https://github.com/BGLuis/skills
# ==============================================================================
set -e

REPO_URL="https://github.com/BGLuis/skills.git"
DEFAULT_HUB_DIR="${HOME}/.agents"

CORE_SKILLS=(
  "create-skill"
  "docker-optimizer"
  "find-docs"
  "github-actions"
  "github-repo-setup"
  "technical-report"
  "testing-strategy"
)

# Colors
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RED="\033[0;31m"
RESET="\033[0m"

info()    { echo -e "${BLUE}[INFO]${RESET} $*"; }
success() { echo -e "${GREEN}[OK]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET} $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }

show_help() {
  cat <<EOF
Instalador do Hub de Skills para Agentes de IA (@BGLuis)

Uso:
  ./install.sh [OPÇÕES]
  curl -fsSL https://raw.githubusercontent.com/BGLuis/skills/main/install.sh | bash -s -- [OPÇÕES]

Opções:
  --core            Instala apenas as 7 skills autorais @BGLuis (Recomendado)
  --all             Instala todas as skills (autorais + curadas da comunidade)
  --skill <nome>    Instala apenas uma skill específica
  --agent <nome>    Alvo específico: gemini, claude, copilot, cursor ou all (padrão: auto-detect)
  --copy            Copia arquivos em vez de criar links simbólicos (symlinks)
  --hub-dir <dir>   Diretório do hub central (padrão: ~/.agents)
  -h, --help        Exibe esta mensagem de ajuda
EOF
}

# Parse flags
MODE=""
CHOSEN_SKILL=""
TARGET_AGENT="auto"
USE_SYMLINK=true
HUB_DIR="${DEFAULT_HUB_DIR}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --core)
      MODE="core"
      shift
      ;;
    --all)
      MODE="all"
      shift
      ;;
    --skill)
      MODE="single"
      CHOSEN_SKILL="$2"
      shift 2
      ;;
    --agent)
      TARGET_AGENT="$2"
      shift 2
      ;;
    --copy)
      USE_SYMLINK=false
      shift
      ;;
    --hub-dir)
      HUB_DIR="$2"
      shift 2
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      error "Opção desconhecida: $1"
      show_help
      exit 1
      ;;
  esac
done

# Banner
echo -e "${BOLD}${CYAN}"
cat << "EOF"
   ___    ____  ___   __  __ _____     _____ _    _ _ _     
  / _ \  | __ )/ _ \ |  \/  | ____|   / ____| |  (_) | |    
 / /_\ \ |  _ \ | | || |\/| |  _|     \___ \| | ___| | |___ 
/_/   \_\| |_) | |_| || |  | | |___    ___) | |/ / | | (_-< 
         |____/ \___(_)_|  |_|_____|  |____/|_|\_\_|_|_/__/ 
EOF
echo -e "${RESET}${BOLD}Hub de Skills para Agentes de IA (Claude, Gemini, Copilot, Cursor)${RESET}\n"

# Determine source skills directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"

if [[ -d "${SCRIPT_DIR}/skills" ]]; then
  SOURCE_SKILLS_DIR="${SCRIPT_DIR}/skills"
elif [[ -d "${HUB_DIR}/skills" ]]; then
  SOURCE_SKILLS_DIR="${HUB_DIR}/skills"
else
  info "Repositório não encontrado localmente. Clonando em ${HUB_DIR}..."
  if ! command -v git &>/dev/null; then
    error "Git não está instalado. Instale o git para continuar."
    exit 1
  fi
  git clone "${REPO_URL}" "${HUB_DIR}"
  SOURCE_SKILLS_DIR="${HUB_DIR}/skills"
fi

if [[ ! -d "${SOURCE_SKILLS_DIR}" ]]; then
  error "Diretório de skills não encontrado em ${SOURCE_SKILLS_DIR}."
  exit 1
fi

# Discover available skills in source
ALL_AVAILABLE_SKILLS=()
for s in "${SOURCE_SKILLS_DIR}"/*; do
  if [[ -d "$s" && -f "$s/SKILL.md" ]]; then
    ALL_AVAILABLE_SKILLS+=("$(basename "$s")")
  fi
done

# Interactive mode if no mode specified and TTY available
if [[ -z "${MODE}" ]]; then
  if [[ -t 0 ]]; then
    echo -e "${BOLD}Escolha o pacote de skills que deseja instalar:${RESET}"
    echo -e "  ${GREEN}1)${RESET} ${BOLD}Skills Autorais @BGLuis${RESET} (Recomendado - 7 skills essenciais e testadas)"
    echo -e "  ${GREEN}2)${RESET} ${BOLD}Completo / All Skills${RESET} (Autorais + Ferramentas curadas da comunidade)"
    echo -e "  ${GREEN}3)${RESET} ${BOLD}Escolher uma skill individualmente${RESET}"
    read -rp "Opção [1-3] (padrão: 1): " choice
    case "${choice}" in
      2) MODE="all" ;;
      3)
        MODE="single"
        echo -e "\nSkills disponíveis:"
        for i in "${!ALL_AVAILABLE_SKILLS[@]}"; do
          echo "  $((i+1))) ${ALL_AVAILABLE_SKILLS[$i]}"
        done
        read -rp "Digite o número ou nome da skill: " skill_choice
        if [[ "${skill_choice}" =~ ^[0-9]+$ ]] && (( skill_choice >= 1 && skill_choice <= ${#ALL_AVAILABLE_SKILLS[@]} )); then
          CHOSEN_SKILL="${ALL_AVAILABLE_SKILLS[$((skill_choice-1))]}"
        else
          CHOSEN_SKILL="${skill_choice}"
        fi
        ;;
      *) MODE="core" ;;
    esac
  else
    MODE="core"
  fi
fi

# Build list of skills to install
SKILLS_TO_INSTALL=()
case "${MODE}" in
  core)
    for s in "${CORE_SKILLS[@]}"; do
      if [[ -d "${SOURCE_SKILLS_DIR}/${s}" ]]; then
        SKILLS_TO_INSTALL+=("${s}")
      else
        warn "Skill autoral '${s}' não encontrada no repositório."
      fi
    done
    ;;
  all)
    SKILLS_TO_INSTALL=("${ALL_AVAILABLE_SKILLS[@]}")
    ;;
  single)
    if [[ -d "${SOURCE_SKILLS_DIR}/${CHOSEN_SKILL}" ]]; then
      SKILLS_TO_INSTALL=("${CHOSEN_SKILL}")
    else
      error "Skill '${CHOSEN_SKILL}' não encontrada em ${SOURCE_SKILLS_DIR}."
      exit 1
    fi
    ;;
esac

info "Skills selecionadas para instalação (${#SKILLS_TO_INSTALL[@]}): ${SKILLS_TO_INSTALL[*]}"

# Detect agent destination directories
DEST_DIRS=()

install_to_agent() {
  local agent_name="$1"
  local target_dir="$2"
  
  mkdir -p "${target_dir}"
  info "Configurando ${agent_name} em ${target_dir}..."
  
  for skill in "${SKILLS_TO_INSTALL[@]}"; do
    local src_path="${SOURCE_SKILLS_DIR}/${skill}"
    local dst_path="${target_dir}/${skill}"
    
    if [[ -L "${dst_path}" ]]; then
      rm "${dst_path}"
    elif [[ -d "${dst_path}" ]]; then
      local bak="${dst_path}.bak.$(date +%s)"
      warn "Pasta já existente em ${dst_path}. Criando backup em ${bak}"
      mv "${dst_path}" "${bak}"
    fi
    
    if [[ "${USE_SYMLINK}" == true ]]; then
      ln -s "${src_path}" "${dst_path}"
      success "  → ${skill} (symlink criado)"
    else
      cp -r "${src_path}" "${dst_path}"
      success "  → ${skill} (copiado)"
    fi
  done
}

# Auto-detect or use target agent
TARGETS=()
if [[ "${TARGET_AGENT}" == "all" || "${TARGET_AGENT}" == "auto" ]]; then
  # Check Gemini CLI / Antigravity
  if [[ -d "${HOME}/.gemini" || "${TARGET_AGENT}" == "all" ]]; then
    TARGETS+=("Gemini CLI / Antigravity:${HOME}/.gemini/skills")
  fi
  # Check Claude Code
  if [[ -d "${HOME}/.claude" || "${TARGET_AGENT}" == "all" ]]; then
    TARGETS+=("Claude Code:${HOME}/.claude/skills")
  fi
  # Check Copilot CLI
  if [[ -d "${HOME}/.copilot" ]]; then
    TARGETS+=("GitHub Copilot:${HOME}/.copilot/skills")
  fi
  # Central Hub ~/.agents/skills (if not source)
  if [[ "${SOURCE_SKILLS_DIR}" != "${HOME}/.agents/skills" ]]; then
    TARGETS+=("Open Agents Hub:${HOME}/.agents/skills")
  fi
else
  case "${TARGET_AGENT}" in
    gemini)  TARGETS+=("Gemini CLI:${HOME}/.gemini/skills") ;;
    claude)  TARGETS+=("Claude Code:${HOME}/.claude/skills") ;;
    copilot) TARGETS+=("GitHub Copilot:${HOME}/.copilot/skills") ;;
    cursor)  TARGETS+=("Cursor:${HOME}/.cursor/skills") ;;
    *)       error "Agente desconhecido: ${TARGET_AGENT}"; exit 1 ;;
  esac
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  info "Nenhum diretório de agente detectado. Instalando no hub padrão ~/.agents/skills..."
  TARGETS+=("Open Agents Hub:${HOME}/.agents/skills")
fi

for target in "${TARGETS[@]}"; do
  agent_name="${target%%:*}"
  target_path="${target##*:}"
  install_to_agent "${agent_name}" "${target_path}"
done

echo ""
echo -e "${GREEN}${BOLD}✔ Instalação concluída com sucesso!${RESET}"
echo -e "As skills estão ativas e prontas para uso nos seus agentes de IA."
echo -e "Dica: Você também pode usar '${CYAN}npx skills add BGLuis/skills${RESET}' a qualquer momento."
