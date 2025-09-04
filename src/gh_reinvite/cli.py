"""
CLI interface for GitHub Reinvite Tool.
"""

import json
import subprocess
import sys
import time
from typing import Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

console = Console()

VALID_PERMISSIONS = ["pull", "triage", "push", "maintain", "admin"]


def run_gh_command(args: list, check: bool = True) -> Tuple[int, str, str]:
    """
    Execute a GitHub CLI command and return the result.
    
    Args:
        args: List of command arguments
        check: Whether to raise on non-zero exit code
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout.strip() if e.stdout else "", e.stderr.strip() if e.stderr else ""
    except FileNotFoundError:
        console.print("[bold red]Error:[/bold red] GitHub CLI (gh) is not installed.")
        console.print("Please install it from: https://cli.github.com/")
        sys.exit(1)


def check_gh_auth():
    """Check if GitHub CLI is authenticated."""
    returncode, _, _ = run_gh_command(["auth", "status"], check=False)
    if returncode != 0:
        console.print("[bold red]Error:[/bold red] Not authenticated with GitHub.")
        console.print("Please run: [bold]gh auth login[/bold]")
        sys.exit(1)


def validate_repository(repo: str) -> bool:
    """
    Validate repository format and existence.
    
    Args:
        repo: Repository in owner/name format
        
    Returns:
        True if valid, False otherwise
    """
    if "/" not in repo:
        console.print(f"[bold red]Error:[/bold red] Invalid repository format: {repo}")
        console.print("Use format: owner/repository")
        return False
    
    # Check if repository exists and is accessible
    returncode, _, stderr = run_gh_command(["repo", "view", repo, "--json", "name"], check=False)
    if returncode != 0:
        console.print(f"[bold red]Error:[/bold red] Cannot access repository: {repo}")
        if "not found" in stderr.lower():
            console.print("Repository not found or you don't have access.")
        return False
    
    return True


def check_collaborator(repo: str, username: str) -> bool:
    """
    Check if user is a collaborator on the repository.
    
    Args:
        repo: Repository in owner/name format
        username: GitHub username
        
    Returns:
        True if user is a collaborator, False otherwise
    """
    returncode, stdout, _ = run_gh_command(
        ["api", f"repos/{repo}/collaborators/{username}"],
        check=False
    )
    return returncode == 0


def check_pending_invitation(repo: str, username: str) -> int:
    """
    Check if user has a pending invitation to the repository.
    
    Args:
        repo: Repository in owner/name format
        username: GitHub username
        
    Returns:
        Invitation ID if found, 0 otherwise
    """
    returncode, stdout, _ = run_gh_command(
        ["api", f"repos/{repo}/invitations"],
        check=False
    )
    
    if returncode == 0 and stdout:
        try:
            invitations = json.loads(stdout)
            for invitation in invitations:
                if invitation.get("invitee", {}).get("login", "").lower() == username.lower():
                    return invitation.get("id", 0)
        except json.JSONDecodeError:
            pass
    
    return 0


def remove_pending_invitation(repo: str, invitation_id: int) -> bool:
    """
    Remove a pending invitation from the repository.
    
    Args:
        repo: Repository in owner/name format
        invitation_id: The invitation ID to remove
        
    Returns:
        True if successful, False otherwise
    """
    returncode, _, stderr = run_gh_command(
        ["api", "-X", "DELETE", f"repos/{repo}/invitations/{invitation_id}"],
        check=False
    )
    
    if returncode == 0:
        console.print(f"[green]✓[/green] Successfully removed pending invitation")
        return True
    else:
        console.print(f"[red]✗[/red] Failed to remove pending invitation: {stderr}")
        return False


def remove_collaborator(repo: str, username: str) -> bool:
    """
    Remove a collaborator from a repository.
    
    Args:
        repo: Repository in owner/name format
        username: GitHub username to remove
        
    Returns:
        True if successful, False otherwise
    """
    returncode, _, stderr = run_gh_command(
        ["api", "-X", "DELETE", f"repos/{repo}/collaborators/{username}"],
        check=False
    )
    
    if returncode == 0:
        console.print(f"[green]✓[/green] Successfully removed [bold]{username}[/bold] from [bold]{repo}[/bold]")
        return True
    else:
        console.print(f"[red]✗[/red] Failed to remove collaborator: {stderr}")
        return False


def invite_collaborator(repo: str, username: str, permission: str) -> bool:
    """
    Invite a collaborator to a repository with specified permissions.
    
    Args:
        repo: Repository in owner/name format
        username: GitHub username to invite
        permission: Permission level (pull, triage, push, maintain, admin)
        
    Returns:
        True if successful, False otherwise
    """
    returncode, stdout, stderr = run_gh_command(
        ["api", "-X", "PUT", f"repos/{repo}/collaborators/{username}",
         "-f", f"permission={permission}"],
        check=False
    )
    
    if returncode == 0:
        console.print(f"[green]✓[/green] Successfully invited [bold]{username}[/bold] to [bold]{repo}[/bold] with [bold]{permission}[/bold] permissions")
        return True
    else:
        console.print(f"[red]✗[/red] Failed to invite collaborator: {stderr}")
        return False


def countdown_delay(seconds: int):
    """Display a countdown for the specified delay."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Waiting {seconds} seconds before reinviting...", total=seconds)
        for i in range(seconds):
            progress.update(task, description=f"Waiting {seconds - i} seconds before reinviting...")
            time.sleep(1)
            progress.update(task, advance=1)


