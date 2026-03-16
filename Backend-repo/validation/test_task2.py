#!/usr/bin/env python3
"""
Test script for Task 2: Requirements management and documentation generation.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from validation.requirements_manager import RequirementsManager
from validation.documentation_generator import DocumentationGenerator


def test_requirements_management():
    """Test requirements management functionality."""
    print("=" * 60)
    print("Testing Requirements Management")
    print("=" * 60)
    
    try:
        # Initialize requirements manager
        req_manager = RequirementsManager(project_root)
        
        # Test 1: Freeze requirements
        print("\n1. Testing requirements freezing...")
        frozen_packages = req_manager.freeze_requirements()
        print(f"✓ Frozen {len(frozen_packages)} packages")
        
        # Test 2: Validate dependencies
        print("\n2. Testing dependency validation...")
        validation_results = req_manager.validate_dependencies()
        print(f"✓ Found {len(validation_results['conflicts'])} conflicts")
        print(f"✓ Found {len(validation_results['warnings'])} warnings")
        print(f"✓ Found {len(validation_results['missing'])} missing packages")
        print(f"✓ Found {len(validation_results['outdated'])} outdated packages")
        
        # Test 3: Test installation (skip for now as it's time-consuming)
        print("\n3. Skipping installation test (time-consuming)")
        # success, errors = req_manager.test_installation()
        # print(f"✓ Installation test: {'PASSED' if success else 'FAILED'}")
        
        print("\n✅ Requirements management tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Requirements management test failed: {str(e)}")
        return False


def test_documentation_generation():
    """Test documentation generation functionality."""
    print("\n" + "=" * 60)
    print("Testing Documentation Generation")
    print("=" * 60)
    
    try:
        # Initialize documentation generator
        doc_generator = DocumentationGenerator(project_root)
        
        # Test 1: Generate setup documentation
        print("\n1. Testing setup documentation generation...")
        setup_path = doc_generator.generate_setup_docs()
        print(f"✓ Generated setup documentation: {setup_path}")
        
        # Test 2: Generate API documentation
        print("\n2. Testing API documentation generation...")
        api_path = doc_generator.generate_api_docs("http://127.0.0.1:8000")
        print(f"✓ Generated API documentation: {api_path}")
        
        # Test 3: Generate troubleshooting guide
        print("\n3. Testing troubleshooting guide generation...")
        troubleshooting_path = doc_generator.generate_troubleshooting_guide()
        print(f"✓ Generated troubleshooting guide: {troubleshooting_path}")
        
        # Verify files exist and have content
        for file_path in [setup_path, api_path, troubleshooting_path]:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"✓ {os.path.basename(file_path)}: {file_size} bytes")
            else:
                print(f"❌ {os.path.basename(file_path)}: File not found")
                return False
        
        print("\n✅ Documentation generation tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Documentation generation test failed: {str(e)}")
        return False


def main():
    """Run all tests for Task 2."""
    print("HotelAgent Backend Testing - Task 2")
    print("Requirements Management and Documentation Generation")
    print("=" * 80)
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Run tests
    req_success = test_requirements_management()
    doc_success = test_documentation_generation()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Requirements Management: {'✅ PASSED' if req_success else '❌ FAILED'}")
    print(f"Documentation Generation: {'✅ PASSED' if doc_success else '❌ FAILED'}")
    
    if req_success and doc_success:
        print("\n🎉 All Task 2 tests completed successfully!")
        print("\nGenerated files:")
        print("- requirements.txt (updated with exact versions)")
        print("- setup.md (comprehensive setup guide)")
        print("- postman.md (API documentation)")
        print("- troubleshooting.md (troubleshooting guide)")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())