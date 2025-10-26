# CI Workflow Not Included

The `.github/workflows/validate.yml` file was created but could not be pushed due to GitHub App permissions (requires `workflows` permission).

## To Add CI Validation

Create `.github/workflows/validate.yml` with the following content:

```yaml
name: Validate Plugins

on:
  push:
    branches: [ main, claude/** ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install jsonschema

      - name: Validate plugin manifests
        run: |
          python tools/validate_plugins.py

      - name: Check for unpinned remote sources
        run: |
          echo "Checking for unpinned remote sources..."
          UNPINNED=$(grep -r "raw.githubusercontent.com.*\/main\/" plugins/ || true)
          if [ -n "$UNPINNED" ]; then
            echo "❌ ERROR: Found unpinned remote sources (using /main/):"
            echo "$UNPINNED"
            echo ""
            echo "Remote sources must be pinned to commit SHAs."
            echo "Example: https://raw.githubusercontent.com/user/repo/<commit-sha>/path/to/file"
            exit 1
          fi
          echo "✓ No unpinned sources found"

      - name: Check for missing integrity hashes
        run: |
          echo "Checking for remote sources without integrity hashes..."
          python -c "
          import json, sys
          from pathlib import Path

          errors = 0
          for pf in Path('plugins').glob('*/plugin.json'):
              data = json.loads(pf.read_text())
              for block in ('agents', 'hooks', 'commands', 'workflows', 'mcp', 'helpers'):
                  for item in data.get(block, []):
                      src = item.get('source', '')
                      if src.startswith('http') and not item.get('integrity'):
                          print(f'⚠️  {pf.parent.name}: {block}/{item.get(\"name\")} missing integrity')
                          errors += 1

          if errors > 0:
              print(f'\n⚠️  {errors} remote sources missing integrity hashes')
              print('Add \"integrity\": \"<sha256-hash>\" to each remote source')
          else:
              print('✓ All remote sources have integrity hashes')
          "

      - name: Lint Python files (if any)
        run: |
          if [ -d "qts" ]; then
            pip install flake8
            flake8 qts --count --select=E9,F63,F7,F82 --show-source --statistics || true
          fi

      - name: Summary
        run: |
          echo "✅ Plugin validation complete"
```

## Manual Validation

You can run validation locally anytime:

```bash
pip install jsonschema
python tools/validate_plugins.py
```

This will check all plugins for:
- Schema compliance
- Unpinned remote sources
- Missing integrity hashes
- Trading plugins missing risk config
