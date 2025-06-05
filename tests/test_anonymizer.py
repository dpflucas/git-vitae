"""Tests for data anonymizer."""

import unittest
from pathlib import Path

from git_vitae.anonymizer import DataAnonymizer
from git_vitae.models import GitRepository, RepoData, CommitStats


class TestDataAnonymizer(unittest.TestCase):
    """Test cases for DataAnonymizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.anonymizer = DataAnonymizer()
        
        # Create test repository data
        self.test_repo = GitRepository(
            path=Path("/test/my-secret-project"),
            name="my-secret-project",
            remote_url="https://github.com/user/secret-project.git"
        )
        
        self.test_repo_data = RepoData(
            repository=self.test_repo,
            languages={"Python": 60.0, "JavaScript": 30.0, "HTML": 10.0},
            frameworks=["Django", "React", "PostgreSQL"],
            total_commits=150,
            file_count=75,
            contributors=["John Doe", "Jane Smith"],
            description="A web application for managing sensitive data",
            lines_added=5000,
            lines_removed=1200,
            commit_stats=CommitStats(
                total_commits=150,
                author_commits=100,
                first_commit=None,
                last_commit=None,
                commits_by_month={"2024-01": 50, "2024-02": 100},
                average_commits_per_month=75.0
            )
        )
    
    def test_anonymize_repo_data_basic(self):
        """Test basic repository data anonymization."""
        repo_list = [self.test_repo_data]
        anonymized = self.anonymizer.anonymize_repo_data(repo_list)
        
        self.assertEqual(len(anonymized), 1)
        anon_repo = anonymized[0]
        
        # Check anonymization
        self.assertEqual(anon_repo["project_id"], "project_1")
        self.assertNotIn("my-secret-project", str(anon_repo))
        self.assertNotIn("secret", str(anon_repo))
        
        # Check preserved data
        self.assertEqual(anon_repo["total_commits"], 150)
        self.assertEqual(anon_repo["file_count"], 75)
        self.assertEqual(anon_repo["contributor_count"], 2)
        self.assertEqual(anon_repo["languages"], {"Python": 60.0, "JavaScript": 30.0, "HTML": 10.0})
    
    def test_sanitize_languages(self):
        """Test language sanitization."""
        languages = {
            "Python": 50.0,
            "JavaScript": 30.0,
            "malicious-script": 10.0,  # Should be filtered out
            "C++": 10.0
        }
        
        sanitized = self.anonymizer._sanitize_languages(languages)
        
        self.assertIn("Python", sanitized)
        self.assertIn("JavaScript", sanitized)
        self.assertIn("C++", sanitized)
        self.assertNotIn("malicious-script", sanitized)
    
    def test_sanitize_frameworks(self):
        """Test framework sanitization."""
        frameworks = [
            "Django",
            "React",
            "secret-internal-tool",  # Should be filtered out
            "Express.js",
            "password-manager"  # Should be filtered out
        ]
        
        sanitized = self.anonymizer._sanitize_frameworks(frameworks)
        
        self.assertIn("Django", sanitized)
        self.assertIn("React", sanitized)
        self.assertIn("Express.js", sanitized)
        self.assertNotIn("secret-internal-tool", sanitized)
        self.assertNotIn("password-manager", sanitized)
    
    def test_contains_sensitive_info(self):
        """Test sensitive information detection."""
        # Sensitive cases
        self.assertTrue(self.anonymizer._contains_sensitive_info("password-tool"))
        self.assertTrue(self.anonymizer._contains_sensitive_info("secret-key"))
        self.assertTrue(self.anonymizer._contains_sensitive_info("private-auth"))
        self.assertTrue(self.anonymizer._contains_sensitive_info("john@example.com"))
        self.assertTrue(self.anonymizer._contains_sensitive_info("192.168.1.1"))
        
        # Safe cases
        self.assertFalse(self.anonymizer._contains_sensitive_info("Django"))
        self.assertFalse(self.anonymizer._contains_sensitive_info("React"))
        self.assertFalse(self.anonymizer._contains_sensitive_info("Python"))
    
    def test_classify_project_type(self):
        """Test project type classification."""
        # Web development project
        web_repo = RepoData(
            repository=self.test_repo,
            languages={"JavaScript": 60.0, "HTML": 20.0, "CSS": 20.0},
            frameworks=["React", "Express.js"]
        )
        self.assertEqual(
            self.anonymizer._classify_project_type(web_repo),
            "fullstack_web"
        )
        
        # Data science project
        ds_repo = RepoData(
            repository=self.test_repo,
            languages={"Python": 100.0},
            frameworks=["Pandas", "NumPy", "Scikit-learn"]
        )
        self.assertEqual(
            self.anonymizer._classify_project_type(ds_repo),
            "data_science"
        )
        
        # Systems programming
        sys_repo = RepoData(
            repository=self.test_repo,
            languages={"C++": 80.0, "C": 20.0},
            frameworks=[]
        )
        self.assertEqual(
            self.anonymizer._classify_project_type(sys_repo),
            "systems_programming"
        )
    
    def test_classify_activity_level(self):
        """Test activity level classification."""
        self.assertEqual(self.anonymizer._classify_activity_level(1000), "high_activity")
        self.assertEqual(self.anonymizer._classify_activity_level(200), "medium_activity")
        self.assertEqual(self.anonymizer._classify_activity_level(50), "low_activity")
        self.assertEqual(self.anonymizer._classify_activity_level(5), "minimal_activity")
    
    def test_classify_size_category(self):
        """Test size category classification."""
        self.assertEqual(self.anonymizer._classify_size_category(2000), "large_project")
        self.assertEqual(self.anonymizer._classify_size_category(500), "medium_project")
        self.assertEqual(self.anonymizer._classify_size_category(50), "small_project")
        self.assertEqual(self.anonymizer._classify_size_category(5), "minimal_project")
    
    def test_generate_anonymized_summary(self):
        """Test anonymized summary generation."""
        repo_list = [self.test_repo_data]
        anonymized_repos = self.anonymizer.anonymize_repo_data(repo_list)
        summary = self.anonymizer.generate_anonymized_summary(anonymized_repos)
        
        # Check structure
        self.assertIn("summary_statistics", summary)
        self.assertIn("technical_profile", summary)
        self.assertIn("development_patterns", summary)
        
        # Check summary statistics
        stats = summary["summary_statistics"]
        self.assertEqual(stats["total_projects"], 1)
        self.assertEqual(stats["total_commits"], 150)
        self.assertEqual(stats["total_lines_added"], 5000)
        
        # Check technical profile
        tech = summary["technical_profile"]
        self.assertIn("primary_languages", tech)
        self.assertIn("frameworks_and_tools", tech)
        self.assertEqual(tech["primary_languages"]["Python"], 60.0)
        
        # Check development patterns
        patterns = summary["development_patterns"]
        self.assertEqual(patterns["average_commits_per_project"], 150.0)
    
    def test_sanitize_text(self):
        """Test text sanitization."""
        sensitive_text = """
        This project uses john@example.com for authentication.
        The API key is sk-1234567890abcdef.
        Files are stored in /Users/john/secret-project/.
        Server IP: 192.168.1.100
        Visit https://internal.company.com/secret for details.
        """
        
        sanitized = self.anonymizer.sanitize_text(sensitive_text)
        
        # Check that sensitive data is removed
        self.assertNotIn("john@example.com", sanitized)
        self.assertNotIn("sk-1234567890abcdef", sanitized)
        self.assertNotIn("/Users/john", sanitized)
        self.assertNotIn("192.168.1.100", sanitized)
        
        # Check that URLs are replaced with domain only
        self.assertIn("[URL:internal.company.com]", sanitized)
        
        # Check redaction markers
        self.assertIn("[REDACTED]", sanitized)
        self.assertIn("[PATH]", sanitized)
    
    def test_multiple_repos_anonymization(self):
        """Test anonymization with multiple repositories."""
        # Create second repo
        repo2 = GitRepository(
            path=Path("/test/another-project"),
            name="another-project",
            remote_url="https://github.com/user/another-project.git"
        )
        
        repo_data2 = RepoData(
            repository=repo2,
            languages={"Go": 80.0, "YAML": 20.0},
            frameworks=["Docker", "Kubernetes"],
            total_commits=75,
            file_count=30,
            contributors=["Alice Johnson"],
            lines_added=2000,
            lines_removed=500
        )
        
        repo_list = [self.test_repo_data, repo_data2]
        anonymized = self.anonymizer.anonymize_repo_data(repo_list)
        
        self.assertEqual(len(anonymized), 2)
        self.assertEqual(anonymized[0]["project_id"], "project_1")
        self.assertEqual(anonymized[1]["project_id"], "project_2")
        
        # Test summary generation
        summary = self.anonymizer.generate_anonymized_summary(anonymized)
        self.assertEqual(summary["summary_statistics"]["total_projects"], 2)
        self.assertEqual(summary["summary_statistics"]["total_commits"], 225)


if __name__ == '__main__':
    unittest.main()