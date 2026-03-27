#!/usr/bin/env python3
"""
Verification script for Project Context Switcher
Tests basic functionality without affecting user's real config.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import subprocess
import json
import yaml

def run_test(name: str, test_func):
    """Run a test and report results."""
    print(f"🧪 {name}...", end=" ", flush=True)
    try:
        test_func()
        print("✅ PASSED")
        return True
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_basic_cli():
    """Test that the CLI runs without errors."""
    script = Path(__file__).parent / "context_switcher.py"
    
    # Test help
    result = subprocess.run([sys.executable, str(script), "--help"], 
                          capture_output=True, text=True)
    assert result.returncode == 0, f"Help command failed: {result.stderr}"
    assert "usage:" in result.stdout.lower(), "Help output missing usage"

def test_list_command():
    """Test list command with empty config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        script = Path(__file__).parent / "context_switcher.py"
        
        # Create empty config
        config_file = tmpdir / "config.yaml"
        config_file.write_text("projects: {}\n")
        
        # Test list
        env = os.environ.copy()
        env["HOME"] = str(tmpdir)  # Override HOME for this test
        
        result = subprocess.run(
            [sys.executable, str(script), "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        
        assert result.returncode == 0, f"List failed: {result.stderr}"
        assert "no projects" in result.stdout.lower(), f"Expected 'no projects' message, got: {result.stdout}"

def test_config_creation():
    """Test that config file is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        script = Path(__file__).parent / "context_switcher.py"
        
        # Remove any existing config
        config_file = tmpdir / ".project_contexts.yaml"
        state_file = tmpdir / ".project_context_active.json"
        
        env = os.environ.copy()
        env["HOME"] = str(tmpdir)
        
        # Run list - should create empty config
        result = subprocess.run(
            [sys.executable, str(script), "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        
        assert result.returncode == 0, f"List failed: {result.stderr}"
        assert config_file.exists(), "Config file should have been created"

def test_sample_config():
    """Test with sample configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        script = Path(__file__).parent / "context_switcher.py"
        sample_config = Path(__file__).parent / "sample-config.yaml"
        
        # Copy sample config
        config_file = tmpdir / ".project_contexts.yaml"
        shutil.copy(sample_config, config_file)
        
        # Create dummy project directories
        projects = ["coach-db", "nightly-builds", "portfolio"]
        for project in projects:
            (tmpdir / f"clawd/{project}").mkdir(parents=True, exist_ok=True)
            (tmpdir / f"clawd/{project}/README.md").write_text("# Test\n")
        
        # Update config paths
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        for proj_name in config.get("projects", {}):
            config["projects"][proj_name]["root"] = str(tmpdir / f"clawd/{proj_name}")
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        env = os.environ.copy()
        env["HOME"] = str(tmpdir)
        
        # Test list
        result = subprocess.run(
            [sys.executable, str(script), "list"],
            env=env,
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        
        assert result.returncode == 0, f"List failed: {result.stderr}"
        assert "coach-db" in result.stdout, f"Expected 'coach-db' in output, got: {result.stdout}"
        assert "nightly-builds" in result.stdout, f"Expected 'nightly-builds' in output"

def test_activate_deactivate():
    """Test activate and deactivate cycle."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        script = Path(__file__).parent / "context_switcher.py"
        
        # Create simple config
        config_file = tmpdir / ".project_contexts.yaml"
        config = {
            "projects": {
                "test-project": {
                    "description": "Test project",
                    "root": str(tmpdir / "test-dir"),
                    "env": {"TEST_VAR": "test_value"},
                    "files": [],
                    "commands": []
                }
            }
        }
        
        # Create project directory
        project_dir = tmpdir / "test-dir"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        env = os.environ.copy()
        env["HOME"] = str(tmpdir)
        
        # Test activate
        result = subprocess.run(
            [sys.executable, str(script), "activate", "test-project"],
            env=env,
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        
        assert result.returncode == 0, f"Activate failed: {result.stderr}"
        assert "activating" in result.stdout.lower(), f"Expected activation message, got: {result.stdout}"
        
        # Check state file
        state_file = tmpdir / ".project_context_active.json"
        assert state_file.exists(), "State file should exist after activation"
        
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        assert state.get("active_project") == "test-project", f"State should have active_project='test-project', got: {state}"
        
        # Check env file
        env_file = tmpdir / ".project_context_env.sh"
        assert env_file.exists(), "Env file should exist after activation"
        
        env_content = env_file.read_text()
        assert "TEST_VAR" in env_content, "Env file should contain TEST_VAR"
        assert "test_value" in env_content, "Env file should contain test_value"
        
        # Test status
        result = subprocess.run(
            [sys.executable, str(script), "status"],
            env=env,
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        
        assert result.returncode == 0, f"Status failed: {result.stderr}"
        assert "test-project" in result.stdout, f"Status should show test-project, got: {result.stdout}"
        
        # Test deactivate
        result = subprocess.run(
            [sys.executable, str(script), "deactivate"],
            env=env,
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        
        assert result.returncode == 0, f"Deactivate failed: {result.stderr}"
        assert not state_file.exists(), "State file should be removed after deactivation"
        assert not env_file.exists(), "Env file should be removed after deactivation"

def test_run_command():
    """Test running commands in project context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        script = Path(__file__).parent / "context_switcher.py"
        
        # Create simple config
        config_file = tmpdir / ".project_contexts.yaml"
        config = {
            "projects": {
                "test-run": {
                    "description": "Test run project",
                    "root": str(tmpdir / "run-dir"),
                    "env": {"RUN_TEST": "yes"},
                    "files": [],
                    "commands": []
                }
            }
        }
        
        # Create project directory with a test file
        project_dir = tmpdir / "run-dir"
        project_dir.mkdir(parents=True, exist_ok=True)
        test_file = project_dir / "test.txt"
        test_file.write_text("hello world\n")
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        env = os.environ.copy()
        env["HOME"] = str(tmpdir)
        
        # Activate first
        result = subprocess.run(
            [sys.executable, str(script), "activate", "test-run"],
            env=env,
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        
        assert result.returncode == 0, f"Activate failed: {result.stderr}"
        
        # Test run command
        result = subprocess.run(
            [sys.executable, str(script), "run", "cat", "test.txt"],
            env=env,
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        
        assert result.returncode == 0, f"Run failed: {result.stderr}"
        assert "hello world" in result.stdout, f"Expected 'hello world' in output, got: {result.stdout}"
        
        # Cleanup
        subprocess.run([sys.executable, str(script), "deactivate"], env=env, cwd=tmpdir)

def main():
    """Run all tests."""
    print("🔍 Running Project Context Switcher verification tests")
    print("=" * 60)
    
    tests = [
        ("Basic CLI", test_basic_cli),
        ("List command", test_list_command),
        ("Config creation", test_config_creation),
        ("Sample config", test_sample_config),
        ("Activate/Deactivate", test_activate_deactivate),
        ("Run command", test_run_command),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        if run_test(name, test_func):
            passed += 1
    
    print("=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Project Context Switcher is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())