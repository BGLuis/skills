#!/usr/bin/env python3
"""Valida a forma de um relatório técnico gerado pela skill technical-report.

Confere só o que é mecânico (as regras de conteúdo ficam em references/checklist.md):
frontmatter ausente, H1 único na linha 1, H2 numerados e contíguos, nenhum H4,
`---` antes de cada H2, blockquote de fechamento, anatomia dos achados P-NN/U-NN,
`**Correção:**` colado ao `**Critério de aceite:**`, subseções obrigatórias por
modo (Precedentes e Não-objetivos no A, Veredicto no B/C), emojis fora do conjunto
permitido, checkbox marcado fora de "Verificação executada" e citações [Fn]
coerentes com a tabela de "Fontes consultadas".

Uso: python3 validate_report.py RELATORIO.md [OUTRO.md ...]
Saída: uma linha `arquivo:linha: mensagem` por erro; código 1 se houver erro.
"""

import re
import sys
from pathlib import Path

ALLOWED_EMOJI = {"✅", "\U0001F7E1", "❌", "⚠"}  # ✅ 🟡 ❌ ⚠
EMOJI_RANGES = [(0x1F000, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF)]
SEVERITIES = "Crítica|Alta|Média|Baixa"

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
H2_RE = re.compile(r"^## (?!#)(.*)$")
H2_NUM_RE = re.compile(r"^(\d+)\. \S")
FINDING_ID_RE = re.compile(r"^### ([PU]-\d+)\b")
FINDING_FULL_RE = re.compile(
    r"^### [PU]-\d{2} · .+ — \*\*(" + SEVERITIES + r")\*\*( \(.+\))?$"
)
CITATION_RE = re.compile(r"\[F(\d+)\]")
SOURCE_ROW_RE = re.compile(r"^\|\s*F(\d+)\s*\|")
CHECKED_RE = re.compile(r"^\s*[-*] \[[xX]\]")
FINDING_FIELDS = ("**Reprodução:**", "**Correção:**", "**Critério de aceite:**")


def prose_lines(lines):
    """Devolve (número, linha) de tudo o que está fora de blocos de código."""
    fence = None
    out = []
    for n, line in enumerate(lines, 1):
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)
                continue
            out.append((n, line))
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
            fence = None
    return out


def prev_nonblank(lines, idx):
    """Linha não vazia anterior ao índice 0-based `idx`, ou None."""
    for j in range(idx - 1, -1, -1):
        if lines[j].strip():
            return lines[j].strip()
    return None


def is_emoji(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in EMOJI_RANGES) and ch not in ALLOWED_EMOJI


