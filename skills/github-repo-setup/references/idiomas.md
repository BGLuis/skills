# Idiomas — um arquivo por idioma

## A regra

**Cada README tem um único idioma.** Com dois idiomas, são dois arquivos.

É proibido, em qualquer forma:

- colocar os dois idiomas no mesmo arquivo, um embaixo do outro;
- títulos bilíngues (`## 📖 Sobre / About`);
- blocos `<details>` ou tabelas com uma coluna por idioma;
- traduzir só parte do arquivo e deixar o resto no outro idioma.

## Nomes dos arquivos

O idioma principal fica em `README.md`, que é o que o GitHub mostra. O outro
recebe o sufixo BCP 47:

| Idioma principal | `README.md` | Segundo arquivo |
|---|---|---|
| Português | português | `README.en.md` |
| Inglês | inglês | `README.pt-BR.md` |

Com um só idioma, existe só `README.md`, sem linha de troca.

Qual é o principal é **sempre perguntado** ao usuário na Fase 1. Nunca decida
sozinho.

## Linha de troca de idioma

Com dois idiomas, os dois READMEs trazem, logo abaixo do banner, uma linha
centralizada com todos os idiomas. O atual fica em negrito sem link, os outros
com link relativo. Cada nome é escrito **no próprio idioma**:

```html
<p align="center"><b>Português (BR)</b> · <a href="README.en.md">English</a></p>
```

```html
<p align="center"><b>English</b> · <a href="README.pt-BR.md">Português (BR)</a></p>
```

O `href` aponta para o nome real do arquivo. No `README.md` principal, o link
para ele mesmo não existe (fica em negrito). Em `README.pt-BR.md` / `README.en.md`,
o link de volta para o principal é `README.md`.

## Como gerar

1. Preencha `templates/<principal>/README.md` com os dados do projeto e grave em `README.md`.
2. Preencha `templates/<secundário>/README.md` com **os mesmos dados**, traduzindo só o
   texto livre (Sobre, Motivo, subtítulo, descrições da tabela de variáveis). Grave com o sufixo.
3. Os títulos de seção vêm prontos do template de cada idioma: não traduza títulos por
   conta própria.
4. O Motivo é do usuário: no idioma dele, copie literalmente; no outro idioma, traduza
   sem acrescentar nem remover nada.
5. Comandos, URLs, nomes de variáveis e badges são idênticos nos dois arquivos, exceto o
   `title`/`subtitle` do banner, que acompanham o idioma.

## O que NÃO é duplicado

Só o README tem versão por idioma. CONTRIBUTING, CODE_OF_CONDUCT, SECURITY,
SUPPORT, CHANGELOG e os templates de issue/PR são gerados **uma vez, no idioma
principal**, a partir de `templates/<principal>/`. O GitHub só liga
automaticamente o arquivo com o nome padrão, então uma segunda versão ficaria
escondida.
