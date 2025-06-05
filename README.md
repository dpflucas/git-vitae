# Git Vitae

An AI-powered terminal utility that scans git repositories and generates a comprehensive curriculum vitae based on your coding activity and projects.

## Features

- 🔍 **Repository Discovery**: Automatically scans and analyzes all git repositories in the current directory
- 📊 **Code Analysis**: Extracts programming languages, frameworks, commit statistics, and project metadata
- 🤖 **AI-Powered Generation**: Uses OpenAI GPT or Anthropic Claude to generate professional CV content
- 📝 **Multiple Formats**: Outputs in Markdown, HTML, JSON, or plain text
- ⚙️ **Customizable**: Configurable templates, styles, and analysis depth
- 🎯 **Professional Focus**: Generates CV content suitable for technical roles
- 🔒 **Privacy-First**: Anonymizes all data before sending to AI services, removing personal and sensitive information

## Installation

### From Source

```bash
git clone https://github.com/your-username/git-vitae.git
cd git-vitae
pip install -e .
```

### Using pip (when published)

```bash
pip install git-vitae
```

## Quick Start

1. **Set up API credentials** (choose one method):
   ```bash
   # Method 1: Environment variables (recommended)
   export OPENAI_API_KEY="your-openai-key"
   # or
   export ANTHROPIC_API_KEY="your-anthropic-key"
   
   # Method 2: Configuration file
   git-vitae config init
   # Then edit ~/.git-vitae/config.yaml to add your ai_api_key
   ```

2. **Generate your CV**:
   ```bash
   cd /path/to/your/projects
   git-vitae generate -o my-cv.md
   ```

3. **View your generated CV**:
   ```bash
   cat my-cv.md
   ```

## Usage

### Getting Help

For detailed information about available commands and options:
```bash
# General help
git-vitae --help

# Help for specific commands
git-vitae generate --help
git-vitae config --help
```

### Basic Commands

Generate CV in different formats:
```bash
# Markdown (default)
git-vitae generate -o cv.md

# HTML
git-vitae generate -f html -o cv.html

# JSON for further processing
git-vitae generate -f json -o cv.json

# Plain text
git-vitae generate -f text -o cv.txt
```

### Advanced Options

```bash
# Use specific AI provider and model
git-vitae generate --ai-provider anthropic --model claude-3-opus -o cv.md

# Customize scanning depth and include private repos
git-vitae generate --max-depth 5 --include-private -o cv.md

# Use custom template and style
git-vitae generate --template technical --style creative -o cv.md

# Scan a specific directory instead of current directory
git-vitae generate --scan-path /path/to/projects -o cv.md

# Privacy options (use with caution)
git-vitae generate --no-anonymize -o cv.md  # Disable anonymization
git-vitae generate --allow-sensitive -o cv.md  # Allow sensitive data
```

### Configuration

Create a configuration file:
```bash
git-vitae config init
```

View current configuration:
```bash
git-vitae config show
```

Example configuration file (`~/.git-vitae/config.yaml`):
```yaml
ai_provider: openai
ai_model: gpt-4
ai_api_key: your-api-key-here  # Optional: env vars take precedence
scan_path: "/path/to/your/projects"  # Optional: defaults to current directory
max_depth: 3
include_hidden: false
include_private: true
ignore_patterns:
  - "node_modules"
  - ".git"
  - "__pycache__"
default_format: markdown
default_template: default
default_style: professional
include_metrics: true
include_timeline: true
group_by_language: true
anonymize_data: true
allow_sensitive_data: false
```

## What Gets Analyzed

Git Vitae analyzes your repositories to extract:

- **Programming Languages**: File extensions and language distribution
- **Frameworks & Libraries**: Package files (package.json, requirements.txt, Cargo.toml, etc.)
- **Project Information**: README descriptions, repository structure
- **Contribution Metrics**: Commit counts, lines of code, activity patterns
- **Technical Skills**: Inferred from code patterns and dependencies
- **Project Timeline**: Commit history and development activity

