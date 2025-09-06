#!/usr/bin/env python3
"""
Demo script showing the automatic options selection functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_auto_build():
    """Demonstrate the automatic build functionality"""
    try:
        from html2exe_pro_premium import AutoOptionsSelector, AppConfig, BuildEngine
        
        print("🚀 HTML2EXE Pro Premium - Auto Build Demo")
        print("=" * 50)
        
        # Create configuration
        config = AppConfig()
        config.metadata.name = "DemoApp"
        config.build.source_path = "/workspace/test_app"
        config.build.source_type = "folder"
        config.build.output_dir = "demo_dist"
        
        print(f"📁 Source: {config.build.source_path}")
        print(f"📦 App Name: {config.metadata.name}")
        print(f"📂 Output: {config.build.output_dir}")
        
        # Analyze source and get recommendations
        print("\n🔍 Analyzing source...")
        analysis = AutoOptionsSelector.analyze_source(
            config.build.source_path, 
            config.build.source_type
        )
        
        print(f"📊 Analysis Results:")
        print(f"  • Single File: {'Yes' if analysis['onefile'] else 'No'}")
        print(f"  • Console Window: {'Yes' if analysis['console'] else 'No'}")
        print(f"  • Debug Mode: {'Yes' if analysis['debug'] else 'No'}")
        print(f"  • UPX Compression: {'Yes' if analysis['upx_compress'] else 'No'}")
        print(f"  • Strip Debug: {'Yes' if analysis['strip_debug'] else 'No'}")
        print(f"  • Offline Mode: {'Yes' if analysis.get('offline_mode', False) else 'No'}")
        print(f"  • Optimization: {analysis['optimization_level']}")
        
        # Apply automatic recommendations
        config.build.onefile = analysis["onefile"]
        config.build.console = analysis["console"]
        config.build.debug = analysis["debug"]
        config.build.upx_compress = analysis["upx_compress"]
        config.build.strip_debug = analysis["strip_debug"]
        config.build.offline_mode = analysis.get("offline_mode", False)
        
        # Get optimal PyInstaller options
        print("\n⚙️ Generating optimal PyInstaller options...")
        options = AutoOptionsSelector.get_optimal_pyinstaller_options(config)
        
        print(f"🔧 PyInstaller Command Options:")
        for i, option in enumerate(options, 1):
            print(f"  {i:2d}. {option}")
        
        # Simulate build process (without actually building)
        print(f"\n🏗️ Build Process Simulation:")
        print(f"  1. ✅ Source analysis completed")
        print(f"  2. ✅ Optimal settings selected")
        print(f"  3. ✅ PyInstaller options generated")
        print(f"  4. ⏳ Ready to build executable")
        
        print(f"\n📋 Build Summary:")
        print(f"  • Source Type: {config.build.source_type}")
        print(f"  • Build Mode: {'Single File' if config.build.onefile else 'Directory'}")
        print(f"  • Window Mode: {'Console' if config.build.console else 'Windowed'}")
        print(f"  • Optimization: {analysis['optimization_level']}")
        print(f"  • Estimated Size: 15-25 MB (single file) or 5-10 MB (directory)")
        
        print(f"\n🎉 Auto Build Configuration Complete!")
        print(f"   The system has automatically selected the optimal settings")
        print(f"   for building your HTML application into a desktop executable.")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_url_analysis():
    """Demonstrate URL analysis"""
    try:
        from html2exe_pro_premium import AutoOptionsSelector
        
        print("\n🌐 URL Analysis Demo")
        print("-" * 30)
        
        # Test URL analysis
        url_analysis = AutoOptionsSelector.analyze_source("https://example.com", "url")
        
        print(f"URL Analysis Results:")
        print(f"  • Single File: {'Yes' if url_analysis['onefile'] else 'No'}")
        print(f"  • Offline Mode: {'Yes' if url_analysis.get('offline_mode', False) else 'No'}")
        print(f"  • Optimization: {url_analysis['optimization_level']}")
        
        print(f"\n💡 URL-based apps are automatically configured for:")
        print(f"   • Single file distribution (portability)")
        print(f"   • Offline mode (caching external resources)")
        print(f"   • Portable optimization (smaller size)")
        
        return True
        
    except Exception as e:
        print(f"❌ URL demo failed: {e}")
        return False

if __name__ == "__main__":
    print("HTML2EXE Pro Premium - Automatic Options Selection Demo")
    print("=" * 60)
    
    success = True
    
    # Run demos
    success &= demo_auto_build()
    success &= demo_url_analysis()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All demos completed successfully!")
        print("\n✨ Key Features Demonstrated:")
        print("  • Automatic source analysis")
        print("  • Optimal settings selection")
        print("  • PyInstaller command generation")
        print("  • URL vs folder mode handling")
        print("  • Build optimization recommendations")
    else:
        print("❌ Some demos failed!")
        sys.exit(1)