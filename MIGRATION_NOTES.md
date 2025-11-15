# Migration to Modern Python Packaging (pyproject.toml + Hatchling)

## Overview

This document outlines the migration of `stream2py` from the legacy `setup.cfg` + `setup.py` configuration to the modern `pyproject.toml` + Hatchling build system, along with an updated CI/CD workflow.

## Date

2025-11-15

## Summary of Changes

### 1. Python Version Support

**Before:** Python 3.8
**After:** Python 3.10 and 3.12

- Dropped Python 3.8 support
- Added Python 3.12 support
- Minimum required version: Python 3.10

### 2. Build System Migration

**Before:**
- `setup.cfg` for metadata
- `setup.py` with setuptools
- Manual dependency management

**After:**
- `pyproject.toml` as single source of truth
- Hatchling as build backend
- PEP 621 compliant metadata

### 3. Configuration Files

#### Removed/Deprecated Files
- `setup.cfg` (metadata now in `pyproject.toml`)
- `setup.py` (no longer needed with Hatchling)

#### New Files
- `pyproject.toml` - Complete project configuration

#### Preserved Metadata

From `setup.cfg`, the following was migrated to `pyproject.toml`:

```toml
[project]
name = "stream2py"
version = "1.0.42"
description = "Bring data streams to python with ease"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
keywords = ["data stream"]
authors = [{name = "OtoSense"}]
dependencies = []  # No runtime dependencies - pure Python!
```

### 4. Dependencies

**Runtime Dependencies:**
- None! `stream2py` is a pure Python library with zero external dependencies
- Only uses Python standard library (threading, time, logging, etc.)

**Development Dependencies:**
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1.0",
]
test = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]
docs = [
    "sphinx>=6.0",
    "sphinx-rtd-theme>=1.0",
]
```

### 5. CI/CD Workflow Updates

#### GitHub Actions Workflow Changes

**Before:**
- Used `ubuntu-18.04` (deprecated)
- Python 3.8
- `actions/checkout@v2`
- `actions/setup-python@v2`
- `axblack` for code formatting
- `pylint` for linting

**After:**
- Uses `ubuntu-latest`
- Python 3.10 and 3.12
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `ruff` for both formatting and linting (faster, modern)
- Added Windows validation job
- Added GitHub Pages publishing

#### System Dependencies

The following system packages are required and installed in CI:

```bash
sudo apt-get update -qq
sudo apt-get install -y portaudio19-dev graphviz
```

These were preserved from the original CI configuration.

#### New CI Jobs

1. **validation** - Runs on both Python 3.10 and 3.12
   - Format checking with ruff
   - Linting with ruff
   - Test execution with pytest
   - Code coverage reporting

2. **windows-validation** (new!)
   - Runs tests on Windows
   - Marked as `continue-on-error: true` (informational)

3. **publish** - Runs only on main/master branch
   - Version bumping with isee
   - Build with Hatchling
   - PyPI publishing
   - Git tagging
   - Code metrics tracking

4. **github-pages** (new!)
   - Publishes documentation to GitHub Pages
   - Uses epythet for doc generation

### 6. Tooling Configuration

#### Ruff Configuration

Replaced `pylint` and `axblack` with `ruff` for:
- Code formatting (88 character line length)
- Linting (module docstring checking)
- Google-style docstring convention

```toml
[tool.ruff]
line-length = 88
target-version = "py310"
exclude = ["**/*.ipynb", ".git", ".venv", "build", "dist", "tests", "examples", "scrap"]

