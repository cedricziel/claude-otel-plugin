#!/usr/bin/env python3
"""
Validation script for Claude Code marketplace plugin structure.
Checks that all required files and metadata are present.
"""

import json
import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and report the result."""
    if os.path.exists(file_path):
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description} missing: {file_path}")
        return False

def validate_plugin_json(plugin_json_path):
    """Validate the plugin.json file has all required fields."""
    print("\n=== Validating plugin.json ===")
    
    if not os.path.exists(plugin_json_path):
        print(f"✗ plugin.json not found at {plugin_json_path}")
        return False
    
    try:
        with open(plugin_json_path, 'r') as f:
            plugin_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"✗ plugin.json is not valid JSON: {e}")
        return False
    
    # Check required top-level fields
    required_fields = ['name', 'version', 'description', 'author']
    all_valid = True
    
    for field in required_fields:
        if field in plugin_data:
            print(f"✓ Required field '{field}': present")
        else:
            print(f"✗ Required field '{field}': missing")
            all_valid = False
    
    # Check marketplace section
    if 'marketplace' in plugin_data:
        print("✓ Marketplace section: present")
        marketplace = plugin_data['marketplace']
        
        marketplace_fields = ['displayName', 'shortDescription', 'category', 'tags']
        for field in marketplace_fields:
            if field in marketplace:
                print(f"  ✓ Marketplace field '{field}': present")
            else:
                print(f"  ✗ Marketplace field '{field}': missing")
                all_valid = False
    else:
        print("✗ Marketplace section: missing")
        all_valid = False
    
    # Check optional but recommended fields
    optional_fields = ['license', 'repository', 'homepage']
    for field in optional_fields:
        if field in plugin_data:
            print(f"✓ Recommended field '{field}': present")
        else:
            print(f"⚠ Recommended field '{field}': missing (optional but recommended)")
    
    # Check skills
    if 'skills' in plugin_data and len(plugin_data['skills']) > 0:
        print(f"✓ Skills: {len(plugin_data['skills'])} skill(s) defined")
    else:
        print("⚠ Skills: no skills defined")
    
    return all_valid

def validate_skills(base_path):
    """Validate that all skill directories have required files."""
    print("\n=== Validating Skills ===")
    
    skills_path = os.path.join(base_path, '.claude', 'skills')
    if not os.path.exists(skills_path):
        print(f"✗ Skills directory not found: {skills_path}")
        return False
    
    skill_dirs = [d for d in os.listdir(skills_path) if os.path.isdir(os.path.join(skills_path, d))]
    
    if not skill_dirs:
        print("⚠ No skill directories found")
        return True
    
    all_valid = True
    for skill_dir in skill_dirs:
        skill_path = os.path.join(skills_path, skill_dir)
        print(f"\nValidating skill: {skill_dir}")
        
        # Check for SKILL.md
        skill_md = os.path.join(skill_path, 'SKILL.md')
        if os.path.exists(skill_md):
            print(f"  ✓ SKILL.md found")
        else:
            print(f"  ✗ SKILL.md missing")
            all_valid = False
    
    return all_valid

def main():
    """Main validation function."""
    print("=" * 60)
    print("Claude Code Marketplace Plugin Validation")
    print("=" * 60)
    
    # Get the repository root
    repo_root = Path(__file__).parent.absolute()
    
    all_checks_passed = True
    
    # Check for LICENSE file
    license_file = os.path.join(repo_root, 'LICENSE')
    if not check_file_exists(license_file, "LICENSE file"):
        all_checks_passed = False
    
    # Check for README.md
    readme_file = os.path.join(repo_root, 'README.md')
    if not check_file_exists(readme_file, "README.md"):
        all_checks_passed = False
    
    # Check for .claude/plugin.json
    plugin_json = os.path.join(repo_root, '.claude', 'plugin.json')
    if not check_file_exists(plugin_json, ".claude/plugin.json"):
        all_checks_passed = False
    
    # Validate plugin.json content
    if os.path.exists(plugin_json):
        if not validate_plugin_json(plugin_json):
            all_checks_passed = False
    
    # Validate skills
    if not validate_skills(repo_root):
        all_checks_passed = False
    
    # Final result
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✓ All validation checks passed!")
        print("=" * 60)
        print("\nYour plugin is ready for the Claude Code marketplace!")
        return 0
    else:
        print("✗ Some validation checks failed")
        print("=" * 60)
        print("\nPlease fix the issues above before submitting to the marketplace.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
