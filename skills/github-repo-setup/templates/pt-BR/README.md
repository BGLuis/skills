<!-- TEMPLATE: banner. Com logo próprio acessível via raw, acrescente &logo=<URL raw codificada> nas duas URLs; se não for acessível, deixe sem logo e acrescente o logo relativo logo abaixo. Se o usuário escolheu o banner do projeto ou outro, troque este bloco por ele. Ver references/shieldcn.md, "Logo do banner" e "Banner próprio do projeto". -->
<p align="center">
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/header/graph.svg?title={{PROJECT_TITLE_URL}}&subtitle={{TAGLINE_URL}}&align=left&font=geist-mono&mode=dark" /><img alt="{{PROJECT_TITLE}}" src="https://shieldcn.dev/header/graph.svg?title={{PROJECT_TITLE_URL}}&subtitle={{TAGLINE_URL}}&align=left&font=geist-mono&mode=light" /></picture>
</p>

<!-- TEMPLATE: linha de troca de idioma. Só com dois idiomas; senão apague a linha. Ver references/idiomas.md -->
<p align="center"><b>Português (BR)</b> · <a href="{{OTHER_README}}">English</a></p>

<p align="center">
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/github/stars/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=dark" /><img alt="GitHub Stars" src="https://shieldcn.dev/github/stars/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=light" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/github/forks/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=dark" /><img alt="GitHub Forks" src="https://shieldcn.dev/github/forks/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=light" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/github/watchers/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=dark" /><img alt="Watchers" src="https://shieldcn.dev/github/watchers/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=light" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/github/contributors/{{OWNER}}/{{REPO}}.svg?theme=emerald&size=sm&mode=dark" /><img alt="Contributors" src="https://shieldcn.dev/github/contributors/{{OWNER}}/{{REPO}}.svg?theme=emerald&size=sm&mode=light" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/github/license/{{OWNER}}/{{REPO}}.svg?variant=ghost&size=sm&mode=dark" /><img alt="License" src="https://shieldcn.dev/github/license/{{OWNER}}/{{REPO}}.svg?variant=ghost&size=sm&mode=light" /></picture>
</p>

<!-- TEMPLATE: um badge por tecnologia detectada no código (3 a 6). Cor fixa: sem <picture>. Ver references/shieldcn.md -->
<p align="center">
  <img alt="{{TECH_NAME}}" src="https://shieldcn.dev/badge/{{TECH_LABEL}}-{{TECH_NAME}}-{{TECH_HEX}}.svg?logo={{TECH_SLUG}}&variant=branded&size=sm" />
</p>

# 📖 Sobre

{{ABOUT}}

# 📋 Motivo

{{MOTIVE}}

# 💻 Como iniciar

### Requisitos

<!-- TEMPLATE: cada ferramenta com link oficial de download e a versão lida do projeto -->
- [{{TOOL}}]({{TOOL_DOWNLOAD_URL}}) {{TOOL_VERSION}}

### Instalação

1. Clone o repositório:

   ```sh
   git clone https://github.com/{{OWNER}}/{{REPO}}.git
   ```

2. Entre no diretório do projeto:

   ```sh
   cd {{REPO}}
   ```

<!-- TEMPLATE: se o projeto tiver Docker E execução nativa, mantenha as duas subseções. Se tiver só uma, apague a outra e os títulos "Opção". -->
#### Opção 1: Docker

3. Suba os containers:

   ```sh
   {{DOCKER_COMMAND}}
   ```

#### Opção 2: Execução local

3. Instale as dependências e inicie:

   ```sh
   {{NATIVE_COMMAND}}
   ```

<!-- TEMPLATE: só se existir .env.example, .env.sample ou .env.template. Senão apague a seção inteira. -->
# ⚙️ Variáveis de Ambiente

| Variável | Descrição | Padrão |
| :--- | :--- | :--- |
| `{{ENV_NAME}}` | {{ENV_DESCRIPTION}} | `{{ENV_DEFAULT}}` |

# 🤝 Contribuidores

<a href="https://github.com/{{OWNER}}/{{REPO}}/graphs/contributors">
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/contributors/{{OWNER}}/{{REPO}}.svg?title=false&preset=transparent&border=false&mode=dark" /><img alt="Contribuidores" src="https://shieldcn.dev/contributors/{{OWNER}}/{{REPO}}.svg?title=false&preset=transparent&border=false&mode=light" /></picture>
</a>

# 📄 Licença

Distribuído sob a licença [{{LICENSE_NAME}}]({{LICENSE_FILE}}).
