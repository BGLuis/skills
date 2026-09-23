#!/usr/bin/env python3
"""Valida os arquivos gerados pela skill github-repo-setup.

Offline (sempre):
  - restos de template: {{PLACEHOLDER}}, comentários TEMPLATE, "[Substitua"/"[Replace";
  - README com dois idiomas no mesmo arquivo (títulos pt-BR e en juntos, ou
    títulos do tipo "English version");
  - README.<lang>.md com títulos do outro idioma;
  - com mais de um README.*, cada um precisa linkar todos os outros;
  - link relativo para um .md (README de outro idioma, CONTRIBUTING,
    SECURITY, CODE_OF_CONDUCT...) que não existe;
  - imagem hospedada fora do shieldcn (img.shields.io, contrib.rocks etc.) ou
    em www.shieldcn.dev (--allow-host HOST libera o host de um banner
    escolhido pelo usuário);
  - imagem relativa que não existe no repositório;
  - vírgula sem espaço dentro de srcset (corta a URL; use %2C);
  - <picture> sem <img> de fallback, ou com mode=dark/light trocados.

Online (--online):
  - badge shieldcn cujo .json devolve "error": true;
  - logo= inexistente (SVG idêntico ao mesmo badge com logo=false; em header,
    "hasLogo": false no .json);
  - header ou contributors que não respondem 200.

Uso: python3 validate_readme.py [--online] [--allow-host HOST ...] ARQUIVO [ARQUIVO ...]
Saída: uma linha `arquivo:linha: mensagem` por erro; código 1 se houver erro.
"""

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SHIELDCN_HOST = "shieldcn.dev"

FORBIDDEN_HOSTS = {
    "www.shieldcn.dev": "use shieldcn.dev, sem www (o www responde 308)",
    "img.shields.io": "badges só via shieldcn.dev",
    "shields.io": "badges só via shieldcn.dev",
    "badgen.net": "badges só via shieldcn.dev",
    "forthebadge.com": "badges só via shieldcn.dev",
    "badge.fury.io": "badges só via shieldcn.dev",
    "contrib.rocks": "use shieldcn.dev/contributors/{owner}/{repo}.svg",
    "contributors-img.web.app": "use shieldcn.dev/contributors/{owner}/{repo}.svg",
    "github-readme-stats.vercel.app": "fora do padrão da skill",
    "skillicons.dev": "use badges de tecnologia do shieldcn",
    "api.star-history.com": "fora do padrão da skill",
    "star-history.com": "fora do padrão da skill",
}

# Imagens do próprio projeto (screenshots, logo) hospedadas pelo GitHub.
ALLOWED_OTHER_HOSTS = {
    "raw.githubusercontent.com",
    "user-images.githubusercontent.com",
    "private-user-images.githubusercontent.com",
}

PT_HEADINGS = ["sobre", "motivo", "como iniciar", "requisitos", "instalação",
               "variáveis de ambiente", "contribuidores", "licença"]
EN_HEADINGS = ["about", "motivation", "getting started", "requirements",
               "installation", "environment variables", "contributors", "license"]
LANG_SECTION_RE = re.compile(
    r"^(english( version)?|portugu[eê]s( \(br\))?|portuguese|vers[aã]o em (portugu[eê]s|ingl[eê]s))$"
)

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$")
PLACEHOLDER_RE = re.compile(r"\{\{[^{}]+\}\}|<!--\s*TEMPLATE|^\s*#\s*TEMPLATE:|\[Substitua|\[Replace")
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)")
SRCSET_RE = re.compile(r"""\bsrcset\s*=\s*["']([^"']+)["']""", re.I)
HTML_SRC_RE = re.compile(r"""\b(?:src|srcset)\s*=\s*["']([^"']+)["']""", re.I)
README_LINK_RE = re.compile(r"""(?:\]\(|href\s*=\s*["'])\s*(?:\./)?(README[\w.-]*\.md)\b""", re.I)
MD_LINK_RE = re.compile(r"""(?:\]\(|href\s*=\s*["'])\s*([^)\s"'#]+\.md)(?:#[^)\s"']*)?""", re.I)
PICTURE_RE = re.compile(r"<picture\b.*?</picture>", re.I | re.S)


