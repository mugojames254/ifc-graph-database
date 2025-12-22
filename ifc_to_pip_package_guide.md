# IFC Graph Database: Pip Package Conversion Guide

This document provides step-by-step instructions for an LLM agent to convert the repository at `https://github.com/mugojames254/ifc-graph-database` into a publishable pip package.

## Overview

**Source Repository:** https://github.com/mugojames254/ifc-graph-database

**Current Structure:**
```
ifc-graph-database/
├── main.py
├── config.yaml
├── requirements.txt
├── .env.example
├── LICENSE
├── README.md
├── graph_processor/
│   ├── __init__.py
│   ├── element_filter.py
│   ├── neo4j_store.py
│   └── query_loader.py
├── cypher_queries/
│   └── *.cypher
└── images/
```

**Target Package Name:** `ifc-graph` (PyPI) / `ifc_graph` (Python import)

---

## Step 1: Restructure the Project

Transform the repository into the `src` layout, which is the modern Python packaging standard.

### Target Structure

```
ifc-graph-database/
├── src/
│   └── ifc_graph/
│       ├── __init__.py
│       ├── cli.py
│       ├── element_filter.py
│       ├── neo4j_store.py
│       ├── query_loader.py
│       └── cypher_queries/
│           ├── clear_database.cypher
│           ├── create_project.cypher
│           ├── create_elements_batch.cypher
│           ├── create_structures_batch.cypher
│           ├── create_materials_batch.cypher
│           └── [other .cypher files]
├── tests/
│   ├── __init__.py
│   ├── test_element_filter.py
│   ├── test_neo4j_store.py
│   └── conftest.py
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── config.yaml.example
└── .env.example
```

### Actions Required

1. Create `src/ifc_graph/` directory
2. Move all files from `graph_processor/` to `src/ifc_graph/`
3. Move `cypher_queries/` inside `src/ifc_graph/`
4. Extract CLI logic from `main.py` into `src/ifc_graph/cli.py`
5. Rename `config.yaml` to `config.yaml.example`
6. Create `tests/` directory with test files
7. Delete the old `graph_processor/` directory
8. Delete `main.py` (logic moved to cli.py)
9. Delete `requirements.txt` (replaced by pyproject.toml)

---

## Step 2: Create pyproject.toml

