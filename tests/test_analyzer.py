"""Tests for repository analyzer."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from git_vitae.analyzer import RepoAnalyzer
from git_vitae.models import GitRepository, RepoData


class TestRepoAnalyzer(unittest.TestCase):
    """Test cases for RepoAnalyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = RepoAnalyzer()
        
        # Create mock repository
        self.mock_repo = GitRepository(
            path=Path("/test/repo"),
            name="test-repo",
            remote_url="https://github.com/user/test-repo.git"
        )
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = RepoAnalyzer()
        self.assertIsInstance(analyzer.file_extensions_to_ignore, set)
        self.assertIsInstance(analyzer.directories_to_ignore, set)
        self.assertIn('.pyc', analyzer.file_extensions_to_ignore)
        self.assertIn('node_modules', analyzer.directories_to_ignore)
    
    @patch('git_vitae.analyzer.Repo')
    def test_analyze_repository_basic(self, mock_repo_class):
        """Test basic repository analysis."""
        # Mock git repository
        mock_repo = MagicMock()
        mock_repo.iter_commits.return_value = []
        mock_repo_class.return_value = mock_repo
        
        with patch.object(self.analyzer, '_analyze_files'):
            with patch.object(self.analyzer, '_extract_metadata'):
                result = self.analyzer.analyze_repository(self.mock_repo)
                
                self.assertIsInstance(result, RepoData)
                self.assertEqual(result.repository, self.mock_repo)
    
    def test_analyze_files_with_python_files(self):
        """Test file analysis with Python files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "main.py").touch()
            (temp_path / "test.py").touch()
            (temp_path / "script.js").touch()
            (temp_path / "README.md").touch()
            
            # Create subdirectory with files
            sub_dir = temp_path / "src"
            sub_dir.mkdir()
            (sub_dir / "module.py").touch()
            
            repo_data = RepoData(repository=self.mock_repo)
            
            # Mock the repository path
            with patch.object(self.mock_repo, 'path', temp_path):
                self.analyzer._analyze_files(temp_path, repo_data)
            
            # Check results
            self.assertEqual(repo_data.file_count, 5)
            self.assertIn('Python', repo_data.languages)
            self.assertIn('JavaScript', repo_data.languages)
            self.assertIn('Markdown', repo_data.languages)
            
            # Python should be the majority
            self.assertGreater(repo_data.languages['Python'], 50)
    
    def test_analyze_files_ignores_unwanted_files(self):
        """Test that file analysis ignores unwanted files and directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files that should be ignored
            (temp_path / "main.py").touch()
            (temp_path / "test.pyc").touch()  # Should be ignored
            (temp_path / ".hidden").touch()   # Should be ignored
            
            # Create directories that should be ignored
            node_modules = temp_path / "node_modules"
            node_modules.mkdir()
            (node_modules / "package.js").touch()  # Should be ignored
            
            git_dir = temp_path / ".git"
            git_dir.mkdir()
            (git_dir / "config").touch()  # Should be ignored
            
            repo_data = RepoData(repository=self.mock_repo)
            self.analyzer._analyze_files(temp_path, repo_data)
            
            # Should only count main.py
            self.assertEqual(repo_data.file_count, 1)
            self.assertEqual(repo_data.languages['Python'], 100.0)
    
    @patch('git_vitae.analyzer.Repo')
    def test_analyze_commits_basic(self, mock_repo_class):
        """Test basic commit analysis."""
        # Create mock commits
        mock_commits = []
        for i in range(5):
            mock_commit = MagicMock()
            mock_commit.committed_date = 1640995200 + i * 86400  # Jan 1, 2022 + i days
            mock_commit.author.name = f"Author {i}"
            mock_commit.author.email = f"author{i}@example.com"
            mock_commit.stats.total = {'insertions': 10, 'deletions': 5}
            mock_commits.append(mock_commit)
        
        mock_repo = MagicMock()
        mock_repo.iter_commits.return_value = mock_commits
        mock_repo.config_reader.return_value.get_value.return_value = "author0@example.com"
        
        repo_data = RepoData(repository=self.mock_repo)
        self.analyzer._analyze_commits(mock_repo, repo_data)
        
        # Check results
        self.assertEqual(repo_data.total_commits, 5)
        self.assertEqual(len(repo_data.contributors), 5)
        self.assertIsNotNone(repo_data.commit_stats)
        self.assertEqual(repo_data.commit_stats.total_commits, 5)
        self.assertEqual(repo_data.commit_stats.author_commits, 1)  # Only author0 matches
    
    def test_calculate_lines_changed(self):
        """Test calculation of lines changed."""
        # Create mock commits with stats
        mock_commits = []
        for i in range(3):
            mock_commit = MagicMock()
            mock_commit.stats.total = {'insertions': 10 + i, 'deletions': 5 + i}
            mock_commits.append(mock_commit)
        
        mock_repo = MagicMock()
        mock_repo.iter_commits.side_effect = [
            mock_commits,  # First call for recent commits
            mock_commits * 2  # Second call for total commits
        ]
        
        lines_added, lines_removed = self.analyzer._calculate_lines_changed(mock_repo)
        
        # Expected: (10+11+12) * 2 = 66 added, (5+6+7) * 2 = 36 removed
        self.assertEqual(lines_added, 66)
        self.assertEqual(lines_removed, 36)
    
    def test_extract_metadata_with_readme(self):
        """Test metadata extraction with README file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create README file
            readme_path = temp_path / "README.md"
            readme_content = """# Test Project
            