def prose_lines(lines):
    """Devolve (número, linha) de tudo o que está fora de blocos de código."""
    fence = None
    for number, line in enumerate(lines, 1):
        match = FENCE_RE.match(line)
        if match:
            marker = match.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is None:
            yield number, line


def normalize_heading(text):
    text = re.sub(r"[^\w\s()]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def heading_lang(text):
    norm = normalize_heading(text)
    has = lambda words: any(re.search(rf"(?<!\w){re.escape(w)}(?!\w)", norm) for w in words)
    return has(PT_HEADINGS), has(EN_HEADINGS), norm


def is_readme(path):
    return re.fullmatch(r"README(\.[\w-]+)?\.md", path.name, re.I) is not None


def readme_lang(path):
    match = re.fullmatch(r"README\.([\w-]+)\.md", path.name, re.I)
    return match.group(1).lower() if match else None


def image_urls(lines):
    for number, line in prose_lines(lines):
        for regex in (MD_IMAGE_RE, HTML_SRC_RE):
            for match in regex.finditer(line):
                # srcset pode ter "url 2x, url2 1x": candidatos separados por vírgula + espaço
                for part in re.split(r",\s+", match.group(1)):
                    url = part.strip().split(" ")[0]
                    if url:
                        yield number, url.replace("&amp;", "&")


def check_offline(path, lines, errors, allowed_hosts=()):
    def err(line, msg):
        errors.append(f"{path}:{line}: {msg}")

    for number, line in enumerate(lines, 1):
        if PLACEHOLDER_RE.search(line):
            err(number, f"resto de template não preenchido: {line.strip()[:80]}")

    if is_readme(path):
        pt_lines, en_lines = [], []
        for number, line in prose_lines(lines):
            match = HEADING_RE.match(line)
            if not match:
                continue
            is_pt, is_en, norm = heading_lang(match.group(1))
            if LANG_SECTION_RE.match(norm):
                err(number, f"título de seção por idioma ('{match.group(1).strip()}'): "
                            "cada idioma vai num README próprio (references/idiomas.md)")
            if is_pt:
                pt_lines.append(number)
            if is_en:
                en_lines.append(number)
        if pt_lines and en_lines:
            err(min(pt_lines + en_lines),
                f"README mistura títulos em português (linhas {pt_lines}) e inglês "
                f"(linhas {en_lines}): um arquivo por idioma (references/idiomas.md)")
        lang = readme_lang(path)
        if lang == "en" and pt_lines:
            err(pt_lines[0], "README.en.md contém títulos em português")
        if lang and lang.startswith("pt") and en_lines:
            err(en_lines[0], f"{path.name} contém títulos em inglês")

        siblings = sorted(p.name for p in path.parent.iterdir() if p.is_file() and is_readme(p))
        linked = {}
        for number, line in prose_lines(lines):
            for match in README_LINK_RE.finditer(line):
                linked.setdefault(match.group(1), number)
        if len(siblings) > 1:
            for other in siblings:
                if other != path.name and other not in linked:
                    err(1, f"falta a linha de troca de idioma com link para {other}")

    for number, line in prose_lines(lines):
        for match in MD_LINK_RE.finditer(line):
            target = match.group(1)
            if urllib.parse.urlsplit(target).scheme:
                continue
            if not (path.parent / urllib.parse.unquote(target)).is_file():
                err(number, f"link para {target}, que não existe: gere o arquivo ou apague o link")

    for number, line in prose_lines(lines):
        for match in SRCSET_RE.finditer(line):
            if re.search(r",(?!\s)", match.group(1)):
                err(number, "vírgula dentro de srcset corta a URL: codifique como %2C")

    for number, url in image_urls(lines):
        parsed = urllib.parse.urlsplit(url)
        if not parsed.scheme:
            if not (path.parent / urllib.parse.unquote(parsed.path)).is_file():
                err(number, f"imagem relativa {url} não existe")
            continue
        host = parsed.hostname or ""
        if host in allowed_hosts:
            continue
        if host in FORBIDDEN_HOSTS:
            err(number, f"imagem em {host}: {FORBIDDEN_HOSTS[host]}")
        elif host == SHIELDCN_HOST:
            continue
        elif host in ALLOWED_OTHER_HOSTS:
            continue
        elif host == "github.com" and ("/user-attachments/" in parsed.path or "/assets/" in parsed.path):
            continue
        else:
            err(number, f"imagem em host não permitido ({host}): badges só via shieldcn.dev; "
                        "imagens do projeto em caminho relativo ou anexo do GitHub")

    text = "\n".join(lines)
    for match in PICTURE_RE.finditer(text):
        block = match.group(0)
        number = text.count("\n", 0, match.start()) + 1
        if not re.search(r"<img\b", block, re.I):
            err(number, "<picture> sem <img> de fallback")
            continue
        source = re.search(r"<source\b[^>]*srcset\s*=\s*[\"']([^\"']+)", block, re.I)
        img = re.search(r"<img\b[^>]*src\s*=\s*[\"']([^\"']+)", block, re.I)
        if source and img and SHIELDCN_HOST in source.group(1):
            if "mode=dark" not in source.group(1) or "mode=light" not in img.group(1):
                err(number, "<picture> do shieldcn: <source> deve ter mode=dark e <img> mode=light")


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "github-repo-setup-validator"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def with_query(parsed, path=None, **params):
    query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    query.update(params)
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, path or parsed.path, urllib.parse.urlencode(query), ""))