def validate(path):
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    errors = []

    def err(n, msg):
        errors.append(f"{path}:{n}: {msg}")

    if not lines:
        return [f"{path}:1: arquivo vazio"]

    if lines[0].strip() == "---":
        err(1, "frontmatter YAML não é permitido; a primeira linha é o H1")
    if not lines[0].startswith("# "):
        err(1, "a primeira linha tem de ser o H1 (`# Título`)")

    prose = prose_lines(lines)

    # Headings
    h1_count = 0
    h2s = []  # (linha, título)
    for n, line in prose:
        if line.startswith("# "):
            h1_count += 1
            if h1_count > 1:
                err(n, "mais de um H1; use um único H1")
        elif line.startswith("####"):
            err(n, "H4 ou mais profundo não é permitido; use H3 ou reestruture")
        else:
            m = H2_RE.match(line)
            if m:
                h2s.append((n, m.group(1).strip()))

    expected = 1
    for n, title in h2s:
        m = H2_NUM_RE.match(title)
        if not m:
            err(n, f"H2 sem numeração (`## {expected}. …`): '{title}'")
            continue
        num = int(m.group(1))
        if num != expected:
            err(n, f"H2 fora de sequência: esperado {expected}, encontrado {num}")
        expected = num + 1
        if prev_nonblank(lines, n - 1) != "---":
            err(n, "falta `---` antes deste H2")

    # Mapa linha → título do H2 corrente
    def section_of(lineno):
        current = ""
        for n, title in h2s:
            if n > lineno:
                break
            current = title
        return current

    # Blockquote de fechamento depois do último `---`
    prose_idx = [n for n, line in prose if line.strip() == "---"]
    if not prose_idx:
        err(len(lines), "falta o `---` seguido do blockquote de fechamento")
    else:
        tail = [(n, line) for n, line in prose if n > prose_idx[-1] and line.strip()]
        if not tail:
            err(prose_idx[-1], "falta o blockquote de fechamento depois do último `---`")
        elif any(not line.lstrip().startswith(">") for _, line in tail):
            bad = next(n for n, line in tail if not line.lstrip().startswith(">"))
            err(bad, "depois do último `---` só pode haver o blockquote de fechamento")

    # Achados P-NN / U-NN
    seen_ids = {}
    finding_starts = []
    for n, line in prose:
        m = FINDING_ID_RE.match(line)
        if not m:
            continue
        fid = m.group(1)
        if fid in seen_ids:
            err(n, f"identificador {fid} repetido (primeiro na linha {seen_ids[fid]})")
        seen_ids[fid] = n
        finding_starts.append(n)
        if not FINDING_FULL_RE.match(line):
            err(n, f"título de achado fora do formato `### {fid[0]}-NN · <título> — "
                   f"**<{SEVERITIES.replace('|', '/')}>**`")
    heading_lines = sorted([n for n, _ in h2s] + [
        n for n, line in prose if line.startswith("### ")
    ])
    for start in finding_starts:
        end = next((h for h in heading_lines if h > start), len(lines) + 1)
        body = [line for n, line in prose if start < n < end]
        for field in FINDING_FIELDS:
            if not any(line.startswith(field) for line in body):
                err(start, f"achado sem o campo {field}")

    # Correção colado ao Critério de aceite
    for i, line in enumerate(lines):
        if not line.startswith("**Correção:**"):
            continue
        j = i + 1
        found = False
        while j < len(lines) and lines[j].strip():
            if lines[j].startswith("**Critério de aceite:**"):
                found = True
                break
            j += 1
        if not found:
            err(i + 1, "`**Critério de aceite:**` tem de vir logo abaixo de `**Correção:**`, "
                       "sem linha em branco")

    # Emojis, checkboxes e citações (fora de blocos e de código inline)
    cited = {}
    for n, line in prose:
        bare = INLINE_CODE_RE.sub("", line)
        for ch in bare:
            if is_emoji(ch):
                err(n, f"emoji fora do conjunto permitido (✅ 🟡 ❌ ⚠️): '{ch}'")
                break
        if CHECKED_RE.match(bare) and "Verificação executada" not in section_of(n):
            err(n, "checkbox marcado `[x]` só é permitido em 'Verificação executada' (modo C)")
        for m in CITATION_RE.finditer(bare):
            cited.setdefault(int(m.group(1)), n)

    # Partes obrigatórias por modo, detectado pelos títulos das seções
    titles = [t for _, t in h2s]
    h3_titles = [line[4:] for _, line in prose if line.startswith("### ")]
    if any("Estado atual" in t for t in titles):  # modo A
        for req in ("Precedentes no código", "Não-objetivos"):
            if not any(req in t for t in h3_titles):
                err(next(n for n, t in h2s if "Estado atual" in t),
                    f"modo A: falta a subseção `### {req}` na seção 'Estado atual'")
    if any("Sumário executivo" in t for t in titles):  # modos B e C
        if not any(line.startswith("**Veredicto:**") for _, line in prose):
            err(next(n for n, t in h2s if "Sumário executivo" in t),
                "falta o `**Veredicto:**` no sumário executivo")

    sources_h2 = [(n, t) for n, t in h2s if "Fontes consultadas" in t]
    defined = {}
    if sources_h2:
        start = sources_h2[0][0]
        if h2s and h2s[-1][0] != start:
            err(start, "'Fontes consultadas' tem de ser a última seção numerada")
        for n, line in prose:
            if n > start:
                m = SOURCE_ROW_RE.match(line)
                if m:
                    defined[int(m.group(1))] = n
    if cited and not sources_h2:
        err(min(cited.values()), "há citações [Fn] mas falta a seção '## N. Fontes consultadas'")
    elif sources_h2:
        for f, n in sorted(cited.items()):
            if f not in defined:
                err(n, f"[F{f}] citado mas ausente da tabela de fontes")
        for f, n in sorted(defined.items()):
            if f not in cited:
                err(n, f"F{f} está na tabela de fontes mas nunca é citado no texto")

    return errors


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 0 if len(argv) >= 2 else 2
    all_errors = []
    for p in argv[1:]:
        if not Path(p).is_file():
            all_errors.append(f"{p}:0: arquivo não encontrado")
            continue
        all_errors.extend(validate(p))
    for e in all_errors:
        print(e)
    if all_errors:
        print(f"\n{len(all_errors)} erro(s).", file=sys.stderr)
        return 1
    print("OK — nenhum erro de forma.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
