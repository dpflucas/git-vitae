# {{ cv.name or "Developer" }}

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