#!/usr/bin/env python3
"""
Simple test script for HTML2EXE Pro Premium
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_auto_build():
    """Test the auto build functionality"""
    try:
        from html2exe_pro_premium import AutoOptionsSelector, AppConfig
        
        print("Testing AutoOptionsSelector...")
        
        # Test folder analysis
        config = AppConfig()
        config.build.source_path = "/workspace/test_app"
        config.build.source_type = "folder"
        config.metadata.name = "TestApp"
        config.build.output_dir = "test_dist"
        
        analysis = AutoOptionsSelector.analyze_source(
            config.build.source_path, 
            config.build.source_type
        )
        
        print(f"Analysis results: {analysis}")
        
        # Test PyInstaller options generation
        options = AutoOptionsSelector.get_optimal_pyinstaller_options(config)
        print(f"PyInstaller options: {options}")
        
        print("✅ AutoOptionsSelector test passed!")
        return True
        
    except Exception as e:
        print(f"❌ AutoOptionsSelector test failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without dependencies"""
    try:
        from html2exe_pro_premium import AppConfig, IconGenerator
        
        print("Testing basic functionality...")
        
        # Test config creation
        config = AppConfig()
        config.metadata.name = "TestApp"
        config.build.source_path = "/workspace/test_app"
        config.build.source_type = "folder"
        
        print(f"Config created: {config.metadata.name}")
        
        # Test icon generation (if PIL available)
        try:
            icon_path = "/tmp/test_icon.ico"
            IconGenerator.generate_icon("TA", icon_path)
            if os.path.exists(icon_path):
                print("✅ Icon generation test passed!")
                os.remove(icon_path)
            else:
                print("⚠️ Icon generation test failed - no PIL")
        except Exception as e:
            print(f"⚠️ Icon generation test failed: {e}")
        
        print("✅ Basic functionality test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("HTML2EXE Pro Premium - Test Suite")
    print("=" * 40)
    
    success = True
    
    # Run tests
    success &= test_basic_functionality()
    success &= test_auto_build()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)