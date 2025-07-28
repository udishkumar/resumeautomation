"""
Simple Setup Script for LaTeX Resume Automation Tool
Run this first to ensure all dependencies are installed correctly
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_api_key(api_key):
    """Test the API key separately to avoid string formatting issues"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Using Haiku for testing (cheapest)
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        return True, "API key is valid!"
    except Exception as e:
        return False, f"API key test failed: {str(e)[:100]}"

def main():
    print("=" * 60)
    print("LaTeX Resume Automation Tool - Setup Script")
    print("=" * 60)
    print()
    
    # Check Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 6):
        print("⚠ WARNING: Python 3.6 or higher is recommended")
    print()
    
    # Upgrade pip first
    print("1. Upgrading pip...")
    success, stdout, stderr = run_command(f"{sys.executable} -m pip install --upgrade pip")
    if success:
        print("   ✓ Pip upgraded successfully")
    else:
        print("   ⚠ Warning: Could not upgrade pip")
        if stderr:
            print(f"   Error: {stderr}")
    print()
    
    # Install packages one by one
    packages = [
        ("anthropic", "Claude AI API - Required for resume optimization"),
    ]
    
    print("2. Installing required packages...")
    failed_packages = []
    
    for package_info in packages:
        if package_info is None:
            continue
            
        package, description = package_info
        print(f"   Installing {package} ({description})...")
        
        success, stdout, stderr = run_command(f"{sys.executable} -m pip install {package}")
        
        if success:
            print(f"   ✓ {package} installed successfully")
            
            # Verify installation
            try:
                if package == "anthropic":
                    import anthropic
                    version = anthropic.__version__ if hasattr(anthropic, '__version__') else "OK"
                    print(f"     Version: {package} version: {version}")
            except Exception as e:
                print(f"     Could not verify version: {e}")
        else:
            print(f"   ✗ Failed to install {package}")
            if stderr:
                print(f"   Error: {stderr}")
            failed_packages.append(package)
        print()
    
    # Check for tkinter (built-in but sometimes missing)
    print("3. Checking built-in dependencies...")
    try:
        import tkinter
        print("   ✓ tkinter is available (GUI support)")
    except ImportError:
        print("   ✗ tkinter is not available")
        print("   Note: tkinter should come with Python. You may need to:")
        print("   - On Ubuntu/Debian: sudo apt-get install python3-tk")
        print("   - On Fedora: sudo dnf install python3-tkinter")
        print("   - On macOS: tkinter should be included with Python")
        print("   - On Windows: Reinstall Python and ensure tkinter is selected")
    print()
    
    # Create required directories
    print("4. Creating directory for LaTeX templates...")
    try:
        os.makedirs("latex_templates", exist_ok=True)
        print("   ✓ Created 'latex_templates/' - Store your LaTeX resume templates here")
    except Exception as e:
        print(f"   ✗ Failed to create 'latex_templates': {e}")
    print()
    
    # Create the input resume template
    print("5. Creating input_resume.tex file...")
    input_resume_template = r"""%-------------------------
% Your Resume Template
% Place your actual resume content here
%------------------------

\documentclass[letterpaper,10pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage{tabularx}

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\begin{document}

\begin{center}
    {\Huge \scshape Your Name} \\ \vspace{1pt}
    your.email@example.com | (123) 456-7890 | LinkedIn: linkedin.com/in/yourprofile
\end{center}

\section{Summary}
Software Engineer with X years of experience...

\section{Experience}
\textbf{Company Name} - Job Title \\
Location | Dates
\begin{itemize}
    \item Achievement 1
    \item Achievement 2
\end{itemize}

\section{Education}
\textbf{University Name} \\
Degree | Dates

\section{Skills}
Programming Languages: Python, Java, JavaScript \\
Technologies: React, Node.js, AWS

\end{document}
"""
    
    # Create input_resume.tex in the root directory
    input_resume_path = "input_resume.tex"
    try:
        # Check if file already exists
        if os.path.exists(input_resume_path):
            print(f"   ⚠ {input_resume_path} already exists - skipping creation")
            print("     (Your existing resume is preserved)")
        else:
            with open(input_resume_path, "w", encoding="utf-8") as f:
                f.write(input_resume_template)
            print(f"   ✓ Created {input_resume_path}")
            print("     IMPORTANT: Replace the content of this file with your actual resume!")
    except Exception as e:
        print(f"   ✗ Failed to create input resume: {e}")
    
    # Also create a sample template in the templates folder
    template_path = os.path.join("latex_templates", "sample_template.tex")
    try:
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(input_resume_template)
        print(f"   ✓ Created sample template: {template_path}")
    except Exception as e:
        print(f"   ✗ Failed to create sample template: {e}")
    print()
    
    # Summary
    print("=" * 60)
    print("Setup Summary:")
    print("=" * 60)
    
    if not failed_packages:
        print("✓ All packages installed successfully!")
        print()
        print("Next steps:")
        print("1. Get your Claude API key from https://console.anthropic.com")
        print("2. IMPORTANT: Edit 'input_resume.tex' with your actual resume content")
        print("3. Run the main script: python resume_automation_fixed.py")
        print()
        print("The tool will automatically read from 'input_resume.tex'")
        print("No need to manually load templates anymore!")
        print()
        print("Benefits of this version:")
        print("- Automatic resume loading from input_resume.tex")
        print("- No manual copy-paste required")
        print("- Direct Overleaf compatibility")
        print("- Professional PDF output")
    else:
        print(f"⚠ Some packages failed to install: {', '.join(failed_packages)}")
        print()
        print("Try installing them manually:")
        for package in failed_packages:
            print(f"   pip install {package}")
        print()
        print("If you're still having issues, try:")
        print("1. Use a virtual environment:")
        print("   python -m venv resume_env")
        if sys.platform == "win32":
            print("   resume_env\\Scripts\\activate (Windows)")
        else:
            print("   source resume_env/bin/activate (Mac/Linux)")
        print("   pip install anthropic")
    
    print()
    
    # Test API key if provided
    print("Optional: Test your Claude API key")
    print("Enter your API key (or press Enter to skip): ", end="", flush=True)
    
    try:
        api_key = input().strip()
    except (KeyboardInterrupt, EOFError):
        print("\nSkipping API key test...")
        api_key = ""
    
    if api_key:
        print("Testing API key...")
        # Import anthropic here to avoid issues if not installed
        try:
            import anthropic
            success, message = test_api_key(api_key)
            if success:
                print(f"   ✓ {message}")
            else:
                print(f"   ✗ {message}")
        except ImportError:
            print("   ✗ Cannot test API key: anthropic package not installed")
        except Exception as e:
            print(f"   ✗ Unexpected error: {e}")
    
    print()
    print("Setup complete! Press Enter to exit...")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        print("Please report this issue if it persists.")