def check_online(path, lines, errors, cache):
    def err(line, msg):
        errors.append(f"{path}:{line}: {msg}")

    for number, url in image_urls(lines):
        parsed = urllib.parse.urlsplit(url)
        if parsed.hostname != SHIELDCN_HOST or not parsed.path.endswith(".svg"):
            continue
        if url in cache:
            problem = cache[url]
        else:
            problem = shieldcn_problem(parsed)
            cache[url] = problem
        if problem:
            err(number, f"{problem}: {url}")


def shieldcn_problem(parsed):
    json_path = parsed.path[: -len(".svg")] + ".json"
    logo = dict(urllib.parse.parse_qsl(parsed.query)).get("logo")
    try:
        if parsed.path.startswith("/contributors/"):
            status, _ = fetch(urllib.parse.urlunsplit(parsed))
            return None if status == 200 else f"contributors respondeu HTTP {status}"
        status, body = fetch(with_query(parsed, path=json_path))
        if status != 200:
            return f"shieldcn respondeu HTTP {status}"
        data = json.loads(body)
        items = data if isinstance(data, list) else [data]
        failed = [i for i in items if isinstance(i, dict) and i.get("error")]
        if failed:
            return f"badge com erro no shieldcn ({failed[0].get('value') or failed[0].get('error')})"
        if logo and logo != "false":
            if parsed.path.startswith("/header/"):
                if isinstance(data, dict) and data.get("hasLogo") is False:
                    return f"logo '{logo}' não existe (hasLogo=false)"
            else:
                _, with_logo = fetch(urllib.parse.urlunsplit(parsed))
                _, without_logo = fetch(with_query(parsed, logo="false"))
                if with_logo == without_logo:
                    return f"logo '{logo}' não existe (SVG igual ao de logo=false)"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return f"não foi possível verificar ({exc})"
    return None


def main(argv):
    online, allowed_hosts, files = False, set(), []
    args = iter(argv)
    for arg in args:
        if arg == "--online":
            online = True
        elif arg == "--allow-host":
            allowed_hosts.add(next(args, "").lower())
        else:
            files.append(arg)
    if not files:
        print(__doc__.strip().splitlines()[-2], file=sys.stderr)
        return 2
    errors, cache = [], {}
    for name in files:
        path = Path(name)
        if not path.is_file():
            errors.append(f"{path}:0: arquivo não encontrado")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        check_offline(path, lines, errors, allowed_hosts)
        if online:
            check_online(path, lines, errors, cache)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