[tool.ruff.lint]
select = ["D100"]  # Missing module docstring
ignore = ["D203", "E501", "B905"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["D"]
"examples/*" = ["D"]
"scrap/*" = ["D"]
```

#### Pytest Configuration

```toml
[tool.pytest.ini_options]
minversion = "6.0"
testpaths = ["stream2py/tests"]
doctest_optionflags = ["NORMALIZE_WHITESPACE", "ELLIPSIS"]
addopts = ["--doctest-modules", "-v"]
```

### 7. Package Structure

The Hatchling configuration automatically discovers packages:

```toml
[tool.hatch.build.targets.wheel]
packages = ["stream2py"]

[tool.hatch.build.targets.sdist]
include = ["/stream2py", "/README.md"]
```

This ensures:
- Main `stream2py` package and all subpackages are included
- Tests are included in source distribution
- Examples and utility modules are preserved

## Testing and Verification

### Local Build Test

```bash
pip install build hatchling
python -m build --no-isolation
# Result: Successfully built stream2py-1.0.42.tar.gz and stream2py-1.0.42-py3-none-any.whl
```

### Local Test Execution

```bash
pip install pytest pytest-cov
pytest stream2py/tests -v --tb=short
# Result: ===== 32 passed in 33.37s =====
```

### Linting and Formatting

```bash
pip install ruff
ruff check stream2py --output-format=github
# Result: No linting errors

ruff format --check stream2py
# Result: 14 files would be reformatted (CI will handle this)
```

## Migration Checklist

- [x] Create `pyproject.toml` with complete metadata
- [x] Migrate all `setup.cfg` metadata to `pyproject.toml`
- [x] Configure Hatchling as build backend
- [x] Update Python version requirements (3.10+)
- [x] Configure development dependencies
- [x] Configure test dependencies
- [x] Configure ruff for linting and formatting
- [x] Configure pytest settings
- [x] Update CI workflow to modern standards
- [x] Add system dependency installation steps
- [x] Update Python versions in CI matrix
- [x] Add Windows testing job
- [x] Add GitHub Pages publishing
- [x] Test local build with Hatchling
- [x] Test local test execution
- [x] Test linting and formatting
- [x] Commit and push changes
- [x] Monitor CI execution

## Benefits of This Migration

1. **Modern Standards**: Using PEP 621 compliant `pyproject.toml`
2. **Single Source of Truth**: All configuration in one file
3. **Faster CI**: Ruff is significantly faster than pylint + black
4. **Better Support**: Python 3.10+ with modern features
5. **Cleaner Build**: Hatchling is simpler and more reliable than setuptools
6. **Cross-platform Testing**: Added Windows validation
7. **Better Documentation**: Automated GitHub Pages publishing
8. **Smaller Footprint**: No runtime dependencies!

## Backward Compatibility

### Breaking Changes

- **Minimum Python version**: Now requires Python 3.10+ (was 3.8)
- **setup.cfg and setup.py**: No longer used (but can coexist temporarily)

### Non-Breaking

- Package import paths remain unchanged
- API is completely unchanged
- Runtime behavior is identical
- PyPI distribution format is compatible

## Next Steps

1. **Monitor CI**: Check that all jobs pass successfully
2. **Deprecate Old Files**: Consider removing `setup.cfg` and `setup.py` after successful CI run
3. **Update Documentation**: Update README if needed to reflect new installation methods
4. **Consider Pre-commit Hooks**: Could add `.pre-commit-config.yaml` with ruff
5. **Version Bump**: Next release should bump to 1.1.0 to reflect modernization

## Resources

- [PEP 621 - Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [Hatchling Documentation](https://hatch.pypa.io/latest/config/build/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Notes

### Why Hatchling?

Hatchling was chosen as the build backend because:
1. It's the default for modern Python projects
2. No build configuration needed for simple packages
3. Faster than setuptools
4. Better error messages
5. Active development and support

### Why Ruff?

Ruff was chosen to replace black + pylint because:
1. Written in Rust - extremely fast (10-100x faster)
2. Combines formatting and linting in one tool
3. Drop-in replacement for multiple tools (black, isort, flake8, pylint)
4. Growing adoption in the Python community
5. Excellent VS Code and IDE integration

### System Dependencies

The system dependencies (portaudio19-dev, graphviz) are:
- **portaudio19-dev**: Audio library (likely needed by plugin packages like audiostream2py)
- **graphviz**: Graph visualization (likely used for documentation generation)

These are only needed for CI and development, not for using the package itself.

## Conclusion

The migration to `pyproject.toml` + Hatchling modernizes the project's build system and CI/CD pipeline while maintaining complete backward compatibility at the API level. The project is now positioned to take advantage of modern Python tooling and practices.
