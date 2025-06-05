"""Utility functions for Git Vitae."""

import re
from pathlib import Path
from typing import Dict, List, Set


def detect_language_from_extension(file_path: Path) -> str:
    """Detect programming language from file extension."""
    extension_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JavaScript',
        '.tsx': 'TypeScript',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.h': 'C/C++',
        '.hpp': 'C++',
        '.cs': 'C#',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.R': 'R',
        '.m': 'Objective-C',
        '.mm': 'Objective-C++',
        '.dart': 'Dart',
        '.lua': 'Lua',
        '.pl': 'Perl',
        '.sh': 'Shell',
        '.bash': 'Shell',
        '.zsh': 'Shell',
        '.fish': 'Shell',
        '.ps1': 'PowerShell',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.vue': 'Vue',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.md': 'Markdown',
        '.tex': 'LaTeX',
    }
    
    return extension_map.get(file_path.suffix.lower(), 'Other')


def extract_frameworks_from_files(repo_path: Path) -> Set[str]:
    """Extract frameworks and libraries from repository files."""
    frameworks = set()
    
    # Check package.json for Node.js frameworks
    package_json = repo_path / "package.json"
    if package_json.exists():
        try:
            import json
            with open(package_json) as f:
                data = json.load(f)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                # Map common packages to frameworks
                framework_map = {
                    'react': 'React',
                    'vue': 'Vue.js',
                    'angular': 'Angular',
                    'express': 'Express.js',
                    'next': 'Next.js',
                    'nuxt': 'Nuxt.js',
                    'svelte': 'Svelte',
                    'gatsby': 'Gatsby',
                    'webpack': 'Webpack',
                    'vite': 'Vite',
                    'typescript': 'TypeScript',
                    'jest': 'Jest',
                    'mocha': 'Mocha',
                    'cypress': 'Cypress',
                }
                
                for pkg in deps:
                    for key, framework in framework_map.items():
                        if key in pkg.lower():
                            frameworks.add(framework)
        except:
            pass
    
    # Check requirements.txt for Python frameworks
    requirements = repo_path / "requirements.txt"
    if requirements.exists():
        try:
            with open(requirements) as f:
                content = f.read().lower()
                python_frameworks = {
                    'django': 'Django',
                    'flask': 'Flask',
                    'fastapi': 'FastAPI',
                    'tornado': 'Tornado',
                    'pyramid': 'Pyramid',
                    'pandas': 'Pandas',
                    'numpy': 'NumPy',
                    'scikit-learn': 'Scikit-learn',
                    'tensorflow': 'TensorFlow',
                    'pytorch': 'PyTorch',
                    'keras': 'Keras',
                    'requests': 'Requests',
                    'selenium': 'Selenium',
                    'pytest': 'Pytest',
                }
                
                for pkg, framework in python_frameworks.items():
                    if pkg in content:
                        frameworks.add(framework)
        except:
            pass
    
    # Check Cargo.toml for Rust
    cargo_toml = repo_path / "Cargo.toml"
    if cargo_toml.exists():
        frameworks.add('Cargo')
        try:
            with open(cargo_toml) as f:
                content = f.read().lower()
                if 'tokio' in content:
                    frameworks.add('Tokio')
                if 'serde' in content:
                    frameworks.add('Serde')
        except:
            pass
    
    # Check pom.xml for Java
    pom_xml = repo_path / "pom.xml"
    if pom_xml.exists():
        frameworks.add('Maven')
        try:
            with open(pom_xml) as f:
                content = f.read().lower()
                if 'spring' in content:
                    frameworks.add('Spring')
                if 'junit' in content:
                    frameworks.add('JUnit')
        except:
            pass
    
    # Check for Docker
    if (repo_path / "Dockerfile").exists() or (repo_path / "docker-compose.yml").exists():
        frameworks.add('Docker')
    
    # Check for Kubernetes
    if (repo_path / "k8s").exists() or (repo_path / "kubernetes").exists():
        frameworks.add('Kubernetes')
    
    return frameworks


def extract_description_from_readme(repo_path: Path) -> str:
    """Extract project description from README file."""
    readme_files = ["README.md", "README.txt", "README.rst", "README"]
    
    for readme_name in readme_files:
        readme_path = repo_path / readme_name
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract first meaningful paragraph
                lines = content.split('\n')
                description_lines = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('#'):
                        continue
                    if line.startswith('!['):
                        continue
                    if line.startswith('[!['):
                        continue
                    
                    description_lines.append(line)
                    if len(description_lines) >= 3:
                        break
                
                description = ' '.join(description_lines)
                
                # Clean up markdown
                description = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', description)
                description = re.sub(r'\*\*([^\*]+)\*\*', r'\1', description)
                description = re.sub(r'\*([^\*]+)\*', r'\1', description)
                description = re.sub(r'`([^`]+)`', r'\1', description)
                
                return description[:500] if description else ""
                
            except:
                continue
    
    return ""


def calculate_language_percentages(language_counts: Dict[str, int]) -> Dict[str, float]:
    """Calculate percentage distribution of languages."""
    total_files = sum(language_counts.values())
    if total_files == 0:
        return {}
    
    return {
        lang: round((count / total_files) * 100, 1)
        for lang, count in language_counts.items()
    }