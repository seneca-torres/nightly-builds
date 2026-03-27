#!/usr/bin/env python3
"""
Project Context Switcher CLI
Helps Victor quickly switch between different project contexts.
"""

import os
import sys
import yaml
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import shlex

CONFIG_FILE = Path.home() / ".project_contexts.yaml"
STATE_FILE = Path.home() / ".project_context_active.json"

class ProjectContext:
    """Represents a project configuration."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.description = config.get("description", "")
        self.root = Path(config.get("root", ".")).expanduser()
        self.env = config.get("env", {})
        self.files = config.get("files", [])
        self.commands = config.get("commands", [])
        self.editor = config.get("editor", "code")  # Default to VS Code
        
    def validate(self) -> List[str]:
        """Validate the project configuration, return list of errors."""
        errors = []
        if not self.root.exists():
            errors.append(f"Root directory does not exist: {self.root}")
        return errors
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description} ({self.root})"

class ProjectManager:
    """Manages project configurations and state."""
    
    def __init__(self, config_file: Path = CONFIG_FILE):
        self.config_file = config_file
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.projects: Dict[str, ProjectContext] = {}
        self.load_config()
        
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_file.exists():
            # Create empty config if it doesn't exist
            self.save_config()
            return
            
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
                
            self.projects = {}
            for name, proj_config in config.get("projects", {}).items():
                self.projects[name] = ProjectContext(name, proj_config)
        except yaml.YAMLError as e:
            print(f"Error loading config file: {e}", file=sys.stderr)
            sys.exit(1)
            
    def save_config(self) -> None:
        """Save configuration to YAML file."""
        config = {"projects": {}}
        for name, project in self.projects.items():
            config["projects"][name] = {
                "description": project.description,
                "root": str(project.root),
                "env": project.env,
                "files": project.files,
                "commands": project.commands,
                "editor": project.editor
            }
            
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config: {e}", file=sys.stderr)
            
    def get_active_project(self) -> Optional[str]:
        """Get the name of the currently active project."""
        if not STATE_FILE.exists():
            return None
            
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
            return state.get("active_project")
        except (json.JSONDecodeError, IOError):
            return None
            
    def set_active_project(self, name: Optional[str]) -> None:
        """Set the active project (or clear it)."""
        if name is None:
            if STATE_FILE.exists():
                STATE_FILE.unlink()
            return
            
        state = {"active_project": name}
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
            
    def activate_project(self, name: str) -> bool:
        """Activate a project."""
        if name not in self.projects:
            print(f"Project '{name}' not found", file=sys.stderr)
            return False
            
        project = self.projects[name]
        
        # Validate project
        errors = project.validate()
        if errors:
            print(f"Cannot activate project '{name}':", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return False
            
        print(f"Activating project: {project}")
        
        # Change to project directory
        try:
            os.chdir(project.root)
            print(f"Changed to: {project.root}")
        except OSError as e:
            print(f"Failed to change directory: {e}", file=sys.stderr)
            return False
            
        # Set environment variables
        env_file = Path.home() / ".project_context_env.sh"
        with open(env_file, 'w') as f:
            f.write("# Project context environment variables\n")
            f.write("# Source this file to set environment variables\n")
            for key, value in project.env.items():
                f.write(f'export {key}="{value}"\n')
            f.write(f'export PROJECT_CONTEXT="{name}"\n')
            f.write(f'cd "{project.root}"\n')
        print(f"Environment variables saved to: {env_file}")
        print(f"To set env vars, run: source {env_file}")
        
        # Run initialization commands
        if project.commands:
            print("Running initialization commands:")
            for cmd in project.commands:
                print(f"  $ {cmd}")
                try:
                    result = subprocess.run(cmd, shell=True, cwd=project.root)
                    if result.returncode != 0:
                        print(f"  ⚠️ Command failed with exit code {result.returncode}")
                except Exception as e:
                    print(f"  ⚠️ Failed to run command: {e}")
                    
        # Open files
        if project.files:
            print("Opening files:")
            for file_pattern in project.files:
                file_path = project.root / file_pattern
                if file_path.exists():
                    print(f"  📄 {file_path}")
                    try:
                        subprocess.run([project.editor, str(file_path)], cwd=project.root)
                    except Exception as e:
                        print(f"  ⚠️ Failed to open file: {e}")
                else:
                    print(f"  ⚠️ File not found: {file_path}")
                    
        # Set as active
        self.set_active_project(name)
        print(f"\n✅ Project '{name}' activated!")
        print(f"Current directory: {project.root}")
        
        return True
        
    def deactivate_project(self) -> None:
        """Deactivate the current project."""
        active = self.get_active_project()
        if active:
            print(f"Deactivating project: {active}")
            self.set_active_project(None)
            
            # Remove env file
            env_file = Path.home() / ".project_context_env.sh"
            if env_file.exists():
                env_file.unlink()
                
            print("✅ Project deactivated")
        else:
            print("No active project to deactivate")
            
    def run_in_context(self, command: List[str]) -> None:
        """Run a command in the active project context."""
        active = self.get_active_project()
        if not active:
            print("No active project. Use 'activate' first.", file=sys.stderr)
            sys.exit(1)
            
        project = self.projects.get(active)
        if not project:
            print(f"Active project '{active}' not found in config", file=sys.stderr)
            sys.exit(1)
            
        # Change to project directory
        try:
            os.chdir(project.root)
        except OSError as e:
            print(f"Failed to change directory: {e}", file=sys.stderr)
            sys.exit(1)
            
        # Set environment variables
        env = os.environ.copy()
        env.update(project.env)
        env["PROJECT_CONTEXT"] = active
        
        # Run command
        try:
            cmd_str = " ".join(shlex.quote(arg) for arg in command)
            print(f"Running in '{active}' context: {cmd_str}")
            result = subprocess.run(command, env=env, cwd=project.root)
            sys.exit(result.returncode)
        except FileNotFoundError:
            print(f"Command not found: {command[0]}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error running command: {e}", file=sys.stderr)
            sys.exit(1)

def list_projects(manager: ProjectManager) -> None:
    """List all available projects."""
    active = manager.get_active_project()
    
    if not manager.projects:
        print("No projects configured.")
        print(f"Add projects to: {CONFIG_FILE}")
        return
        
    print("Available projects:")
    for name, project in manager.projects.items():
        status = " (active)" if name == active else ""
        print(f"  {name:20} {project.description}{status}")
        
def show_status(manager: ProjectManager) -> None:
    """Show current status."""
    active = manager.get_active_project()
    
    if active:
        project = manager.projects.get(active)
        if project:
            print(f"Active project: {active}")
            print(f"Description: {project.description}")
            print(f"Directory: {project.root}")
            print(f"Environment variables: {len(project.env)}")
            print(f"Files: {len(project.files)}")
            print(f"Commands: {len(project.commands)}")
        else:
            print(f"Active project '{active}' not found in config")
    else:
        print("No active project")
        
def add_project_interactive(manager: ProjectManager) -> None:
    """Interactively add a new project."""
    print("Add a new project")
    print("(Leave blank to use defaults)")
    
    name = input("Project name: ").strip()
    if not name:
        print("Project name is required")
        return
        
    if name in manager.projects:
        print(f"Project '{name}' already exists")
        return
        
    description = input("Description: ").strip()
    root = input(f"Root directory [{os.getcwd()}]: ").strip()
    if not root:
        root = os.getcwd()
        
    # Simple env vars input
    print("\nEnter environment variables (key=value, one per line, empty line to finish):")
    env = {}
    while True:
        line = input("env> ").strip()
        if not line:
            break
        if "=" in line:
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
            
    # Files to open
    print("\nEnter files to open (one per line, empty line to finish):")
    files = []
    while True:
        line = input("file> ").strip()
        if not line:
            break
        files.append(line)
        
    # Commands to run
    print("\nEnter commands to run on activation (one per line, empty line to finish):")
    commands = []
    while True:
        line = input("cmd> ").strip()
        if not line:
            break
        commands.append(line)
        
    # Create project
    project_config = {
        "description": description,
        "root": root,
        "env": env,
        "files": files,
        "commands": commands
    }
    
    manager.projects[name] = ProjectContext(name, project_config)
    manager.save_config()
    print(f"\n✅ Project '{name}' added!")
    
def main():
    parser = argparse.ArgumentParser(description="Project Context Switcher")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # List command
    subparsers.add_parser("list", help="List all available projects")
    
    # Activate command
    activate_parser = subparsers.add_parser("activate", help="Activate a project")
    activate_parser.add_argument("name", help="Project name to activate")
    
    # Deactivate command
    subparsers.add_parser("deactivate", help="Deactivate current project")
    
    # Status command
    subparsers.add_parser("status", help="Show current status")
    
    # Add command
    subparsers.add_parser("add", help="Add a new project interactively")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a command in active project context")
    run_parser.add_argument("command_args", nargs=argparse.REMAINDER, help="Command to run")
    
    # Open command
    open_parser = subparsers.add_parser("open", help="Open project files")
    open_parser.add_argument("name", nargs="?", help="Project name (default: active project)")
    
    args = parser.parse_args()
    
    manager = ProjectManager()
    
    if args.command == "list":
        list_projects(manager)
    elif args.command == "activate":
        manager.activate_project(args.name)
    elif args.command == "deactivate":
        manager.deactivate_project()
    elif args.command == "status":
        show_status(manager)
    elif args.command == "add":
        add_project_interactive(manager)
    elif args.command == "run":
        if not args.command_args:
            print("Error: No command specified", file=sys.stderr)
            sys.exit(1)
        manager.run_in_context(args.command_args)
    elif args.command == "open":
        name = args.name or manager.get_active_project()
        if not name:
            print("No project specified and no active project", file=sys.stderr)
            sys.exit(1)
            
        if name not in manager.projects:
            print(f"Project '{name}' not found", file=sys.stderr)
            sys.exit(1)
            
        project = manager.projects[name]
        if project.files:
            for file_pattern in project.files:
                file_path = project.root / file_pattern
                if file_path.exists():
                    print(f"Opening: {file_path}")
                    try:
                        subprocess.run([project.editor, str(file_path)], cwd=project.root)
                    except Exception as e:
                        print(f"Failed to open file: {e}")
                else:
                    print(f"File not found: {file_path}")
        else:
            print(f"No files configured for project '{name}'")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()