Create a `pyproject.toml` file in the repository root with the following content:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ifc-graph"
version = "0.1.0"
description = "Convert IFC BIM models to Neo4j graph database for querying building information"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "James Mugo", email = "deeplearningcentral@gmail.com"}
]
maintainers = [
    {name = "James Mugo", email = "deeplearningcentral@gmail.com"}
]
keywords = [
    "ifc",
    "bim",
    "neo4j",
    "graph-database",
    "building-information-modeling",
    "architecture",
    "construction",
    "aec",
    "ifcopenshell"
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
requires-python = ">=3.9"
dependencies = [
    "ifcopenshell>=0.7.0",
    "neo4j>=5.0.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]
docs = [
    "sphinx>=6.0",
    "sphinx-rtd-theme>=1.0",
]

[project.urls]
Homepage = "https://github.com/mugojames254/ifc-graph-database"
Documentation = "https://github.com/mugojames254/ifc-graph-database#readme"
Repository = "https://github.com/mugojames254/ifc-graph-database"
Issues = "https://github.com/mugojames254/ifc-graph-database/issues"
Changelog = "https://github.com/mugojames254/ifc-graph-database/releases"

[project.scripts]
ifc-graph = "ifc_graph.cli:main"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
ifc_graph = ["cypher_queries/*.cypher"]

[tool.black]
line-length = 88
target-version = ["py39", "py310", "py311", "py312"]

[tool.ruff]
line-length = 88
target-version = "py39"
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --cov=ifc_graph --cov-report=term-missing"

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

---

## Step 3: Update __init__.py

Replace the content of `src/ifc_graph/__init__.py` with:

```python
"""
IFC Graph Database

A Python library for converting IFC BIM models to Neo4j graph databases.
Enables graph-based querying of building information models.
"""

from .element_filter import IFCElementFilter
from .neo4j_store import Neo4jStore
from .query_loader import QueryLoader

__version__ = "0.1.0"
__author__ = "James Mugo"
__email__ = "deeplearningcentral@gmail.com"

__all__ = [
    "IFCElementFilter",
    "Neo4jStore", 
    "QueryLoader",
    "__version__",
]
```

**Note:** Adjust the class/function names based on what is actually exported from each module. Inspect the existing `graph_processor/__init__.py` and the module files to determine the correct exports.

---

## Step 4: Create the CLI Module

Create `src/ifc_graph/cli.py` by extracting and refactoring the logic from `main.py`:

```python
"""
Command-line interface for IFC Graph Database.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .element_filter import IFCElementFilter
from .neo4j_store import Neo4jStore


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the CLI."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="ifc-graph",
        description="Convert IFC BIM models to Neo4j graph database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ifc-graph --ifc-file model.ifc
  ifc-graph --ifc-file model.ifc --clear-db
  ifc-graph --ifc-file model.ifc --dry-run
  ifc-graph --config custom_config.yaml --ifc-file model.ifc
        """,
    )

    parser.add_argument(
        "--ifc-file",
        type=str,
        help="Path to the IFC file to process",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--clear-db",
        action="store_true",
        help="Clear database before importing (WARNING: deletes all existing data)",
    )
    parser.add_argument(
        "--neo4j-uri",
        type=str,
        help="Neo4j connection URI (overrides .env)",
    )
    parser.add_argument(
        "--neo4j-user",
        type=str,
        help="Neo4j username (overrides .env)",
    )
    parser.add_argument(
        "--neo4j-password",
        type=str,
        help="Neo4j password (overrides .env)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview import without modifying the database",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    return parser.parse_args()


def get_version() -> str:
    """Get the package version."""
    from . import __version__
    return __version__


def main() -> int:
    """Main entry point for the CLI."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    args = parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Get Neo4j connection details
    neo4j_uri = args.neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = args.neo4j_user or os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = args.neo4j_password or os.getenv("NEO4J_PASSWORD", "")

    # Get IFC file path
    ifc_file = args.ifc_file or os.getenv("IFC_FILE_PATH")
    
    if not ifc_file:
        logger.error("No IFC file specified. Use --ifc-file or set IFC_FILE_PATH in .env")
        return 1

    ifc_path = Path(ifc_file)
    if not ifc_path.exists():
        logger.error(f"IFC file not found: {ifc_path}")
        return 1

    try:
        # TODO: Implement the actual processing logic
        # This should be adapted from the original main.py
        
        logger.info(f"Processing IFC file: {ifc_path}")
        
        if args.dry_run:
            logger.info("DRY RUN: No changes will be made to the database")
            # Perform dry run logic
            return 0

        # Connect to Neo4j and process
        # ... (adapt from original main.py)

        logger.info("Processing complete!")
        return 0

    except Exception as e:
        logger.exception(f"Error processing IFC file: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

**Important:** The CLI module above is a template. You must adapt it by:
1. Copying the actual processing logic from the original `main.py`
2. Importing the correct classes and functions
3. Preserving all existing CLI arguments and functionality

---

## Step 5: Update Module Imports

In each module file (`element_filter.py`, `neo4j_store.py`, `query_loader.py`), update any relative imports.

### Example: If query_loader.py loads cypher files

Update the path resolution to use package resources:

```python
import importlib.resources as pkg_resources
from pathlib import Path

def get_cypher_query(query_name: str) -> str:
    """Load a Cypher query from the package's cypher_queries directory."""
    # For Python 3.9+
    with pkg_resources.files("ifc_graph.cypher_queries").joinpath(f"{query_name}.cypher").open() as f:
        return f.read()
```

Or using the older approach for broader compatibility:

```python
from pathlib import Path

def get_cypher_queries_dir() -> Path:
    """Get the path to the cypher_queries directory."""
    return Path(__file__).parent / "cypher_queries"

def get_cypher_query(query_name: str) -> str:
    """Load a Cypher query from file."""
    query_file = get_cypher_queries_dir() / f"{query_name}.cypher"
    return query_file.read_text()
```

---

## Step 6: Create Test Files

### tests/conftest.py

```python
"""
Pytest configuration and fixtures for IFC Graph tests.
"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_ifc_path() -> Path:
    """Path to a sample IFC file for testing."""
    # You may need to include a small test IFC file in tests/fixtures/
    return Path(__file__).parent / "fixtures" / "test_model.ifc"


@pytest.fixture
def neo4j_test_config() -> dict:
    """Neo4j configuration for testing."""
    return {
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "test_password",
    }
```

### tests/test_element_filter.py

```python
"""
Tests for the IFC element filter module.
"""

import pytest
from ifc_graph import IFCElementFilter


class TestIFCElementFilter:
    """Tests for IFCElementFilter class."""

    def test_filter_initialization(self):
        """Test that the filter can be initialized."""
        # Add actual tests based on the class implementation
        pass

    def test_extract_elements(self, sample_ifc_path):
        """Test element extraction from IFC file."""
        # Add actual tests
        pass
```

### tests/test_neo4j_store.py

```python
"""
Tests for the Neo4j store module.
"""

import pytest
from ifc_graph import Neo4jStore


class TestNeo4jStore:
    """Tests for Neo4jStore class."""

    def test_store_initialization(self, neo4j_test_config):
        """Test that the store can be initialized."""
        # Add actual tests based on the class implementation
        pass
```

---

## Step 7: Update .gitignore

Ensure `.gitignore` includes Python packaging artifacts:

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# IDE
.idea/
.vscode/
*.swp
*.swo

# Project specific
*.ifc
!tests/fixtures/*.ifc
config.yaml
```

---

## Step 8: Update README.md

Update the README to reflect the new installation method:

Add this section after the existing installation instructions:

```markdown
## Installation

### From PyPI (Recommended)

```bash
pip install ifc-graph
```

### From Source

```bash
git clone https://github.com/mugojames254/ifc-graph-database.git
cd ifc-graph-database
pip install -e .
```

### With Development Dependencies

```bash
pip install -e ".[dev]"
```

## Usage

### As a Command-Line Tool

```bash
# Basic usage
ifc-graph --ifc-file path/to/model.ifc

# With all options
ifc-graph --ifc-file model.ifc --clear-db --log-level DEBUG
```

### As a Python Library

```python
from ifc_graph import IFCElementFilter, Neo4jStore

# Extract elements from IFC file
filter = IFCElementFilter("path/to/model.ifc")
elements = filter.extract_elements()

# Store in Neo4j
store = Neo4jStore(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="your_password"
)
store.import_elements(elements)
```
```

---

## Step 9: Build the Package

Execute these commands to build and verify the package:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# This creates:
#   dist/ifc_graph-0.1.0.tar.gz      (source distribution)
#   dist/ifc_graph-0.1.0-py3-none-any.whl  (wheel)

# Verify the package contents
tar -tzf dist/ifc_graph-0.1.0.tar.gz
unzip -l dist/ifc_graph-0.1.0-py3-none-any.whl

# Check package metadata
twine check dist/*
```

---

## Step 10: Test Local Installation

```bash
# Create a fresh virtual environment for testing
python -m venv test_env
source test_env/bin/activate  # or test_env\Scripts\activate on Windows

# Install from the built wheel
pip install dist/ifc_graph-0.1.0-py3-none-any.whl

# Test the CLI
ifc-graph --version
ifc-graph --help

# Test the Python import
python -c "from ifc_graph import IFCElementFilter, Neo4jStore; print('Import successful!')"

# Run tests
pip install -e ".[dev]"
pytest
```

---

## Step 11: Publish to PyPI

### First: Publish to TestPyPI

```bash
# Create account at https://test.pypi.org/account/register/
# Generate API token at https://test.pypi.org/manage/account/token/

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ifc-graph
```

### Then: Publish to PyPI

```bash
# Create account at https://pypi.org/account/register/
# Generate API token at https://pypi.org/manage/account/token/

# Upload to PyPI
twine upload dist/*

# Verify installation
pip install ifc-graph
```

### Using a .pypirc File (Optional)

Create `~/.pypirc` for easier uploads:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
username = __token__
password = pypi-your-test-api-token-here
```

---

## Checklist Summary

Use this checklist to track progress:

- [ ] Create `src/ifc_graph/` directory structure
- [ ] Move `graph_processor/*.py` to `src/ifc_graph/`
- [ ] Move `cypher_queries/` to `src/ifc_graph/cypher_queries/`
- [ ] Create `pyproject.toml` with all metadata
- [ ] Update `src/ifc_graph/__init__.py` with exports
- [ ] Create `src/ifc_graph/cli.py` from `main.py` logic
- [ ] Update relative imports in all modules
- [ ] Update query_loader.py to find cypher files within package
- [ ] Create `tests/` directory with test files
- [ ] Update `.gitignore` for packaging artifacts
- [ ] Update `README.md` with pip install instructions
- [ ] Delete old files (`main.py`, `requirements.txt`, `graph_processor/`)
- [ ] Build package with `python -m build`
- [ ] Verify with `twine check dist/*`
- [ ] Test local installation in clean virtual environment
- [ ] Run tests with `pytest`
- [ ] Publish to TestPyPI
- [ ] Test installation from TestPyPI
- [ ] Publish to PyPI

---

## Common Issues and Solutions

### Issue: Cypher query files not included in package

**Solution:** Ensure `pyproject.toml` includes:
```toml
[tool.setuptools.package-data]
ifc_graph = ["cypher_queries/*.cypher"]
```

And verify with:
```bash
unzip -l dist/*.whl | grep cypher
```

### Issue: ifcopenshell installation fails

**Solution:** ifcopenshell may require system dependencies. Add to README:
```markdown
### Installing ifcopenshell

On some systems, you may need to install ifcopenshell separately:

```bash
# Using conda (recommended)
conda install -c conda-forge ifcopenshell

# Or using pip with pre-built wheels
pip install ifcopenshell
```
```

### Issue: Import errors after installation

**Solution:** Check that:
1. All `__init__.py` files exist
2. Relative imports use correct syntax (`.module` not `module`)
3. Package structure matches `[tool.setuptools.packages.find]` configuration

### Issue: CLI command not found after installation

**Solution:** Verify `[project.scripts]` in pyproject.toml points to correct function:
```toml
[project.scripts]
ifc-graph = "ifc_graph.cli:main"
```

And ensure `cli.py` has a `main()` function.

---

## Version Management

For future releases, update the version in two places:
1. `pyproject.toml`: `version = "X.Y.Z"`
2. `src/ifc_graph/__init__.py`: `__version__ = "X.Y.Z"`

Consider using `setuptools-scm` for automatic versioning from git tags:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel", "setuptools-scm>=8.0"]
build-backend = "setuptools.build_meta"

[project]
dynamic = ["version"]

[tool.setuptools_scm]
```

---

## Notes for the LLM Agent

1. **Preserve all existing functionality** - The goal is repackaging, not rewriting
2. **Test thoroughly** - Ensure the package works identically to the original
3. **Check imports carefully** - Moving files changes import paths
4. **Verify cypher files are included** - These are critical for functionality
5. **Maintain backward compatibility** - Users should be able to use the same CLI interface
6. **Document any changes** - Update README if behavior changes

---

*End of conversion guide*
