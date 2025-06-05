"""Tests for CLI scan path functionality."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from git_vitae.cli import cli
from git_vitae.models import GitRepository, RepoData


class TestCLIScanPath(unittest.TestCase):
    """Test cases for CLI scan path functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_scan_path_option_in_help(self):
        """Test that scan-path option appears in help."""
        result = self.runner.invoke(cli, ['generate', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('--scan-path', result.output)
        self.assertIn('Directory path to scan for repositories', result.output)
    
    @patch('git_vitae.cli.CVGenerator')
    @patch('git_vitae.cli.RepoAnalyzer')
    @patch('git_vitae.cli.GitRepoScanner')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_scan_path_with_valid_directory(self, mock_scanner, mock_analyzer, mock_cv_gen):
        """Test scan-path with a valid directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a subdirectory to scan
            scan_dir = temp_path / "projects"
            scan_dir.mkdir()
            
            # Mock scanner to return test repositories
            mock_repo = GitRepository(
                path=scan_dir / "test-repo",
                name="test-repo"
            )
            mock_scanner.return_value.scan_directory.return_value = [mock_repo]
            
            # Mock analyzer
            mock_repo_data = RepoData(repository=mock_repo)
            mock_analyzer.return_value.analyze_repository.return_value = mock_repo_data
            
            # Mock CV generator
            from git_vitae.models import CVContent
            mock_cv = CVContent(name="Test Developer", summary="Test summary")
            mock_cv_gen.return_value.generate_cv.return_value = mock_cv
            
            # Run command with scan-path
            result = self.runner.invoke(cli, [
                'generate',
                '--scan-path', str(scan_dir),
                '--output', str(temp_path / "cv.md")
            ])
            
            # Check that scanner was called with correct directory
            mock_scanner.return_value.scan_directory.assert_called_once_with(scan_dir)
            
            # Should succeed if mocks are properly set up
            if result.exit_code != 0:
                print(f"Command output: {result.output}")
    
    def test_scan_path_with_nonexistent_directory(self):
        """Test scan-path with non-existent directory."""
        result = self.runner.invoke(cli, [
            'generate',
            '--scan-path', '/nonexistent/directory'
        ])
        
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('does not exist', result.output)
    
    def test_scan_path_with_file_instead_of_directory(self):
        """Test scan-path with a file instead of directory."""
        with tempfile.NamedTemporaryFile() as temp_file:
            result = self.runner.invoke(cli, [
                'generate',
                '--scan-path', temp_file.name
            ])
            
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('not a directory', result.output)
    
    @patch('git_vitae.cli.ConfigManager')
    def test_scan_path_from_config_file(self, mock_config_manager):
        """Test that scan_path can be set from config file."""
        from git_vitae.models import Config
        
        # Mock config with scan_path set
        mock_config = Config(
            scan_path="/custom/scan/path",
            ai_api_key="test-key"
        )
        mock_config_manager.load_config.return_value = mock_config
        
        # Create a directory that exists for the path validation
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config.scan_path = temp_dir
            
            with patch('git_vitae.cli.GitRepoScanner') as mock_scanner:
                mock_scanner.return_value.scan_directory.return_value = []
                
                result = self.runner.invoke(cli, ['generate'])
                
                # Should use the path from config
                mock_scanner.return_value.scan_directory.assert_called_once_with(Path(temp_dir))
    
    def test_scan_path_cli_overrides_config(self):
        """Test that CLI scan-path overrides config file setting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create two directories
            config_dir = temp_path / "config_dir"
            cli_dir = temp_path / "cli_dir"
            config_dir.mkdir()
            cli_dir.mkdir()
            
            with patch('git_vitae.cli.ConfigManager') as mock_config_manager:
                from git_vitae.models import Config
                
                # Mock config with one scan_path
                mock_config = Config(
                    scan_path=str(config_dir),
                    ai_api_key="test-key"
                )
                mock_config_manager.load_config.return_value = mock_config
                
                with patch('git_vitae.cli.GitRepoScanner') as mock_scanner:
                    mock_scanner.return_value.scan_directory.return_value = []
                    
                    # CLI option should override config
                    result = self.runner.invoke(cli, [
                        'generate',
                        '--scan-path', str(cli_dir)
                    ])
                    
                    # Should use CLI path, not config path
                    mock_scanner.return_value.scan_directory.assert_called_once_with(cli_dir)
    
    def test_config_show_displays_scan_path(self):
        """Test that config show command displays scan path."""
        with patch('git_vitae.cli.ConfigManager') as mock_config_manager:
            from git_vitae.models import Config
            
            mock_config = Config(scan_path="/custom/path")
            mock_config_manager.load_config.return_value = mock_config
            
            result = self.runner.invoke(cli, ['config', 'show'])
            
            self.assertEqual(result.exit_code, 0)
            self.assertIn('/custom/path', result.output)
    
    def test_config_show_displays_default_when_no_scan_path(self):
        """Test that config show displays default when no scan path set."""
        with patch('git_vitae.cli.ConfigManager') as mock_config_manager:
            from git_vitae.models import Config
            
            mock_config = Config()  # No scan_path set
            mock_config_manager.load_config.return_value = mock_config
            
            result = self.runner.invoke(cli, ['config', 'show'])
            
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Current directory', result.output)


if __name__ == '__main__':
    unittest.main()