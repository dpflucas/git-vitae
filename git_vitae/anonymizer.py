"""Data anonymization utilities for Git Vitae."""

import hashlib
import re
from typing import Dict, List, Any, Set
from urllib.parse import urlparse


class DataAnonymizer:
    """Anonymizes sensitive data before sending to AI services."""
    
    def __init__(self):
        """Initialize anonymizer with patterns and mappings."""
        self.name_mapping = {}
        self.email_mapping = {}
        self.url_mapping = {}
        self.sensitive_patterns = [
            # Email patterns
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # IP addresses
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            # API keys (common patterns)
            r'\b[A-Za-z0-9]{32,}\b',
            r'\bsk-[A-Za-z0-9]+\b',
            r'\bghp_[A-Za-z0-9]+\b',
            # File paths with usernames
            r'/Users/[^/\s]+',
            r'C:\\Users\\[^\\s]+',
            # SSH keys
            r'ssh-[a-z0-9]+ [A-Za-z0-9+/]+=*',
        ]
        
        # Common sensitive keywords
        self.sensitive_keywords = {
            'password', 'passwd', 'secret', 'token', 'key', 'credential',
            'auth', 'private', 'confidential', 'internal', 'proprietary'
        }
    
    def anonymize_repo_data(self, repo_data_list: List[Any]) -> List[Dict[str, Any]]:
        """Anonymize repository data for AI processing."""
        anonymized_repos = []
        
        for i, repo_data in enumerate(repo_data_list):
            anonymized_repo = {
                "project_id": f"project_{i + 1}",
                "languages": self._sanitize_languages(repo_data.languages),
                "frameworks": self._sanitize_frameworks(repo_data.frameworks),
                "total_commits": repo_data.total_commits,
                "file_count": repo_data.file_count,
                "contributor_count": len(repo_data.contributors),
                "lines_added": repo_data.lines_added,
                "lines_removed": repo_data.lines_removed,
                "project_type": self._classify_project_type(repo_data),
                "activity_level": self._classify_activity_level(repo_data.total_commits),
                "size_category": self._classify_size_category(repo_data.file_count)
            }
            
            # Add commit statistics if available
            if repo_data.commit_stats:
                anonymized_repo["commit_stats"] = {
                    "total_commits": repo_data.commit_stats.total_commits,
                    "average_commits_per_month": repo_data.commit_stats.average_commits_per_month,
                    "active_months": len(repo_data.commit_stats.commits_by_month)
                }
            
            anonymized_repos.append(anonymized_repo)
        
        return anonymized_repos
    
    def _sanitize_languages(self, languages: Dict[str, float]) -> Dict[str, float]:
        """Sanitize language data, keeping only the languages and percentages."""
        # Languages are generally safe, but remove any suspicious entries
        safe_languages = {}
        for lang, percentage in languages.items():
            # Only keep recognized programming languages
            if self._is_programming_language(lang):
                safe_languages[lang] = percentage
        return safe_languages
    
    def _sanitize_frameworks(self, frameworks: List[str]) -> List[str]:
        """Sanitize framework list, removing any suspicious entries."""
        safe_frameworks = []
        for framework in frameworks:
            # Remove frameworks that might contain sensitive info
            if not self._contains_sensitive_info(framework):
                safe_frameworks.append(framework)
        return safe_frameworks
    
    def _is_programming_language(self, lang: str) -> bool:
        """Check if string is a recognized programming language."""
        known_languages = {
            'python', 'javascript', 'typescript', 'java', 'c', 'c++', 'c#',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'r',
            'matlab', 'shell', 'bash', 'powershell', 'sql', 'html', 'css',
            'scss', 'sass', 'less', 'vue', 'jsx', 'tsx', 'dart', 'lua',
            'perl', 'haskell', 'clojure', 'erlang', 'elixir', 'f#',
            'objective-c', 'assembly', 'vb.net', 'cobol', 'fortran',
            'markdown', 'json', 'xml', 'yaml', 'toml', 'other'
        }
        return lang.lower() in known_languages
    
    def _contains_sensitive_info(self, text: str) -> bool:
        """Check if text contains sensitive information."""
        text_lower = text.lower()
        
        # Check for sensitive keywords
        for keyword in self.sensitive_keywords:
            if keyword in text_lower:
                return True
        
        # Check for sensitive patterns
        for pattern in self.sensitive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _classify_project_type(self, repo_data: Any) -> str:
        """Classify project type based on languages and frameworks."""
        languages = set(lang.lower() for lang in repo_data.languages.keys())
        frameworks = set(fw.lower() for fw in repo_data.frameworks)
        
        # Web development
        if any(lang in languages for lang in ['javascript', 'typescript', 'html', 'css']):
            frontend_frameworks = any(fw in frameworks for fw in ['react', 'vue', 'angular', 'next.js'])
            backend_frameworks = any(fw in frameworks for fw in ['express', 'express.js', 'fastapi', 'django', 'flask'])
            
            if frontend_frameworks and backend_frameworks:
                return 'fullstack_web'
            elif frontend_frameworks:
                return 'frontend_web'
            elif backend_frameworks:
                return 'fullstack_web'
            else:
                return 'web_development'
        
        # Mobile development
        if any(lang in languages for lang in ['swift', 'kotlin', 'dart']):
            return 'mobile_development'
        
        # Data science/ML
        if any(fw in frameworks for fw in ['pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn']):
            return 'data_science'
        
        # Systems programming
        if any(lang in languages for lang in ['c', 'c++', 'rust', 'go']):
            return 'systems_programming'
        
        # DevOps/Infrastructure
        if any(fw in frameworks for fw in ['docker', 'kubernetes', 'terraform']):
            return 'devops_infrastructure'
        
        # Desktop application
        if any(lang in languages for lang in ['java', 'c#', 'python']):
            return 'desktop_application'
        
        return 'general_software'
    
    def _classify_activity_level(self, commits: int) -> str:
        """Classify activity level based on commit count."""
        if commits >= 500:
            return 'high_activity'
        elif commits >= 100:
            return 'medium_activity'
        elif commits >= 10:
            return 'low_activity'
        else:
            return 'minimal_activity'
    
    def _classify_size_category(self, file_count: int) -> str:
        """Classify project size based on file count."""
        if file_count >= 1000:
            return 'large_project'
        elif file_count >= 100:
            return 'medium_project'
        elif file_count >= 10:
            return 'small_project'
        else:
            return 'minimal_project'
    
    def generate_anonymized_summary(self, anonymized_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate aggregated anonymous summary for AI processing."""
        total_projects = len(anonymized_data)
        total_commits = sum(repo.get('total_commits', 0) for repo in anonymized_data)
        total_lines_added = sum(repo.get('lines_added', 0) for repo in anonymized_data)
        total_lines_removed = sum(repo.get('lines_removed', 0) for repo in anonymized_data)
        
        # Aggregate languages
        language_stats = {}
        for repo in anonymized_data:
            for lang, percentage in repo.get('languages', {}).items():
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
        for repo in anonymized_data:
            all_frameworks.update(repo.get('frameworks', []))
        
        # Project type distribution
        project_types = {}
        activity_levels = {}
        size_categories = {}
        
        for repo in anonymized_data:
            proj_type = repo.get('project_type', 'unknown')
            activity = repo.get('activity_level', 'unknown')
            size = repo.get('size_category', 'unknown')
            
            project_types[proj_type] = project_types.get(proj_type, 0) + 1
            activity_levels[activity] = activity_levels.get(activity, 0) + 1
            size_categories[size] = size_categories.get(size, 0) + 1
        
        return {
            "summary_statistics": {
                "total_projects": total_projects,
                "total_commits": total_commits,
                "total_lines_added": total_lines_added,
                "total_lines_removed": total_lines_removed,
                "active_projects": len([r for r in anonymized_data if r.get('total_commits', 0) > 5])
            },
            "technical_profile": {
                "primary_languages": dict(sorted(language_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
                "frameworks_and_tools": sorted(list(all_frameworks)),
                "project_type_distribution": project_types,
                "activity_level_distribution": activity_levels,
                "project_size_distribution": size_categories
            },
            "development_patterns": {
                "average_commits_per_project": round(total_commits / total_projects, 1) if total_projects > 0 else 0,
                "average_files_per_project": round(sum(r.get('file_count', 0) for r in anonymized_data) / total_projects, 1) if total_projects > 0 else 0,
                "code_productivity": {
                    "lines_per_commit": round(total_lines_added / total_commits, 1) if total_commits > 0 else 0,
                    "net_lines": total_lines_added - total_lines_removed
                }
            }
        }
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text by removing sensitive patterns."""
        sanitized = text
        
        # Remove URLs first (keep only domain for context)
        def replace_url(match):
            url = match.group(0)
            try:
                parsed = urlparse(url)
                if parsed.netloc:
                    return f"[URL:{parsed.netloc}]"
                return "[URL]"
            except:
                return "[URL]"
        
        sanitized = re.sub(r'https?://[^\s]+', replace_url, sanitized)
        
        # Remove sensitive patterns
        for pattern in self.sensitive_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Remove potential file paths (avoid affecting URLs)
        sanitized = re.sub(r'(?<!:)[/\\][^\s]*[/\\][^\s]*', '[PATH]', sanitized)
        
        return sanitized