This is a test project for demonstrating Git Vitae functionality.
It includes multiple features and technologies.

## Features
- Feature 1
- Feature 2
"""
            readme_path.write_text(readme_content)
            
            # Create package.json
            package_json = temp_path / "package.json"
            package_json.write_text('{"dependencies": {"react": "^18.0.0", "express": "^4.0.0"}}')
            
            repo_data = RepoData(repository=self.mock_repo)
            self.analyzer._extract_metadata(temp_path, repo_data)
            
            # Check description extraction
            self.assertIn("test project", repo_data.description.lower())
            
            # Check framework detection
            self.assertIn("React", repo_data.frameworks)
            self.assertIn("Express.js", repo_data.frameworks)
    
    def test_extract_metadata_with_python_project(self):
        """Test metadata extraction with Python project files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create requirements.txt
            requirements = temp_path / "requirements.txt"
            requirements.write_text("django>=3.0.0\nflask>=2.0.0\npandas>=1.0.0\n")
            
            repo_data = RepoData(repository=self.mock_repo)
            self.analyzer._extract_metadata(temp_path, repo_data)
            
            # Check framework detection
            self.assertIn("Django", repo_data.frameworks)
            self.assertIn("Flask", repo_data.frameworks)
            self.assertIn("Pandas", repo_data.frameworks)
    
    def test_extract_metadata_with_docker(self):
        """Test metadata extraction with Docker files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create Dockerfile
            dockerfile = temp_path / "Dockerfile"
            dockerfile.write_text("FROM python:3.9\nCOPY . /app\n")
            
            repo_data = RepoData(repository=self.mock_repo)
            self.analyzer._extract_metadata(temp_path, repo_data)
            
            # Check Docker detection
            self.assertIn("Docker", repo_data.frameworks)
    
    @patch('git_vitae.analyzer.Repo')
    def test_analyze_repository_handles_errors(self, mock_repo_class):
        """Test that analyze_repository handles errors gracefully."""
        # Mock repo to raise exception
        mock_repo_class.side_effect = Exception("Git error")
        
        result = self.analyzer.analyze_repository(self.mock_repo)
        
        # Should return basic repo data even on error
        self.assertIsInstance(result, RepoData)
        self.assertEqual(result.repository, self.mock_repo)
        self.assertEqual(result.total_commits, 0)


if __name__ == '__main__':
    unittest.main()