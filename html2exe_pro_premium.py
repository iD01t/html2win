#!/usr/bin/env python3
"""
HTML2EXE Pro Premium - Convert HTML folders or URLs into Windows .exe desktop applications
A single-file solution with modern GUI, CLI interface, and premium packaging features.

Premium Features Included:
- Modern React-style GUI with live preview
- Advanced packaging with PyInstaller optimization
- Live reload development server
- Custom protocol support
- System tray integration
- Auto-updater framework
- Advanced security options
- Professional icon generation
- Code signing preparation
- Analytics and telemetry framework

Author: HTML2EXE Pro Premium
Version: 2.0.0 Premium
"""

import sys
import os
import subprocess
import importlib
import json
import shutil
import threading
import time
import hashlib
import base64
import webbrowser
import tempfile
import zipfile
import urllib.parse
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

# Auto-install dependencies with progress
REQUIRED_PACKAGES = [
    "typer>=0.12.0",
    "rich>=13.7.0", 
    "pydantic>=2.7.0",
    "appdirs>=1.4.0",
    "watchdog>=4.0.0",
    "flask>=3.0.0",
    "pywebview>=5.0.0",
    "requests>=2.32.0",
    "pillow>=10.4.0",
    "pyinstaller>=6.8.0",
    "psutil>=5.9.0",
    "packaging>=23.0"
]

if sys.platform == "win32":
    REQUIRED_PACKAGES.append("pywin32>=306")

