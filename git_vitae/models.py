"""Data models for Git Vitae."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class GitRepository:
    """Represents a Git repository."""
    path: Path
    name: str
    remote_url: Optional[str] = None
    is_private: bool = False
    last_commit: Optional[datetime] = None


@dataclass
class CommitStats:
    """Statistics about commits in a repository."""
    total_commits: int
    author_commits: int
    first_commit: Optional[datetime]
    last_commit: Optional[datetime]
    commits_by_month: Dict[str, int] = field(default_factory=dict)
    average_commits_per_month: float = 0.0


@dataclass
class RepoData:
    """Comprehensive data extracted from a repository."""
    repository: GitRepository
    languages: Dict[str, float] = field(default_factory=dict)
    total_commits: int = 0
    file_count: int = 0
    contributors: List[str] = field(default_factory=list)
    description: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    commit_stats: Optional[CommitStats] = None
    lines_added: int = 0
    lines_removed: int = 0


@dataclass
class Project:
    """Represents a project for CV display."""
    name: str
    description: str
    technologies: List[str]
    commits: int
    lines_of_code: int
    url: Optional[str] = None


@dataclass
class CVContent:
    """Generated CV content."""
    name: str
    email: Optional[str] = None
    github_url: Optional[str] = None
    summary: str = ""
    skills: Dict[str, List[str]] = field(default_factory=dict)
    projects: List[Project] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Config:
    """Configuration for Git Vitae."""
    ai_provider: str = "openai"
    ai_model: str = "gpt-4"
    ai_api_key: Optional[str] = None
    scan_path: Optional[str] = None
    max_depth: int = 3
    include_hidden: bool = False
    include_private: bool = True
    ignore_patterns: List[str] = field(default_factory=lambda: ["node_modules", ".git", "__pycache__"])
    default_format: str = "markdown"
    default_template: str = "default"
    default_style: str = "professional"
    include_metrics: bool = True
    include_timeline: bool = True
    group_by_language: bool = True
    anonymize_data: bool = True
    allow_sensitive_data: bool = False