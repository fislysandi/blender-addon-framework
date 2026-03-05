# Shell Completion Setup

This guide explains how to enable shell completion for `baf` command workflows.

## Generate completion script

Use the built-in generator:

```bash
uv run completion script bash
uv run completion script zsh
uv run completion script fish
```

You can preview suggestions directly:

```bash
uv run completion suggest test
uv run completion suggest renmae-addon
```

## Bash setup

Temporary (current shell only):

```bash
source <(uv run completion script bash)
```

Persistent:

```bash
mkdir -p ~/.local/share/bash-completion/completions
uv run completion script bash > ~/.local/share/bash-completion/completions/baf
```

Then restart shell, or run:

```bash
source ~/.local/share/bash-completion/completions/baf
```

## Zsh setup

Temporary (current shell only):

```bash
source <(uv run completion script zsh)
```

Persistent:

```bash
mkdir -p ~/.zfunc
uv run completion script zsh > ~/.zfunc/_baf
```

Add this to your `~/.zshrc` if missing:

```zsh
fpath=(~/.zfunc $fpath)
autoload -Uz compinit
compinit
```

Reload shell:

```bash
exec zsh
```

## Fish setup

Persistent:

```bash
mkdir -p ~/.config/fish/completions
uv run completion script fish > ~/.config/fish/completions/baf.fish
```

Reload fish:

```bash
exec fish
```

## Scope and behavior

- completion supports root commands (`test`, `compile`, `create`, `rename-addon`, `addon-deps`, `template`, and others)
- addon-name suggestions are available for command positions that expect addon names
- template completion includes `template apply` template-name suggestions

Current limitation:

- root-command suggestions are defined by current completion command list and may lag newly added CLI commands during migration

## Notes

- if you use `baf` from a different framework checkout, regenerate completion from that checkout
- completion uses live project context (addons/templates), so suggestions update as project files change
