# {{ cv.name or "Professional Developer" }}

{% if cv.email %}**Email**: {{ cv.email }}  {% endif %}
{% if cv.github_url %}**GitHub**: {{ cv.github_url }}  {% endif %}
**Generated**: {{ cv.generated_at.strftime('%Y-%m-%d') }}

---

## Executive Summary

{{ cv.summary }}

## Core Competencies

{% for category, skills in cv.skills.items() %}
{% if skills %}
**{{ category }}**: {{ skills | join(' • ') }}  
{% endif %}
{% endfor %}

## Professional Projects

{% for project in cv.projects %}
### {{ project.name }}
{{ project.description }}

- **Technology Stack**: {{ project.technologies | join(', ') }}
- **Development Metrics**: {{ project.commits }} commits, {{ project.lines_of_code | number_format }} lines of code
{% if project.url %}- **Repository**: {{ project.url }}{% endif %}

{% endfor %}

## Development Metrics

{% if cv.metrics %}
| Metric | Value |
|--------|-------|
{% for key, value in cv.metrics.items() %}
| {{ key.replace('_', ' ').title() }} | {% if value is number and value > 1000 %}{{ value | number_format }}{% else %}{{ value }}{% endif %} |
{% endfor %}
{% endif %}

---
*Generated using Git Vitae - Professional CV Template*