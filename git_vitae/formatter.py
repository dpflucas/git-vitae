"""CV formatter for different output formats."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, Template

from .models import CVContent


class CVFormatter:
    """Formats CV content into various output formats."""
    
    def __init__(self, template_dir: Path = None):
        """Initialize formatter with template directory."""
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"
        
        self.template_dir = template_dir
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.jinja_env.filters['number_format'] = self._format_number
    
    def format_cv(self, cv_content: CVContent, output_format: str = "markdown", template_name: str = "default") -> str:
        """Format CV content into specified output format."""
        if output_format == "json":
            return self._format_json(cv_content)
        elif output_format == "text":
            return self._format_text(cv_content)
        elif output_format == "markdown":
            return self._format_markdown(cv_content, template_name)
        elif output_format == "html":
            return self._format_html(cv_content, template_name)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def validate_template(self, template_name: str, format_type: str = "markdown") -> bool:
        """Check if a template exists for the given format."""
        template_file = self.template_dir / f"{template_name}.{format_type.replace('markdown', 'md')}"
        return template_file.exists()
    
    def list_available_templates(self, format_type: str = "markdown") -> list:
        """List all available templates for the given format."""
        extension = "md" if format_type == "markdown" else format_type
        pattern = f"*.{extension}"
        templates = []
        for template_file in self.template_dir.glob(pattern):
            templates.append(template_file.stem)
        return sorted(templates)
    
    def _format_json(self, cv_content: CVContent) -> str:
        """Format CV as JSON."""
        cv_dict = {
            "name": cv_content.name,
            "email": cv_content.email,
            "github_url": cv_content.github_url,
            "summary": cv_content.summary,
            "skills": cv_content.skills,
            "projects": [
                {
                    "name": project.name,
                    "description": project.description,
                    "technologies": project.technologies,
                    "commits": project.commits,
                    "lines_of_code": project.lines_of_code,
                    "url": project.url
                }
                for project in cv_content.projects
            ],
            "metrics": cv_content.metrics,
            "generated_at": cv_content.generated_at.isoformat()
        }
        return json.dumps(cv_dict, indent=2)
    
    def _format_text(self, cv_content: CVContent) -> str:
        """Format CV as plain text."""
        lines = []
        
        # Header
        lines.append(f"{'=' * 60}")
        lines.append(f"{cv_content.name or 'Developer'}")
        if cv_content.email:
            lines.append(f"Email: {cv_content.email}")
        if cv_content.github_url:
            lines.append(f"GitHub: {cv_content.github_url}")
        lines.append(f"Generated: {cv_content.generated_at.strftime('%Y-%m-%d')}")
        lines.append(f"{'=' * 60}")
        lines.append("")
        
        # Summary
        if cv_content.summary:
            lines.append("PROFESSIONAL SUMMARY")
            lines.append("-" * 20)
            lines.append(cv_content.summary)
            lines.append("")
        
        # Skills
        if cv_content.skills:
            lines.append("TECHNICAL SKILLS")
            lines.append("-" * 15)
            for category, skills in cv_content.skills.items():
                if skills:
                    lines.append(f"{category}:")
                    lines.append(f"  {', '.join(skills)}")
            lines.append("")
        
        # Projects
        if cv_content.projects:
            lines.append("KEY PROJECTS")
            lines.append("-" * 12)
            for project in cv_content.projects:
                lines.append(f"• {project.name}")
                lines.append(f"  {project.description}")
                lines.append(f"  Technologies: {', '.join(project.technologies)}")
                lines.append(f"  Commits: {project.commits}, Lines: {project.lines_of_code:,}")
                if project.url:
                    lines.append(f"  URL: {project.url}")
                lines.append("")
        
        # Metrics
        if cv_content.metrics:
            lines.append("CONTRIBUTION METRICS")
            lines.append("-" * 20)
            for key, value in cv_content.metrics.items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, int) and value > 1000:
                    lines.append(f"{formatted_key}: {value:,}")
                else:
                    lines.append(f"{formatted_key}: {value}")
        
        return "\n".join(lines)
    
    def _format_markdown(self, cv_content: CVContent, template_name: str) -> str:
        """Format CV as Markdown using template."""
        try:
            template = self.jinja_env.get_template(f"{template_name}.md")
        except:
            # Fallback to built-in template
            template_content = self._get_default_markdown_template()
            template = Template(template_content)
        
        return template.render(cv=cv_content)
    
    def _format_html(self, cv_content: CVContent, template_name: str) -> str:
        """Format CV as HTML using template."""
        try:
            template = self.jinja_env.get_template(f"{template_name}.html")
        except:
            # Fallback to built-in template
            template_content = self._get_default_html_template()
            template = Template(template_content)
        
        return template.render(cv=cv_content)
    
    def _get_default_markdown_template(self) -> str:
        """Get default Markdown template."""
        return """# {{ cv.name or "Developer" }}

