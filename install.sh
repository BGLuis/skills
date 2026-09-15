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
Instalador do Hub de Skills Personalizadas (@BGLuis)

Uso:
  ./install.sh [OPÇÕES]
  curl -fsSL https://raw.githubusercontent.com/BGLuis/skills/main/install.sh | bash -s -- [OPÇÕES]

Opções:
  --all             Instala todas as 7 skills autorais @BGLuis (padrão)
  --skill <nome>    Instala apenas uma skill específica
  --agent <nome>    Alvo específico: gemini, claude, copilot, cursor ou all (padrão: auto-detect)
  --copy            Copia arquivos em vez de criar links simbólicos (symlinks)
  --hub-dir <dir>   Diretório do hub central (padrão: ~/.agents)
  -h, --help        Exibe esta mensagem de ajuda
EOF
}

# Parse flags
MODE="all"
CHOSEN_SKILL=""
TARGET_AGENT="auto"
USE_SYMLINK=true
HUB_DIR="${DEFAULT_HUB_DIR}"

while [[ $# -gt 0 ]]; do
  case "$1" in
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
echo -e "${RESET}${BOLD}Skills Autorais @BGLuis para Agentes de IA (Claude, Gemini, Copilot, Cursor)${RESET}\n"

# Determine source skills directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"

if [[ -d "${SCRIPT_DIR}/skills" ]]; then
  SOURCE_SKILLS_DIR="${SCRIPT_DIR}/skills"
elif [[ -d "${HUB_DIR}/skills" ]]; then
  SOURCE_SKILLS_DIR="${HUB_DIR}/skills"
else
  info "Clonando repositório em ${HUB_DIR}..."
  if ! command -v git &>/dev/null; then
    error "Git não está instalado. Instale o git para continuar."
    exit 1
  fi
  git clone "${REPO_URL}" "${HUB_DIR}"
  SOURCE_SKILLS_DIR="${HUB_DIR}/skills"
fi

# Determine skills to install
SKILLS_TO_INSTALL=()
if [[ "${MODE}" == "single" ]]; then
  if [[ -d "${SOURCE_SKILLS_DIR}/${CHOSEN_SKILL}" ]]; then
    SKILLS_TO_INSTALL=("${CHOSEN_SKILL}")
  else
    error "Skill '${CHOSEN_SKILL}' não encontrada em ${SOURCE_SKILLS_DIR}."
    exit 1
  fi
else
  for s in "${CORE_SKILLS[@]}"; do
    if [[ -d "${SOURCE_SKILLS_DIR}/${s}" ]]; then
      SKILLS_TO_INSTALL+=("${s}")
    fi
  done
fi

info "Skills a instalar (${#SKILLS_TO_INSTALL[@]}): ${SKILLS_TO_INSTALL[*]}"

# Detect target agent directories
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

TARGETS=()
if [[ "${TARGET_AGENT}" == "all" || "${TARGET_AGENT}" == "auto" ]]; then
  if [[ -d "${HOME}/.gemini" || "${TARGET_AGENT}" == "all" ]]; then
    TARGETS+=("Gemini CLI / Antigravity:${HOME}/.gemini/skills")
  fi
  if [[ -d "${HOME}/.claude" || "${TARGET_AGENT}" == "all" ]]; then
    TARGETS+=("Claude Code:${HOME}/.claude/skills")
  fi
  if [[ -d "${HOME}/.copilot" ]]; then
    TARGETS+=("GitHub Copilot:${HOME}/.copilot/skills")
  fi
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

for target in "${TARGETS[@]}"; do
  agent_name="${target%%:*}"
  target_path="${target##*:}"
  install_to_agent "${agent_name}" "${target_path}"
done

echo ""
echo -e "${GREEN}${BOLD}✔ Instalação concluída com sucesso!${RESET}"
echo -e "As skills autorais @BGLuis estão disponíveis para os seus agentes."
