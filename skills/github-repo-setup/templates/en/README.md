<!-- TEMPLATE: banner. With an own logo reachable via raw, add &logo=<encoded raw URL> to both URLs; if it is not reachable, leave the banner without a logo and add the relative logo right below it. If the user chose the project's banner or another one, replace this block with it. See references/shieldcn.md, "Logo do banner" and "Banner próprio do projeto". -->
<p align="center">
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/header/graph.svg?title={{PROJECT_TITLE_URL}}&subtitle={{TAGLINE_URL}}&align=left&font=geist-mono&mode=dark" /><img alt="{{PROJECT_TITLE}}" src="https://shieldcn.dev/header/graph.svg?title={{PROJECT_TITLE_URL}}&subtitle={{TAGLINE_URL}}&align=left&font=geist-mono&mode=light" /></picture>
</p>

<!-- TEMPLATE: language switch line. Only with two languages; otherwise delete the line. See references/idiomas.md -->
<p align="center"><b>English</b> · <a href="{{OTHER_README}}">Português (BR)</a></p>

<p align="center">
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/github/stars/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=dark" /><img alt="GitHub Stars" src="https://shieldcn.dev/github/stars/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=light" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/github/forks/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=dark" /><img alt="GitHub Forks" src="https://shieldcn.dev/github/forks/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=light" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/github/watchers/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=dark" /><img alt="Watchers" src="https://shieldcn.dev/github/watchers/{{OWNER}}/{{REPO}}.svg?variant=secondary&size=sm&mode=light" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/github/contributors/{{OWNER}}/{{REPO}}.svg?theme=emerald&size=sm&mode=dark" /><img alt="Contributors" src="https://shieldcn.dev/github/contributors/{{OWNER}}/{{REPO}}.svg?theme=emerald&size=sm&mode=light" /></picture>
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/github/license/{{OWNER}}/{{REPO}}.svg?variant=ghost&size=sm&mode=dark" /><img alt="License" src="https://shieldcn.dev/github/license/{{OWNER}}/{{REPO}}.svg?variant=ghost&size=sm&mode=light" /></picture>
</p>

<!-- TEMPLATE: one badge per technology found in the code (3 to 6). Fixed color: no <picture>. See references/shieldcn.md -->
<p align="center">
  <img alt="{{TECH_NAME}}" src="https://shieldcn.dev/badge/{{TECH_LABEL}}-{{TECH_NAME}}-{{TECH_HEX}}.svg?logo={{TECH_SLUG}}&variant=branded&size=sm" />
</p>

# 📖 About

{{ABOUT}}

# 📋 Motivation

{{MOTIVE}}

# 💻 Getting Started

### Requirements

<!-- TEMPLATE: each tool with its official download link and the version read from the project -->
- [{{TOOL}}]({{TOOL_DOWNLOAD_URL}}) {{TOOL_VERSION}}

### Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/{{OWNER}}/{{REPO}}.git
   ```

2. Enter the project directory:

   ```sh
   cd {{REPO}}
   ```

<!-- TEMPLATE: if the project supports Docker AND native execution, keep both subsections. If only one, delete the other and the "Option" headings. -->
#### Option 1: Docker

3. Start the containers:

   ```sh
   {{DOCKER_COMMAND}}
   ```

#### Option 2: Local execution

3. Install the dependencies and start:

   ```sh
   {{NATIVE_COMMAND}}
   ```

<!-- TEMPLATE: only if .env.example, .env.sample or .env.template exists. Otherwise delete the whole section. -->
# ⚙️ Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `{{ENV_NAME}}` | {{ENV_DESCRIPTION}} | `{{ENV_DEFAULT}}` |

# 🤝 Contributors

<a href="https://github.com/{{OWNER}}/{{REPO}}/graphs/contributors">
  <picture><source media="(prefers-color-scheme: dark)" srcset="https://shieldcn.dev/contributors/{{OWNER}}/{{REPO}}.svg?title=false&preset=transparent&border=false&mode=dark" /><img alt="Contributors" src="https://shieldcn.dev/contributors/{{OWNER}}/{{REPO}}.svg?title=false&preset=transparent&border=false&mode=light" /></picture>
</a>

# 📄 License

Distributed under the [{{LICENSE_NAME}}]({{LICENSE_FILE}}) license.
