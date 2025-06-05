# 🚀 {{ cv.name or "Creative Developer" }} 

{% if cv.email %}📧 {{ cv.email }}  {% endif %}
{% if cv.github_url %}🔗 [GitHub]({{ cv.github_url }})  {% endif %}
📅 {{ cv.generated_at.strftime('%B %d, %Y') }}

---

## 💡 About Me

{{ cv.summary }}

## 🛠️ Technical Arsenal

{% for category, skills in cv.skills.items() %}
{% if skills %}
### {{ category }}
{% for skill in skills %}
- `{{ skill }}`
{%- endfor %}

{% endif %}
{% endfor %}

## 🎯 Featured Projects

{% for project in cv.projects %}
### 🔥 {{ project.name }}

> {{ project.description }}

**🔧 Built With**: {{ project.technologies | join(' • ') }}  
**📈 Impact**: {{ project.commits }} commits contributing {{ project.lines_of_code | number_format }} lines
{% if project.url %}**🌐 Live**: [View Project]({{ project.url }}){% endif %}

---

{% endfor %}

## 📊 By The Numbers

{% if cv.metrics %}
{% for key, value in cv.metrics.items() %}
**{{ key.replace('_', ' ').title() }}**: {% if value is number and value > 1000 %}{{ value | number_format }}{% else %}{{ value }}{% endif %}  
{% endfor %}
{% endif %}

---
*✨ Crafted with passion using Git Vitae*