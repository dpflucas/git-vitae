"""AI processor for generating CV content from repository data."""

import json
import logging
from typing import List, Optional, Dict, Any

from .models import RepoData, CVContent, Project, Config
from .anonymizer import DataAnonymizer


logger = logging.getLogger(__name__)


class CVGenerator:
    """Generates CV content using AI services."""
    
    def __init__(self, config: Config):
        """Initialize with configuration."""
        self.config = config
        self.client = None
        self.anonymizer = DataAnonymizer()
        self._setup_ai_client()
    
    def _setup_ai_client(self) -> None:
        """Setup AI client based on provider."""
        try:
            if self.config.ai_provider == "openai":
                import openai
                self.client = openai.OpenAI(api_key=self.config.ai_api_key)
            elif self.config.ai_provider == "anthropic":
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.config.ai_api_key)
            else:
                raise ValueError(f"Unsupported AI provider: {self.config.ai_provider}")
        except ImportError as e:
            logger.error(f"Failed to import {self.config.ai_provider} library: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to setup AI client: {e}")
            raise
    
    def generate_cv(self, repo_data_list: List[RepoData], style: str = "professional") -> CVContent:
        """Generate CV content from repository data."""
        try:
            # Prepare data for AI service (anonymized or raw based on config)
            if self.config.anonymize_data:
                # Use anonymized data
                anonymized_repos = self.anonymizer.anonymize_repo_data(repo_data_list)
                ai_data = self.anonymizer.generate_anonymized_summary(anonymized_repos)
                cv_content = self._call_ai_service_anonymized(ai_data, style)
            else:
                # Use raw repository data
                ai_data = self._prepare_repo_data(repo_data_list)
                cv_content = self._call_ai_service_raw(ai_data, style)
            
            # Extract and structure the response (using original data for final CV)
            structured_cv = self._structure_cv_response(cv_content, repo_data_list)
            
            return structured_cv
            
        except Exception as e:
            logger.error(f"Error generating CV: {e}")
            # Return basic CV if AI generation fails
            return self._create_fallback_cv(repo_data_list)
    
    def _prepare_repo_data(self, repo_data_list: List[RepoData]) -> Dict[str, Any]:
        """Prepare repository data for AI processing."""
        # Aggregate statistics
        total_commits = sum(data.total_commits for data in repo_data_list)
        total_lines_added = sum(data.lines_added for data in repo_data_list)
        total_lines_removed = sum(data.lines_removed for data in repo_data_list)
        
        # Aggregate languages
        language_stats = {}
        for data in repo_data_list:
            for lang, percentage in data.languages.items():
                if lang in language_stats:
                    language_stats[lang] += percentage
                else:
                    language_stats[lang] = percentage
        
        # Normalize language percentages
        total_percentage = sum(language_stats.values())
        if total_percentage > 0:
            language_stats = {
                lang: round((percent / total_percentage) * 100, 1)
                for lang, percent in language_stats.items()
            }
        
        # Aggregate frameworks
        all_frameworks = set()
        for data in repo_data_list:
            all_frameworks.update(data.frameworks)
        
        # Create project summaries
        projects = []
        for data in repo_data_list:
            if data.total_commits > 0:  # Only include projects with commits
                projects.append({
                    "name": data.repository.name,
                    "description": data.description or "Software project",
                    "languages": list(data.languages.keys()),
                    "frameworks": data.frameworks,
                    "commits": data.total_commits,
                    "contributors": len(data.contributors),
                    "lines_added": data.lines_added,
                    "lines_removed": data.lines_removed,
                    "url": data.repository.remote_url
                })
        
        # Sort projects by commit count
        projects.sort(key=lambda p: p["commits"], reverse=True)
        
        return {
            "total_repositories": len(repo_data_list),
            "total_commits": total_commits,
            "total_lines_added": total_lines_added,
            "total_lines_removed": total_lines_removed,
            "language_distribution": language_stats,
            "frameworks_and_tools": list(all_frameworks),
            "projects": projects[:10],  # Top 10 projects
            "active_repositories": len([d for d in repo_data_list if d.total_commits > 5])
        }
    
    def _call_ai_service_anonymized(self, anonymized_data: Dict[str, Any], style: str) -> str:
        """Call AI service to generate CV content using anonymized data."""
        prompt = self._create_anonymized_prompt(anonymized_data, style)
        return self._make_ai_request(prompt)
    
    def _call_ai_service_raw(self, repo_data: Dict[str, Any], style: str) -> str:
        """Call AI service to generate CV content using raw repository data."""
        prompt = self._create_raw_prompt(repo_data, style)
        return self._make_ai_request(prompt)
    
    def _make_ai_request(self, prompt: str) -> str:
        """Make the actual AI service request."""
        try:
            if self.config.ai_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.config.ai_model,
                    messages=[
                        {"role": "system", "content": "You are a professional CV writer with expertise in technical resumes."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif self.config.ai_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.config.ai_model,
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
            
        except Exception as e:
            logger.error(f"AI service call failed: {e}")
            raise
    
    def _create_anonymized_prompt(self, anonymized_data: Dict[str, Any], style: str) -> str:
        """Create prompt for AI service using anonymized data."""
        summary_stats = anonymized_data["summary_statistics"]
        tech_profile = anonymized_data["technical_profile"]
        dev_patterns = anonymized_data["development_patterns"]
        
        prompt = f"""Based on the following anonymized software development portfolio analysis, create a comprehensive professional summary and technical profile in {style} style.

PORTFOLIO OVERVIEW:
- Total projects analyzed: {summary_stats['total_projects']}
- Total contributions: {summary_stats['total_commits']} commits
- Code volume: {summary_stats['total_lines_added']} lines added, {summary_stats['total_lines_removed']} lines removed
- Active projects: {summary_stats['active_projects']}

TECHNICAL EXPERTISE:
Programming Languages (by codebase percentage):
{json.dumps(tech_profile['primary_languages'], indent=2)}

Frameworks and Tools:
{', '.join(tech_profile['frameworks_and_tools'])}

PROJECT PORTFOLIO:
Project Types: {tech_profile['project_type_distribution']}
Activity Levels: {tech_profile['activity_level_distribution']}
Project Sizes: {tech_profile['project_size_distribution']}

DEVELOPMENT METRICS:
- Average commits per project: {dev_patterns['average_commits_per_project']}
- Average files per project: {dev_patterns['average_files_per_project']}
- Code productivity: {dev_patterns['code_productivity']['lines_per_commit']} lines per commit
- Net code contribution: {dev_patterns['code_productivity']['net_lines']} lines

Generate a professional CV content focusing on:
1. Professional Summary (highlighting technical breadth and development experience)
2. Technical Skills (categorized by Programming Languages, Frameworks, Tools)
3. Project Experience (describe typical project types and technical approaches)
4. Development Achievements (quantified metrics and productivity indicators)

Requirements:
- Use generic project descriptions (e.g., "web application", "data processing system")
- Focus on technical skills and architectural patterns
- Emphasize development methodology and code quality
- Highlight cross-functional technical expertise
- Use professional language suitable for software engineering roles
- Quantify achievements using the provided metrics

Do not include any specific project names, personal names, company names, or identifying information."""
        
        return prompt
    
    def _create_raw_prompt(self, repo_data: Dict[str, Any], style: str) -> str:
        """Create prompt for AI service using raw repository data."""
        prompt = f"""Based on the following software development portfolio analysis, create a comprehensive professional summary and technical profile in {style} style.

PORTFOLIO OVERVIEW:
- Total repositories: {repo_data['total_repositories']}
- Total contributions: {repo_data['total_commits']} commits
- Code volume: {repo_data['total_lines_added']} lines added, {repo_data['total_lines_removed']} lines removed
- Active repositories: {repo_data['active_repositories']}

TECHNICAL EXPERTISE:
Programming Languages (by codebase percentage):
{json.dumps(repo_data['language_distribution'], indent=2)}

Frameworks and Tools:
{', '.join(repo_data['frameworks_and_tools'])}

PROJECT PORTFOLIO:
{json.dumps(repo_data['projects'], indent=2)}

Generate a professional CV content focusing on:
1. Professional Summary (highlighting technical breadth and development experience)
2. Technical Skills (categorized by Programming Languages, Frameworks, Tools)
3. Project Experience (describe project types and technical approaches using actual project data)
4. Development Achievements (quantified metrics and productivity indicators)

Requirements:
- Use the actual project data provided
- Focus on technical skills and architectural patterns
- Emphasize development methodology and code quality
- Highlight cross-functional technical expertise
- Use professional language suitable for software engineering roles
- Quantify achievements using the provided metrics"""
        
        return prompt
    
    def _structure_cv_response(self, ai_response: str, repo_data_list: List[RepoData]) -> CVContent:
        """Structure AI response into CVContent object."""
        # Parse the AI response to extract structured data
        # This is a simplified implementation - in practice, you might want more sophisticated parsing
        
        # Extract skills from repo data
        skills = self._extract_skills_from_data(repo_data_list)
        
        # Create project objects
        projects = self._create_project_objects(repo_data_list)
        
        # Calculate metrics
        metrics = self._calculate_metrics(repo_data_list)
        
        return CVContent(
            name="Developer",  # This could be extracted from git config
            summary=ai_response,  # In practice, you'd parse this to extract just the summary
            skills=skills,
            projects=projects,
            metrics=metrics
        )
    
    def _extract_skills_from_data(self, repo_data_list: List[RepoData]) -> Dict[str, List[str]]:
        """Extract and categorize skills from repository data."""
        skills = {
            "Programming Languages": [],
            "Frameworks & Libraries": [],
            "Tools & Platforms": [],
            "Databases": [],
            "DevOps": []
        }
        
        # Extract languages
        all_languages = set()
        for data in repo_data_list:
            all_languages.update(data.languages.keys())
        skills["Programming Languages"] = sorted(list(all_languages))
        
        # Extract frameworks
        all_frameworks = set()
        for data in repo_data_list:
            all_frameworks.update(data.frameworks)
        
        # Categorize frameworks
        for framework in all_frameworks:
            framework_lower = framework.lower()
            if any(db in framework_lower for db in ['postgres', 'mysql', 'mongo', 'redis']):
                skills["Databases"].append(framework)
            elif any(devops in framework_lower for devops in ['docker', 'kubernetes', 'jenkins', 'github']):
                skills["DevOps"].append(framework)
            else:
                skills["Frameworks & Libraries"].append(framework)
        
        # Add common tools based on repository patterns
        if any('git' in str(data.repository.path) for data in repo_data_list):
            skills["Tools & Platforms"].append("Git")
        
        return skills
    
    def _generate_project_name(self, project_type: str, data: Any) -> str:
        """Generate more specific project names based on technologies and frameworks."""
        frameworks = [fw.lower() for fw in data.frameworks]
        languages = [lang.lower() for lang in data.languages.keys()]
        
        # React-based projects
        if 'react' in frameworks:
            if 'next.js' in frameworks or 'next' in frameworks:
                return "Next.js Enterprise Platform"
            elif 'typescript' in languages:
                return "React TypeScript Application"
            else:
                return "React Web Application"
        
        # Angular projects
        elif 'angular' in frameworks:
            return "Angular Enterprise Application"
        
        # Vue projects
        elif 'vue' in frameworks:
            return "Vue.js Progressive Web App"
        
        # Node.js/Express projects
        elif 'express.js' in frameworks or 'express' in frameworks:
            if 'react' in frameworks or 'angular' in frameworks:
                return "Full-Stack Web Platform"
            else:
                return "RESTful API Service"
        
        # Python-based projects
        elif 'python' in languages:
            if 'django' in frameworks or 'flask' in frameworks:
                return "Python Web Application"
            elif any(fw in frameworks for fw in ['pandas', 'numpy', 'tensorflow', 'pytorch']):
                return "Data Science & Analytics Platform"
            else:
                return "Python Backend Service"
        
        # Authentication/Security projects
        elif any(fw in frameworks for fw in ['auth', 'authentication', 'security']):
            return "Authentication & Security Platform"
        
        # Docker/DevOps projects
        elif 'docker' in frameworks:
            return "Containerized Application Platform"
        
        # Testing-focused projects
        elif any(fw in frameworks for fw in ['cypress', 'jest', 'mocha']):
            return "Test-Driven Development Platform"
        
        # Mobile projects
        elif project_type == 'mobile_development':
            return "Mobile Application"
        
        # Healthcare/Management systems
        elif any(keyword in str(data).lower() for keyword in ['health', 'management', 'admin']):
            return "Management System Platform"
        
        # Fallback to improved generic names
        type_mapping = {
            'frontend_web': 'Frontend Development Platform',
            'fullstack_web': 'Full-Stack Web Platform', 
            'web_development': 'Web Development Platform',
            'data_science': 'Data Science & Analytics Platform',
            'systems_programming': 'Systems Programming Project',
            'devops_infrastructure': 'DevOps Infrastructure Platform',
            'desktop_application': 'Desktop Application',
            'general_software': 'Software Development Platform'
        }
        
        return type_mapping.get(project_type, f"{project_type.replace('_', ' ').title()} Platform")

    def _create_project_objects(self, repo_data_list: List[RepoData]) -> List[Project]:
        """Create anonymized Project objects from repository data."""
        projects = []
        
        # Sort by commit count and take top projects
        sorted_repos = sorted(repo_data_list, key=lambda x: x.total_commits, reverse=True)
        
        for i, data in enumerate(sorted_repos[:5]):  # Top 5 projects
            if data.total_commits > 0:
                # Create specific project name and description
                project_type = self.anonymizer._classify_project_type(data)
                generic_name = self._generate_project_name(project_type, data)
                
                # Create anonymized description
                languages = list(data.languages.keys())[:3]
                generic_description = f"Software project demonstrating expertise in {', '.join(languages)}"
                if data.frameworks:
                    safe_frameworks = [fw for fw in data.frameworks if not self.anonymizer._contains_sensitive_info(fw)]
                    if safe_frameworks:
                        generic_description += f" using {', '.join(safe_frameworks[:3])}"
                
                project = Project(
                    name=generic_name,
                    description=generic_description,
                    technologies=list(data.languages.keys()) + [fw for fw in data.frameworks if not self.anonymizer._contains_sensitive_info(fw)],
                    commits=data.total_commits,
                    lines_of_code=data.lines_added,
                    url=None  # Remove URLs for privacy
                )
                projects.append(project)
        
        return projects
    
    def _calculate_metrics(self, repo_data_list: List[RepoData]) -> Dict[str, Any]:
        """Calculate overall contribution metrics."""
        total_commits = sum(data.total_commits for data in repo_data_list)
        total_lines_added = sum(data.lines_added for data in repo_data_list)
        total_lines_removed = sum(data.lines_removed for data in repo_data_list)
        active_repos = len([data for data in repo_data_list if data.total_commits > 5])
        
        return {
            "total_commits": total_commits,
            "total_repositories": len(repo_data_list),
            "active_repositories": active_repos,
            "lines_added": total_lines_added,
            "lines_removed": total_lines_removed,
            "net_lines": total_lines_added - total_lines_removed,
            "average_commits_per_repo": round(total_commits / len(repo_data_list), 1) if repo_data_list else 0
        }
    
    def _create_fallback_cv(self, repo_data_list: List[RepoData]) -> CVContent:
        """Create a basic CV when AI generation fails."""
        logger.warning("Using fallback CV generation")
        
        skills = self._extract_skills_from_data(repo_data_list)
        projects = self._create_project_objects(repo_data_list)
        metrics = self._calculate_metrics(repo_data_list)
        
        summary = f"Experienced developer with {metrics['total_commits']} commits across {metrics['total_repositories']} repositories. "
        summary += f"Proficient in {', '.join(skills['Programming Languages'][:3])} and various frameworks."
        
        return CVContent(
            name="Developer",
            summary=summary,
            skills=skills,
            projects=projects,
            metrics=metrics
        )