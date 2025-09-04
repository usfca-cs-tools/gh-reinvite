# gh-reinvite

A Python CLI tool to automate removing and reinviting GitHub repository collaborators. This tool is useful when you need to refresh a collaborator's access or reset their permissions.

## Features

- Remove and reinvite collaborators with a single command
- **NEW**: Automatically handles pending invitations - removes and resends them
- Configurable delay between removal and reinvite
- Support for all GitHub permission levels (pull, triage, push, maintain, admin)
- Interactive confirmation prompts with bypass option
- Beautiful terminal output with progress indicators
- Validation of repository access and collaborator status

## Prerequisites

- Python 3.8 or higher (3.12 recommended)
- [GitHub CLI (gh)](https://cli.github.com/) installed and authenticated
  ```bash
  # Install GitHub CLI (if not already installed)
  # macOS:
  brew install gh
  
  # Authenticate with GitHub
  gh auth login
  ```

## Installation

### Quick Install with UV (Recommended)

If you have [UV](https://github.com/astral-sh/uv) installed, you can install and run gh-reinvite in several ways:

#### Option 1: Install as a global tool
```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install gh-reinvite as a global tool
uv tool install git+https://github.com/yourusername/gh-reinvite.git

# Now use it anywhere
gh-reinvite owner/repository username
```

#### Option 2: Run without installation (one-off usage)
```bash
# Run directly with uvx
uvx --from git+https://github.com/yourusername/gh-reinvite.git gh-reinvite owner/repo username
```

#### Option 3: Local development installation
```bash
# Clone and install for development
git clone https://github.com/yourusername/gh-reinvite.git
cd gh-reinvite

# Install in development mode
uv pip install -e .

# Run with uv
uv run gh-reinvite owner/repository username
```

### Traditional Installation (pip)

```bash
# Clone the repository
git clone https://github.com/yourusername/gh-reinvite.git
cd gh-reinvite

# Install the package
pip install .

# Or install in editable mode for development
pip install -e .
```

## Usage

### Basic Usage

Remove and reinvite a collaborator with default settings (5-second delay, push permissions):

```bash
gh-reinvite owner/repository username
```

### Examples

```bash
# Remove and reinvite with default settings
gh-reinvite octocat/hello-world johndoe

# With a custom delay of 10 seconds
gh-reinvite octocat/hello-world johndoe --delay 10

# With admin permissions
gh-reinvite octocat/hello-world johndoe --permission admin

# Skip confirmation prompt
gh-reinvite octocat/hello-world johndoe --yes

# Combine options
gh-reinvite octocat/hello-world johndoe -d 3 -p maintain -y

# Show version
gh-reinvite --version
```

### Command Options

- `REPOSITORY`: GitHub repository in `owner/name` format (required)
- `USERNAME`: GitHub username to remove and reinvite (required)
- `-d, --delay INTEGER`: Delay in seconds between remove and reinvite (default: 5)
- `-p, --permission`: Permission level for reinvite (default: push)
  - Options: `pull`, `triage`, `push`, `maintain`, `admin`
- `-y, --yes`: Skip confirmation prompt

### Permission Levels

- **pull**: Read access (view code, clone, create issues)
- **triage**: Read + manage issues and pull requests  
- **push**: Write access (same as "Write" in GitHub UI - push to branches, merge PRs)
- **maintain**: Push + manage repository settings (without access to sensitive actions)
- **admin**: Full administrative access

## How It Works

1. **Authentication Check**: Verifies GitHub CLI is authenticated
2. **Repository Validation**: Confirms the repository exists and is accessible
3. **Status Check**: Determines if the user is:
   - An existing collaborator → Removes them
   - Has a pending invitation → Removes the pending invitation
   - Neither → Proceeds directly to invitation
4. **Removal** (if applicable): Removes the collaborator or pending invitation
5. **Delay**: Waits for the specified duration with a countdown
6. **Reinvite**: Sends a new invitation with the specified permission level

## Error Handling

The tool includes comprehensive error handling for:
- Missing GitHub CLI installation
- Authentication issues
- Invalid repository names or access
- Network errors
- Failed API operations

## License

MIT License - See LICENSE file for details
