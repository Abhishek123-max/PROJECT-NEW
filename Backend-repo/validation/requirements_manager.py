"""
Requirements management module for HotelAgent backend validation system.
Handles requirements freezing, dependency validation, and backup management.
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pkg_resources
import importlib.metadata
from packaging import version
from packaging.requirements import Requirement


class RequirementsManager:
    """Manages Python package requirements and dependencies."""
    
    def __init__(self, project_root: str = None):
        """
        Initialize requirements manager.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.requirements_file = self.project_root / "requirements.txt"
        self.backup_dir = self.project_root / "requirements_backups"
        
    def freeze_requirements(self) -> Dict[str, str]:
        """
        Generate requirements.txt with exact package versions.
        
        Returns:
            Dict mapping package names to their exact versions
            
        Raises:
            Exception: If requirements freezing fails
        """
        try:
            # Create backup directory if it doesn't exist
            self.backup_dir.mkdir(exist_ok=True)
            
            # Backup existing requirements file if it exists
            if self.requirements_file.exists():
                self._backup_current_requirements()
            
            # Get currently installed packages
            installed_packages = self._get_installed_packages()
            
            # Filter out development packages and system packages
            filtered_packages = self._filter_packages(installed_packages)
            
            # Generate new requirements content
            requirements_content = self._generate_requirements_content(filtered_packages)
            
            # Write new requirements file
            with open(self.requirements_file, 'w', encoding='utf-8') as f:
                f.write(requirements_content)
            
            return filtered_packages
            
        except Exception as e:
            raise Exception(f"Failed to freeze requirements: {str(e)}")
    
    def validate_dependencies(self) -> Dict[str, List[str]]:
        """
        Validate dependency compatibility and detect conflicts.
        
        Returns:
            Dict with validation results including conflicts and warnings
        """
        try:
            validation_results = {
                "conflicts": [],
                "warnings": [],
                "missing": [],
                "outdated": []
            }
            
            if not self.requirements_file.exists():
                validation_results["warnings"].append("No requirements.txt file found")
                return validation_results
            
            # Parse requirements file
            requirements = self._parse_requirements_file()
            
            # Check for conflicts
            conflicts = self._check_dependency_conflicts(requirements)
            validation_results["conflicts"].extend(conflicts)
            
            # Check for missing packages
            missing = self._check_missing_packages(requirements)
            validation_results["missing"].extend(missing)
            
            # Check for outdated packages
            outdated = self._check_outdated_packages(requirements)
            validation_results["outdated"].extend(outdated)
            
            return validation_results
            
        except Exception as e:
            return {
                "conflicts": [],
                "warnings": [f"Dependency validation failed: {str(e)}"],
                "missing": [],
                "outdated": []
            }
    
    def test_installation(self) -> Tuple[bool, List[str]]:
        """
        Test if frozen requirements can be installed successfully.
        
        Returns:
            Tuple of (success, error_messages)
        """
        try:
            if not self.requirements_file.exists():
                return False, ["Requirements file not found"]
            
            # Create a temporary virtual environment for testing
            test_env_path = self.project_root / "temp_test_env"
            
            try:
                # Create virtual environment
                subprocess.run([
                    sys.executable, "-m", "venv", str(test_env_path)
                ], check=True, capture_output=True, text=True)
                
                # Get pip path in virtual environment
                if os.name == 'nt':  # Windows
                    pip_path = test_env_path / "Scripts" / "pip.exe"
                else:  # Unix/Linux/macOS
                    pip_path = test_env_path / "bin" / "pip"
                
                # Test installation
                result = subprocess.run([
                    str(pip_path), "install", "-r", str(self.requirements_file)
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    return True, []
                else:
                    return False, [result.stderr]
                    
            finally:
                # Clean up test environment
                if test_env_path.exists():
                    shutil.rmtree(test_env_path, ignore_errors=True)
                    
        except subprocess.TimeoutExpired:
            return False, ["Installation test timed out"]
        except Exception as e:
            return False, [f"Installation test failed: {str(e)}"]
    
    def _backup_current_requirements(self) -> str:
        """
        Create backup of current requirements file.
        
        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"requirements_backup_{timestamp}.txt"
        backup_path = self.backup_dir / backup_filename
        
        shutil.copy2(self.requirements_file, backup_path)
        return str(backup_path)
    
    def _get_installed_packages(self) -> Dict[str, str]:
        """
        Get all currently installed packages with their versions.
        
        Returns:
            Dict mapping package names to versions
        """
        packages = {}
        
        try:
            # Use importlib.metadata (Python 3.8+)
            for dist in importlib.metadata.distributions():
                packages[dist.metadata['name']] = dist.version
        except ImportError:
            # Fallback to pkg_resources for older Python versions
            for dist in pkg_resources.working_set:
                packages[dist.project_name] = dist.version
        
        return packages
    
    def _filter_packages(self, packages: Dict[str, str]) -> Dict[str, str]:
        """
        Filter out development and system packages.
        
        Args:
            packages: Dict of all installed packages
            
        Returns:
            Dict of filtered packages
        """
        # Packages to exclude (development tools, system packages, etc.)
        exclude_packages = {
            'pip', 'setuptools', 'wheel', 'pkg-resources',
            'pytest', 'pytest-cov', 'pytest-asyncio',
            'black', 'flake8', 'mypy', 'isort',
            'pre-commit', 'bandit'
        }
        
        # Keep only production packages
        filtered = {}
        for name, version_str in packages.items():
            if name.lower() not in exclude_packages:
                filtered[name] = version_str
        
        return filtered
    
    def _generate_requirements_content(self, packages: Dict[str, str]) -> str:
        """
        Generate requirements.txt content from packages dict.
        
        Args:
            packages: Dict mapping package names to versions
            
        Returns:
            Requirements file content as string
        """
        lines = []
        
        # Add header comment
        lines.append("# Requirements generated automatically")
        lines.append(f"# Generated on: {datetime.now().isoformat()}")
        lines.append("")
        
        # Group packages by category
        web_packages = []
        db_packages = []
        auth_packages = []
        util_packages = []
        other_packages = []
        
        for name, version_str in sorted(packages.items()):
            package_line = f"{name}=={version_str}"
            
            # Categorize packages
            name_lower = name.lower()
            if any(web in name_lower for web in ['fastapi', 'uvicorn', 'starlette', 'httpx']):
                web_packages.append(package_line)
            elif any(db in name_lower for db in ['sqlalchemy', 'asyncpg', 'psycopg2', 'alembic']):
                db_packages.append(package_line)
            elif any(auth in name_lower for auth in ['bcrypt', 'jwt', 'jose', 'passlib']):
                auth_packages.append(package_line)
            elif any(util in name_lower for util in ['redis', 'pydantic', 'python-dotenv', 'dateutil']):
                util_packages.append(package_line)
            else:
                other_packages.append(package_line)
        
        # Add categorized packages
        if web_packages:
            lines.append("# FastAPI and ASGI server")
            lines.extend(web_packages)
            lines.append("")
        
        if db_packages:
            lines.append("# Database")
            lines.extend(db_packages)
            lines.append("")
        
        if auth_packages:
            lines.append("# Authentication and Security")
            lines.extend(auth_packages)
            lines.append("")
        
        if util_packages:
            lines.append("# Utilities and Configuration")
            lines.extend(util_packages)
            lines.append("")
        
        if other_packages:
            lines.append("# Other Dependencies")
            lines.extend(other_packages)
            lines.append("")
        
        return "\n".join(lines)
    
    def _parse_requirements_file(self) -> List[Requirement]:
        """
        Parse requirements.txt file into Requirement objects.
        
        Returns:
            List of Requirement objects
        """
        requirements = []
        
        with open(self.requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        req = Requirement(line)
                        requirements.append(req)
                    except Exception:
                        # Skip invalid requirement lines
                        continue
        
        return requirements
    
    def _check_dependency_conflicts(self, requirements: List[Requirement]) -> List[str]:
        """
        Check for dependency conflicts.
        
        Args:
            requirements: List of requirements to check
            
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        
        # This is a simplified conflict detection
        # In a real implementation, you'd use a proper dependency resolver
        package_versions = {}
        
        for req in requirements:
            if req.name in package_versions:
                existing_version = package_versions[req.name]
                if str(req.specifier) != existing_version:
                    conflicts.append(
                        f"Version conflict for {req.name}: "
                        f"{existing_version} vs {req.specifier}"
                    )
            else:
                package_versions[req.name] = str(req.specifier)
        
        return conflicts
    
    def _check_missing_packages(self, requirements: List[Requirement]) -> List[str]:
        """
        Check for packages that are required but not installed.
        
        Args:
            requirements: List of requirements to check
            
        Returns:
            List of missing package names
        """
        missing = []
        installed_packages = self._get_installed_packages()
        
        for req in requirements:
            if req.name not in installed_packages:
                missing.append(req.name)
        
        return missing
    
    def _check_outdated_packages(self, requirements: List[Requirement]) -> List[str]:
        """
        Check for packages that have newer versions available.
        
        Args:
            requirements: List of requirements to check
            
        Returns:
            List of outdated package descriptions
        """
        outdated = []
        installed_packages = self._get_installed_packages()
        
        for req in requirements:
            if req.name in installed_packages:
                installed_version = installed_packages[req.name]
                
                # Simple check - in a real implementation, you'd check PyPI
                # For now, just check if the installed version matches requirements
                if req.specifier and not req.specifier.contains(installed_version):
                    outdated.append(
                        f"{req.name}: installed {installed_version}, "
                        f"required {req.specifier}"
                    )
        
        return outdated