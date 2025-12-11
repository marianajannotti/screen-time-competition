# Utility Scripts

This directory contains utility scripts for database setup, testing, and maintenance.

## Scripts

### `test_setup_badges.py`
Seeds the database with initial badge data.

**Usage:**
```bash
python scripts/test_setup_badges.py
```

**Purpose:**
- Creates all badge definitions in the database
- Useful for initial setup or resetting badge data
- Can be run multiple times safely (checks for existing badges)

### `test_badge_logic.py`
Manual script to test badge awarding logic.

**Usage:**
```bash
python scripts/test_badge_logic.py
```

**Purpose:**
- Tests badge awarding functionality
- Updates user streak and checks which badges are awarded
- Useful for debugging badge logic

## Running Scripts

All scripts should be run from the project root:

```bash
# From project root
python scripts/script_name.py
```

Scripts use the development database (`instance/app.db`) by default.

## Adding New Scripts

When adding utility scripts:
1. Place them in this directory
2. Add documentation to this README
3. Use `#!/usr/bin/env python3` shebang
4. Include usage instructions in the script docstring
