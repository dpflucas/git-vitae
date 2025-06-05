"""Repository analyzer for Git Vitae."""

import logging
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from git import Repo
from git.exc import GitCommandError

from .models import GitRepository, RepoData, CommitStats
from .utils import detect_language_from_extension, extract_frameworks_from_files, extract_description_from_readme, calculate_language_percentages


logger = logging.getLogger(__name__)


class RepoAnalyzer:
    """Analyzes Git repositories to extract meaningful data."""
    
    def __init__(self):
        """Initialize analyzer."""
        self.file_extensions_to_ignore = {'.pyc', '.pyo', '.pyd', '.so', '.dylib', '.dll', '.exe', '.obj', '.o'}
        self.directories_to_ignore = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 'env', 'build', 'dist'}
    
    def analyze_repository(self, git_repo: GitRepository) -> RepoData:
        """Extract comprehensive data from a git repository."""
        try:
            repo = Repo(git_repo.path)
            
            # Basic repository data
            repo_data = RepoData(repository=git_repo)
            
            # Analyze files and languages
            self._analyze_files(git_repo.path, repo_data)
            
            # Analyze commit history
            self._analyze_commits(repo, repo_data)
            
            # Extract project metadata
            self._extract_metadata(git_repo.path, repo_data)
            
            logger.info(f"Analyzed repository: {git_repo.name}")
            return repo_data
            
        except Exception as e:
            logger.error(f"Error analyzing repository {git_repo.path}: {e}")
            # Return basic repo data even if analysis fails
            return RepoData(repository=git_repo)
    
    def _analyze_files(self, repo_path: Path, repo_data: RepoData) -> None:
        """Analyze files in the repository."""
        language_counts = Counter()
        total_files = 0
        
        try:
            for file_path in repo_path.rglob('*'):
                if not file_path.is_file():
                    continue
                
                # Skip files in ignored directories
                if any(ignored_dir in file_path.parts for ignored_dir in self.directories_to_ignore):
                    continue
                
                # Skip ignored file extensions
                if file_path.suffix in self.file_extensions_to_ignore:
                    continue
                
                # Skip hidden files
                if file_path.name.startswith('.') and file_path.suffix not in {'.py', '.js', '.ts'}:
                    continue
                
                total_files += 1
                language = detect_language_from_extension(file_path)
                language_counts[language] += 1
            
            repo_data.file_count = total_files
            repo_data.languages = calculate_language_percentages(dict(language_counts))
            
        except Exception as e:
            logger.warning(f"Error analyzing files in {repo_path}: {e}")
    
    def _analyze_commits(self, repo: Repo, repo_data: RepoData) -> None:
        """Analyze commit history."""
        try:
            commits = list(repo.iter_commits())
            if not commits:
                return
            
            # Get current user's email for filtering commits
            try:
                user_email = repo.config_reader().get_value("user", "email")
            except:
                user_email = None
            
            # Count commits by author
            author_commits = 0
            commits_by_month = defaultdict(int)
            first_commit = None
            last_commit = None
            
            for commit in commits:
                commit_date = datetime.fromtimestamp(commit.committed_date)
                month_key = commit_date.strftime("%Y-%m")
                commits_by_month[month_key] += 1
                
                # Count commits by current user
                if user_email and commit.author.email == user_email:
                    author_commits += 1
                
                # Track first and last commits
                if first_commit is None or commit_date < first_commit:
                    first_commit = commit_date
                if last_commit is None or commit_date > last_commit:
                    last_commit = commit_date
            
            # Calculate average commits per month
            if first_commit and last_commit:
                months_active = max(1, (last_commit - first_commit).days / 30)
                avg_commits_per_month = len(commits) / months_active
            else:
                avg_commits_per_month = 0
            
            # Get unique contributors
            contributors = list(set(commit.author.name for commit in commits))
            
            # Calculate lines changed (approximate from recent commits)
            lines_added, lines_removed = self._calculate_lines_changed(repo)
            
            repo_data.total_commits = len(commits)
            repo_data.contributors = contributors
            repo_data.lines_added = lines_added
            repo_data.lines_removed = lines_removed
            
            repo_data.commit_stats = CommitStats(
                total_commits=len(commits),
                author_commits=author_commits,
                first_commit=first_commit,
                last_commit=last_commit,
                commits_by_month=dict(commits_by_month),
                average_commits_per_month=round(avg_commits_per_month, 1)
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing commits: {e}")
    
    def _calculate_lines_changed(self, repo: Repo) -> tuple[int, int]:
        """Calculate approximate lines added and removed."""
        try:
            # Look at recent commits to estimate lines changed
            recent_commits = list(repo.iter_commits(max_count=50))
            total_added = 0
            total_removed = 0
            
            for commit in recent_commits:
                try:
                    stats = commit.stats
                    total_added += stats.total['insertions']
                    total_removed += stats.total['deletions']
                except:
                    continue
            
            # Extrapolate based on total commits
            if recent_commits:
                total_commits = len(list(repo.iter_commits()))
                extrapolation_factor = total_commits / len(recent_commits)
                total_added = int(total_added * extrapolation_factor)
                total_removed = int(total_removed * extrapolation_factor)
            
            return total_added, total_removed
            
        except Exception as e:
            logger.warning(f"Error calculating lines changed: {e}")
            return 0, 0
    
    def _extract_metadata(self, repo_path: Path, repo_data: RepoData) -> None:
        """Extract project metadata."""
        try:
            # Extract description from README
            repo_data.description = extract_description_from_readme(repo_path)
            
            # Extract frameworks and technologies
            frameworks = extract_frameworks_from_files(repo_path)
            repo_data.frameworks = list(frameworks)
            
            # Extract topics from GitHub (if available in .github folder)
            self._extract_github_topics(repo_path, repo_data)
            
        except Exception as e:
            logger.warning(f"Error extracting metadata from {repo_path}: {e}")
    
    def _extract_github_topics(self, repo_path: Path, repo_data: RepoData) -> None:
        """Extract GitHub topics if available."""
        try:
            # Look for GitHub workflow files or other indicators
            github_dir = repo_path / ".github"
            if github_dir.exists():
                # Simple heuristic: infer topics from directory structure and files
                topics = set()
                
                # Check for common patterns
                if (repo_path / "Dockerfile").exists():
                    topics.add("docker")
                if (repo_path / ".github" / "workflows").exists():
                    topics.add("github-actions")
                if (repo_path / "requirements.txt").exists():
                    topics.add("python")
                if (repo_path / "package.json").exists():
                    topics.add("javascript")
                if (repo_path / "Cargo.toml").exists():
                    topics.add("rust")
                
                repo_data.topics = list(topics)
        except:
            pass