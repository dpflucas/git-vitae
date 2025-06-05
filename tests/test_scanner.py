"""Tests for repository scanner."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from git import Repo

from git_vitae.scanner import GitRepoScanner
from git_vitae.models import GitRepository


class TestGitRepoScanner(unittest.TestCase):
    """Test cases for GitRepoScanner."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scanner = GitRepoScanner(max_depth=2, include_hidden=False)
    
    def test_scanner_initialization(self):
        """Test scanner initialization with default values."""
        scanner = GitRepoScanner()
        self.assertEqual(scanner.max_depth, 3)
        self.assertFalse(scanner.include_hidden)
        self.assertIn("node_modules", scanner.ignore_patterns)
    
    def test_scanner_custom_initialization(self):
        """Test scanner initialization with custom values."""
        custom_patterns = ["custom_ignore"]
        scanner = GitRepoScanner(
            max_depth=5, 
            include_hidden=True, 
            ignore_patterns=custom_patterns
        )
        self.assertEqual(scanner.max_depth, 5)
        self.assertTrue(scanner.include_hidden)
        self.assertEqual(scanner.ignore_patterns, custom_patterns)
    
    @patch('git_vitae.scanner.Repo')
    def test_is_git_repo_valid(self, mock_repo):
        """Test is_git_repo with valid repository."""
        mock_repo.return_value = MagicMock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.scanner.is_git_repo(Path(temp_dir))
            self.assertTrue(result)
            mock_repo.assert_called_once_with(Path(temp_dir))
    
    @patch('git_vitae.scanner.Repo')
    def test_is_git_repo_invalid(self, mock_repo):
        """Test is_git_repo with invalid repository."""
        from git import InvalidGitRepositoryError
        mock_repo.side_effect = InvalidGitRepositoryError("Not a git repo")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.scanner.is_git_repo(Path(temp_dir))
            self.assertFalse(result)
    
    @patch('git_vitae.scanner.GitRepoScanner.is_git_repo')
    def test_scan_directory_no_repos(self, mock_is_git):
        """Test scanning directory with no git repositories."""
        mock_is_git.return_value = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repos = self.scanner.scan_directory(Path(temp_dir))
            self.assertEqual(len(repos), 0)
    
    @patch('git_vitae.scanner.GitRepoScanner._create_git_repository')
    @patch('git_vitae.scanner.GitRepoScanner.is_git_repo')
    def test_scan_directory_with_repo(self, mock_is_git, mock_create_repo):
        """Test scanning directory with git repository."""
        mock_is_git.return_value = True
        mock_repo = GitRepository(
            path=Path("/test/repo"),
            name="test-repo"
        )
        mock_create_repo.return_value = mock_repo
        
        with tempfile.TemporaryDirectory() as temp_dir:
            repos = self.scanner.scan_directory(Path(temp_dir))
            self.assertEqual(len(repos), 1)
            self.assertEqual(repos[0].name, "test-repo")
    
    def test_scan_directory_respects_max_depth(self):
        """Test that scanning respects max_depth setting."""
        scanner = GitRepoScanner(max_depth=1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create nested directories beyond max_depth
            deep_dir = temp_path / "level1" / "level2" / "level3"
            deep_dir.mkdir(parents=True)
            
            # Mock to check if deep directory is scanned
            with patch.object(scanner, 'is_git_repo', return_value=False) as mock_is_git:
                scanner.scan_directory(temp_path)
                
                # Check that deep directory was not scanned
                called_paths = [call[0][0] for call in mock_is_git.call_args_list]
                self.assertNotIn(deep_dir, called_paths)
    
    @patch('git_vitae.scanner.Repo')
    def test_create_git_repository_with_remote(self, mock_repo_class):
        """Test creating GitRepository object with remote URL."""
        # Mock repo object
        mock_repo = MagicMock()
        mock_remote = MagicMock()
        mock_remote.url = "https://github.com/user/repo.git"
        
        # Mock remotes to be truthy and have origin attribute
        mock_remotes = MagicMock()
        mock_remotes.__bool__ = lambda x: True  # Make it truthy
        mock_remotes.origin = mock_remote
        mock_repo.remotes = mock_remotes
        
        # Mock commit
        mock_commit = MagicMock()
        mock_commit.committed_datetime = "2024-01-01"
        mock_repo.head.commit = mock_commit
        mock_repo.head.is_valid.return_value = True
        
        mock_repo_class.return_value = mock_repo
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            git_repo = self.scanner._create_git_repository(temp_path)
            
            self.assertIsNotNone(git_repo)
            self.assertEqual(git_repo.path, temp_path)
            self.assertEqual(git_repo.name, temp_path.name)
            self.assertEqual(git_repo.remote_url, "https://github.com/user/repo.git")
            self.assertFalse(git_repo.is_private)  # GitHub repo is considered public
    
    @patch('git_vitae.scanner.Repo')
    def test_create_git_repository_local_only(self, mock_repo_class):
        """Test creating GitRepository object without remote."""
        # Mock repo object without remotes
        mock_repo = MagicMock()
        mock_repo.remotes = []
        mock_repo.head.is_valid.return_value = False
        
        mock_repo_class.return_value = mock_repo
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            git_repo = self.scanner._create_git_repository(temp_path)
            
            self.assertIsNotNone(git_repo)
            self.assertEqual(git_repo.path, temp_path)
            self.assertIsNone(git_repo.remote_url)
            self.assertTrue(git_repo.is_private)  # Local repo is considered private
    
    def test_scan_ignores_patterns(self):
        """Test that scanning ignores specified patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directories that should be ignored
            (temp_path / "node_modules").mkdir()
            (temp_path / ".git").mkdir()
            (temp_path / "valid_dir").mkdir()
            
            with patch.object(self.scanner, 'is_git_repo', return_value=False) as mock_is_git:
                self.scanner.scan_directory(temp_path)
                
                # Check which directories were scanned
                called_paths = [call[0][0] for call in mock_is_git.call_args_list]
                
                # Should not scan ignored directories
                self.assertNotIn(temp_path / "node_modules", called_paths)
                self.assertNotIn(temp_path / ".git", called_paths)
                
                # Should scan valid directory
                self.assertIn(temp_path / "valid_dir", called_paths)


if __name__ == '__main__':
    unittest.main()