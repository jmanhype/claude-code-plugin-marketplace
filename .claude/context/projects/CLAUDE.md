# Projects Context

## Purpose

This file serves as the project index and navigation guide for Claude Code agent working on repositories.

---

## Current Project: Claude Code Plugin Marketplace

### Overview

- **Repository**: jmanhype/claude-code-plugin-marketplace
- **Purpose**: Community-driven marketplace for Claude Code plugins, skills, and MCP servers
- **Main Branch**: main (or master)
- **Current Feature Branch**: claude/create-ace-context-md-011CUUG1B8WM9uWwRvgYRZK6

### Project Structure

```
claude-code-plugin-marketplace/
├── plugins/                    # Plugin definitions
│   ├── example-plugin/        # Individual plugin directories
│   │   ├── metadata.json      # Plugin metadata
│   │   └── README.md          # Plugin documentation
├── schemas/                    # JSON schemas for validation
│   └── plugin.schema.json     # Plugin metadata schema
├── scripts/                    # Utility scripts
│   └── validate.js            # Validation tools
├── marketplace.json            # Central marketplace index
├── README.md                   # Main documentation
└── .claude/                    # Claude Code context (new)
    └── context/                # Context system files
```

### Key Files

- `marketplace.json`: Central registry of all plugins
- `schemas/plugin.schema.json`: Validation schema for plugin metadata
- `README.md`: Marketplace documentation and usage guide
- Plugin directories: Each contains `metadata.json` and `README.md`

### Conventions

#### Plugin Structure

Each plugin should have:

- Unique directory under `plugins/`
- `metadata.json` with required fields (name, version, description, author, etc.)
- `README.md` with detailed documentation
- Entry in `marketplace.json`

#### Naming Conventions

- Plugin directories: kebab-case (e.g., `example-plugin`)
- Branch names: `claude/<descriptive-name>-<session-id>`
- Commit messages: Conventional Commits style (feat:, fix:, docs:, etc.)

#### Validation

- All plugins must pass schema validation
- Use `scripts/validate.js` to check plugin metadata
- Ensure `marketplace.json` is valid JSON

---

## Navigation Patterns

### Finding Plugins

```bash
# List all plugins
ls plugins/

# Search for specific functionality
grep -r "keyword" plugins/*/metadata.json

# Find plugins by tag
grep -r '"tags":.*"specific-tag"' plugins/*/metadata.json
```

### Common Tasks

#### Adding a New Plugin

1. Create plugin directory: `plugins/new-plugin/`
2. Create `metadata.json` with required fields
3. Create `README.md` with documentation
4. Add entry to `marketplace.json`
5. Validate with `scripts/validate.js`
6. Commit and push

#### Updating Plugin

1. Modify `metadata.json` and/or `README.md`
2. Update `marketplace.json` if metadata changed
3. Increment version number
4. Validate changes
5. Commit with descriptive message

---

## Project-Specific Patterns

### Git Workflow

- Always work on feature branches starting with `claude/`
- Push to feature branch, not main/master
- Use `-u origin <branch-name>` when pushing
- Retry push up to 4 times with exponential backoff on network errors

### Commit Style

```
feat: Add new plugin for X functionality
fix: Correct schema validation for Y field
docs: Update README with installation instructions
refactor: Reorganize plugin directory structure
```

### Testing

- Validate all JSON files before committing
- Check that `marketplace.json` has valid structure
- Ensure plugin metadata matches schema
- Test that README renders correctly

---

## Domain-Specific Knowledge

### Marketplace Schema Requirements

Plugin `metadata.json` typically requires:

- `name`: Unique plugin identifier
- `version`: Semantic version (e.g., "1.0.0")
- `description`: Brief description of functionality
- `author`: Plugin author information
- `tags`: Array of relevant tags for categorization
- `repository`: Source repository URL (optional)
- `license`: License identifier (e.g., "MIT")

### Plugin Categories

Common plugin types in this marketplace:

- **Skills**: Extend Claude Code with new capabilities
- **Tools**: Utility tools and integrations
- **Templates**: Project templates and boilerplates
- **MCP Servers**: Model Context Protocol server integrations
- **Workflows**: Common development workflows

---

## Project Dependencies

### Required Tools

- Node.js (for validation scripts)
- Git (for version control)
- Text editor with JSON validation

### Optional Tools

- `jq` for JSON manipulation
- `prettier` for JSON formatting
- JSON schema validators

---

## Common Pitfalls

### ❌ Anti-patterns

- Modifying `marketplace.json` without updating plugin metadata
- Creating plugins without proper validation
- Pushing directly to main branch
- Inconsistent naming conventions
- Missing or incomplete documentation

### ✅ Best Practices

- Validate before committing
- Keep plugin metadata and marketplace.json in sync
- Write comprehensive READMEs
- Use semantic versioning
- Follow established directory structure
- Test plugins before publishing

---

## Related Projects

This marketplace is designed for Claude Code plugins. Related ecosystems:

- Claude Code official documentation
- MCP (Model Context Protocol) servers
- Community-contributed skills and tools

---

## Quick Reference

### Before Starting Work

- [ ] Confirm current branch
- [ ] Read project README
- [ ] Review existing plugin structure
- [ ] Check schema requirements

### Before Committing

- [ ] Validate all JSON files
- [ ] Check `marketplace.json` syntax
- [ ] Verify plugin metadata completeness
- [ ] Test that changes don't break existing structure
- [ ] Write clear commit message

### Before Pushing

- [ ] Ensure on correct feature branch
- [ ] Verify branch name starts with `claude/`
- [ ] Use `git push -u origin <branch-name>`
- [ ] Retry on network errors if needed

---

## Future Enhancements

Potential improvements for this project:

- Automated plugin validation in CI/CD
- Plugin search and discovery tools
- Version compatibility checking
- Automated marketplace.json updates
- Plugin installation tools
- Community ratings and reviews

---

**Last Updated**: 2025-10-25
