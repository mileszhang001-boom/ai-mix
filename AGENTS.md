# AGENTS.md - Agent Guidelines for This Repository

## Overview

This repository is a **Specify/OpenCode template project** containing:
- Bash scripts in `.specify/scripts/bash/`
- Markdown command files in `.opencode/command/`
- Specification templates in `.specify/templates/`

## Build/Lint/Test Commands

Since this is a template/documentation project, there are no traditional build/test commands. However:

### Running Scripts

```bash
# Run a specific bash script
./music_mix/.specify/scripts/bash/<script-name>.sh

# Run with JSON output for parsing
./music_mix/.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```

### Validation Commands

```bash
# Check bash script syntax
bash -n script.sh

# Validate markdown files (install markdownlint first)
npx markdownlint ./**/*.md

# Check for common markdown issues
npx remark . --use remark-validate-links
```

### Linting

```bash
# ShellCheck for bash scripts (install via: brew install shellcheck)
shellcheck .specify/scripts/bash/*.sh
```

## Code Style Guidelines

### Bash Scripts (`.specify/scripts/bash/`)

#### File Structure
- Shebang: `#!/usr/bin/env bash` (not `/bin/bash` for portability)
- Include comment header describing script purpose
- Use `set -euo pipefail` for strict error handling
- Group related functions logically

#### Naming Conventions
- Functions: `snake_case` with descriptive names (e.g., `get_repo_root`)
- Variables: `snake_case`, lowercase (e.g., `repo_root`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `SPECIFY_FEATURE`)
- Scripts: `kebab-case` with `.sh` extension (e.g., `check-prerequisites.sh`)

#### Error Handling
- Use `local` for all function variables
- Redirect errors to stderr with `>&2`
- Return proper exit codes (0 for success, 1 for error)
- Check command results with `if command; then` pattern
- Use `[[ -d "$dir" ]]` and `[[ -f "$file" ]]` for file checks

#### Variables and Parameter Handling
- Always quote variables: `"$variable"` not `$variable`
- Use `${variable:-default}` for defaults
- Use `${BASH_SOURCE[0]}` for script path resolution
- Handle edge cases with `CDPATH=""` when changing directories

#### Example Function Pattern
```bash
#!/usr/bin/env bash

get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi
}
```

### Markdown Files (`.opencode/command/`)

#### Frontmatter
- Include YAML frontmatter with `description` field
- Use `---` fences for frontmatter

#### Structure
- Use numbered sections with `##` for major sections
- Use `###` for subsections
- Include "User Input" section for command arguments
- Use code blocks with language hints: ```bash, ```text, ```json

#### Formatting
- Maximum line width: 120 characters
- Use tables for structured data
- Use bullet points for lists
- Include code examples in fenced blocks

#### Command Files Pattern
```markdown
---
description: [One-line description of what the command does]
---

## User Input

$ARGUMENTS

## Outline

1. Step one
2. Step two

## Operating Principles

- Principle one
- Principle two
```

### Template Files (`.specify/templates/`)

#### Structure
- Include placeholder comments: `<!-- Example: ... -->`
- Use ALL_CAPS for placeholders: `[PLACEHOLDER_NAME]`
- Include version metadata at bottom
- Document all sections with examples

### Git Conventions

#### Branch Naming
- Format: `XXX-description` (e.g., `001-add-feature`, `004-fix-bug`)
- Three-digit numeric prefix for ordering

#### Commit Messages
- Use conventional commits format: `type: description`
- Types: `feat`, `fix`, `docs`, `chore`, `refactor`

### Best Practices

1. **Idempotency**: Scripts should be safe to run multiple times
2. **Portability**: Use POSIX-compliant patterns where possible
3. **Error Messages**: Provide clear, actionable error messages
4. **Documentation**: Document all functions with comments
5. **Testing**: Test edge cases (empty inputs, missing files, etc.)
6. **Security**: Never expose secrets in logs or error messages
7. **Performance**: Avoid subshells where not needed; use local variables

### File Organization

```
.specify/
├── memory/
│   └── constitution.md          # Project principles
├── scripts/
│   └── bash/
│       ├── common.sh            # Shared functions
│       ├── check-prerequisites.sh
│       └── ...
└── templates/
    ├── spec-template.md
    ├── plan-template.md
    └── tasks-template.md

.opencode/
└── command/
    ├── speckit.analyze.md
    ├── speckit.implement.md
    └── ...
```

### Common Patterns

#### Path Resolution
```bash
local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
```

#### JSON Parsing
```bash
# Use jq if available
result=$(some_command --json | jq -r '.field')
```

#### Checking Prerequisites
```bash
check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
```

### Error Codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | General error |
| 2    | Misuse of command |
| 126  | Command not executable |
| 127  | Command not found |

## Version

This AGENTS.md was created for Specify/OpenCode template projects.
Last updated: 2026-02-17