{% if cv.email %}**Email**: {{ cv.email }}  {% endif %}
{% if cv.github_url %}**GitHub**: {{ cv.github_url }}  {% endif %}
**Generated**: {{ cv.generated_at.strftime('%Y-%m-%d') }}

## Professional Summary

{{ cv.summary }}

## Technical Skills

{% for category, skills in cv.skills.items() %}
{% if skills %}
### {{ category }}
{% for skill in skills %}
- {{ skill }}
{%- endfor %}
{% endif %}
{% endfor %}

## Key Projects

{% for project in cv.projects %}
### {{ project.name }}
{{ project.description }}

**Technologies**: {{ project.technologies | join(', ') }}  
**Contributions**: {{ project.commits }} commits, {{ "{:,}".format(project.lines_of_code) }} lines of code  
{% if project.url %}**Repository**: {{ project.url }}{% endif %}

{% endfor %}

## Contribution Metrics

{% for key, value in cv.metrics.items() %}
- **{{ key.replace('_', ' ').title() }}**: {% if value is number and value > 1000 %}{{ "{:,}".format(value) }}{% else %}{{ value }}{% endif %}
{% endfor %}

---
*Generated with Git Vitae on {{ cv.generated_at.strftime('%Y-%m-%d') }}*
"""
    
    def _get_default_html_template(self) -> str:
        """Get default HTML template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ cv.name or "Developer" }} - CV</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; }
        h2 { color: #34495e; margin-top: 30px; }
        h3 { color: #7f8c8d; }
        .header-info { color: #7f8c8d; margin-bottom: 20px; }
        .skills-category { margin-bottom: 15px; }
        .project { margin-bottom: 25px; padding: 15px; border-left: 4px solid #3498db; background: #f8f9fa; }
        .metrics { background: #e8f4f8; padding: 15px; border-radius: 5px; }
        .footer { text-align: center; margin-top: 40px; color: #95a5a6; font-style: italic; }
    </style>
</head>
<body>
    <h1>{{ cv.name or "Developer" }}</h1>
    
    <div class="header-info">
        {% if cv.email %}<strong>Email:</strong> {{ cv.email }}<br>{% endif %}
        {% if cv.github_url %}<strong>GitHub:</strong> <a href="{{ cv.github_url }}">{{ cv.github_url }}</a><br>{% endif %}
        <strong>Generated:</strong> {{ cv.generated_at.strftime('%Y-%m-%d') }}
    </div>

    <h2>Professional Summary</h2>
    <p>{{ cv.summary }}</p>

    <h2>Technical Skills</h2>
    {% for category, skills in cv.skills.items() %}
    {% if skills %}
    <div class="skills-category">
        <h3>{{ category }}</h3>
        <p>{{ skills | join(', ') }}</p>
    </div>
    {% endif %}
    {% endfor %}

    <h2>Key Projects</h2>
    {% for project in cv.projects %}
    <div class="project">
        <h3>{{ project.name }}</h3>
        <p>{{ project.description }}</p>
        <p><strong>Technologies:</strong> {{ project.technologies | join(', ') }}</p>
        <p><strong>Contributions:</strong> {{ project.commits }} commits, {{ "{:,}".format(project.lines_of_code) }} lines of code</p>
        {% if project.url %}<p><strong>Repository:</strong> <a href="{{ project.url }}">{{ project.url }}</a></p>{% endif %}
    </div>
    {% endfor %}

    <h2>Contribution Metrics</h2>
    <div class="metrics">
        <ul>
        {% for key, value in cv.metrics.items() %}
            <li><strong>{{ key.replace('_', ' ').title() }}:</strong> 
                {% if value is number and value > 1000 %}{{ "{:,}".format(value) }}{% else %}{{ value }}{% endif %}
            </li>
        {% endfor %}
        </ul>
    </div>

    <div class="footer">
        Generated with Git Vitae on {{ cv.generated_at.strftime('%Y-%m-%d') }}
    </div>
</body>
</html>
"""
    
    def _format_number(self, value):
        """Format numbers with commas for thousands."""
        if isinstance(value, (int, float)) and value >= 1000:
            return f"{value:,}"
        return str(value)