@click.command()
@click.argument('repository')
@click.argument('username')
@click.option('--delay', '-d', default=5, type=int, help='Delay in seconds between remove and reinvite (default: 5)')
@click.option('--permission', '-p', default='push', 
              type=click.Choice(VALID_PERMISSIONS, case_sensitive=False),
              help='Permission level for reinvite (default: push)')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.version_option(version='0.2.0', prog_name='gh-reinvite')
def main(repository: str, username: str, delay: int, permission: str, yes: bool):
    """
    GitHub Reinvite Tool - Remove and reinvite a collaborator from/to a GitHub repository.
    
    This tool automates the process of removing a collaborator from a GitHub repository,
    waiting for a specified delay, and then reinviting them with the specified permissions.
    
    REPOSITORY: GitHub repository in owner/name format
    USERNAME: GitHub username to remove and reinvite
    """
    
    # Display header
    console.print(Panel.fit(
        "[bold blue]GitHub Reinvite Tool[/bold blue]\n"
        f"Repository: [bold]{repository}[/bold]\n"
        f"User: [bold]{username}[/bold]\n"
        f"Delay: [bold]{delay}[/bold] seconds\n"
        f"Permission: [bold]{permission}[/bold]",
        title="Configuration"
    ))
    
    # Check GitHub CLI authentication
    with console.status("Checking GitHub authentication..."):
        check_gh_auth()
    console.print("[green]✓[/green] GitHub CLI authenticated")
    
    # Validate repository
    with console.status(f"Validating repository {repository}..."):
        if not validate_repository(repository):
            sys.exit(1)
    console.print(f"[green]✓[/green] Repository [bold]{repository}[/bold] is accessible")
    
    # Check if user is a collaborator
    with console.status(f"Checking if {username} is a collaborator..."):
        is_collaborator = check_collaborator(repository, username)
    
    if not is_collaborator:
        console.print(f"[yellow]⚠[/yellow] [bold]{username}[/bold] is not currently a collaborator on [bold]{repository}[/bold]")
        
        # Check for pending invitation
        with console.status(f"Checking for pending invitation..."):
            invitation_id = check_pending_invitation(repository, username)
        
        if invitation_id:
            console.print(f"[yellow]⚠[/yellow] Found pending invitation for [bold]{username}[/bold]")
            
            # Confirmation prompt for pending invitation
            if not yes:
                if not Confirm.ask(f"Remove pending invitation and reinvite [bold]{username}[/bold]?"):
                    console.print("Operation cancelled.")
                    sys.exit(0)
            
            # Remove pending invitation
            console.print("\n[bold]Step 1:[/bold] Removing pending invitation...")
            if not remove_pending_invitation(repository, invitation_id):
                console.print("[red]Failed to remove pending invitation. Aborting.[/red]")
                sys.exit(1)
        else:
            console.print("[yellow]⚠[/yellow] No pending invitation found")
            
            # Confirmation prompt for new invitation
            if not yes:
                if not Confirm.ask(f"Invite [bold]{username}[/bold] to [bold]{repository}[/bold]?"):
                    console.print("Operation cancelled.")
                    sys.exit(0)
    else:
        console.print(f"[green]✓[/green] [bold]{username}[/bold] is currently a collaborator")
        
        # Confirmation prompt
        if not yes:
            if not Confirm.ask(f"Remove [bold]{username}[/bold] from [bold]{repository}[/bold] and reinvite them?"):
                console.print("Operation cancelled.")
                sys.exit(0)
        
        # Remove collaborator
        console.print("\n[bold]Step 1:[/bold] Removing collaborator...")
        if not remove_collaborator(repository, username):
            console.print("[red]Failed to remove collaborator. Aborting.[/red]")
            sys.exit(1)
    
    # Delay
    if delay > 0:
        console.print(f"\n[bold]Step 2:[/bold] Waiting {delay} seconds...")
        countdown_delay(delay)
    
    # Reinvite collaborator
    console.print("\n[bold]Step 3:[/bold] Reinviting collaborator...")
    if not invite_collaborator(repository, username, permission):
        console.print("[red]Failed to reinvite collaborator.[/red]")
        sys.exit(1)
    
    console.print("\n[bold green]✓ Operation completed successfully![/bold green]")
    console.print(f"[bold]{username}[/bold] has been reinvited to [bold]{repository}[/bold] with [bold]{permission}[/bold] permissions.")


def run():
    """Entry point for the CLI."""
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()