"""Command-line interface for Git Vitae."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import track
from rich.table import Table

from .config import ConfigManager
from .scanner import GitRepoScanner
from .analyzer import RepoAnalyzer
from .ai_processor import CVGenerator
from .formatter import CVFormatter
from .models import Config


console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('git-vitae.log'),
            logging.StreamHandler()
        ]
    )


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """Git Vitae - AI-powered CV generation from git repositories."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', type=click.Choice(['text', 'markdown', 'json', 'html']), 
              default='markdown', help='Output format')
@click.option('--ai-provider', type=click.Choice(['openai', 'anthropic']), 
              help='AI service provider')
@click.option('--model', type=str, help='AI model to use')
@click.option('--api-key', type=str, help='API key (or use environment variable)')
@click.option('--max-depth', type=int, help='Maximum directory depth to scan')
@click.option('--include-hidden', is_flag=True, help='Include hidden directories (starting with .)')
@click.option('--include-private', is_flag=True, help='Include private repositories')
@click.option('--template', type=str, help='CV template to use')
@click.option('--style', type=click.Choice(['professional', 'creative', 'technical']), 
              help='CV style')
@click.option('--config', type=click.Path(exists=True), help='Configuration file path')
@click.option('--scan-path', type=click.Path(exists=True), help='Directory path to scan for repositories')
@click.option('--no-anonymize', is_flag=True, help='Disable data anonymization (not recommended)')
@click.option('--allow-sensitive', is_flag=True, help='Allow sensitive data in AI processing (use with caution)')
@click.pass_context
def generate(ctx, output, format, ai_provider, model, api_key, max_depth, 
             include_hidden, include_private, template, style, config, scan_path, no_anonymize, allow_sensitive):
    """Generate CV from git repositories in specified or current directory."""
    
    try:
        # Load configuration
        config_path = Path(config) if config else None
        app_config = ConfigManager.load_config(config_path)
        
        # Override config with command line options
        if ai_provider:
            app_config.ai_provider = ai_provider
        if model:
            app_config.ai_model = model
        if api_key:
            app_config.ai_api_key = api_key
        if max_depth is not None:
            app_config.max_depth = max_depth
        if include_hidden:
            app_config.include_hidden = True
        if include_private:
            app_config.include_private = True
        if template:
            app_config.default_template = template
        # Use config default style if not provided
        if style is None:
            style = app_config.default_style
        elif style != app_config.default_style:  # Only save if different from current default
            app_config.default_style = style
        if scan_path:
            app_config.scan_path = str(scan_path)
        if no_anonymize:
            app_config.anonymize_data = False
            console.print("[yellow]Warning: Data anonymization disabled. Personal data may be sent to AI service.[/yellow]")
        if allow_sensitive:
            app_config.allow_sensitive_data = True
            console.print("[red]Warning: Sensitive data filtering disabled. Use with extreme caution.[/red]")
        
        # Check for API key
        if not app_config.ai_api_key:
            if app_config.ai_provider == 'openai' and os.getenv('OPENAI_API_KEY'):
                app_config.ai_api_key = os.getenv('OPENAI_API_KEY')
            elif app_config.ai_provider == 'anthropic' and os.getenv('ANTHROPIC_API_KEY'):
                app_config.ai_api_key = os.getenv('ANTHROPIC_API_KEY')
            else:
                console.print("[red]Error: No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable, or use --api-key option.[/red]")
                sys.exit(1)
        
        # Determine scan path
        scan_directory = Path(app_config.scan_path) if app_config.scan_path else Path.cwd()
        
        console.print(f"[green]Scanning for repositories in {scan_directory}...[/green]")
        
        # Validate scan path
        if not scan_directory.exists():
            console.print(f"[red]Error: Scan path does not exist: {scan_directory}[/red]")
            sys.exit(1)
        
        if not scan_directory.is_dir():
            console.print(f"[red]Error: Scan path is not a directory: {scan_directory}[/red]")
            sys.exit(1)
        
        # Scan for repositories
        scanner = GitRepoScanner(
            max_depth=app_config.max_depth,
            include_hidden=app_config.include_hidden,
            ignore_patterns=app_config.ignore_patterns
        )
        
        repositories = scanner.scan_directory(scan_directory)
        
        # Filter private repositories if not included
        if not app_config.include_private:
            repositories = [repo for repo in repositories if not repo.is_private]
        
        if not repositories:
            console.print(f"[yellow]No git repositories found in {scan_directory}.[/yellow]")
            sys.exit(0)
        
        console.print(f"[green]Found {len(repositories)} repositories[/green]")
        
        # Display found repositories
        table = Table(title="Discovered Repositories")
        table.add_column("Name", style="cyan")
        table.add_column("Path", style="blue")
        table.add_column("Remote", style="green")
        
        for repo in repositories:
            remote = repo.remote_url or "Local only"
            table.add_row(repo.name, str(repo.path), remote)
        
        console.print(table)
        
        # Analyze repositories
        console.print(f"[green]Analyzing repositories...[/green]")
        analyzer = RepoAnalyzer()
        repo_data_list = []
        
        for repo in track(repositories, description="Analyzing..."):
            repo_data = analyzer.analyze_repository(repo)
            repo_data_list.append(repo_data)
        
        # Generate CV using AI
        console.print(f"[green]Generating CV using {app_config.ai_provider}...[/green]")
        cv_generator = CVGenerator(app_config)
        cv_content = cv_generator.generate_cv(repo_data_list, style)
        
        # Format output
        console.print(f"[green]Formatting CV...[/green]")
        formatter = CVFormatter()
        
        # Use style as template if no explicit template provided
        effective_template = template or (style if style != "professional" else app_config.default_template)
        
        # Validate template exists
        if not formatter.validate_template(effective_template, format):
            available_templates = formatter.list_available_templates(format)
            console.print(f"[red]Error: Template '{effective_template}' not found for {format} format.[/red]")
            if available_templates:
                console.print(f"[yellow]Available templates: {', '.join(available_templates)}[/yellow]")
            else:
                console.print(f"[yellow]No templates found for {format} format. Using built-in template.[/yellow]")
            # Fall back to default template
            effective_template = "default"
        
        formatted_cv = formatter.format_cv(
            cv_content, 
            output_format=format, 
            template_name=effective_template
        )
        
        # Write output
        if output:
            output_path = Path(output)
            output_path.write_text(formatted_cv, encoding='utf-8')
            console.print(f"[green]CV written to {output_path}[/green]")
        else:
            console.print(formatted_cv)
        
        # Display summary
        console.print(f"\n[green]✓ Successfully generated CV from {len(repositories)} repositories[/green]")
        console.print(f"[blue]Total commits analyzed: {cv_content.metrics.get('total_commits', 0)}[/blue]")
        console.print(f"[blue]Languages detected: {', '.join(cv_content.skills.get('Programming Languages', []))}[/blue]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.group()
def config():
    """Manage configuration."""
    pass


@config.command()
@click.option('--path', type=click.Path(), help='Configuration file path')
def init(path):
    """Create default configuration file."""
    try:
        config_path = ConfigManager.create_default_config()
        console.print(f"[green]Default configuration created at {config_path}[/green]")
        console.print("Edit this file to customize your settings.")
    except Exception as e:
        console.print(f"[red]Error creating configuration: {e}[/red]")
        sys.exit(1)


@config.command()
@click.option('--path', type=click.Path(exists=True), help='Configuration file path')
def show(path):
    """Display current configuration."""
    try:
        config_path = Path(path) if path else None
        app_config = ConfigManager.load_config(config_path)
        
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("AI Provider", app_config.ai_provider)
        table.add_row("AI Model", app_config.ai_model)
        table.add_row("AI API Key Set", "Yes" if app_config.ai_api_key else "No")
        table.add_row("Max Depth", str(app_config.max_depth))
        table.add_row("Include Hidden", str(app_config.include_hidden))
        table.add_row("Scan Path", app_config.scan_path or "Current directory")
        table.add_row("Default Format", app_config.default_format)
        table.add_row("Default Template", app_config.default_template)
        table.add_row("Anonymize Data", str(app_config.anonymize_data))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error reading configuration: {e}[/red]")
        sys.exit(1)


@cli.command()
def version():
    """Show version information."""
    from . import __version__
    console.print(f"Git Vitae v{__version__}")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()