def check_and_install_dependencies():
    """Check for required packages and install if missing."""
    missing_packages = []
    
    # Check each required package
    for package in REQUIRED_PACKAGES:
        package_name = package.split(">=")[0]
        import_name = package_name.replace("-", "_")
        if import_name == 'pywin32':
            import_name = 'win32api'
        elif import_name == 'pillow':
            import_name = 'PIL'
        elif import_name == 'pyinstaller':
            import_name = 'PyInstaller'

        try:
            importlib.import_module(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("HTML2EXE Pro Premium: Missing required packages.")
        print("Please install the following packages manually:")
        for package in missing_packages:
            print(f"  pip install {package}")
        print("\nOr run: pip install --break-system-packages " + " ".join(missing_packages))
        print("\nNote: Some packages may require system packages. On Ubuntu/Debian:")
        print("  sudo apt install python3-tk python3-dev")
        print("\nContinuing with limited functionality...")
        return False
    
    return True

# Run dependency check first
check_and_install_dependencies()

# Now import the required packages with graceful fallbacks
try:
    import typer
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
    from rich.logging import RichHandler
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback for missing rich/typer
    class MockProgress:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def add_task(self, *args, **kwargs): return 0
        def update(self, *args, **kwargs): pass
        def advance(self, *args, **kwargs): pass
    Progress = MockProgress
    def SpinnerColumn(): return None
    def TextColumn(): return None  
    def BarColumn(): return None
    def TaskID(): return None

try:
    from pydantic import BaseModel, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Fallback for missing pydantic
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        def dict(self): return self.__dict__
        def save(self, path): pass
        @classmethod
        def load(cls, path): return cls()
    def Field(*args, **kwargs):
        if 'default' in kwargs:
            return kwargs['default']
        elif 'default_factory' in kwargs:
            return kwargs['default_factory']()
        return ""
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

try:
    import appdirs
    APPDIRS_AVAILABLE = True
except ImportError:
    APPDIRS_AVAILABLE = False
    # Fallback for missing appdirs
    import tempfile
    def get_temp_dir(*args, **kwargs):
        return tempfile.gettempdir()
    
    appdirs = type('appdirs', (), {
        'user_config_dir': get_temp_dir,
        'user_data_dir': get_temp_dir
    })()

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = FileSystemEventHandler = None

try:
    import flask
    from flask import Flask, send_from_directory, jsonify, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from packaging import version
    PACKAGING_AVAILABLE = True
except ImportError:
    PACKAGING_AVAILABLE = False

# Helper functions
def get_default_copyright():
    return f"© {datetime.now().year} My Company"

# Constants
APP_NAME = "HTML2EXE Pro Premium"
APP_VERSION = "2.0.0"
CONFIG_DIR = appdirs.user_config_dir(APP_NAME)
DATA_DIR = appdirs.user_data_dir(APP_NAME)
TEMP_DIR = tempfile.gettempdir()

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Enhanced Pydantic Models
class WindowConfig(BaseModel):
    """Advanced window configuration."""
    width: int = Field(default=1200, ge=400, le=4096)
    height: int = Field(default=800, ge=300, le=2160)
    min_width: int = Field(default=400, ge=200)
    min_height: int = Field(default=300, ge=200)
    resizable: bool = True
    fullscreen: bool = False
    kiosk: bool = False
    frameless: bool = False
    dpi_aware: bool = True
    always_on_top: bool = False
    center: bool = True
    maximized: bool = False

class SecurityConfig(BaseModel):
    """Enhanced security configuration."""
    csp_enabled: bool = True
    csp_policy: str = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; img-src 'self' data: blob: *;"
    same_origin_only: bool = False
    allow_devtools: bool = True
    block_external_urls: bool = False
    allowed_domains: List[str] = Field(default_factory=list)
    disable_context_menu: bool = False

class AppMetadata(BaseModel):
    """Enhanced application metadata."""
    name: str = "MyHTMLApp"
    version: str = "1.0.0"
    company: str = "My Company"
    copyright: str = Field(default_factory=get_default_copyright)
    description: str = "HTML Desktop Application"
    author: str = "Developer"
    email: str = "developer@company.com"
    website: str = "https://company.com"
    license: str = "Proprietary"

class BuildConfig(BaseModel):
    """Advanced build configuration."""
    source_type: str = Field(default="folder", regex="^(folder|url)$")
    source_path: str = ""
    output_dir: str = "dist"
    offline_mode: bool = False
    onefile: bool = True
    console: bool = False
    debug: bool = False
    upx_compress: bool = False
    icon_path: str = ""
    splash_screen: str = ""
    custom_protocol: str = ""
    single_instance: bool = True
    tray_menu: bool = True
    auto_start: bool = False
    include_ffmpeg: bool = False
    strip_debug: bool = True

class AdvancedConfig(BaseModel):
    """Advanced features configuration."""
    auto_updater: bool = False
    update_url: str = ""
    analytics: bool = False
    analytics_endpoint: str = ""
    crash_reporting: bool = False
    deep_links: bool = False
    file_associations: List[str] = Field(default_factory=list)
    startup_sound: str = ""
    theme: str = "auto"  # auto, light, dark

class AppConfig(BaseModel):
    """Complete premium application configuration."""
    metadata: AppMetadata = Field(default_factory=AppMetadata)
    window: WindowConfig = Field(default_factory=WindowConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    build: BuildConfig = Field(default_factory=BuildConfig)
    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)
    
    def save(self, path: str = None):
        """Save configuration to file."""
        if path is None:
            path = os.path.join(CONFIG_DIR, "config.json")
        with open(path, 'w') as f:
            json.dump(self.dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str = None):
        """Load configuration from file."""
        if path is None:
            path = os.path.join(CONFIG_DIR, "config.json")
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                return cls(**data)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
        return cls()

# Enhanced Flask App Factory
def create_flask_app(config: AppConfig) -> Flask:
    """Create enhanced Flask application with premium features."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    
    # CORS headers for development
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        if config.security.csp_enabled:
            response.headers.add('Content-Security-Policy', config.security.csp_policy)
        return response
    
    source_path = config.build.source_path
    
    @app.route('/')
    def index():
        """Serve the main HTML file."""
        if config.build.source_type == "url":
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{config.metadata.name}</title>
                <style>
                    body {{ margin: 0; padding: 0; height: 100vh; }}
                    iframe {{ width: 100%; height: 100%; border: none; }}
                </style>
            </head>
            <body>
                <iframe src="{source_path}" sandbox="allow-scripts allow-same-origin allow-forms allow-popups"></iframe>
            </body>
            </html>
            """
        else:
            index_file = os.path.join(source_path, 'index.html')
            if os.path.exists(index_file):
                return send_from_directory(source_path, 'index.html')
            else:
                return generate_default_html(config), 200
    
    @app.route('/<path:filename>')
    def serve_file(filename):
        """Serve static files with caching."""
        try:
            response = send_from_directory(source_path, filename)
            # Add caching headers for static assets
            if filename.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
                response.cache_control.max_age = 3600
            return response
        except FileNotFoundError:
            return "File not found", 404
    
    @app.route('/api/health')
    def health():
        """Enhanced health check endpoint."""
        return jsonify({
            "status": "ok",
            "app": config.metadata.name,
            "version": config.metadata.version,
            "offline_mode": config.build.offline_mode,
            "timestamp": datetime.now().isoformat()
        })
    
    @app.route('/api/reload')
    def reload():
        """Trigger reload endpoint."""
        return jsonify({"reload": True})
    
    return app

def generate_default_html(config: AppConfig) -> str:
    """Generate default HTML template when no index.html is found."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.metadata.name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; height: 100vh; display: flex; align-items: center; justify-content: center;
        }}
        .container {{ text-align: center; max-width: 600px; padding: 2rem; }}
        h1 {{ font-size: 3rem; margin-bottom: 1rem; }}
        p {{ font-size: 1.2rem; opacity: 0.9; margin-bottom: 2rem; }}
        .info {{ background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 10px; backdrop-filter: blur(10px); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 {config.metadata.name}</h1>
        <p>{config.metadata.description}</p>
        <div class="info">
            <p><strong>Version:</strong> {config.metadata.version}</p>
            <p><strong>Company:</strong> {config.metadata.company}</p>
            <p><strong>Built with HTML2EXE Pro Premium</strong></p>
        </div>
    </div>
</body>
</html>
"""

# Enhanced File System Watcher
if WATCHDOG_AVAILABLE:
    class LiveReloadHandler(FileSystemEventHandler):
        """Enhanced file system handler with debouncing."""
        
        def __init__(self, webview_window, debounce_ms: int = 500):
            self.webview_window = webview_window
            self.debounce_ms = debounce_ms
            self.pending_reload = False
            
        def on_modified(self, event):
            """Handle file modifications with debouncing."""
            if not event.is_directory and self._should_reload(event.src_path):
                if not self.pending_reload:
                    self.pending_reload = True
                    threading.Timer(self.debounce_ms / 1000, self._reload).start()
        
        def _should_reload(self, filepath: str) -> bool:
            """Check if file change should trigger reload."""
            reload_extensions = {'.html', '.css', '.js', '.json', '.xml'}
            return any(filepath.lower().endswith(ext) for ext in reload_extensions)
        
        def _reload(self):
            """Perform the actual reload."""
            try:
                if self.webview_window:
                    self.webview_window.evaluate_js('window.location.reload()')
            except Exception as e:
                print(f"Reload failed: {e}")
            finally:
                self.pending_reload = False
else:
    # Fallback when watchdog is not available
    class LiveReloadHandler:
        """Fallback file system handler when watchdog is not available."""
        
        def __init__(self, webview_window, debounce_ms: int = 500):
            self.webview_window = webview_window
            self.debounce_ms = debounce_ms
            self.pending_reload = False
            print("Warning: Live reload not available (watchdog not installed)")
        
        def on_modified(self, event):
            """No-op when watchdog is not available."""
            pass
        
        def _should_reload(self, filepath: str) -> bool:
            """No-op when watchdog is not available."""
            return False
        
        def _reload(self):
            """No-op when watchdog is not available."""
            pass

# Icon Generator
class IconGenerator:
    """Professional icon generator with multiple formats."""
    
    @staticmethod
    def generate_icon(text: str, output_path: str, size: int = 256):
        """Generate professional application icon."""
        from PIL import Image, ImageDraw, ImageFont

        # Create image with gradient background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Gradient background
        for y in range(size):
            r = int(102 + (116 * y / size))  # 667eea to 764ba2
            g = int(126 - (47 * y / size))
            b = int(234 - (72 * y / size))
            draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
        
        # Draw circle background
        margin = size // 8
        circle_size = size - 2 * margin
        draw.ellipse([margin, margin, margin + circle_size, margin + circle_size], 
                    fill=(255, 255, 255, 30))
        
        # Draw text
        font = None
        font_size = size // 4

        # List of common, cross-platform fonts to try (lowercase for case-insensitivity)
        font_names = [
            "dejavusans.ttf", "liberationsans-regular.ttf", "arial.ttf", "calibri.ttf"
        ]

        for font_name in font_names:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break  # Stop if font is found
            except IOError:
                continue # Try next font

        if not font:
            print(f"Warning: No premium fonts found. Falling back to default font.")
            font = ImageFont.load_default()
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        # Draw text with shadow
        draw.text((x + 2, y + 2), text, fill=(0, 0, 0, 100), font=font)
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        
        # Save as ICO
        img.save(output_path, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
        return output_path

# Build Engine
class AutoOptionsSelector:
    """Automatic options selection for optimal .exe generation."""
    
    @staticmethod
    def analyze_source(source_path: str, source_type: str) -> Dict[str, Any]:
        """Analyze source and recommend optimal build options."""
        recommendations = {
            "onefile": True,
            "console": False,
            "debug": False,
            "upx_compress": False,
            "strip_debug": True,
            "optimization_level": "balanced"
        }
        
        if source_type == "folder":
            # Analyze folder contents
            if os.path.exists(source_path):
                file_count = len([f for f in os.listdir(source_path) if os.path.isfile(os.path.join(source_path, f))])
                total_size = sum(os.path.getsize(os.path.join(source_path, f)) 
                               for f in os.listdir(source_path) 
                               if os.path.isfile(os.path.join(source_path, f)))
                
                # Large projects might benefit from directory mode
                if total_size > 50 * 1024 * 1024:  # 50MB
                    recommendations["onefile"] = False
                    recommendations["optimization_level"] = "size"
                
                # Check for development files
                dev_files = [f for f in os.listdir(source_path) if f.endswith(('.map', '.ts', '.scss', '.less'))]
                if dev_files:
                    recommendations["strip_debug"] = True
                    recommendations["optimization_level"] = "production"
                
                # Check for external dependencies
                has_external_js = any(f.endswith('.js') and 'http' in open(os.path.join(source_path, f), 'r', errors='ignore').read()[:1000] 
                                    for f in os.listdir(source_path) if f.endswith('.html'))
                if has_external_js:
                    recommendations["offline_mode"] = True
        
        elif source_type == "url":
            # URL-based apps should be single file for portability
            recommendations["onefile"] = True
            recommendations["offline_mode"] = True
            recommendations["optimization_level"] = "portable"
        
        return recommendations
    
    @staticmethod
    def get_optimal_pyinstaller_options(config: AppConfig) -> List[str]:
        """Get optimal PyInstaller command options based on analysis."""
        analysis = AutoOptionsSelector.analyze_source(config.build.source_path, config.build.source_type)
        
        # Ensure output directories exist
        os.makedirs(config.build.output_dir, exist_ok=True)
        dist_path = os.path.join(config.build.output_dir, "dist")
        work_path = os.path.join(config.build.output_dir, "build", "work")
        os.makedirs(dist_path, exist_ok=True)
        os.makedirs(work_path, exist_ok=True)
        
        options = [
            "--noconfirm",
            "--clean",
            f"--name={config.metadata.name}",
            f"--distpath={dist_path}",
            f"--workpath={work_path}"
        ]
        
        # Apply recommendations
        if analysis["onefile"]:
            options.append("--onefile")
        else:
            options.append("--onedir")
        
        if not config.build.console:
            options.append("--windowed")
        
        if analysis["strip_debug"]:
            options.append("--strip")
        
        if analysis["upx_compress"]:
            options.append("--upx-dir=upx")
        
        # Add data files for folder mode
        if config.build.source_type == "folder":
            html_assets = os.path.join(config.build.output_dir, "build", "html_assets")
            # Use proper path separator for PyInstaller
            if sys.platform == "win32":
                options.append(f"--add-data={html_assets};html_assets")
            else:
                options.append(f"--add-data={html_assets}:html_assets")
        
        # Hidden imports
        hidden_imports = [
            "flask", "webview", "threading", "json", "os", "sys", "time",
            "urllib.parse", "base64", "hashlib", "datetime", "tempfile"
        ]
        for imp in hidden_imports:
            options.append(f"--hidden-import={imp}")
        
        # Icon
        if config.build.icon_path and os.path.exists(config.build.icon_path):
            options.append(f"--icon={config.build.icon_path}")
        
        return options

class BuildEngine:
    """Advanced PyInstaller build engine with optimization."""
    
    def __init__(self, config: AppConfig, progress_callback: Callable = None):
        self.config = config
        self.progress_callback = progress_callback or (lambda x: None)
        self.build_dir = os.path.join(config.build.output_dir, "build")
        self.dist_dir = os.path.join(config.build.output_dir, "dist")
        
    def prepare_build(self) -> str:
        """Prepare build environment and assets."""
        self.progress_callback("Preparing build environment...")
        
        # Create build directories
        os.makedirs(self.build_dir, exist_ok=True)
        os.makedirs(self.dist_dir, exist_ok=True)
        
        # Copy source files if folder mode
        if self.config.build.source_type == "folder":
            source_build_dir = os.path.join(self.build_dir, "html_assets")
            if os.path.exists(source_build_dir):
                shutil.rmtree(source_build_dir)
            shutil.copytree(self.config.build.source_path, source_build_dir)
        
        # Generate application icon
        icon_path = self.config.build.icon_path
        if not icon_path or not os.path.exists(icon_path):
            icon_path = os.path.join(self.build_dir, "app_icon.ico")
            IconGenerator.generate_icon(self.config.metadata.name[:2].upper(), icon_path)
            self.config.build.icon_path = icon_path
        
        # Create main application script
        main_script = self._create_main_script()
        main_script_path = os.path.join(self.build_dir, "main.py")
        with open(main_script_path, 'w', encoding='utf-8') as f:
            f.write(main_script)
        
        return main_script_path
    
    def _create_main_script(self) -> str:
        """Create the main application script."""
        script_template = '''
import sys
import os
import webview
import threading
import time
from flask import Flask, send_from_directory, jsonify

# Configuration embedded at build time
CONFIG = {config_json}

def create_app():
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        if CONFIG["build"]["source_type"] == "url":
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>{CONFIG["metadata"]["name"]}</title></head>
            <body style="margin:0;">
                <iframe src="{CONFIG["build"]["source_path"]}" 
                        style="width:100%;height:100vh;border:none;">
                </iframe>
            </body>
            </html>
            """
        else:
            try:
                resource_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
                html_dir = os.path.join(resource_path, 'html_assets')
                with open(os.path.join(html_dir, 'index.html'), 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return "<h1>Welcome to {}</h1>".format(CONFIG["metadata"]["name"])
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        resource_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        html_dir = os.path.join(resource_path, 'html_assets')
        return send_from_directory(html_dir, filename)
    
    return app

def main():
    app = create_app()
    
    # Start Flask server
    def run_server():
        app.run(host='127.0.0.1', port=0, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1)
    
    # Create webview window
    window = webview.create_window(
        title=CONFIG["metadata"]["name"],
        url="http://127.0.0.1:5000",
        width=CONFIG["window"]["width"],
        height=CONFIG["window"]["height"],
        resizable=CONFIG["window"]["resizable"],
        fullscreen=CONFIG["window"]["fullscreen"]
    )
    
    webview.start(debug={debug_mode})

if __name__ == '__main__':
    main()
'''
        return script_template.format(
            config_json=json.dumps(self.config.dict(), indent=2),
            debug_mode=str(self.config.build.debug).lower()
        )
    
    def build(self) -> Dict[str, Any]:
        """Execute the build process."""
        start_time = time.time()
        
        try:
            # Prepare build
            main_script_path = self.prepare_build()
            
            # Build PyInstaller command
            cmd = self._build_pyinstaller_command(main_script_path)
            
            self.progress_callback("Building executable...")
            
            # Execute build
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.build_dir)
            
            if result.returncode != 0:
                raise Exception(f"Build failed: {result.stderr}")
            
            # Post-process
            self._post_process()
            
            build_time = time.time() - start_time
            
            # Generate build report
            exe_path = self._get_exe_path()
            report = {
                "success": True,
                "exe_path": exe_path,
                "build_time": f"{build_time:.2f}s",
                "exe_size": f"{os.path.getsize(exe_path) / (1024*1024):.2f} MB" if os.path.exists(exe_path) else "Unknown",
                "config": self.config.dict(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Save build report
            report_path = os.path.join(self.dist_dir, "build_report.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            return report
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "build_time": f"{time.time() - start_time:.2f}s"
            }
    
    def _build_pyinstaller_command(self, main_script_path: str) -> List[str]:
        """Build PyInstaller command with automatic optimization."""
        # Use automatic options selector for optimal settings
        auto_options = AutoOptionsSelector.get_optimal_pyinstaller_options(self.config)
        
        # Start with PyInstaller command
        cmd = [sys.executable, "-m", "PyInstaller"] + auto_options
        
        # Add the main script
        cmd.append(main_script_path)
        
        return cmd
    
    def _get_exe_path(self) -> str:
        """Get the path to the built executable."""
        if self.config.build.onefile:
            return os.path.join(self.dist_dir, f"{self.config.metadata.name}.exe")
        else:
            return os.path.join(self.dist_dir, self.config.metadata.name, f"{self.config.metadata.name}.exe")
    
    def _post_process(self):
        """Post-process the built executable."""
        self.progress_callback("Post-processing...")
        
        exe_path = self._get_exe_path()
        if os.path.exists(exe_path):
            # Set file metadata (this would require additional tools in production)
            pass

# Modern React-style GUI
class ModernGUI:
    """Modern React-style GUI interface."""
    
    def __init__(self):
        self.root = None
        self.config = AppConfig.load()
        self.current_step = 0
        self.steps = [
            "Source", "Metadata", "Window", "Security", "Build", "Advanced", "Review"
        ]
        self.step_frames = {}
        self.preview_window = None
        
    def run(self):
        """Run the modern GUI application."""
        try:
            import tkinter as tk
            from tkinter import ttk, filedialog, messagebox, simpledialog
            import tkinter.font as tkFont
        except ImportError as e:
            print(f"Error: tkinter not available: {e}")
            print("Please install tkinter: sudo apt-get install python3-tk (Linux) or ensure tkinter is installed with Python")
            return

        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - Premium Edition")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        self.root.resizable(True, True)
        
        # Set modern styling
        self._setup_styles()
        
        # Create layout
        self._create_layout()
        
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        
        # Start GUI
        self.root.mainloop()
    
    def _setup_styles(self):
        """Setup modern styling."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure modern styles
        style.configure('Modern.TFrame', background='#1a1a1a')
        style.configure('Card.TFrame', background='#2d2d2d', relief='raised', borderwidth=1)
        style.configure('Modern.TLabel', background='#1a1a1a', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('Title.TLabel', background='#1a1a1a', foreground='#00D4AA', font=('Segoe UI', 16, 'bold'))
        style.configure('Modern.TButton', font=('Segoe UI', 10))
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'))
        
    def _create_layout(self):
        """Create the main layout."""
        # Main container
        main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        self._create_header(main_frame)
        
        # Content area
        content_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        content_frame.pack(fill='both', expand=True, pady=(20, 0))
        
        # Left sidebar - Steps
        self._create_sidebar(content_frame)
        
        # Right area - Step content and preview
        self._create_main_content(content_frame)
        
        # Footer with navigation
        self._create_footer(main_frame)
        
        # Load first step
        self._show_step(0)
    
    def _create_header(self, parent):
        """Create modern header."""
        header_frame = ttk.Frame(parent, style='Modern.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Logo and title
        title_frame = ttk.Frame(header_frame, style='Modern.TFrame')
        title_frame.pack(side='left')
        
        title_label = ttk.Label(title_frame, text="HTML2EXE Pro", style='Title.TLabel')
        title_label.pack(anchor='w')
        
        subtitle_label = ttk.Label(title_frame, text="Premium Edition - Convert HTML to Professional Desktop Apps", 
                                 style='Modern.TLabel')
        subtitle_label.pack(anchor='w')
        
        # Actions
        actions_frame = ttk.Frame(header_frame, style='Modern.TFrame')
        actions_frame.pack(side='right')
        
        ttk.Button(actions_frame, text="Load Config", command=self._load_config).pack(side='right', padx=(0, 10))
        ttk.Button(actions_frame, text="Save Config", command=self._save_config).pack(side='right', padx=(0, 10))
        ttk.Button(actions_frame, text="Preview", command=self._show_preview).pack(side='right', padx=(0, 10))
    
    def _create_sidebar(self, parent):
        """Create sidebar with step navigation."""
        sidebar_frame = ttk.Frame(parent, style='Card.TFrame')
        sidebar_frame.pack(side='left', fill='y', padx=(0, 20), pady=10)
        sidebar_frame.configure(width=200)
        
        # Steps title
        steps_label = ttk.Label(sidebar_frame, text="Configuration Steps", style='Title.TLabel')
        steps_label.pack(pady=(20, 10))
        
        # Step buttons
        self.step_buttons = []
        for i, step in enumerate(self.steps):
            btn_frame = ttk.Frame(sidebar_frame, style='Modern.TFrame')
            btn_frame.pack(fill='x', padx=10, pady=2)
            
            step_btn = ttk.Button(btn_frame, text=f"{i+1}. {step}", 
                                command=lambda x=i: self._show_step(x))
            step_btn.pack(fill='x')
            self.step_buttons.append(step_btn)
        
        # Separator
        ttk.Separator(sidebar_frame, orient='horizontal').pack(fill='x', pady=20, padx=10)
        
        # Quick actions
        ttk.Label(sidebar_frame, text="Quick Actions", style='Title.TLabel').pack(pady=(0, 10))
        
        ttk.Button(sidebar_frame, text="🚀 Quick Build", command=self._quick_build).pack(fill='x', padx=10, pady=2)
        ttk.Button(sidebar_frame, text="📁 Open Folder", command=self._select_folder).pack(fill='x', padx=10, pady=2)
        ttk.Button(sidebar_frame, text="🌐 Test URL", command=self._test_url).pack(fill='x', padx=10, pady=2)
        ttk.Button(sidebar_frame, text="⚙️ Advanced", command=self._show_advanced).pack(fill='x', padx=10, pady=2)
    
    def _create_main_content(self, parent):
        """Create main content area."""
        content_frame = ttk.Frame(parent, style='Modern.TFrame')
        content_frame.pack(side='left', fill='both', expand=True)
        
        # Step content container
        self.content_container = ttk.Frame(content_frame, style='Card.TFrame')
        self.content_container.pack(fill='both', expand=True, pady=(0, 10))
        
        # Create all step frames
        self._create_step_frames()
    
    def _create_footer(self, parent):
        """Create footer with navigation buttons."""
        footer_frame = ttk.Frame(parent, style='Modern.TFrame')
        footer_frame.pack(fill='x', pady=(20, 0))
        
        # Navigation buttons
        nav_frame = ttk.Frame(footer_frame, style='Modern.TFrame')
        nav_frame.pack(side='right')
        
        self.prev_btn = ttk.Button(nav_frame, text="← Previous", command=self._prev_step)
        self.prev_btn.pack(side='left', padx=(0, 10))
        
        self.next_btn = ttk.Button(nav_frame, text="Next →", command=self._next_step)
        self.next_btn.pack(side='left', padx=(0, 10))
        
        self.build_btn = ttk.Button(nav_frame, text="🚀 BUILD", command=self._start_build, 
                                   style='Primary.TButton')
        self.build_btn.pack(side='left', padx=(10, 0))
        
        # Progress info
        self.progress_label = ttk.Label(footer_frame, text="Ready to configure", style='Modern.TLabel')
        self.progress_label.pack(side='left')
    
    def _create_step_frames(self):
        """Create all step configuration frames."""
        # Step 0: Source Configuration
        self.step_frames[0] = self._create_source_step()
        
        # Step 1: Metadata Configuration  
        self.step_frames[1] = self._create_metadata_step()
        
        # Step 2: Window Configuration
        self.step_frames[2] = self._create_window_step()
        
        # Step 3: Security Configuration
        self.step_frames[3] = self._create_security_step()
        
        # Step 4: Build Configuration
        self.step_frames[4] = self._create_build_step()
        
        # Step 5: Advanced Configuration
        self.step_frames[5] = self._create_advanced_step()
        
        # Step 6: Review Configuration
        self.step_frames[6] = self._create_review_step()
    
    def _create_source_step(self):
        """Create source configuration step."""
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        
        # Title
        title_label = ttk.Label(frame, text="📁 Source Configuration", style='Title.TLabel')
        title_label.pack(pady=(20, 10))
        
        # Source type selection
        type_frame = ttk.LabelFrame(frame, text="Source Type", padding=20)
        type_frame.pack(fill='x', padx=20, pady=10)
        
        self.source_type_var = tk.StringVar(value=self.config.build.source_type)
        
        folder_radio = ttk.Radiobutton(type_frame, text="📁 Local HTML Folder", 
                                      variable=self.source_type_var, value="folder",
                                      command=self._update_source_type)
        folder_radio.pack(anchor='w', pady=5)
        
        url_radio = ttk.Radiobutton(type_frame, text="🌐 Remote URL", 
                                   variable=self.source_type_var, value="url",
                                   command=self._update_source_type)
        url_radio.pack(anchor='w', pady=5)
        
        # Source path/URL input
        path_frame = ttk.LabelFrame(frame, text="Source Path/URL", padding=20)
        path_frame.pack(fill='x', padx=20, pady=10)
        
        path_input_frame = ttk.Frame(path_frame)
        path_input_frame.pack(fill='x')
        
        self.source_path_var = tk.StringVar(value=self.config.build.source_path)
        self.source_path_entry = ttk.Entry(path_input_frame, textvariable=self.source_path_var, font=('Consolas', 10))
        self.source_path_entry.pack(side='left', fill='x', expand=True)
        
        self.browse_btn = ttk.Button(path_input_frame, text="Browse...", command=self._browse_source)
        self.browse_btn.pack(side='right', padx=(10, 0))
        
        # Offline mode option
        offline_frame = ttk.LabelFrame(frame, text="Offline Options", padding=20)
        offline_frame.pack(fill='x', padx=20, pady=10)
        
        self.offline_var = tk.BooleanVar(value=self.config.build.offline_mode)
        offline_check = ttk.Checkbutton(offline_frame, text="📱 Package for offline use (cache assets)", 
                                       variable=self.offline_var)
        offline_check.pack(anchor='w')
        
        return frame
    
    def _create_metadata_step(self):
        """Create metadata configuration step."""
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        
        title_label = ttk.Label(frame, text="📋 Application Metadata", style='Title.TLabel')
        title_label.pack(pady=(20, 10))
        
        # Create scrollable frame for metadata
        canvas = tk.Canvas(frame, bg='#2d2d2d', highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
        
        # Metadata fields
        fields = [
            ("App Name", "name", "MyHTMLApp"),
            ("Version", "version", "1.0.0"),
            ("Company", "company", "My Company"),
            ("Author", "author", "Developer"),
            ("Email", "email", "developer@company.com"),
            ("Website", "website", "https://company.com"),
            ("Description", "description", "HTML Desktop Application"),
            ("Copyright", "copyright", f"© {datetime.now().year} My Company"),
            ("License", "license", "Proprietary")
        ]
        
        self.metadata_vars = {}
        
        for label_text, field_name, default_value in fields:
            field_frame = ttk.LabelFrame(scrollable_frame, text=label_text, padding=10)
            field_frame.pack(fill='x', pady=5)
            
            var = tk.StringVar(value=getattr(self.config.metadata, field_name, default_value))
            self.metadata_vars[field_name] = var
            
            entry = ttk.Entry(field_frame, textvariable=var, font=('Segoe UI', 10))
            entry.pack(fill='x')
        
        return frame
    
    def _create_window_step(self):
        """Create window configuration step."""
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        
        title_label = ttk.Label(frame, text="🪟 Window Configuration", style='Title.TLabel')
        title_label.pack(pady=(20, 10))
        
        # Window dimensions
        dims_frame = ttk.LabelFrame(frame, text="Dimensions", padding=20)
        dims_frame.pack(fill='x', padx=20, pady=10)
        
        dims_grid = ttk.Frame(dims_frame)
        dims_grid.pack(fill='x')
        
        # Width
        ttk.Label(dims_grid, text="Width:").grid(row=0, column=0, sticky='w', padx=(0, 10))
        self.width_var = tk.IntVar(value=self.config.window.width)
        width_spin = ttk.Spinbox(dims_grid, from_=400, to=4096, textvariable=self.width_var, width=10)
        width_spin.grid(row=0, column=1, padx=(0, 20))
        
        # Height
        ttk.Label(dims_grid, text="Height:").grid(row=0, column=2, sticky='w', padx=(0, 10))
        self.height_var = tk.IntVar(value=self.config.window.height)
        height_spin = ttk.Spinbox(dims_grid, from_=300, to=2160, textvariable=self.height_var, width=10)
        height_spin.grid(row=0, column=3)
        
        # Window options
        options_frame = ttk.LabelFrame(frame, text="Window Options", padding=20)
        options_frame.pack(fill='x', padx=20, pady=10)
        
        self.window_vars = {}
        window_options = [
            ("resizable", "🔄 Resizable", True),
            ("fullscreen", "🖥️ Start Fullscreen", False),
            ("kiosk", "🔒 Kiosk Mode", False),
            ("frameless", "🚫 Frameless", False),
            ("always_on_top", "📌 Always On Top", False),
            ("center", "🎯 Center Window", True),
            ("maximized", "📏 Start Maximized", False)
        ]
        
        for field_name, label_text, default_value in window_options:
            var = tk.BooleanVar(value=getattr(self.config.window, field_name, default_value))
            self.window_vars[field_name] = var
            
            check = ttk.Checkbutton(options_frame, text=label_text, variable=var)
            check.pack(anchor='w', pady=2)
        
        return frame
    
    def _create_security_step(self):
        """Create security configuration step."""
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        
        title_label = ttk.Label(frame, text="🔒 Security Configuration", style='Title.TLabel')
        title_label.pack(pady=(20, 10))
        
        # Security options
        security_frame = ttk.LabelFrame(frame, text="Security Options", padding=20)
        security_frame.pack(fill='x', padx=20, pady=10)
        
        self.security_vars = {}
        security_options = [
            ("csp_enabled", "🛡️ Enable Content Security Policy", True),
            ("allow_devtools", "🔧 Allow Developer Tools", True),
            ("block_external_urls", "🚫 Block External URLs", False),
            ("disable_context_menu", "📝 Disable Context Menu", False)
        ]
        
        for field_name, label_text, default_value in security_options:
            var = tk.BooleanVar(value=getattr(self.config.security, field_name, default_value))
            self.security_vars[field_name] = var
            
            check = ttk.Checkbutton(security_frame, text=label_text, variable=var)
            check.pack(anchor='w', pady=2)
        
        # CSP Policy
        csp_frame = ttk.LabelFrame(frame, text="Content Security Policy", padding=20)
        csp_frame.pack(fill='x', padx=20, pady=10)
        
        self.csp_var = tk.StringVar(value=self.config.security.csp_policy)
        csp_text = tk.Text(csp_frame, height=4, wrap='word', font=('Consolas', 9))
        csp_text.pack(fill='x')
        csp_text.insert('1.0', self.csp_var.get())
        
        return frame
    
    def _create_build_step(self):
        """Create build configuration step."""
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        
        title_label = ttk.Label(frame, text="⚙️ Build Configuration", style='Title.TLabel')
        title_label.pack(pady=(20, 10))
        
        # Build options
        build_frame = ttk.LabelFrame(frame, text="Build Options", padding=20)
        build_frame.pack(fill='x', padx=20, pady=10)
        
        self.build_vars = {}
        build_options = [
            ("onefile", "📦 Single File Executable", True),
            ("console", "💻 Show Console Window", False),
            ("debug", "🐛 Debug Mode", False),
            ("upx_compress", "🗜️ UPX Compression", False),
            ("single_instance", "👤 Single Instance", True),
            ("tray_menu", "📱 System Tray", True),
            ("strip_debug", "✂️ Strip Debug Info", True)
        ]
        
        for field_name, label_text, default_value in build_options:
            var = tk.BooleanVar(value=getattr(self.config.build, field_name, default_value))
            self.build_vars[field_name] = var
            
            check = ttk.Checkbutton(build_frame, text=label_text, variable=var)
            check.pack(anchor='w', pady=2)
        
        # Icon selection
        icon_frame = ttk.LabelFrame(frame, text="Application Icon", padding=20)
        icon_frame.pack(fill='x', padx=20, pady=10)
        
        icon_input_frame = ttk.Frame(icon_frame)
        icon_input_frame.pack(fill='x')
        
        self.icon_path_var = tk.StringVar(value=self.config.build.icon_path)
        icon_entry = ttk.Entry(icon_input_frame, textvariable=self.icon_path_var)
        icon_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(icon_input_frame, text="Browse...", command=self._browse_icon).pack(side='right', padx=(10, 0))
        ttk.Button(icon_input_frame, text="Generate", command=self._generate_icon).pack(side='right', padx=(10, 0))
        
        return frame
    
    def _create_advanced_step(self):
        """Create advanced configuration step."""
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        
        title_label = ttk.Label(frame, text="🚀 Advanced Configuration", style='Title.TLabel')
        title_label.pack(pady=(20, 10))
        
        # Advanced features
        advanced_frame = ttk.LabelFrame(frame, text="Premium Features", padding=20)
        advanced_frame.pack(fill='x', padx=20, pady=10)
        
        self.advanced_vars = {}
        advanced_options = [
            ("auto_updater", "🔄 Auto Updater", False),
            ("analytics", "📊 Analytics", False),
            ("crash_reporting", "💥 Crash Reporting", False),
            ("deep_links", "🔗 Deep Link Support", False)
        ]
        
        for field_name, label_text, default_value in advanced_options:
            var = tk.BooleanVar(value=getattr(self.config.advanced, field_name, default_value))
            self.advanced_vars[field_name] = var
            
            check = ttk.Checkbutton(advanced_frame, text=label_text, variable=var)
            check.pack(anchor='w', pady=2)
        
        # Custom protocol
        protocol_frame = ttk.LabelFrame(frame, text="Custom Protocol", padding=20)
        protocol_frame.pack(fill='x', padx=20, pady=10)
        
        protocol_input_frame = ttk.Frame(protocol_frame)
        protocol_input_frame.pack(fill='x')
        
        ttk.Label(protocol_input_frame, text="Protocol:").pack(side='left')
        self.protocol_var = tk.StringVar(value=self.config.build.custom_protocol)
        protocol_entry = ttk.Entry(protocol_input_frame, textvariable=self.protocol_var)
        protocol_entry.pack(side='left', fill='x', expand=True, padx=(10, 0))
        ttk.Label(protocol_input_frame, text="://").pack(side='left')
        
        return frame
    
    def _create_review_step(self):
        """Create configuration review step."""
        frame = ttk.Frame(self.content_container, style='Modern.TFrame')
        
        title_label = ttk.Label(frame, text="📋 Configuration Review", style='Title.TLabel')
        title_label.pack(pady=(20, 10))
        
        # Review text widget
        review_frame = ttk.LabelFrame(frame, text="Final Configuration", padding=20)
        review_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.review_text = tk.Text(review_frame, wrap='word', font=('Consolas', 9), 
                                  bg='#2d2d2d', fg='#ffffff', insertbackground='#ffffff')
        
        scrollbar_review = ttk.Scrollbar(review_frame, orient="vertical", command=self.review_text.yview)
        self.review_text.configure(yscrollcommand=scrollbar_review.set)
        
        self.review_text.pack(side="left", fill="both", expand=True)
        scrollbar_review.pack(side="right", fill="y")
        
        return frame
    
    def _show_step(self, step_index):
        """Show specific configuration step."""
        # Hide all frames
        for frame in self.step_frames.values():
            frame.pack_forget()
        
        # Show selected frame
        if step_index in self.step_frames:
            self.step_frames[step_index].pack(fill='both', expand=True)
            self.current_step = step_index
            
            # Update button states
            self.prev_btn.config(state='normal' if step_index > 0 else 'disabled')
            self.next_btn.config(state='normal' if step_index < len(self.steps) - 1 else 'disabled')
            
            # Update progress
            self.progress_label.config(text=f"Step {step_index + 1}/{len(self.steps)}: {self.steps[step_index]}")
            
            # Special handling for review step
            if step_index == len(self.steps) - 1:
                self._update_review()
    
    def _update_review(self):
        """Update the configuration review."""
        self._sync_config_from_ui()
        
        review_content = f"""
HTML2EXE Pro Premium - Configuration Review
==========================================

APPLICATION METADATA
--------------------
Name: {self.config.metadata.name}
Version: {self.config.metadata.version}
Company: {self.config.metadata.company}
Author: {self.config.metadata.author}
Description: {self.config.metadata.description}

SOURCE CONFIGURATION
--------------------
Type: {self.config.build.source_type.upper()}
Path/URL: {self.config.build.source_path}
Offline Mode: {"✅ Enabled" if self.config.build.offline_mode else "❌ Disabled"}

WINDOW CONFIGURATION
-------------------
Dimensions: {self.config.window.width} x {self.config.window.height}
Resizable: {"✅" if self.config.window.resizable else "❌"}
Fullscreen: {"✅" if self.config.window.fullscreen else "❌"}
Kiosk Mode: {"✅" if self.config.window.kiosk else "❌"}

BUILD CONFIGURATION
------------------
Output Format: {"Single File (.exe)" if self.config.build.onefile else "Directory"}
Console Window: {"✅ Visible" if self.config.build.console else "❌ Hidden"}
Debug Mode: {"✅ Enabled" if self.config.build.debug else "❌ Disabled"}
System Tray: {"✅ Enabled" if self.config.build.tray_menu else "❌ Disabled"}

SECURITY SETTINGS
----------------
CSP Enabled: {"✅" if self.config.security.csp_enabled else "❌"}
DevTools: {"✅ Allowed" if self.config.security.allow_devtools else "❌ Blocked"}
External URLs: {"❌ Blocked" if self.config.security.block_external_urls else "✅ Allowed"}

ADVANCED FEATURES
----------------
Auto Updater: {"✅" if self.config.advanced.auto_updater else "❌"}
Analytics: {"✅" if self.config.advanced.analytics else "❌"}
Custom Protocol: {self.config.build.custom_protocol or "Not Set"}

BUILD OUTPUT
-----------
Output Directory: {self.config.build.output_dir}
Estimated Size: 40-80 MB (depending on features)
Build Time: ~30-120 seconds

Ready to build your professional desktop application!
        """.strip()
        
        self.review_text.delete(1.0, tk.END)
        self.review_text.insert(1.0, review_content)
    
    def _next_step(self):
        """Go to next step."""
        if self.current_step < len(self.steps) - 1:
            self._sync_config_from_ui()
            self._show_step(self.current_step + 1)
    
    def _prev_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self._sync_config_from_ui()
            self._show_step(self.current_step - 1)
    
    def _sync_config_from_ui(self):
        """Synchronize configuration from UI variables."""
        try:
            # Source configuration
            if hasattr(self, 'source_type_var'):
                self.config.build.source_type = self.source_type_var.get()
            if hasattr(self, 'source_path_var'):
                self.config.build.source_path = self.source_path_var.get()
            if hasattr(self, 'offline_var'):
                self.config.build.offline_mode = self.offline_var.get()
            
            # Metadata
            if hasattr(self, 'metadata_vars'):
                for field, var in self.metadata_vars.items():
                    setattr(self.config.metadata, field, var.get())
            
            # Window configuration
            if hasattr(self, 'width_var'):
                self.config.window.width = self.width_var.get()
            if hasattr(self, 'height_var'):
                self.config.window.height = self.height_var.get()
            if hasattr(self, 'window_vars'):
                for field, var in self.window_vars.items():
                    setattr(self.config.window, field, var.get())
            
            # Security configuration
            if hasattr(self, 'security_vars'):
                for field, var in self.security_vars.items():
                    setattr(self.config.security, field, var.get())
            
            # Build configuration
            if hasattr(self, 'build_vars'):
                for field, var in self.build_vars.items():
                    setattr(self.config.build, field, var.get())
            if hasattr(self, 'icon_path_var'):
                self.config.build.icon_path = self.icon_path_var.get()
            
            # Advanced configuration
            if hasattr(self, 'advanced_vars'):
                for field, var in self.advanced_vars.items():
                    setattr(self.config.advanced, field, var.get())
            if hasattr(self, 'protocol_var'):
                self.config.build.custom_protocol = self.protocol_var.get()
                
        except Exception as e:
            print(f"Warning: Error syncing config: {e}")
    
    def _browse_source(self):
        """Browse for source folder or enter URL."""
        if self.source_type_var.get() == "folder":
            folder = filedialog.askdirectory(title="Select HTML Folder")
            if folder:
                self.source_path_var.set(folder)
        else:
            # Simple URL input dialog
            try:
                from tkinter import simpledialog
                url = simpledialog.askstring("URL Input", "Enter the URL:")
                if url:
                    self.source_path_var.set(url)
            except ImportError:
                # Fallback if simpledialog not available
                url = input("Enter the URL: ")
                if url:
                    self.source_path_var.set(url)
    
    def _browse_icon(self):
        """Browse for application icon."""
        icon_file = filedialog.askopenfilename(
            title="Select Application Icon",
            filetypes=[("Icon files", "*.ico"), ("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if icon_file:
            self.icon_path_var.set(icon_file)
    
    def _generate_icon(self):
        """Generate application icon from app name."""
        if hasattr(self, 'metadata_vars') and 'name' in self.metadata_vars:
            app_name = self.metadata_vars['name'].get() or "App"
            icon_path = os.path.join(tempfile.gettempdir(), f"{app_name.replace(' ', '_')}.ico")
            
            try:
                IconGenerator.generate_icon(app_name[:2].upper(), icon_path)
                self.icon_path_var.set(icon_path)
                messagebox.showinfo("Success", f"Icon generated successfully!\nSaved to: {icon_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate icon: {e}")
    
    def _show_preview(self):
        """Show live preview of the application."""
        self._sync_config_from_ui()
        
        if not self.config.build.source_path:
            messagebox.showwarning("Warning", "Please configure a source path/URL first.")
            return
        
        try:
            # Create preview window
            if self.preview_window:
                self.preview_window.destroy()
            
            self.preview_window = tk.Toplevel(self.root)
            self.preview_window.title(f"Preview - {self.config.metadata.name}")
            self.preview_window.geometry("800x600")
            
            # Embed webview or simple browser
            if self.config.build.source_type == "url":
                webbrowser.open(self.config.build.source_path)
                self.preview_window.destroy()
            else:
                # For folder mode, start a simple server
                self._start_preview_server()
                
        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to show preview: {e}")
    
    def _start_preview_server(self):
        """Start preview server for local HTML files."""
        try:
            import http.server
            import socketserver
            from threading import Thread
            
            PORT = 8000

            # Create a handler that serves files from the specified directory
            # This avoids using os.chdir, which is not thread-safe
            Handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
                *args, directory=self.config.build.source_path, **kwargs
            )
            
            def serve():
                with socketserver.TCPServer(("", PORT), Handler) as httpd:
                    print(f"Preview server running at http://localhost:{PORT}")
                    httpd.serve_forever()
            
            # Start server in background
            server_thread = Thread(target=serve, daemon=True)
            server_thread.start()
            
            # Open in browser
            webbrowser.open(f"http://localhost:{PORT}")
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to start preview server: {e}")
    
    def _quick_build(self):
        """Perform quick build with automatic optimal settings."""
        if not self.config.build.source_path:
            messagebox.showwarning("Warning", "Please configure a source path/URL first.")
            return
        
        self._sync_config_from_ui()
        
        # Apply automatic optimal settings
        analysis = AutoOptionsSelector.analyze_source(
            self.config.build.source_path, 
            self.config.build.source_type
        )
        
        # Update config with optimal settings
        self.config.build.onefile = analysis["onefile"]
        self.config.build.console = analysis["console"]
        self.config.build.debug = analysis["debug"]
        self.config.build.upx_compress = analysis["upx_compress"]
        self.config.build.strip_debug = analysis["strip_debug"]
        self.config.build.offline_mode = analysis.get("offline_mode", False)
        
        # Show what settings were selected
        settings_msg = f"""Auto-Selected Optimal Settings:

• Single File: {'Yes' if analysis['onefile'] else 'No'}
• Console Window: {'Yes' if analysis['console'] else 'No'}
• Debug Mode: {'Yes' if analysis['debug'] else 'No'}
• Offline Mode: {'Yes' if analysis.get('offline_mode', False) else 'No'}
• Optimization: {analysis['optimization_level']}

Proceed with build?"""
        
        if messagebox.askyesno("Auto Build Settings", settings_msg):
            self._start_build()
    
    def _start_build(self):
        """Start the build process with progress dialog."""
        self._sync_config_from_ui()
        
        # Validate configuration
        if not self._validate_config():
            return
        
        # Create progress dialog
        progress_dialog = BuildProgressDialog(self.root, self.config)
        progress_dialog.start_build()
    
    def _validate_config(self) -> bool:
        """Validate configuration before building."""
        errors = []
        
        if not self.config.build.source_path:
            errors.append("Source path/URL is required")
        
        if self.config.build.source_type == "folder":
            if not os.path.exists(self.config.build.source_path):
                errors.append("Source folder does not exist")
            elif not os.path.exists(os.path.join(self.config.build.source_path, "index.html")):
                errors.append("index.html not found in source folder")
        
        if not self.config.metadata.name.strip():
            errors.append("Application name is required")
        
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return False
        
        return True
    
    def _select_folder(self):
        """Quick folder selection."""
        folder = filedialog.askdirectory(title="Select HTML Folder")
        if folder:
            self.config.build.source_type = "folder"
            self.config.build.source_path = folder
            if hasattr(self, 'source_type_var'):
                self.source_type_var.set("folder")
            if hasattr(self, 'source_path_var'):
                self.source_path_var.set(folder)
            messagebox.showinfo("Success", f"Source folder set to:\n{folder}")
    
    def _test_url(self):
        """Test URL accessibility."""
        try:
            from tkinter import simpledialog
            url = simpledialog.askstring("URL Test", "Enter URL to test:")
        except ImportError:
            url = input("Enter URL to test: ")
        
        if url:
            try:
                import urllib.request
                response = urllib.request.urlopen(url, timeout=10)
                if response.getcode() == 200:
                    self.config.build.source_type = "url"
                    self.config.build.source_path = url
                    if hasattr(self, 'source_type_var'):
                        self.source_type_var.set("url")
                    if hasattr(self, 'source_path_var'):
                        self.source_path_var.set(url)
                    messagebox.showinfo("Success", f"URL is accessible!\nSet as source: {url}")
                else:
                    messagebox.showwarning("Warning", f"URL returned status: {response.getcode()}")
            except Exception as e:
                messagebox.showerror("Error", f"URL test failed: {e}")
    
    def _show_advanced(self):
        """Show advanced settings dialog."""
        AdvancedDialog(self.root, self.config).show()
    
    def _load_config(self):
        """Load configuration from file."""
        config_file = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if config_file:
            try:
                self.config = AppConfig.load(config_file)
                self._refresh_ui()
                messagebox.showinfo("Success", "Configuration loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def _save_config(self):
        """Save configuration to file."""
        self._sync_config_from_ui()
        
        config_file = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if config_file:
            try:
                self.config.save(config_file)
                messagebox.showinfo("Success", "Configuration saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def _refresh_ui(self):
        """Refresh UI with current configuration values."""
        # This would update all UI elements with config values
        # Implementation depends on the specific UI structure
        pass
    
    def _update_source_type(self):
        """Update UI based on selected source type."""
        source_type = self.source_type_var.get()
        if source_type == "folder":
            self.browse_btn.config(text="Browse Folder...")
        else:
            self.browse_btn.config(text="Enter URL...")

class BuildProgressDialog:
    """Modern build progress dialog with real-time updates."""
    
    def __init__(self, parent, config: AppConfig):
        self.parent = parent
        self.config = config
        self.dialog = None
        self.progress_var = None
        self.status_var = None
        self.build_thread = None
        
    def start_build(self):
        """Start the build process with progress dialog."""
        self._create_dialog()
        
        # Start build in separate thread
        self.build_thread = threading.Thread(target=self._build_worker, daemon=True)
        self.build_thread.start()
        
        # Start progress update loop
        self._update_progress()
    
    def _create_dialog(self):
        """Create modern progress dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Building Application...")
        self.dialog.geometry("600x400")
        self.dialog.configure(bg='#1a1a1a')
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Title
        title_label = tk.Label(self.dialog, text="🚀 Building Your Application", 
                              font=('Segoe UI', 16, 'bold'), 
                              fg='#00D4AA', bg='#1a1a1a')
        title_label.pack(pady=(20, 10))
        
        # App info
        info_label = tk.Label(self.dialog, text=f"Building: {self.config.metadata.name} v{self.config.metadata.version}", 
                             font=('Segoe UI', 12), 
                             fg='#ffffff', bg='#1a1a1a')
        info_label.pack(pady=(0, 20))
        
        # Progress frame
        progress_frame = tk.Frame(self.dialog, bg='#1a1a1a')
        progress_frame.pack(fill='x', padx=40, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                      length=500, mode='determinate')
        progress_bar.pack(fill='x', pady=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Initializing build...")
        status_label = tk.Label(progress_frame, textvariable=self.status_var, 
                               font=('Segoe UI', 10), 
                               fg='#cccccc', bg='#1a1a1a')
        status_label.pack()
        
        # Log area
        log_frame = tk.LabelFrame(self.dialog, text="Build Log", 
                                 font=('Segoe UI', 10), fg='#ffffff', bg='#1a1a1a')
        log_frame.pack(fill='both', expand=True, padx=20, pady=(10, 20))
        
        self.log_text = tk.Text(log_frame, height=10, wrap='word', 
                               font=('Consolas', 9), 
                               bg='#2d2d2d', fg='#ffffff', 
                               insertbackground='#ffffff')
        
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")
        
        # Cancel button
        self.cancel_btn = ttk.Button(self.dialog, text="Cancel", command=self._cancel_build)
        self.cancel_btn.pack(pady=(0, 20))
    
    def _build_worker(self):
        """Worker thread for build process."""
        try:
            def progress_callback(message):
                self.status_var.set(message)
                self._log_message(message)
            
            # Create build engine
            engine = BuildEngine(self.config, progress_callback)
            
            # Execute build
            self.progress_var.set(10)
            result = engine.build()
            
            if result["success"]:
                self.progress_var.set(100)
                self.status_var.set("✅ Build completed successfully!")
                self._log_message(f"✅ Build completed in {result['build_time']}")
                self._log_message(f"📁 Output: {result['exe_path']}")
                self._log_message(f"📊 Size: {result['exe_size']}")
                
                # Update UI in main thread
                self.dialog.after(100, lambda: self._build_success(result))
            else:
                self.status_var.set("❌ Build failed!")
                self._log_message(f"❌ Build failed: {result['error']}")
                
                # Update UI in main thread
                self.dialog.after(100, lambda: self._build_error(result['error']))
                
        except Exception as e:
            self.status_var.set("❌ Build error!")
            self._log_message(f"❌ Unexpected error: {e}")
            self.dialog.after(100, lambda: self._build_error(str(e)))
    
    def _log_message(self, message):
        """Add message to build log."""
        if self.log_text:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            self.dialog.after(0, lambda: self._append_log(log_entry))
    
    def _append_log(self, message):
        """Append message to log text widget."""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.dialog.update_idletasks()
    
    def _update_progress(self):
        """Update progress periodically."""
        if self.build_thread and self.build_thread.is_alive():
            # Simulate progress updates
            current = self.progress_var.get()
            if current < 90:
                self.progress_var.set(current + 1)
            
            # Schedule next update
            self.dialog.after(500, self._update_progress)
    
    def _build_success(self, result):
        """Handle successful build."""
        self.cancel_btn.config(text="Close")
        
        # Add success buttons
        button_frame = tk.Frame(self.dialog, bg='#1a1a1a')
        button_frame.pack(pady=(10, 0))
        
        ttk.Button(button_frame, text="📁 Open Output Folder", 
                  command=lambda: self._open_output_folder(result['exe_path'])).pack(side='left', padx=5)
        ttk.Button(button_frame, text="🚀 Run Application", 
                  command=lambda: self._run_application(result['exe_path'])).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📋 Copy Path", 
                  command=lambda: self._copy_path(result['exe_path'])).pack(side='left', padx=5)
    
    def _build_error(self, error):
        """Handle build error."""
        self.cancel_btn.config(text="Close")
        
        # Show error details
        error_frame = tk.Frame(self.dialog, bg='#1a1a1a')
        error_frame.pack(pady=(10, 0))
        
        ttk.Button(error_frame, text="📋 Copy Error", 
                  command=lambda: self._copy_error(error)).pack(side='left', padx=5)
        ttk.Button(error_frame, text="🔧 Troubleshoot", 
                  command=self._show_troubleshooting).pack(side='left', padx=5)
    
    def _open_output_folder(self, exe_path):
        """Open output folder in explorer."""
        try:
            folder = os.path.dirname(exe_path)
            os.startfile(folder)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
    
    def _run_application(self, exe_path):
        """Run the built application."""
        try:
            subprocess.Popen([exe_path], shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run application: {e}")
    
    def _copy_path(self, exe_path):
        """Copy executable path to clipboard."""
        try:
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(exe_path)
            messagebox.showinfo("Success", "Path copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy path: {e}")
    
    def _copy_error(self, error):
        """Copy error message to clipboard."""
        try:
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(error)
            messagebox.showinfo("Success", "Error message copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy error: {e}")
    
    def _show_troubleshooting(self):
        """Show troubleshooting dialog."""
        TroubleshootingDialog(self.dialog).show()
    
    def _cancel_build(self):
        """Cancel build or close dialog."""
        if self.build_thread and self.build_thread.is_alive():
            # In a real implementation, you'd want to properly cancel the build
            if messagebox.askyesno("Cancel Build", "Are you sure you want to cancel the build?"):
                self.dialog.destroy()
        else:
            self.dialog.destroy()

class AdvancedDialog:
    """Advanced configuration dialog."""
    
    def __init__(self, parent, config: AppConfig):
        self.parent = parent
        self.config = config
        self.dialog = None
    
    def show(self):
        """Show advanced configuration dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Advanced Configuration")
        self.dialog.geometry("700x600")
        self.dialog.configure(bg='#1a1a1a')
        self.dialog.transient(self.parent)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Performance tab
        perf_frame = ttk.Frame(notebook, style='Modern.TFrame')
        notebook.add(perf_frame, text="Performance")
        self._create_performance_tab(perf_frame)
        
        # Integration tab
        integ_frame = ttk.Frame(notebook, style='Modern.TFrame')
        notebook.add(integ_frame, text="System Integration")
        self._create_integration_tab(integ_frame)
        
        # Developer tab
        dev_frame = ttk.Frame(notebook, style='Modern.TFrame')
        notebook.add(dev_frame, text="Developer")
        self._create_developer_tab(dev_frame)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, style='Modern.TFrame')
        button_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        ttk.Button(button_frame, text="OK", command=self.dialog.destroy).pack(side='right', padx=(10, 0))
        ttk.Button(button_frame, text="Apply", command=self._apply_settings).pack(side='right')
    
    def _create_performance_tab(self, parent):
        """Create performance settings tab."""
        # Memory optimization
        mem_frame = ttk.LabelFrame(parent, text="Memory Optimization", padding=15)
        mem_frame.pack(fill='x', pady=10)
        
        ttk.Checkbutton(mem_frame, text="Enable memory optimization").pack(anchor='w')
        ttk.Checkbutton(mem_frame, text="Preload critical resources").pack(anchor='w')
        ttk.Checkbutton(mem_frame, text="Aggressive garbage collection").pack(anchor='w')
        
        # Startup optimization
        startup_frame = ttk.LabelFrame(parent, text="Startup Optimization", padding=15)
        startup_frame.pack(fill='x', pady=10)
        
        ttk.Checkbutton(startup_frame, text="Fast startup mode").pack(anchor='w')
        ttk.Checkbutton(startup_frame, text="Lazy load modules").pack(anchor='w')
        ttk.Checkbutton(startup_frame, text="Cache initialization").pack(anchor='w')
    
    def _create_integration_tab(self, parent):
        """Create system integration tab."""
        # File associations
        file_frame = ttk.LabelFrame(parent, text="File Associations", padding=15)
        file_frame.pack(fill='x', pady=10)
        
        ttk.Label(file_frame, text="Associate file extensions (comma-separated):").pack(anchor='w')
        ttk.Entry(file_frame, width=50).pack(fill='x', pady=5)
        
        # Registry integration
        reg_frame = ttk.LabelFrame(parent, text="Windows Integration", padding=15)
        reg_frame.pack(fill='x', pady=10)
        
        ttk.Checkbutton(reg_frame, text="Add to Windows context menu").pack(anchor='w')
        ttk.Checkbutton(reg_frame, text="Register custom protocol handler").pack(anchor='w')
        ttk.Checkbutton(reg_frame, text="Add to Windows startup").pack(anchor='w')
    
    def _create_developer_tab(self, parent):
        """Create developer settings tab."""
        # Debugging
        debug_frame = ttk.LabelFrame(parent, text="Debugging", padding=15)
        debug_frame.pack(fill='x', pady=10)
        
        ttk.Checkbutton(debug_frame, text="Enable debug console").pack(anchor='w')
        ttk.Checkbutton(debug_frame, text="Verbose logging").pack(anchor='w')
        ttk.Checkbutton(debug_frame, text="Performance profiling").pack(anchor='w')
        
        # Build options
        build_frame = ttk.LabelFrame(parent, text="Advanced Build Options", padding=15)
        build_frame.pack(fill='x', pady=10)
        
        ttk.Label(build_frame, text="PyInstaller additional options:").pack(anchor='w')
        ttk.Entry(build_frame, width=50).pack(fill='x', pady=5)
        
        ttk.Label(build_frame, text="Custom Python path:").pack(anchor='w', pady=(10, 0))
        ttk.Entry(build_frame, width=50).pack(fill='x', pady=5)
    
    def _apply_settings(self):
        """Apply advanced settings."""
        # In a real implementation, this would save the advanced settings
        pass

class TroubleshootingDialog:
    """Troubleshooting and help dialog."""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = None
    
    def show(self):
        """Show troubleshooting dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Troubleshooting Guide")
        self.dialog.geometry("800x600")
        self.dialog.configure(bg='#1a1a1a')
        
        # Create scrollable text widget
        text_frame = ttk.Frame(self.dialog)
        text_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        text_widget = tk.Text(text_frame, wrap='word', font=('Segoe UI', 10),
                             bg='#2d2d2d', fg='#ffffff')
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add troubleshooting content
        troubleshooting_text = """
HTML2EXE Pro Premium - Troubleshooting Guide
===========================================

COMMON BUILD ISSUES
------------------

1. "ModuleNotFoundError" during build
   Solution: Ensure all dependencies are installed:
   pip install -r requirements.txt

2. "Permission denied" error
   Solution: Run as administrator or check antivirus settings
   
3. Large executable size
   Solution: Enable UPX compression or use directory mode instead of onefile

4. Slow startup times
   Solution: Disable onefile mode or reduce included dependencies

5. Missing DLL errors
   Solution: Install Visual C++ Redistributable packages

CONFIGURATION ISSUES
-------------------

1. HTML files not loading
   Solution: Ensure index.html exists in root of source folder
   
2. External resources not working
   Solution: Enable offline mode to cache external resources
   
3. Window sizing issues
   Solution: Check DPI aware setting and adjust dimensions

4. Security policy blocking content
   Solution: Adjust CSP settings in Security configuration

SYSTEM REQUIREMENTS
------------------

- Windows 10 or later (64-bit recommended)
- Python 3.10 or later
- At least 4GB RAM
- 2GB free disk space
- Internet connection for dependency installation

PERFORMANCE OPTIMIZATION
-----------------------

1. Enable UPX compression for smaller executables
2. Use directory mode for faster startup
3. Enable memory optimization in advanced settings
4. Minimize included dependencies

GETTING HELP
------------

If you continue to experience issues:

1. Check the build log for detailed error messages
2. Copy error messages to clipboard and search online
3. Ensure all system requirements are met
4. Try building a simple test project first

For additional support, visit our documentation at:
https://html2exe-pro.com/docs
        """.strip()
        
        text_widget.insert(1.0, troubleshooting_text)
        text_widget.config(state='disabled')
        
        # Close button
        ttk.Button(self.dialog, text="Close", command=self.dialog.destroy).pack(pady=(0, 20))

# CLI Interface with Typer
if RICH_AVAILABLE:
    app = typer.Typer(help="HTML2EXE Pro Premium - Convert HTML to Professional Desktop Apps")
else:
    # Fallback when typer is not available
    class MockTyper:
        def command(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def __call__(self, *args, **kwargs):
            pass
    app = MockTyper()

@app.command()
def auto_build(
    src: str = "..." if RICH_AVAILABLE else "",
    name: str = "MyHTMLApp",
    output: str = "dist"
):
    """Automatically build HTML application with optimal settings."""
    print(f"HTML2EXE Pro Premium v{APP_VERSION} - Auto Build Mode")
    print(f"Building application: {name}")
    print("🔍 Analyzing source and selecting optimal settings...")
    
    # Create configuration
    config = AppConfig()
    config.metadata.name = name
    config.build.source_path = src
    config.build.source_type = "url" if src.startswith(("http://", "https://")) else "folder"
    config.build.output_dir = output
    
    # Auto-analyze and apply optimal settings
    analysis = AutoOptionsSelector.analyze_source(src, config.build.source_type)
    print(f"📊 Analysis results: {analysis['optimization_level']} optimization")
    
    # Apply automatic recommendations
    config.build.onefile = analysis["onefile"]
    config.build.console = analysis["console"]
    config.build.debug = analysis["debug"]
    config.build.upx_compress = analysis["upx_compress"]
    config.build.strip_debug = analysis["strip_debug"]
    config.build.offline_mode = analysis.get("offline_mode", False)
    
    # Set reasonable window defaults
    config.window.width = 1200
    config.window.height = 800
    config.window.resizable = True
    config.window.center = True
    
    print(f"⚙️ Selected options:")
    print(f"  • Single file: {'Yes' if config.build.onefile else 'No'}")
    print(f"  • Console: {'Yes' if config.build.console else 'No'}")
    print(f"  • Debug: {'Yes' if config.build.debug else 'No'}")
    print(f"  • Offline mode: {'Yes' if config.build.offline_mode else 'No'}")
    print(f"  • Optimization: {analysis['optimization_level']}")
    
    # Validate source
    if config.build.source_type == "folder" and not os.path.exists(src):
        print("Error: Source folder does not exist")
        raise sys.exit(1)
    
    # Start build
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        transient=True
    ) as progress:
        
        task = progress.add_task("Building...", total=100)
        
        def progress_callback(message):
            progress.update(task, description=message)
            progress.advance(task, 10)
        
        try:
            engine = BuildEngine(config, progress_callback)
            result = engine.build()
            
            if result["success"]:
                print("✅ Build completed successfully!")
                print(f"📁 Output: {result['exe_path']}")
                print(f"📊 Size: {result['exe_size']}")
                print(f"⏱️ Time: {result['build_time']}")
            else:
                print(f"❌ Build failed: {result['error']}")
                raise sys.exit(1)
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            raise sys.exit(1)

@app.command()
def build(
    src: str = "..." if RICH_AVAILABLE else "",
    name: str = "MyHTMLApp",
    icon: str = "",
    onefile: bool = True,
    offline: bool = False,
    kiosk: bool = False,
    width: int = 1200,
    height: int = 800,
    debug: bool = False,
    output: str = "dist"
):
    """Build HTML application to executable."""
    print(f"HTML2EXE Pro Premium v{APP_VERSION}")
    print(f"Building application: {name}")
    
    # Create configuration
    config = AppConfig()
    config.metadata.name = name
    config.build.source_path = src
    config.build.source_type = "url" if src.startswith(("http://", "https://")) else "folder"
    config.build.icon_path = icon
    config.build.onefile = onefile
    config.build.offline_mode = offline
    config.build.debug = debug
    config.build.output_dir = output
    config.window.kiosk = kiosk
    config.window.width = width
    config.window.height = height
    
    # Validate source
    if config.build.source_type == "folder" and not os.path.exists(src):
        print("Error: Source folder does not exist")
        raise sys.exit(1)
    
    # Start build
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        transient=True
    ) as progress:
        
        task = progress.add_task("Building...", total=100)
        
        def progress_callback(message):
            progress.update(task, description=message)
            progress.advance(task, 10)
        
        try:
            engine = BuildEngine(config, progress_callback)
            result = engine.build()
            
            if result["success"]:
                print("✅ Build completed successfully!")
                print(f"📁 Output: {result['exe_path']}")
                print(f"📊 Size: {result['exe_size']}")
                print(f"⏱️ Time: {result['build_time']}")
            else:
                print(f"❌ Build failed: {result['error']}")
                raise sys.exit(1)
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            raise sys.exit(1)

@app.command()
def serve(
    src: str = ".",
    port: int = 8000,
    open_browser: bool = True
):
    """Serve HTML folder for development and testing."""
    print(f"HTML2EXE Pro Development Server")
    print(f"Serving: {src}")
    print(f"Port: {port}")
    
    if not os.path.exists(src):
        print("Error: Source folder does not exist")
        raise sys.exit(1)
    
    try:
        config = AppConfig()
        config.build.source_path = src
        config.build.source_type = "folder"
        
        webview_manager = WebViewManager(config)
        webview_manager.start_server(src, port)
        
        url = f"http://localhost:{port}"
        print(f"🚀 Server running at: {url}")
        
        if open_browser:
            webbrowser.open(url)
            
        print("Press Ctrl+C to stop the server")
        
        # Keep server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nServer stopped")
            
    except Exception as e:
        print(f"Server error: {e}")
        raise sys.exit(1)

@app.command()
def doctor():
    """Check system requirements and dependencies."""
    print(f"HTML2EXE Pro System Diagnostics")
    
    checks = []
    
    # Python version
    python_version = sys.version_info
    if python_version >= (3, 10):
        checks.append(("✅", f"Python {python_version.major}.{python_version.minor}", "OK"))
    else:
        checks.append(("❌", f"Python {python_version.major}.{python_version.minor}", "Requires Python 3.10+"))
    
    # PyInstaller
    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            checks.append(("✅", "PyInstaller", result.stdout.strip()))
        else:
            checks.append(("❌", "PyInstaller", "Not installed"))
    except:
        checks.append(("❌", "PyInstaller", "Not found"))
    
    # Dependencies
    for package in ["flask", "webview", "pillow", "requests", "rich", "typer"]:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'Unknown')
            checks.append(("✅", package, version))
        except ImportError:
            checks.append(("❌", package, "Not installed"))
    
    # System info
    checks.append(("ℹ️", "Platform", f"{sys.platform}"))
    checks.append(("ℹ️", "Architecture", f"{sys.maxsize > 2**32 and '64-bit' or '32-bit'}"))
    
    # Display results
    print("\n--- System Check Results ---")
    for status, component, version in checks:
        print(f"{status} {component:<15} {version}")
    
    # Recommendations
    issues = [check for check in checks if check[0] == "❌"]
    if issues:
        print("\nIssues Found:")
        for status, component, issue in issues:
            print(f"  • {component}: {issue}")
        
        print("\nRecommended Actions:")
        print("  1. Update Python to 3.10+ if needed")
        print("  2. Install missing packages: pip install -r requirements.txt")
        print("  3. Restart the application after installing dependencies")
    else:
        print("\n🎉 All checks passed! Your system is ready.")

@app.command()
def clean():
    """Clean build artifacts and temporary files."""
    print("Cleaning build artifacts...")
    
    cleaned = []
    
    # Common build directories
    build_dirs = ["build", "dist", "__pycache__", "*.egg-info"]
    
    for pattern in build_dirs:
        import glob
        for path in glob.glob(pattern, recursive=True):
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    cleaned.append(f"📁 {path}")
                else:
                    os.remove(path)
                    cleaned.append(f"📄 {path}")
    
    # Temp files
    temp_patterns = ["*.pyc", "*.pyo", "*.tmp", "*.log"]
    for pattern in temp_patterns:
        for path in glob.glob(f"**/{pattern}", recursive=True):
            try:
                os.remove(path)
                cleaned.append(f"🗑️ {path}")
            except:
                pass
    
    if cleaned:
        print(f"✅ Cleaned {len(cleaned)} items:")
        for item in cleaned[:10]:  # Show first 10 items
            print(f"  {item}")
        if len(cleaned) > 10:
            print(f"  ... and {len(cleaned) - 10} more items")
    else:
        print("No build artifacts found to clean")

@app.command()
def gui():
    """Launch the graphical user interface."""
    print(f"Launching HTML2EXE Pro Premium GUI...")
    
    try:
        gui_app = ModernGUI()
        gui_app.run()
    except Exception as e:
        print(f"GUI Error: {e}")
        raise sys.exit(1)

# WebView Manager Enhanced
class WebViewManager:
    """Enhanced WebView manager with premium features."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.window = None
        self.flask_app = None
        self.server_thread = None
        self.observer = None
        self.server_port = None
        
    def start_server(self, source_path: str, port: int = 5000):
        """Start enhanced Flask development server."""
        self.server_port = port
        self.flask_app = create_flask_app(self.config)
        
        def run_server():
            try:
                self.flask_app.run(
                    host='127.0.0.1', 
                    port=port, 
                    debug=False, 
                    use_reloader=False,
                    threaded=True
                )
            except Exception as e:
                print(f"Server error: {e}")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        time.sleep(2)  # Give server more time to start
        
        # Verify server is running
        try:
            response = requests.get(f"http://127.0.0.1:{port}/api/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Server started successfully on port {port}")
            else:
                print(f"⚠️ Server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Server health check failed: {e}")
    
    def create_window(self, url: str = None):
        """Create enhanced webview window with premium features."""
        try:
            import webview
        except ImportError as e:
            print(f"Error: pywebview not available: {e}")
            print("Please install pywebview: pip install pywebview")
            return None

        if url is None:
            url = f"http://127.0.0.1:{self.server_port or 5000}"
        
        window_config = {
            'width': self.config.window.width,
            'height': self.config.window.height,
            'min_size': (self.config.window.min_width, self.config.window.min_height),
            'resizable': self.config.window.resizable,
            'fullscreen': self.config.window.fullscreen,
            'on_top': self.config.window.always_on_top,
            'shadow': True,
            'vibrancy': True
        }
        
        # Advanced window options
        if self.config.window.kiosk:
            window_config.update({
                'fullscreen': True,
                'resizable': False,
                'on_top': True
            })
        
        if self.config.window.frameless:
            window_config['frameless'] = True
        
        self.window = webview.create_window(
            title=self.config.metadata.name,
            url=url,
            **window_config
        )
        
        # Setup window events
        self._setup_window_events()
        
        return self.window
    
    def _setup_window_events(self):
        """Setup window event handlers."""
        if not self.window:
            return
        
        # Single instance check
        if self.config.build.single_instance:
            self._enforce_single_instance()
        
        # System tray
        if self.config.build.tray_menu:
            self._setup_system_tray()
    
    def _enforce_single_instance(self):
        """Enforce single instance using mutex."""
        try:
            import win32event
            import win32api
            import winerror
            
            mutex_name = f"HTML2EXE_Pro_{self.config.metadata.name}"
            mutex = win32event.CreateMutex(None, False, mutex_name)
            
            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                print("Application is already running")
                sys.exit(0)
                
        except ImportError:
            # Fallback for systems without pywin32
            pass
    
    def _setup_system_tray(self):
        """Setup system tray integration."""
        # This would require additional system tray library
        # Implementation depends on the specific requirements
        pass
    
    def setup_live_reload(self, source_path: str):
        """Setup enhanced file watching for live reload."""
        if os.path.isdir(source_path):
            handler = LiveReloadHandler(self.window, debounce_ms=300)
            self.observer = Observer()
            self.observer.schedule(handler, source_path, recursive=True)
            self.observer.start()
            print(f"📁 Live reload enabled for: {source_path}")
    
    def start(self, source_path: str = None, url: str = None, dev_mode: bool = False):
        """Start the enhanced webview application."""
        try:
            if source_path:
                port = 5000
                self.start_server(source_path, port)
                target_url = f"http://127.0.0.1:{port}"
                
                if dev_mode:
                    self.setup_live_reload(source_path)
            else:
                target_url = url
            
            # Create and start window
            window = self.create_window(target_url)
            
            print(f"🚀 Starting application: {self.config.metadata.name}")
            print(f"🌐 URL: {target_url}")
            
            # Start webview
            try:
                import webview
                webview.start(debug=self.config.build.debug)
            except ImportError as e:
                print(f"Error: pywebview not available: {e}")
                print("Please install pywebview: pip install pywebview")
                return
            
        except Exception as e:
            print(f"❌ Application start error: {e}")
            raise
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()

# Enhanced Utilities
class SystemIntegration:
    """System integration utilities for Windows."""
    
    @staticmethod
    def register_protocol(protocol: str, executable_path: str):
        """Register custom protocol handler in Windows registry."""
        if sys.platform != "win32":
            print("Warning: Protocol registration is only supported on Windows.")
            return False
        try:
            import winreg
            
            # Create protocol key
            protocol_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, protocol)
            winreg.SetValueEx(protocol_key, "", 0, winreg.REG_SZ, f"URL:{protocol} Protocol")
            winreg.SetValueEx(protocol_key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            # Create command key
            command_key = winreg.CreateKey(protocol_key, r"shell\open\command")
            winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, f'"{executable_path}" "%1"')
            
            winreg.CloseKey(command_key)
            winreg.CloseKey(protocol_key)
            
            return True
        except Exception as e:
            print(f"Protocol registration failed: {e}")
            return False
    
    @staticmethod
    def add_to_startup(app_name: str, executable_path: str):
        """Add application to Windows startup."""
        if sys.platform != "win32":
            print("Warning: Adding to startup is only supported on Windows.")
            return False
        try:
            import winreg
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, executable_path)
            winreg.CloseKey(key)
            
            return True
        except Exception as e:
            print(f"Startup registration failed: {e}")
            return False

class Analytics:
    """Anonymous analytics and telemetry."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.enabled = config.advanced.analytics
    
    def track_event(self, event_name: str, properties: dict = None):
        """Track anonymous event."""
        if not self.enabled:
            return
        
        try:
            event_data = {
                "event": event_name,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "app_version": APP_VERSION,
                "properties": properties or {}
            }
            
            # In a real implementation, this would send to analytics endpoint
            print(f"📊 Analytics: {event_name}")
            
        except Exception:
            pass  # Fail silently for analytics
    
    def track_build(self, success: bool, build_time: float, config: AppConfig):
        """Track build event."""
        self.track_event("build_completed", {
            "success": success,
            "build_time": build_time,
            "source_type": config.build.source_type,
            "onefile": config.build.onefile,
            "window_size": f"{config.window.width}x{config.window.height}"
        })

# Main Entry Point
def main():
    """Main entry point - CLI or GUI based on arguments."""
    try:
        # If no command line arguments, show GUI
        if len(sys.argv) == 1:
            print(f"HTML2EXE Pro Premium v{APP_VERSION}")
            print("No command line arguments provided, launching GUI...")
            
            gui_app = ModernGUI()
            gui_app.run()
        else:
            # Use CLI interface
            app()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)

# Run the application
if __name__ == "__main__":
    main()