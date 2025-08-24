# Root Directory Structure

## Essential Files Kept in Root

### Documentation
- `README.md` - Main project documentation
- `CLAUDE.md` - Claude AI development guidelines
- `AGENTS.md` - Agent architecture documentation

### Configuration
- `.env` - Environment variables (git-ignored)
- `.env.example` - Example environment configuration
- `.env.streamlit` - Streamlit-specific config
- `.gitignore` - Git ignore rules
- `.pre-commit-config.yaml` - Pre-commit hooks

### Project Files
- `Makefile` - Build and development commands
- `pyproject.toml` - Python project configuration
- `uv.lock` - Dependency lock file
- `LICENSE` - Project license

### Testing
- `.coverage` - Test coverage data (git-ignored)

## Archived Content

### `/docs/fixes/`
All fix-related documentation has been moved here:
- Codebase fixes and audits
- GPT-5 integration fixes
- Production issue resolutions
- Post-mortem analyses

### `/docs/`
- `API_CONTRACT_RESPONSES.md` - API contract documentation
- Other design and architecture documents

### `/tests/archived/`
- One-off test scripts
- Debug artifacts
- Test images and JSON responses

## Clean Root Benefits

1. **Clarity** - Only essential files visible at first glance
2. **Organization** - Related documentation grouped together
3. **Maintenance** - Easier to find current vs historical docs
4. **Professional** - Clean root shows well-organized project