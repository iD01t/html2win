#!/usr/bin/env python3
"""
Simple test for HTML2EXE Pro Premium - Test core functionality
"""

import sys
import os

def test_auto_options():
    """Test the AutoOptionsSelector functionality"""
    try:
        # Import the module
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from html2exe_pro_premium import AutoOptionsSelector
        
        print("Testing AutoOptionsSelector...")
        
        # Test folder analysis
        analysis = AutoOptionsSelector.analyze_source("/workspace/test_app", "folder")
        print(f"Folder analysis: {analysis}")
        
        # Test URL analysis
        analysis_url = AutoOptionsSelector.analyze_source("https://example.com", "url")
        print(f"URL analysis: {analysis_url}")
        
        print("✅ AutoOptionsSelector test passed!")
        return True
        
    except Exception as e:
        print(f"❌ AutoOptionsSelector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_imports():
    """Test basic imports work"""
    try:
        print("Testing basic imports...")
        
        # Test basic Python imports
        import json
        import tempfile
        import datetime
        import hashlib
        import base64
        import webbrowser
        import zipfile
        import urllib.parse
        from pathlib import Path
        from typing import Optional, List, Dict, Any, Union, Callable
        from datetime import datetime, timedelta
        from dataclasses import dataclass
        
        print("✅ Basic imports test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Basic imports test failed: {e}")
        return False

if __name__ == "__main__":
    print("HTML2EXE Pro Premium - Simple Test Suite")
    print("=" * 50)
    
    success = True
    
    # Run tests
    success &= test_basic_imports()
    success &= test_auto_options()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)