"""Tests for CV formatter."""

import json
import unittest
from datetime import datetime
from pathlib import Path

from git_vitae.formatter import CVFormatter
from git_vitae.models import CVContent, Project


class TestCVFormatter(unittest.TestCase):
    """Test cases for CVFormatter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = CVFormatter()
        
        # Create sample CV content
        self.sample_cv = CVContent(
            name="John Developer",
            email="john@example.com",
            github_url="https://github.com/johndeveloper",
            summary="Experienced software developer with expertise in Python and JavaScript.",
            skills={
                "Programming Languages": ["Python", "JavaScript", "TypeScript"],
                "Frameworks": ["Django", "React", "Express.js"],
                "Tools": ["Git", "Docker", "AWS"]
            },
            projects=[
                Project(
                    name="Web Application",
                    description="A full-stack web application built with React and Django",
                    technologies=["Python", "JavaScript", "React", "Django"],
                    commits=150,
                    lines_of_code=5000,
                    url="https://github.com/johndeveloper/webapp"
                ),
                Project(
                    name="API Service",
                    description="RESTful API service for data processing",
                    technologies=["Python", "Flask", "PostgreSQL"],
                    commits=75,
                    lines_of_code=2500
                )
            ],
            metrics={
                "total_commits": 225,
                "total_repositories": 2,
                "lines_added": 7500,
                "lines_removed": 1200
            },
            generated_at=datetime(2024, 1, 15, 10, 30, 0)
        )
    
    def test_format_json(self):
        """Test JSON formatting."""
        result = self.formatter.format_cv(self.sample_cv, "json")
        
        # Parse JSON to verify it's valid
        data = json.loads(result)
        
        # Check basic structure
        self.assertEqual(data["name"], "John Developer")
        self.assertEqual(data["email"], "john@example.com")
        self.assertEqual(len(data["projects"]), 2)
        self.assertEqual(len(data["skills"]), 3)
        
        # Check project data
        self.assertEqual(data["projects"][0]["name"], "Web Application")
        self.assertEqual(data["projects"][0]["commits"], 150)
        
        # Check skills
        self.assertIn("Python", data["skills"]["Programming Languages"])
        
        # Check metrics
        self.assertEqual(data["metrics"]["total_commits"], 225)
    
    def test_format_text(self):
        """Test plain text formatting."""
        result = self.formatter.format_cv(self.sample_cv, "text")
        
        # Check header
        self.assertIn("John Developer", result)
        self.assertIn("john@example.com", result)
        self.assertIn("https://github.com/johndeveloper", result)
        self.assertIn("2024-01-15", result)
        
        # Check sections
        self.assertIn("PROFESSIONAL SUMMARY", result)
        self.assertIn("TECHNICAL SKILLS", result)
        self.assertIn("KEY PROJECTS", result)
        self.assertIn("CONTRIBUTION METRICS", result)
        
        # Check content
        self.assertIn("Experienced software developer", result)
        self.assertIn("Programming Languages:", result)
        self.assertIn("Python, JavaScript, TypeScript", result)
        self.assertIn("Web Application", result)
        self.assertIn("Total Commits: 225", result)
    
    def test_format_markdown_default_template(self):
        """Test Markdown formatting with default template."""
        result = self.formatter.format_cv(self.sample_cv, "markdown")
        
        # Check Markdown structure
        self.assertIn("# John Developer", result)
        self.assertIn("## Professional Summary", result)
        self.assertIn("## Technical Skills", result)
        self.assertIn("## Key Projects", result)
        self.assertIn("## Contribution Metrics", result)
        
        # Check content formatting
        self.assertIn("**Email**: john@example.com", result)
        self.assertIn("**GitHub**: https://github.com/johndeveloper", result)
        self.assertIn("### Programming Languages", result)
        self.assertIn("- Python", result)
        self.assertIn("### Web Application", result)
        self.assertIn("**Technologies**: Python, JavaScript, React, Django", result)
        self.assertIn("**Contributions**: 150 commits, 5,000 lines of code", result)
    
    def test_format_html_default_template(self):
        """Test HTML formatting with default template."""
        result = self.formatter.format_cv(self.sample_cv, "html")
        
        # Check HTML structure
        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn("<html lang=\"en\">", result)
        self.assertIn("<title>John Developer - CV</title>", result)
        self.assertIn("<h1>John Developer</h1>", result)
        self.assertIn("<h2>Professional Summary</h2>", result)
        self.assertIn("<h2>Technical Skills</h2>", result)
        
        # Check content
        self.assertIn("john@example.com", result)
        self.assertIn("Experienced software developer", result)
        self.assertIn("Web Application", result)
        
        # Check styling
        self.assertIn("<style>", result)
        self.assertIn("font-family: Arial", result)
    
    def test_format_unsupported_format(self):
        """Test error handling for unsupported format."""
        with self.assertRaises(ValueError) as context:
            self.formatter.format_cv(self.sample_cv, "pdf")
        
        self.assertIn("Unsupported output format: pdf", str(context.exception))
    
    def test_format_with_empty_cv(self):
        """Test formatting with minimal CV content."""
        minimal_cv = CVContent(
            name="",
            summary="",
            skills={},
            projects=[],
            metrics={}
        )
        
        # Should not raise errors
        json_result = self.formatter.format_cv(minimal_cv, "json")
        text_result = self.formatter.format_cv(minimal_cv, "text")
        md_result = self.formatter.format_cv(minimal_cv, "markdown")
        
        # Check that formatting still works
        self.assertIsInstance(json_result, str)
        self.assertIsInstance(text_result, str)
        self.assertIsInstance(md_result, str)
        
        # JSON should parse correctly
        json.loads(json_result)
    
    def test_format_with_special_characters(self):
        """Test formatting with special characters in content."""
        special_cv = CVContent(
            name="José García-López",
            summary="Developer with expertise in C++ & C#, HTML/CSS, and Node.js",
            skills={
                "Languages": ["C++", "C#", "HTML/CSS"],
                "Frameworks": ["ASP.NET", "Node.js"]
            },
            projects=[
                Project(
                    name="Project with 'quotes' & symbols",
                    description="Description with <tags> and & symbols",
                    technologies=["C++", "C#"],
                    commits=50,
                    lines_of_code=1000
                )
            ],
            metrics={"total_commits": 50}
        )
        
        # Should handle special characters without errors
        json_result = self.formatter.format_cv(special_cv, "json")
        text_result = self.formatter.format_cv(special_cv, "text")
        md_result = self.formatter.format_cv(special_cv, "markdown")
        html_result = self.formatter.format_cv(special_cv, "html")
        
        # Verify content is preserved
        self.assertIn("José García-López", text_result)
        self.assertIn("C++", json_result)
        self.assertIn("Node.js", md_result)
        
        # JSON should still be valid
        json.loads(json_result)
    
    def test_format_large_numbers(self):
        """Test formatting with large numbers."""
        large_numbers_cv = CVContent(
            name="Developer",
            summary="Test",
            metrics={
                "total_commits": 12345,
                "lines_added": 1234567,
                "total_repositories": 50
            }
        )
        
        text_result = self.formatter.format_cv(large_numbers_cv, "text")
        md_result = self.formatter.format_cv(large_numbers_cv, "markdown")
        
        # Check number formatting with commas
        self.assertIn("12,345", text_result)
        self.assertIn("1,234,567", text_result)
        self.assertIn("12,345", md_result)
    
    def test_template_fallback(self):
        """Test fallback to built-in template when template file not found."""
        # Use non-existent template
        result = self.formatter.format_cv(self.sample_cv, "markdown", "nonexistent")
        
        # Should still generate output using built-in template
        self.assertIn("# John Developer", result)
        self.assertIn("## Professional Summary", result)


if __name__ == '__main__':
    unittest.main()