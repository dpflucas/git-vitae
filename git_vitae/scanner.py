"""Git repository scanner for Git Vitae."""

import logging
from pathlib import Path
from typing import List, Optional
from git import Repo, InvalidGitRepositoryError

from .models import GitRepository


logger = logging.getLogger(__name__)


class GitRepoScanner:
    """Scans directories for Git repositories."""
    
    def __init__(self, max_depth: int = 3, include_hidden: bool = False, ignore_patterns: Optional[List[str]] = None):
        """Initialize scanner with configuration."""
        self.max_depth = max_depth
        self.include_hidden = include_hidden
        self.ignore_patterns = ignore_patterns or ["node_modules", ".git", "__pycache__", ".venv", "venv"]
    
    def scan_directory(self, root_path: Path) -> List[GitRepository]:
        """Recursively find all git repositories."""
        repositories = []
        
        try:
            self._scan_recursive(root_path, repositories, 0)
        except Exception as e:
            logger.error(f"Error scanning directory {root_path}: {e}")
        
        return repositories
    
    def _scan_recursive(self, path: Path, repositories: List[GitRepository], depth: int) -> None:
        """Recursively scan directories for git repos."""
        if depth > self.max_depth:
            return
        
        if not path.is_dir():
            return
        
        # Skip hidden directories if not included
        if not self.include_hidden and path.name.startswith('.') and depth > 0:
            return
        
        # Skip ignored patterns
        if any(pattern in str(path) for pattern in self.ignore_patterns):
            return
        
        # Check if current directory is a git repository
        if self.is_git_repo(path):
            git_repo = self._create_git_repository(path)
            if git_repo:
                repositories.append(git_repo)
            # Don't scan subdirectories of git repos to avoid nested repos
            return
        
        # Scan subdirectories
        try:
            for child in path.iterdir():
                if child.is_dir():
                    self._scan_recursive(child, repositories, depth + 1)
        except PermissionError:
            logger.warning(f"Permission denied accessing {path}")
        except Exception as e:
            logger.warning(f"Error accessing {path}: {e}")
    
    def is_git_repo(self, path: Path) -> bool:
        """Check if directory is a git repository."""
        try:
            Repo(path)
            return True
        except InvalidGitRepositoryError:
            return False
        except Exception:
            return False
    
    def _create_git_repository(self, path: Path) -> Optional[GitRepository]:
        """Create GitRepository object from path."""
        try:
            repo = Repo(path)
            
            # Get remote URL if available
            remote_url = None
            try:
                if repo.remotes:
                    remote_url = repo.remotes.origin.url
            except:
                pass
            
            # Get last commit date
            last_commit = None
            try:
                if repo.head.is_valid():
                    last_commit = repo.head.commit.committed_datetime
            except:
                pass
            
            # Determine if repo is private (heuristic: no remote or local only)
            is_private = remote_url is None or 'github.com' not in str(remote_url)
            
            return GitRepository(
                path=path,
                name=path.name,
                remote_url=remote_url,
                is_private=is_private,
                last_commit=last_commit
            )
            
        except Exception as e:
            logger.error(f"Error creating GitRepository for {path}: {e}")
            return None