## Privacy & Security

Git Vitae is designed with privacy as a priority:

### Data Anonymization (Default)
- **Project names** are replaced with generic identifiers (e.g., "Web Development Project")
- **Personal names** and **email addresses** are removed from all data
- **URLs** and **file paths** are sanitized or removed
- **API keys**, **passwords**, and other **sensitive patterns** are filtered out
- Only **technical metadata** (languages, frameworks, metrics) is sent to AI services

### What Gets Sent to AI
When anonymization is enabled (default), only the following anonymous data is sent:
- Programming language percentages
- Framework and tool names (after safety filtering)
- Project type classifications (e.g., "web_development", "data_science")
- Aggregated metrics (commit counts, file counts, lines of code)
- Activity patterns (without timestamps or personal identifiers)

### Privacy Controls
```bash
# Default: Full anonymization (recommended)
git-vitae generate -o cv.md

# Disable anonymization (not recommended)
git-vitae generate --no-anonymize -o cv.md

# Allow sensitive data patterns (use with extreme caution)
git-vitae generate --allow-sensitive -o cv.md
```

⚠️ **Warning**: Disabling anonymization may send personal information, project names, and potentially sensitive data to AI services.

## Sample Output

```markdown
# John Developer

**Email**: john@example.com  
**GitHub**: github.com/johndeveloper  
**Generated**: 2024-01-15

## Professional Summary

Experienced full-stack developer with demonstrated expertise across 15+ projects spanning web development, data analysis, and DevOps automation. Strong proficiency in Python, JavaScript, and cloud technologies with a track record of building scalable applications.

## Technical Skills

### Programming Languages
- Python (Expert): 45% of codebase, 2,341 commits
- JavaScript (Advanced): 30% of codebase, 1,567 commits  
- TypeScript (Intermediate): 15% of codebase, 834 commits

### Frameworks & Libraries
- Backend: Django, FastAPI, Express.js, Flask
- Frontend: React, Vue.js, Next.js
- Data Science: Pandas, NumPy, Scikit-learn

## Key Projects

### E-Commerce Platform
**Technologies**: Python, Django, PostgreSQL, Redis, Docker  
**Contributions**: 834 commits, 45,000+ lines of code
- Architected scalable backend serving 100k+ daily users
- Implemented real-time inventory management system

## Contribution Metrics

- **Total Commits**: 5,234 across 15 repositories
- **Code Volume**: 127,000+ lines added
- **Active Period**: 3 years of consistent contributions
```

## Supported AI Providers

- **OpenAI**
- **Anthropic**

## Templates

- **default**: Clean, professional layout
- **professional**: Business-focused template with formal styling
- **creative**: Stylized template with emojis and creative formatting
- **technical**: Code-focused template with technical formatting

## Requirements

- Python 3.8+
- Git repositories to analyze
- API key for OpenAI or Anthropic

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and add tests
4. Run tests: `python -m pytest tests/`
5. Submit a pull request

## Development Setup

```bash
git clone https://github.com/your-username/git-vitae.git
cd git-vitae
pip install -e .
pip install -r requirements-dev.txt
```

Run tests:
```bash
python -m pytest tests/ -v
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Troubleshooting

### Common Issues

**No repositories found**: Ensure you're running the command in a directory containing git repositories.

**API errors**: Verify your API key is correctly set and has sufficient credits/quota.

**Permission errors**: Make sure you have read access to all repositories being scanned.

**Memory issues**: Use `--max-depth` to limit scanning depth for large directory structures.

## Support

- 📖 [Documentation](docs/)
- 🐛 [Report Issues](https://github.com/your-username/git-vitae/issues)
- 💬 [Discussions](https://github.com/your-username/git-vitae/discussions)

---

*Generate your professional CV from your code contributions with Git Vitae.*