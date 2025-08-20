"""
Resume Automation Tool - LaTeX Version
Generates LaTeX code for tailored resumes using Claude API
Automatically reads from templates and generates PDFs
"""

import os
import sys
import subprocess
from subprocess import TimeoutExpired
import json
import time
from datetime import datetime
from pathlib import Path
import re
import threading
import tempfile
import shutil
import base64
import configparser

# First, let's check and install dependencies
def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except:
        return False

def check_and_install_dependencies():
    """Check and install all required dependencies"""
    print("Checking dependencies...")
    
    dependencies = {
        'anthropic': 'anthropic',
        'tkinter': None  # Built-in, no need to install
    }
    
    missing = []
    
    for module, package in dependencies.items():
        if package is None:
            continue
        try:
            __import__(module)
            print(f"✓ {module} is installed")
        except ImportError:
            print(f"✗ {module} is missing, installing {package}...")
            if install_package(package):
                print(f"✓ Successfully installed {package}")
            else:
                missing.append(package)
    
    if missing:
        print(f"\nError: Could not install: {', '.join(missing)}")
        print("Please try installing manually with:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

# Check dependencies before importing
if not check_and_install_dependencies():
    print("\nPress Enter to exit...")
    input()
    sys.exit(1)

# Now import everything
try:
    import anthropic
    import tkinter as tk
    from tkinter import ttk, scrolledtext, filedialog, messagebox
    import math  # Add math import for spinner
except Exception as e:
    print(f"Unexpected error during imports: {e}")
    sys.exit(1)

class LaTeXResumeOptimizer:
    """Main class for LaTeX resume optimization"""
    
    def __init__(self):
        self.client = None
        self.api_key = None
        self.latex_template = None
        self.model_choice = "claude-sonnet-4-20250514"  # Default to Sonnet 4
        self.templates_dir = "resume_templates"
        self.output_dir = "generated_resumes"
        self.available_templates = {}
        self.current_template_type = None
        self.candidate_name = None
        self.config_file = "config.ini"
        
        # Create directories if they don't exist
        self.setup_directories()
        
        # Load available templates
        self.load_available_templates()
        
        # Load API key from config if exists
        self.load_api_key_from_config()
    
    def load_api_key_from_config(self):
        """Load and decrypt API key from config file"""
        if os.path.exists(self.config_file):
            try:
                config = configparser.ConfigParser()
                config.read(self.config_file)
                
                if 'API' in config and 'key' in config['API']:
                    encrypted_key = config['API']['key']
                    # Decrypt base64 encoded key
                    self.api_key = base64.b64decode(encrypted_key.encode()).decode('utf-8')
                    print("API key loaded from config file")
                    return True
            except Exception as e:
                print(f"Error loading API key from config: {e}")
        return False
    
    def save_api_key_to_config(self, api_key):
        """Encrypt and save API key to config file"""
        try:
            # Encrypt key using base64
            encrypted_key = base64.b64encode(api_key.encode()).decode('utf-8')
            
            config = configparser.ConfigParser()
            if os.path.exists(self.config_file):
                config.read(self.config_file)
            
            if 'API' not in config:
                config['API'] = {}
            
            config['API']['key'] = encrypted_key
            
            with open(self.config_file, 'w') as f:
                config.write(f)
            
            print("API key saved to config file")
            return True
        except Exception as e:
            print(f"Error saving API key to config: {e}")
            return False
    
    def setup_directories(self):
        """Create necessary directories"""
        dirs = [self.templates_dir, self.output_dir]
        for dir_name in dirs:
            if not os.path.exists(dir_name):
                try:
                    os.makedirs(dir_name)
                    print(f"Created {dir_name} directory")
                except Exception as e:
                    print(f"Error creating {dir_name}: {e}")
    
    def load_available_templates(self):
        """Load all .tex files from templates directory"""
        self.available_templates = {}
        if os.path.exists(self.templates_dir):
            print(f"Scanning directory: {self.templates_dir}")
            files = os.listdir(self.templates_dir)
            print(f"Files found: {files}")
            
            for file in files:
                if file.endswith('.tex'):
                    template_name = file.replace('.tex', '')
                    file_path = os.path.join(self.templates_dir, file)
                    
                    # Determine template type from filename
                    if 'new_grad' in template_name.lower() or 'newgrad' in template_name.lower():
                        template_type = "new_grad"
                    elif 'experienced' in template_name.lower() or 'sde' in template_name.lower():
                        template_type = "experienced"
                    else:
                        template_type = "general"
                    
                    self.available_templates[template_name] = {
                        'path': file_path,
                        'type': template_type
                    }
                    print(f"Added template: {template_name} (type: {template_type})")
            
            print(f"Total templates found: {len(self.available_templates)}")
        else:
            print(f"Warning: {self.templates_dir} directory not found")
    
    def load_template_by_name(self, template_name):
        """Load a specific template by name"""
        print(f"Attempting to load template: {template_name}")
        
        if template_name not in self.available_templates:
            print(f"Error: Template '{template_name}' not found in available templates")
            print(f"Available templates: {list(self.available_templates.keys())}")
            return False
            
        template_info = self.available_templates[template_name]
        file_path = template_info['path']
        
        print(f"Loading from path: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"Error: File does not exist: {file_path}")
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.latex_template = f.read()
            self.current_template_type = template_info['type']
            print(f"Successfully loaded template: {template_name} (type: {self.current_template_type})")
            print(f"Template content length: {len(self.latex_template)} characters")
            return True
        except Exception as e:
            print(f"Error loading template {template_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_model(self, model_choice):
        """Set the Claude model to use"""
        self.model_choice = model_choice
        
    def setup_claude_api(self, api_key):
        """Initialize Claude API client"""
        try:
            self.api_key = api_key
            self.client = anthropic.Anthropic(api_key=api_key)
            # Test the API key
            test_message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception as e:
            print(f"Error setting up Claude API: {e}")
            return False
    
    def extract_candidate_name(self, latex_content):
        """Extract candidate name from LaTeX resume"""
        # Try to find name in common patterns
        patterns = [
            r'\\Huge\s+\\scshape\s+([^}]+)}',  # {\Huge \scshape Name}
            r'\\Large\s+\\scshape\s+([^}]+)}',  # {\Large \scshape Name}
            r'\\textbf\{([^}]+)\}.*\\\\.*email',  # \textbf{Name} followed by email
            r'\\name\{([^}]+)\}',  # \name{Name}
        ]
        
        for pattern in patterns:
            match = re.search(pattern, latex_content)
            if match:
                name = match.group(1).strip()
                # Clean up any LaTeX commands
                name = re.sub(r'\\[a-zA-Z]+', '', name).strip()
                # Replace spaces with underscores for filename
                self.candidate_name = name.replace(' ', '_').upper()
                return self.candidate_name
        
        # Default if no name found
        self.candidate_name = "RESUME"
        return self.candidate_name
    
    def compile_latex_to_pdf(self, latex_content, company_name):
        """Compile LaTeX to PDF and save with proper naming"""
        try:
            # Extract candidate name
            candidate_name = self.extract_candidate_name(latex_content)
            
            # Create filename
            date_str = datetime.now().strftime("%b%d")
            safe_company = re.sub(r'[^a-zA-Z0-9_-]', '_', company_name.strip())
            filename_base = f"{candidate_name}_{safe_company}_{date_str}"
            
            print(f"\nStarting PDF compilation for: {filename_base}")
            
            # Create temp directory for compilation
            with tempfile.TemporaryDirectory() as temp_dir:
                tex_path = os.path.join(temp_dir, f"{filename_base}.tex")
                
                # Write LaTeX content
                with open(tex_path, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                print(f"LaTeX file written to: {tex_path}")
                
                # Detect if this is a moderncv document
                is_moderncv = '\\moderncvstyle{' in latex_content or '\\moderncvcolor{' in latex_content
                
                # Choose compiler order based on document type
                if is_moderncv:
                    # For moderncv, xelatex and lualatex handle colors better
                    compilers = ['xelatex', 'lualatex', 'pdflatex']
                    print("Detected moderncv document - prioritizing xelatex/lualatex for color support")
                else:
                    # For other documents, pdflatex is usually fine
                    compilers = ['pdflatex', 'xelatex', 'lualatex']
                
                compiled = False
                compilation_errors = []
                
                for compiler in compilers:
                    print(f"\nTrying {compiler}...")
                    try:
                        # Check if compiler exists
                        check_result = subprocess.run([compiler, '--version'], 
                                                    capture_output=True, text=True, timeout=30)
                        if check_result.returncode != 0:
                            print(f"{compiler} not found or not working")
                            continue
                        
                        # Compiler-specific arguments for moderncv color support
                        if is_moderncv:
                            if compiler == 'xelatex':
                                compile_args = [compiler, '-interaction=nonstopmode', 
                                              '-halt-on-error', '-shell-escape', tex_path]
                            elif compiler == 'lualatex':
                                compile_args = [compiler, '-interaction=nonstopmode', 
                                              '-halt-on-error', '-shell-escape', tex_path]
                            else:  # pdflatex
                                compile_args = [compiler, '-interaction=nonstopmode', 
                                              '-halt-on-error', '-shell-escape', tex_path]
                        else:
                            compile_args = [compiler, '-interaction=nonstopmode', 
                                          '-halt-on-error', tex_path]
                        
                        print(f"  Using command: {' '.join(compile_args)}")
                        
                        # Run compiler twice for references and proper color rendering
                        for run in range(2):
                            print(f"  Run {run + 1} of 2...")
                            result = subprocess.run(
                                compile_args,
                                cwd=temp_dir,
                                capture_output=True,
                                text=True,
                                timeout=120  # Increased timeout for color processing
                            )
                            
                            if result.returncode != 0:
                                error_msg = f"{compiler} failed with return code {result.returncode}"
                                print(f"  {error_msg}")
                                
                                # Extract error from log with focus on color/package issues
                                if result.stdout:
                                    lines = result.stdout.split('\n')
                                    for i, line in enumerate(lines):
                                        if any(keyword in line.lower() for keyword in 
                                             ['error', '!', 'undefined', 'package', 'color', 'moderncv']):
                                            error_details = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                                            print(f"  Error details:\n{error_details}")
                                            compilation_errors.append(f"{compiler}: {error_details}")
                                            break
                                
                                if result.stderr:
                                    print(f"  Stderr: {result.stderr[:500]}")
                                break
                            else:
                                print(f"  Run {run + 1} completed successfully")
                        
                        # Check if PDF was created
                        pdf_temp_path = os.path.join(temp_dir, f"{filename_base}.pdf")
                        if os.path.exists(pdf_temp_path):
                            # Copy PDF to output directory
                            pdf_final_path = os.path.join(self.output_dir, f"{filename_base}.pdf")
                            shutil.copy2(pdf_temp_path, pdf_final_path)
                            print(f"✓ PDF successfully created with {compiler}: {pdf_final_path}")
                            
                            # Verify colors are working by checking file size (colored PDFs are usually larger)
                            pdf_size = os.path.getsize(pdf_final_path)
                            if is_moderncv:
                                print(f"  PDF size: {pdf_size} bytes (moderncv document with colors)")
                            
                            compiled = True
                            return True, pdf_final_path
                        else:
                            print(f"  No PDF file generated by {compiler}")
                            
                    except FileNotFoundError:
                        print(f"{compiler} not found in PATH")
                        compilation_errors.append(f"{compiler}: Not found in system PATH")
                        continue
                    except subprocess.TimeoutExpired:
                        print(f"Timeout with {compiler} - compilation took too long")
                        compilation_errors.append(f"{compiler}: Compilation timeout (>120s)")
                        continue
                    except Exception as e:
                        print(f"Error with {compiler}: {e}")
                        compilation_errors.append(f"{compiler}: {str(e)}")
                        continue
                
                if not compiled:
                    print("\n❌ All compilers failed. Saving LaTeX file...")
                    # Save LaTeX file even if compilation failed
                    tex_final_path = os.path.join(self.output_dir, f"{filename_base}.tex")
                    with open(tex_final_path, 'w', encoding='utf-8') as f:
                        f.write(latex_content)
                    
                    # Also save error log with moderncv-specific troubleshooting
                    error_log_path = os.path.join(self.output_dir, f"{filename_base}_errors.txt")
                    with open(error_log_path, 'w', encoding='utf-8') as f:
                        f.write("PDF Compilation Errors\n")
                        f.write("=" * 50 + "\n\n")
                        
                        if is_moderncv:
                            f.write("MODERNCV COLOR SUPPORT TROUBLESHOOTING:\n")
                            f.write("-" * 40 + "\n")
                            f.write("• ModernCV colors require XeLaTeX or LuaLaTeX\n")
                            f.write("• Install full TeX Live distribution for complete package support\n")
                            f.write("• On macOS: brew install --cask mactex\n")
                            f.write("• On Windows: Install MiKTeX or TeX Live with all packages\n")
                            f.write("• On Linux: sudo apt-get install texlive-full\n")
                            f.write("• Alternatively, copy the LaTeX code to Overleaf for color support\n\n")
                        
                        for error in compilation_errors:
                            f.write(error + "\n\n")
                    
                    print(f"LaTeX saved to: {tex_final_path}")
                    print(f"Error log saved to: {error_log_path}")
                    
                    if is_moderncv:
                        print(f"\n💡 ModernCV Color Support:")
                        print(f"   Your template uses moderncv colors which require:")
                        print(f"   • XeLaTeX or LuaLaTeX compiler (better color support)")
                        print(f"   • Full LaTeX distribution with all packages")
                        print(f"   • Copy the LaTeX code to Overleaf for guaranteed color support")
                    
                    return False, tex_final_path
                    
        except Exception as e:
            print(f"Error in compile_latex_to_pdf: {e}")
            import traceback
            traceback.print_exc()
            return False, None
    
    def optimize_resume_latex(self, job_description, original_latex_content):
        """Send resume and job description to Claude for optimization with improved strategic prompt"""
        
        # Determine section order based on template type
        if self.current_template_type == "new_grad":
            section_order = "Education → Skills → Projects → Experience"
            template_type_desc = "NEW GRAD template"
        elif self.current_template_type == "experienced":
            section_order = "Professional Summary → Skills → Experience → Education → Projects"
            template_type_desc = "EXPERIENCED template"
        else:
            section_order = "Professional Summary → Skills → Experience → Education → Projects"
            template_type_desc = "GENERAL template (using experienced order)"
        
        # IMPROVED STRATEGIC PROMPT FOCUSED ON CONTENT PRESERVATION
        prompt = f"""Expert ATS optimizer & Resume Content Specialist: Optimize this LaTeX resume content for 90%+ keyword match while PRESERVING the exact LaTeX format and structure.

TEMPLATE TYPE: {template_type_desc}
CRITICAL INSTRUCTION: PRESERVE ALL LaTeX formatting, commands, packages, and document structure EXACTLY as provided.

WHAT TO PRESERVE (DO NOT CHANGE):
- All \\documentclass, \\usepackage, and preamble commands
- All LaTeX formatting commands (\\cventry, \\cvitem, \\section, etc.)  
- Document structure and section organization
- All spacing, margins, and layout commands
- Font specifications and styling commands
- Date formats and positioning
- Bullet point formatting (\\begin{{itemize}}, \\item, etc.)
- Any custom commands or environments

WHAT TO OPTIMIZE (CONTENT ONLY):
1. **Professional Summary/Objective**: Enhance with top 8-10 job keywords naturally while keeping same format
2. **Technical Skills**: Update skill names and technologies to match job requirements, keep same categories and LaTeX structure
3. **Experience Bullets**: Rewrite bullet point CONTENT to include relevant keywords and metrics, keep same \\item structure
4. **Education/Projects**: Update descriptions to highlight relevant coursework/technologies, preserve LaTeX formatting
5. **Strategic Bold Formatting**: Add \\textbf{{}} around key metrics, technologies, and achievements (like existing template)

KEYWORD INTEGRATION STRATEGY:
- Extract ALL relevant keywords from job description
- Naturally integrate keywords into existing content without changing LaTeX structure
- Prioritize must-have technical skills and experience requirements
- Include industry-standard acronyms and full forms where appropriate
- Maintain authentic tone while optimizing for ATS scanning

CONTENT ENHANCEMENT RULES:
- Keep all existing section headers and LaTeX section commands
- Preserve all date ranges and company/school names exactly as formatted
- Maintain bullet point structure but enhance content for impact
- Add quantified achievements where possible using existing metrics format
- Use strategic \\textbf{{}} for key numbers, technologies, and achievements

CRITICAL FORMATTING PRESERVATION:
- Keep exact same \\documentclass and all \\usepackage commands
- Preserve all margin, spacing, and geometry settings
- Maintain all custom commands and their usage
- Keep same font selections and styling
- Preserve header/contact information formatting exactly
- Do not change section ordering or LaTeX structure

OUTPUT REQUIREMENT:
Return the COMPLETE LaTeX document with:
- Exact same structure and formatting as the original
- Enhanced CONTENT optimized for the job description
- All LaTeX commands, packages, and formatting preserved
- Only text content within sections updated for keyword optimization

Current LaTeX Resume Template:
```latex
{original_latex_content}
```

Job Description to Optimize For:
{job_description}

Return ONLY the complete LaTeX code with preserved formatting and optimized content.


Finally, tailor summary(if it exists) and skills sections to resonate with experience and other sections of the resume
"""

        try:
            # Use Claude to optimize
            message = self.client.messages.create(
                model=self.model_choice,  # Use selected model
                max_tokens=8000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Extract LaTeX code from response
            # Remove any markdown code blocks if present
            latex_match = re.search(r'\\documentclass.*?\\end\{document\}', response_text, re.DOTALL)
            if latex_match:
                latex_code = latex_match.group(0)
            else:
                # If no match, assume the whole response is LaTeX
                latex_code = response_text
            
            # Check if the LaTeX seems truncated
            if latex_code and not latex_code.strip().endswith(r'\end{document}'):
                print("Warning: LaTeX output appears truncated")
                # Try to fix common truncation issues
                if latex_code.count('{') > latex_code.count('}'):
                    # Add missing closing braces
                    missing_braces = latex_code.count('{') - latex_code.count('}')
                    latex_code += '}' * missing_braces
                
                # Ensure it ends with \end{document}
                if not latex_code.strip().endswith(r'\end{document}'):
                    # Close any open environments
                    if r'\resumeItemListStart' in latex_code and latex_code.count(r'\resumeItemListStart') > latex_code.count(r'\resumeItemListEnd'):
                        latex_code += '\n\\resumeItemListEnd'
                    if r'\resumeSubHeadingListStart' in latex_code and latex_code.count(r'\resumeSubHeadingListStart') > latex_code.count(r'\resumeSubHeadingListEnd'):
                        latex_code += '\n\\resumeSubHeadingListEnd'
                    latex_code += '\n\n\\end{document}'
                
                print("Attempted to fix truncated LaTeX")
            
            return latex_code
                
        except Exception as e:
            print(f"Error optimizing resume: {e}")
            return None

class EnterpriseSpinner:
    """Enterprise-style spinning wheel progress indicator"""
    
    def __init__(self, parent, size=40):
        self.parent = parent
        self.size = size
        # Fix: Use default background color instead of trying to get parent bg
        self.canvas = tk.Canvas(parent, width=size, height=size, 
                               highlightthickness=0, bg='#ffffff')
        self.angle = 0
        self.running = False
        self.animation_job = None
        
        # Create spinning elements
        self.create_spinner()
    
    def create_spinner(self):
        """Create the spinner graphics"""
        center = self.size // 2
        radius = center - 5
        
        # Create 8 lines around the circle
        self.lines = []
        for i in range(8):
            angle = i * 45  # 360/8 = 45 degrees apart
            x1 = center + radius * 0.6 * math.cos(math.radians(angle))
            y1 = center + radius * 0.6 * math.sin(math.radians(angle))
            x2 = center + radius * math.cos(math.radians(angle))
            y2 = center + radius * math.sin(math.radians(angle))
            
            line = self.canvas.create_line(x1, y1, x2, y2, width=3, 
                                         fill='#0078d4', capstyle=tk.ROUND)
            self.lines.append(line)
    
    def animate(self):
        """Animate the spinner"""
        if not self.running:
            return
        
        try:
            # Update opacity/color of each line to create spinning effect
            for i, line in enumerate(self.lines):
                # Calculate opacity based on position relative to current angle
                offset = (i * 45 - self.angle) % 360
                if offset > 180:
                    offset = 360 - offset
                
                # Create fade effect
                opacity = max(0.2, 1.0 - (offset / 180.0))
                
                # Convert opacity to color (darker = less visible)
                if opacity > 0.8:
                    color = '#0078d4'  # Full blue
                elif opacity > 0.6:
                    color = '#4a9eff'  # Lighter blue
                elif opacity > 0.4:
                    color = '#7fb8ff'  # Even lighter
                elif opacity > 0.2:
                    color = '#b3d6ff'  # Very light
                else:
                    color = '#e6f3ff'  # Almost invisible
                    
                self.canvas.itemconfig(line, fill=color)
            
            # Update angle for next frame
            self.angle = (self.angle + 15) % 360
            
            # Schedule next animation frame
            if self.running:  # Double check we're still running
                self.animation_job = self.parent.after(50, self.animate)  # 20 FPS
        except Exception as e:
            print(f"Error in spinner animation: {e}")
            self.running = False
    
    def start(self):
        """Start the spinner animation"""
        if not self.running:
            self.running = True
            self.animate()
    
    def stop(self):
        """Stop the spinner animation"""
        self.running = False
        if self.animation_job:
            try:
                # Check if parent is still alive before trying to cancel
                if hasattr(self, 'parent') and self.parent:
                    self.parent.winfo_width()  # Test if parent is still alive
                    self.parent.after_cancel(self.animation_job)
            except (tk.TclError, AttributeError):
                pass  # Ignore errors if parent is destroyed
            self.animation_job = None
        
        # Reset all lines to default color
        try:
            if hasattr(self, 'canvas') and self.canvas:
                for line in self.lines:
                    self.canvas.itemconfig(line, fill='#cccccc')
        except (tk.TclError, AttributeError):
            pass  # Ignore errors if canvas is destroyed
    
    def pack(self, **kwargs):
        """Pack the canvas"""
        self.canvas.pack(**kwargs)
    
    def pack_forget(self):
        """Hide the canvas"""
        self.canvas.pack_forget()

class LaTeXResumeAutomationGUI:
    """GUI for the LaTeX Resume Automation Tool"""
    
    def __init__(self):
        self.optimizer = LaTeXResumeOptimizer()
        self.notebook = None  # Will store reference to notebook
        self.current_pdf_path = None  # Store path to generated PDF
        self.template_mapping = {}  # Store display name to actual name mapping
        self.spinner = None  # Will store the spinner widget
        self.setup_gui()
        
    def setup_gui(self):
        """Create GUI elements"""
        self.root = tk.Tk()
        self.root.title("LaTeX Resume Automation Tool")
        self.root.geometry("1000x700")
        
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tab 1: Setup & Input
        setup_tab = ttk.Frame(self.notebook)
        self.notebook.add(setup_tab, text="Setup & Input")
        
        # Tab 2: Output
        output_tab = ttk.Frame(self.notebook)
        self.notebook.add(output_tab, text="Generated Output")
        
        # --- SETUP TAB ---
        setup_frame = ttk.Frame(setup_tab, padding="10")
        setup_frame.pack(fill="both", expand=True)
        
        # Title
        title = ttk.Label(setup_frame, text="LaTeX Resume Automation Tool", font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # API Configuration
        api_frame = ttk.LabelFrame(setup_frame, text="API Configuration", padding="10")
        api_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky="w")
        self.api_key_entry = ttk.Entry(api_frame, width=40, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=5)
        
        # Load API key if available
        if self.optimizer.api_key:
            self.api_key_entry.insert(0, self.optimizer.api_key)
        
        # Save API key button
        ttk.Button(api_frame, text="Save Key", command=self.save_api_key).grid(row=0, column=2, padx=5)
        
        # Model Selection (more compact)
        ttk.Label(api_frame, text="Model:").grid(row=1, column=0, sticky="w", pady=(5,0))
        self.model_var = tk.StringVar(value="claude-sonnet-4-20250514")
        model_frame = ttk.Frame(api_frame)
        model_frame.grid(row=1, column=1, sticky="w", pady=(5,0))
        
        ttk.Radiobutton(model_frame, text="Sonnet 4 ($3/$15)", variable=self.model_var, 
                       value="claude-sonnet-4-20250514").pack(side=tk.LEFT)
        ttk.Radiobutton(model_frame, text="Opus 4 ($15/$75)", variable=self.model_var, 
                       value="claude-opus-4-20250514").pack(side=tk.LEFT, padx=(10,0))
        
        # Template Selection
        template_frame = ttk.LabelFrame(setup_frame, text="Resume Template", padding="10")
        template_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=5)
        
        ttk.Label(template_frame, text="Template:").grid(row=0, column=0, sticky="w")
        self.template_var = tk.StringVar()
        self.template_dropdown = ttk.Combobox(template_frame, textvariable=self.template_var,
                                            state="readonly", width=30)
        self.template_dropdown.grid(row=0, column=1, padx=5)
        
        ttk.Button(template_frame, text="Load", command=self.load_selected_template).grid(row=0, column=2, padx=5)
        ttk.Button(template_frame, text="Refresh", command=self.refresh_templates).grid(row=0, column=3, padx=5)
        
        # Custom template button
        ttk.Button(template_frame, text="Load Custom Template", 
                  command=self.load_custom_template).grid(row=0, column=4, padx=5)
        
        self.template_status = ttk.Label(template_frame, text="No template loaded", foreground="red")
        self.template_status.grid(row=1, column=0, columnspan=5, pady=(5,0))
        
        # Job Description (side by side layout)
        job_frame = ttk.LabelFrame(setup_frame, text="Job Information", padding="10")
        job_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=5)
        setup_frame.grid_rowconfigure(3, weight=1)
        
        # Company name field
        company_frame = ttk.Frame(job_frame)
        company_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(company_frame, text="Company Name:").pack(side=tk.LEFT, padx=(0, 5))
        self.company_name_entry = ttk.Entry(company_frame, width=30)
        self.company_name_entry.pack(side=tk.LEFT)
        ttk.Label(company_frame, text="(for filename)", foreground="gray").pack(side=tk.LEFT, padx=(5, 0))
        
        # Job description
        ttk.Label(job_frame, text="Job Description:").pack(anchor="w", pady=(5, 2))
        self.job_desc = scrolledtext.ScrolledText(job_frame, height=12, width=70, wrap=tk.WORD)
        self.job_desc.pack(fill="both", expand=True)
        
        # Generate button and progress area
        button_frame = ttk.Frame(setup_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.process_btn = ttk.Button(button_frame, text="Generate Optimized Resume", 
                                     command=self.process_resume, 
                                     style='Accent.TButton')
        self.process_btn.pack()
        
        # Enterprise Progress Area (initially hidden)
        self.progress_frame = ttk.Frame(button_frame)
        
        # Create spinner
        self.spinner = EnterpriseSpinner(self.progress_frame, size=40)
        
        # Progress status with multiple lines
        self.main_status = ttk.Label(self.progress_frame, text="", 
                                   foreground="#0078d4", font=('Arial', 10, 'bold'))
        self.sub_status = ttk.Label(self.progress_frame, text="", 
                                  foreground="#666666", font=('Arial', 9))
        self.time_status = ttk.Label(self.progress_frame, text="", 
                                   foreground="#888888", font=('Arial', 8))
        
        # Status label for final results (moved up before refresh_templates call)
        self.status_label = ttk.Label(button_frame, text="Ready", foreground="green")
        self.status_label.pack(pady=(5,0))
        
        # Configure grid weights
        setup_frame.grid_columnconfigure(1, weight=1)
        
        # --- OUTPUT TAB ---
        output_frame = ttk.Frame(output_tab, padding="10")
        output_frame.pack(fill="both", expand=True)
        
        # Output text
        output_label = ttk.Label(output_frame, text="Generated LaTeX Code:", font=('Arial', 12, 'bold'))
        output_label.pack(anchor="w", pady=(0,5))
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=25, width=80, wrap=tk.NONE)
        self.output_text.pack(fill="both", expand=True)
        
        # Output buttons
        output_btn_frame = ttk.Frame(output_frame)
        output_btn_frame.pack(pady=10)
        
        self.copy_btn = ttk.Button(output_btn_frame, text="Copy to Clipboard", 
                                  command=self.copy_to_clipboard, state='disabled')
        self.copy_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(output_btn_frame, text="Save as .tex File", 
                                  command=self.save_latex_file, state='disabled')
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_pdf_btn = ttk.Button(output_btn_frame, text="Open PDF", 
                                      command=self.open_pdf, state='disabled')
        self.open_pdf_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_folder_btn = ttk.Button(output_btn_frame, text="Open Output Folder", 
                                         command=self.open_output_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        # Style
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 12, 'bold'))
        
        # Populate templates (moved to end after all widgets are created)
        self.refresh_templates()
        
    def setup_gui(self):
        """Create GUI elements"""
        self.root = tk.Tk()
        self.root.title("LaTeX Resume Automation Tool")
        self.root.geometry("1000x700")
        
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tab 1: Setup & Input
        setup_tab = ttk.Frame(self.notebook)
        self.notebook.add(setup_tab, text="Setup & Input")
        
        # Tab 2: Output
        output_tab = ttk.Frame(self.notebook)
        self.notebook.add(output_tab, text="Generated Output")
        
        # --- SETUP TAB ---
        setup_frame = ttk.Frame(setup_tab, padding="10")
        setup_frame.pack(fill="both", expand=True)
        
        # Title
        title = ttk.Label(setup_frame, text="LaTeX Resume Automation Tool", font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # API Configuration
        api_frame = ttk.LabelFrame(setup_frame, text="API Configuration", padding="10")
        api_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky="w")
        self.api_key_entry = ttk.Entry(api_frame, width=40, show="*")
        self.api_key_entry.grid(row=0, column=1, padx=5)
        
        # Load API key if available
        if self.optimizer.api_key:
            self.api_key_entry.insert(0, self.optimizer.api_key)
        
        # Save API key button
        ttk.Button(api_frame, text="Save Key", command=self.save_api_key).grid(row=0, column=2, padx=5)
        
        # Model Selection (more compact)
        ttk.Label(api_frame, text="Model:").grid(row=1, column=0, sticky="w", pady=(5,0))
        self.model_var = tk.StringVar(value="claude-sonnet-4-20250514")
        model_frame = ttk.Frame(api_frame)
        model_frame.grid(row=1, column=1, sticky="w", pady=(5,0))
        
        ttk.Radiobutton(model_frame, text="Sonnet 4 ($3/$15)", variable=self.model_var, 
                       value="claude-sonnet-4-20250514").pack(side=tk.LEFT)
        ttk.Radiobutton(model_frame, text="Opus 4 ($15/$75)", variable=self.model_var, 
                       value="claude-opus-4-20250514").pack(side=tk.LEFT, padx=(10,0))
        
        # Template Selection
        template_frame = ttk.LabelFrame(setup_frame, text="Resume Template", padding="10")
        template_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=5)
        
        ttk.Label(template_frame, text="Template:").grid(row=0, column=0, sticky="w")
        self.template_var = tk.StringVar()
        self.template_dropdown = ttk.Combobox(template_frame, textvariable=self.template_var,
                                            state="readonly", width=30)
        self.template_dropdown.grid(row=0, column=1, padx=5)
        
        ttk.Button(template_frame, text="Load", command=self.load_selected_template).grid(row=0, column=2, padx=5)
        ttk.Button(template_frame, text="Refresh", command=self.refresh_templates).grid(row=0, column=3, padx=5)
        
        # Custom template button
        ttk.Button(template_frame, text="Load Custom Template", 
                  command=self.load_custom_template).grid(row=0, column=4, padx=5)
        
        self.template_status = ttk.Label(template_frame, text="No template loaded", foreground="red")
        self.template_status.grid(row=1, column=0, columnspan=5, pady=(5,0))
        
        # Job Description (side by side layout)
        job_frame = ttk.LabelFrame(setup_frame, text="Job Information", padding="10")
        job_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=5)
        setup_frame.grid_rowconfigure(3, weight=1)
        
        # Company name field
        company_frame = ttk.Frame(job_frame)
        company_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(company_frame, text="Company Name:").pack(side=tk.LEFT, padx=(0, 5))
        self.company_name_entry = ttk.Entry(company_frame, width=30)
        self.company_name_entry.pack(side=tk.LEFT)
        ttk.Label(company_frame, text="(for filename)", foreground="gray").pack(side=tk.LEFT, padx=(5, 0))
        
        # Job description
        ttk.Label(job_frame, text="Job Description:").pack(anchor="w", pady=(5, 2))
        self.job_desc = scrolledtext.ScrolledText(job_frame, height=12, width=70, wrap=tk.WORD)
        self.job_desc.pack(fill="both", expand=True)
        
        # Generate button and progress area
        button_frame = ttk.Frame(setup_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.process_btn = ttk.Button(button_frame, text="Generate Optimized Resume", 
                                     command=self.process_resume, 
                                     style='Accent.TButton')
        self.process_btn.pack()
        
        # Enterprise Progress Area (initially hidden)
        self.progress_frame = ttk.Frame(button_frame)
        
        # Create spinner
        self.spinner = EnterpriseSpinner(self.progress_frame, size=40)
        
        # Progress status with multiple lines
        self.main_status = ttk.Label(self.progress_frame, text="", 
                                   foreground="#0078d4", font=('Arial', 10, 'bold'))
        self.sub_status = ttk.Label(self.progress_frame, text="", 
                                  foreground="#666666", font=('Arial', 9))
        self.time_status = ttk.Label(self.progress_frame, text="", 
                                   foreground="#888888", font=('Arial', 8))
        
        # Status label for final results
        self.status_label = ttk.Label(button_frame, text="Ready", foreground="green")
        self.status_label.pack(pady=(5,0))
        
        # Configure grid weights
        setup_frame.grid_columnconfigure(1, weight=1)
        
        # --- OUTPUT TAB ---
        output_frame = ttk.Frame(output_tab, padding="10")
        output_frame.pack(fill="both", expand=True)
        
        # Output text
        output_label = ttk.Label(output_frame, text="Generated LaTeX Code:", font=('Arial', 12, 'bold'))
        output_label.pack(anchor="w", pady=(0,5))
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=25, width=80, wrap=tk.NONE)
        self.output_text.pack(fill="both", expand=True)
        
        # Output buttons
        output_btn_frame = ttk.Frame(output_frame)
        output_btn_frame.pack(pady=10)
        
        self.copy_btn = ttk.Button(output_btn_frame, text="Copy to Clipboard", 
                                  command=self.copy_to_clipboard, state='disabled')
        self.copy_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(output_btn_frame, text="Save as .tex File", 
                                  command=self.save_latex_file, state='disabled')
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_pdf_btn = ttk.Button(output_btn_frame, text="Open PDF", 
                                      command=self.open_pdf, state='disabled')
        self.open_pdf_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_folder_btn = ttk.Button(output_btn_frame, text="Open Output Folder", 
                                         command=self.open_output_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        # Style
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 12, 'bold'))
        
        # Populate templates
        self.refresh_templates()
    
    def save_api_key(self):
        """Save API key to config file"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key")
            return
        
        if self.optimizer.save_api_key_to_config(api_key):
            self.optimizer.api_key = api_key
            messagebox.showinfo("Success", "API key saved successfully!")
        else:
            messagebox.showerror("Error", "Failed to save API key")
    
    def show_enterprise_progress(self, main_message, sub_message="", elapsed_time=0):
        """Show enterprise-style progress with spinner and detailed status"""
        try:
            # Check if GUI is still alive
            if not self.is_gui_alive():
                return
                
            # Update status messages
            self.main_status.config(text=main_message)
            self.sub_status.config(text=sub_message)
            if elapsed_time > 0:
                self.time_status.config(text=f"Elapsed: {elapsed_time}s")
            else:
                self.time_status.config(text="")
            
            # Show progress frame and components
            self.progress_frame.pack(pady=(10, 0))
            self.spinner.pack(pady=(0, 10))
            self.main_status.pack(pady=(0, 2))
            if sub_message:
                self.sub_status.pack(pady=(0, 2))
            if elapsed_time > 0:
                self.time_status.pack(pady=(0, 5))
            
            # Start spinner animation
            self.spinner.start()
            
            # Update the UI immediately
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error showing progress: {e}")
    
    def hide_enterprise_progress(self):
        """Hide enterprise progress indicators"""
        try:
            # Check if GUI is still alive
            if not self.is_gui_alive():
                return
                
            # Stop and hide spinner
            if hasattr(self, 'spinner') and self.spinner:
                self.spinner.stop()
                self.spinner.pack_forget()
            
            # Hide status labels
            if hasattr(self, 'main_status'):
                self.main_status.pack_forget()
            if hasattr(self, 'sub_status'):
                self.sub_status.pack_forget()
            if hasattr(self, 'time_status'):
                self.time_status.pack_forget()
            
            # Hide progress frame
            if hasattr(self, 'progress_frame'):
                self.progress_frame.pack_forget()
        except Exception as e:
            print(f"Error hiding progress: {e}")
    
    def update_progress_status(self, main_message, sub_message="", elapsed_time=0):
        """Update progress status without hiding/showing the progress area"""
        try:
            # Check if GUI is still alive
            if not self.is_gui_alive():
                return
                
            if hasattr(self, 'main_status'):
                self.main_status.config(text=main_message)
            if hasattr(self, 'sub_status'):
                self.sub_status.config(text=sub_message)
            if hasattr(self, 'time_status') and elapsed_time > 0:
                self.time_status.config(text=f"Elapsed: {elapsed_time}s")
            
            # Update the UI immediately
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error updating progress: {e}")
    
    def safe_ui_call(self, func):
        """Safely call a UI function from background thread"""
        try:
            if self.is_gui_alive():
                self.root.after(0, func)
            else:
                print("GUI no longer exists, skipping UI update")
        except tk.TclError:
            # GUI has been destroyed
            print("GUI destroyed, skipping UI update")
        except Exception as e:
            print(f"Error in safe_ui_call: {e}")
    
    def is_gui_alive(self):
        """Check if GUI is still alive and responsive"""
        try:
            if not hasattr(self, 'root') or not self.root:
                return False
            # Try a simple operation to test if the GUI is responsive
            self.root.winfo_width()
            return True
        except (tk.TclError, AttributeError):
            return False
    
    def show_progress(self, message):
        """Legacy method for backward compatibility - redirects to enterprise progress"""
        self.show_enterprise_progress(message)
    
    def hide_progress(self):
        """Legacy method for backward compatibility - redirects to enterprise progress"""
        self.hide_enterprise_progress()
    
    def save_api_key(self):
        """Save API key to config file"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key")
            return
        
        if self.optimizer.save_api_key_to_config(api_key):
            self.optimizer.api_key = api_key
            messagebox.showinfo("Success", "API key saved successfully!")
        else:
            messagebox.showerror("Error", "Failed to save API key")
    
    def refresh_templates(self):
        """Refresh the templates dropdown"""
        print("\nRefreshing templates...")
        self.optimizer.load_available_templates()
        
        if self.optimizer.available_templates:
            # Create display names with type indicators
            template_names = []
            self.template_mapping = {}  # Store mapping of display names to actual names
            
            for name, info in self.optimizer.available_templates.items():
                if info['type'] == 'new_grad':
                    display_name = f"{name} [New Grad]"
                elif info['type'] == 'experienced':
                    display_name = f"{name} [Experienced]"
                else:
                    display_name = f"{name} [General]"
                template_names.append(display_name)
                self.template_mapping[display_name] = name
                print(f"Mapped: '{display_name}' -> '{name}'")
            
            self.template_dropdown['values'] = template_names
            if template_names:
                self.template_dropdown.set(template_names[0])  # Set first item as default
                print(f"Set default selection to: {template_names[0]}")
            
            self.status_label.config(text=f"Found {len(template_names)} templates", foreground="green")
            print(f"Total templates available: {len(template_names)}")
        else:
            self.template_dropdown['values'] = []
            self.template_dropdown.set('')  # Clear the selection
            self.status_label.config(text=f"No templates found in {self.optimizer.templates_dir}", 
                                   foreground="orange")
            print("No templates found!")
            messagebox.showwarning("No Templates", 
                                 f"No .tex files found in '{self.optimizer.templates_dir}' folder.\n\n" +
                                 "Please add your resume templates there.")
    
    def load_custom_template(self):
        """Load a custom LaTeX template file from anywhere"""
        file_path = filedialog.askopenfilename(
            title="Select LaTeX Template",
            filetypes=[("LaTeX Files", "*.tex"), ("All Files", "*.*")]
        )
        
        if file_path:
            print(f"\nLoading custom template from: {file_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.optimizer.latex_template = f.read()
                
                # Determine template type from filename
                filename = os.path.basename(file_path).lower()
                if 'new_grad' in filename or 'newgrad' in filename:
                    self.optimizer.current_template_type = "new_grad"
                    type_display = "New Grad"
                elif 'experienced' in filename or 'sde' in filename:
                    self.optimizer.current_template_type = "experienced"
                    type_display = "Experienced"
                else:
                    # Ask user to specify type
                    response = messagebox.askyesno(
                        "Template Type",
                        "Is this a New Grad template?\n\n" +
                        "Click 'Yes' for New Grad (Education → Skills → Projects → Experience)\n" +
                        "Click 'No' for Experienced (Skills → Experience → Education → Projects)"
                    )
                    if response:
                        self.optimizer.current_template_type = "new_grad"
                        type_display = "New Grad"
                    else:
                        self.optimizer.current_template_type = "experienced"
                        type_display = "Experienced"
                
                # Update status
                template_name = os.path.basename(file_path)
                self.template_status.config(
                    text=f"✓ Loaded: {template_name} ({type_display} format) [Custom]", 
                    foreground="green"
                )
                self.status_label.config(text="Custom template loaded successfully", foreground="green")
                
                # Clear dropdown selection since we're using custom
                self.template_dropdown.set("")
                
                print(f"Custom template loaded successfully")
                print(f"Template type: {self.optimizer.current_template_type}")
                print(f"Template content length: {len(self.optimizer.latex_template)} characters")
                
            except Exception as e:
                print(f"Error loading custom template: {e}")
                messagebox.showerror("Error", f"Failed to load template:\n{str(e)}")
                self.template_status.config(text="Failed to load custom template", foreground="red")
                self.status_label.config(text="Error loading custom template", foreground="red")
    
    def load_selected_template(self):
        """Load the selected template"""
        selected_value = self.template_var.get()
        print(f"\nLoad button clicked. Selected value: '{selected_value}'")
        
        if not selected_value:
            messagebox.showerror("Error", "Please select a template first")
            return
        
        # Check if templates are available
        if not self.optimizer.available_templates:
            print("No templates available in optimizer")
            messagebox.showerror("Error", "No templates found. Please add .tex files to the resume_templates folder.")
            return
        
        # Get actual template name from mapping
        if selected_value in self.template_mapping:
            template_name = self.template_mapping[selected_value]
            print(f"Found template name in mapping: {template_name}")
        else:
            # Fallback to old method if mapping not found
            template_name = selected_value.split(' [')[0]
            print(f"Using fallback method to extract template name: {template_name}")
        
        if self.optimizer.load_template_by_name(template_name):
            template_type = self.optimizer.current_template_type
            type_display = template_type.replace('_', ' ').title()
            self.template_status.config(
                text=f"✓ Loaded: {template_name} ({type_display} format)", 
                foreground="green"
            )
            self.status_label.config(text="Template loaded successfully", foreground="green")
            print(f"Template loaded successfully: {template_name}")
        else:
            self.template_status.config(text="Failed to load template", foreground="red")
            self.status_label.config(text="Error loading template", foreground="red")
            print(f"Failed to load template: {template_name}")
            messagebox.showerror("Error", f"Failed to load template: {template_name}\nCheck console for details.")
    
    def copy_to_clipboard(self):
        """Copy LaTeX code to clipboard"""
        latex_code = self.output_text.get("1.0", tk.END).strip()
        if latex_code:
            self.root.clipboard_clear()
            self.root.clipboard_append(latex_code)
            self.status_label.config(text="LaTeX code copied to clipboard!", foreground="green")
    
    def save_latex_file(self):
        """Save LaTeX code to file"""
        latex_code = self.output_text.get("1.0", tk.END).strip()
        if latex_code:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            default_filename = f"optimized_resume_{timestamp}.tex"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".tex",
                filetypes=[("LaTeX Files", "*.tex"), ("All Files", "*.*")],
                initialfile=default_filename
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(latex_code)
                    self.status_label.config(text=f"Saved to {os.path.basename(file_path)}", 
                                           foreground="green")
                    
                    # Offer to open file location
                    if messagebox.askyesno("Success", 
                                         "LaTeX file saved successfully!\n\nOpen file location?"):
                        if sys.platform == "win32":
                            os.startfile(os.path.dirname(file_path))
                        elif sys.platform == "darwin":  # macOS
                            subprocess.Popen(["open", os.path.dirname(file_path)])
                        else:  # linux
                            subprocess.Popen(["xdg-open", os.path.dirname(file_path)])
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def open_pdf(self):
        """Open the generated PDF"""
        if self.current_pdf_path and os.path.exists(self.current_pdf_path):
            try:
                if sys.platform == "win32":
                    os.startfile(self.current_pdf_path)
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", self.current_pdf_path], check=True)
                else:  # linux variants
                    # Try different Linux file openers
                    for opener in ["xdg-open", "gnome-open", "kde-open"]:
                        try:
                            subprocess.run([opener, self.current_pdf_path], check=True)
                            break
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            continue
                    else:
                        messagebox.showerror("Error", "Could not find a PDF viewer")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open PDF: {e}")
        else:
            messagebox.showerror("Error", "PDF file not found")
    
    def open_output_folder(self):
        """Open the output folder"""
        try:
            output_path = self.optimizer.output_dir
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            
            if sys.platform == "win32":
                os.startfile(output_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", output_path], check=True)
            else:  # linux variants
                for opener in ["xdg-open", "gnome-open", "kde-open", "nautilus"]:
                    try:
                        subprocess.run([opener, output_path], check=True)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                else:
                    messagebox.showerror("Error", "Could not open file manager")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
    
    def process_resume(self):
        """Process resume optimization"""
        print("Process resume button clicked!")  # Debug print
        
        # Get API key from entry or from optimizer
        api_key = self.api_key_entry.get().strip() or self.optimizer.api_key
        
        # Validate inputs
        if not api_key:
            messagebox.showerror("Error", "Please enter your Claude API key or save it in config")
            return
            
        if not self.optimizer.latex_template:
            messagebox.showerror("Error", 
                               "No resume template loaded!\n\n" +
                               "Please select and load a template from the dropdown,\n" +
                               f"or add .tex files to the '{self.optimizer.templates_dir}' folder.")
            return
            
        if not self.company_name_entry.get().strip():
            messagebox.showerror("Error", "Please enter the company name")
            return
            
        if not self.job_desc.get("1.0", tk.END).strip():
            messagebox.showerror("Error", "Please enter the job description")
            return
        
        # Save the API key for this session
        self.optimizer.api_key = api_key
        
        print("Starting background thread...")  # Debug print
        # Process in thread to keep UI responsive
        threading.Thread(target=self._process_resume_thread, daemon=True).start()
    
    def refresh_templates(self):
        """Refresh the templates dropdown"""
        print("\nRefreshing templates...")
        self.optimizer.load_available_templates()
        
        if self.optimizer.available_templates:
            # Create display names with type indicators
            template_names = []
            self.template_mapping = {}  # Store mapping of display names to actual names
            
            for name, info in self.optimizer.available_templates.items():
                if info['type'] == 'new_grad':
                    display_name = f"{name} [New Grad]"
                elif info['type'] == 'experienced':
                    display_name = f"{name} [Experienced]"
                else:
                    display_name = f"{name} [General]"
                template_names.append(display_name)
                self.template_mapping[display_name] = name
                print(f"Mapped: '{display_name}' -> '{name}'")
            
            self.template_dropdown['values'] = template_names
            if template_names:
                self.template_dropdown.set(template_names[0])  # Set first item as default
                print(f"Set default selection to: {template_names[0]}")
            
            self.status_label.config(text=f"Found {len(template_names)} templates", foreground="green")
            print(f"Total templates available: {len(template_names)}")
        else:
            self.template_dropdown['values'] = []
            self.template_dropdown.set('')  # Clear the selection
            self.status_label.config(text=f"No templates found in {self.optimizer.templates_dir}", 
                                   foreground="orange")
            print("No templates found!")
            messagebox.showwarning("No Templates", 
                                 f"No .tex files found in '{self.optimizer.templates_dir}' folder.\n\n" +
                                 "Please add your resume templates there.")
    
    def load_custom_template(self):
        """Load a custom LaTeX template file from anywhere"""
        file_path = filedialog.askopenfilename(
            title="Select LaTeX Template",
            filetypes=[("LaTeX Files", "*.tex"), ("All Files", "*.*")]
        )
        
        if file_path:
            print(f"\nLoading custom template from: {file_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.optimizer.latex_template = f.read()
                
                # Determine template type from filename
                filename = os.path.basename(file_path).lower()
                if 'new_grad' in filename or 'newgrad' in filename:
                    self.optimizer.current_template_type = "new_grad"
                    type_display = "New Grad"
                elif 'experienced' in filename or 'sde' in filename:
                    self.optimizer.current_template_type = "experienced"
                    type_display = "Experienced"
                else:
                    # Ask user to specify type
                    response = messagebox.askyesno(
                        "Template Type",
                        "Is this a New Grad template?\n\n" +
                        "Click 'Yes' for New Grad (Education → Skills → Projects → Experience)\n" +
                        "Click 'No' for Experienced (Skills → Experience → Education → Projects)"
                    )
                    if response:
                        self.optimizer.current_template_type = "new_grad"
                        type_display = "New Grad"
                    else:
                        self.optimizer.current_template_type = "experienced"
                        type_display = "Experienced"
                
                # Update status
                template_name = os.path.basename(file_path)
                self.template_status.config(
                    text=f"✓ Loaded: {template_name} ({type_display} format) [Custom]", 
                    foreground="green"
                )
                self.status_label.config(text="Custom template loaded successfully", foreground="green")
                
                # Clear dropdown selection since we're using custom
                self.template_dropdown.set("")
                
                print(f"Custom template loaded successfully")
                print(f"Template type: {self.optimizer.current_template_type}")
                print(f"Template content length: {len(self.optimizer.latex_template)} characters")
                
            except Exception as e:
                print(f"Error loading custom template: {e}")
                messagebox.showerror("Error", f"Failed to load template:\n{str(e)}")
                self.template_status.config(text="Failed to load custom template", foreground="red")
                self.status_label.config(text="Error loading custom template", foreground="red")
    
    def load_selected_template(self):
        """Load the selected template"""
        selected_value = self.template_var.get()
        print(f"\nLoad button clicked. Selected value: '{selected_value}'")
        
        if not selected_value:
            messagebox.showerror("Error", "Please select a template first")
            return
        
        # Check if templates are available
        if not self.optimizer.available_templates:
            print("No templates available in optimizer")
            messagebox.showerror("Error", "No templates found. Please add .tex files to the resume_templates folder.")
            return
        
        # Get actual template name from mapping
        if selected_value in self.template_mapping:
            template_name = self.template_mapping[selected_value]
            print(f"Found template name in mapping: {template_name}")
        else:
            # Fallback to old method if mapping not found
            template_name = selected_value.split(' [')[0]
            print(f"Using fallback method to extract template name: {template_name}")
        
        if self.optimizer.load_template_by_name(template_name):
            template_type = self.optimizer.current_template_type
            type_display = template_type.replace('_', ' ').title()
            self.template_status.config(
                text=f"✓ Loaded: {template_name} ({type_display} format)", 
                foreground="green"
            )
            self.status_label.config(text="Template loaded successfully", foreground="green")
            print(f"Template loaded successfully: {template_name}")
        else:
            self.template_status.config(text="Failed to load template", foreground="red")
            self.status_label.config(text="Error loading template", foreground="red")
            print(f"Failed to load template: {template_name}")
            messagebox.showerror("Error", f"Failed to load template: {template_name}\nCheck console for details.")
    
    def reload_resume(self):
        """Reload the current template"""
        if self.template_var.get():
            self.load_selected_template()
        else:
            messagebox.showinfo("Info", "Please select a template first")
    
    def copy_to_clipboard(self):
        """Copy LaTeX code to clipboard"""
        latex_code = self.output_text.get("1.0", tk.END).strip()
        if latex_code:
            self.root.clipboard_clear()
            self.root.clipboard_append(latex_code)
            self.status_label.config(text="LaTeX code copied to clipboard!", foreground="green")
    
    def save_latex_file(self):
        """Save LaTeX code to file"""
        latex_code = self.output_text.get("1.0", tk.END).strip()
        if latex_code:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            default_filename = f"optimized_resume_{timestamp}.tex"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".tex",
                filetypes=[("LaTeX Files", "*.tex"), ("All Files", "*.*")],
                initialfile=default_filename
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(latex_code)
                    self.status_label.config(text=f"Saved to {os.path.basename(file_path)}", 
                                           foreground="green")
                    
                    # Offer to open file location
                    if messagebox.askyesno("Success", 
                                         "LaTeX file saved successfully!\n\nOpen file location?"):
                        if sys.platform == "win32":
                            os.startfile(os.path.dirname(file_path))
                        elif sys.platform == "darwin":  # macOS
                            subprocess.Popen(["open", os.path.dirname(file_path)])
                        else:  # linux
                            subprocess.Popen(["xdg-open", os.path.dirname(file_path)])
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def open_pdf(self):
        """Open the generated PDF"""
        if self.current_pdf_path and os.path.exists(self.current_pdf_path):
            try:
                if sys.platform == "win32":
                    os.startfile(self.current_pdf_path)
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", self.current_pdf_path], check=True)
                else:  # linux variants
                    # Try different Linux file openers
                    for opener in ["xdg-open", "gnome-open", "kde-open"]:
                        try:
                            subprocess.run([opener, self.current_pdf_path], check=True)
                            break
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            continue
                    else:
                        messagebox.showerror("Error", "Could not find a PDF viewer")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open PDF: {e}")
        else:
            messagebox.showerror("Error", "PDF file not found")
    
    def open_output_folder(self):
        """Open the output folder"""
        try:
            output_path = self.optimizer.output_dir
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            
            if sys.platform == "win32":
                os.startfile(output_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", output_path], check=True)
            else:  # linux variants
                for opener in ["xdg-open", "gnome-open", "kde-open", "nautilus"]:
                    try:
                        subprocess.run([opener, output_path], check=True)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                else:
                    messagebox.showerror("Error", "Could not open file manager")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
    
    def process_resume(self):
        """Process resume optimization"""
        # Get API key from entry or from optimizer
        api_key = self.api_key_entry.get().strip() or self.optimizer.api_key
        
        # Validate inputs
        if not api_key:
            messagebox.showerror("Error", "Please enter your Claude API key or save it in config")
            return
            
        if not self.optimizer.latex_template:
            messagebox.showerror("Error", 
                               "No resume template loaded!\n\n" +
                               "Please select and load a template from the dropdown,\n" +
                               f"or add .tex files to the '{self.optimizer.templates_dir}' folder.")
            return
            
        if not self.company_name_entry.get().strip():
            messagebox.showerror("Error", "Please enter the company name")
            return
            
        if not self.job_desc.get("1.0", tk.END).strip():
            messagebox.showerror("Error", "Please enter the job description")
            return
        
        # Save the API key for this session
        self.optimizer.api_key = api_key
        
        # Process in thread to keep UI responsive
        threading.Thread(target=self._process_resume_thread, daemon=True).start()
    
    def _process_resume_thread(self):
        """Process resume in background thread with enterprise-level progress updates"""
        start_time = time.time()
        print("Background thread started!")  # Debug print
        
        try:
            # Initial setup
            self.safe_ui_call(lambda: self.show_enterprise_progress(
                "Initializing Resume Optimization", 
                "Preparing API connection and validating inputs..."
            ))
            self.safe_ui_call(lambda: self.process_btn.config(state='disabled'))
            self.safe_ui_call(lambda: self.output_text.delete("1.0", tk.END))
            self.current_pdf_path = None
            
            # Setup API
            self.safe_ui_call(lambda: self.update_progress_status(
                "Connecting to Claude AI", 
                "Authenticating API credentials...",
                int(time.time() - start_time)
            ))
            
            if not self.optimizer.setup_claude_api(self.optimizer.api_key):
                self.safe_ui_call(lambda: self.hide_enterprise_progress())
                self.safe_ui_call(lambda: self.status_label.config(text="API authentication failed", foreground="red"))
                self.safe_ui_call(lambda: messagebox.showerror("Authentication Error", 
                    "Failed to authenticate with Claude AI. Please check your API key and try again."))
                return
            
            # Set selected model
            self.optimizer.set_model(self.model_var.get())
            model_name = "Sonnet 4" if "sonnet" in self.model_var.get() else "Opus 4"
            
            # Get inputs
            job_description = self.job_desc.get("1.0", tk.END).strip()
            company_name = self.company_name_entry.get().strip()
            
            # Analyze job description
            self.safe_ui_call(lambda: self.update_progress_status(
                "Analyzing Job Requirements", 
                f"Processing job description using {model_name}...",
                int(time.time() - start_time)
            ))
            
            # Small delay to show the analysis step
            time.sleep(0.5)
            
            # Resume optimization
            self.safe_ui_call(lambda: self.update_progress_status(
                "Optimizing Resume Content", 
                "Strategic positioning, keyword matching, and ATS optimization...",
                int(time.time() - start_time)
            ))
            
            optimized_latex = self.optimizer.optimize_resume_latex(
                job_description,
                self.optimizer.latex_template
            )
            
            if optimized_latex:
                # Display result
                self.safe_ui_call(lambda: self.output_text.insert("1.0", optimized_latex))
                self.safe_ui_call(lambda: self.copy_btn.config(state='normal'))
                self.safe_ui_call(lambda: self.save_btn.config(state='normal'))
                
                # PDF compilation phase
                self.safe_ui_call(lambda: self.update_progress_status(
                    "Generating PDF Document", 
                    "Compiling LaTeX to PDF format...",
                    int(time.time() - start_time)
                ))
                
                # Try to compile to PDF
                pdf_success, output_path = self.optimizer.compile_latex_to_pdf(optimized_latex, company_name)
                
                # Hide progress
                self.safe_ui_call(lambda: self.hide_enterprise_progress())
                
                total_time = int(time.time() - start_time)
                
                if pdf_success:
                    self.current_pdf_path = output_path
                    filename = os.path.basename(output_path)
                    
                    self.safe_ui_call(lambda: self.open_pdf_btn.config(state='normal'))
                    self.safe_ui_call(lambda: self.status_label.config(
                        text=f"✓ Resume successfully generated: {filename} ({total_time}s)", 
                        foreground="green"))
                    
                    # Switch to output tab
                    self.safe_ui_call(lambda: self.notebook.select(1))
                    
                    # Show success message with more details
                    def show_success():
                        messagebox.showinfo(
                            "Success - Resume Generated", 
                            f"🎉 Resume optimization completed successfully!\n\n" +
                            f"⏱️  Processing time: {total_time} seconds\n" +
                            f"📄 PDF saved as: {filename}\n" +
                            f"📁 Location: {self.optimizer.output_dir}/\n\n" +
                            f"🔍 Optimized for: {model_name}\n" +
                            f"🎯 Company: {company_name}\n\n" +
                            "Next steps:\n" +
                            "• Click 'Open PDF' to review your resume\n" +
                            "• Use 'Open Output Folder' to access all versions\n" +
                            "• Copy LaTeX code for further customization"
                        )
                    self.safe_ui_call(show_success)
                else:
                    # PDF compilation failed but LaTeX saved
                    if output_path:
                        filename = os.path.basename(output_path)
                        self.safe_ui_call(lambda: self.status_label.config(
                            text=f"⚠️ LaTeX generated: {filename} (PDF compilation failed) ({total_time}s)", 
                            foreground="orange"))
                        
                        # Switch to output tab
                        self.safe_ui_call(lambda: self.notebook.select(1))
                        
                        def show_warning():
                            messagebox.showwarning(
                                "Partial Success - LaTeX Generated", 
                                f"✅ Resume optimization completed in {total_time} seconds\n" +
                                f"⚠️  PDF compilation failed (LaTeX saved instead)\n\n" +
                                f"📄 LaTeX file: {filename}\n" +
                                f"📁 Location: {self.optimizer.output_dir}/\n\n" +
                                "💡 Solutions:\n" +
                                "• Copy the LaTeX code and compile in Overleaf\n" +
                                "• Install a LaTeX distribution for local PDF generation:\n" +
                                "  - Windows: MiKTeX or TeX Live\n" +
                                "  - Mac: MacTeX\n" +
                                "  - Linux: texlive-full\n\n" +
                                "Your optimized resume content is ready to use!"
                            )
                        self.safe_ui_call(show_warning)
                    else:
                        self.safe_ui_call(lambda: self.status_label.config(
                            text=f"✅ Resume optimized - use Overleaf for PDF ({total_time}s)", 
                            foreground="green"))
                        self.safe_ui_call(lambda: self.notebook.select(1))
            else:
                self.safe_ui_call(lambda: self.hide_enterprise_progress())
                self.safe_ui_call(lambda: self.status_label.config(text="❌ Optimization failed", foreground="red"))
                def show_error():
                    messagebox.showerror("Optimization Failed", 
                        "Failed to optimize resume. Please check:\n\n" +
                        "• API key is valid and has sufficient credits\n" +
                        "• Job description is properly formatted\n" +
                        "• Resume template is loaded correctly\n" +
                        "• Internet connection is stable\n\n" +
                        "Try again or contact support if the issue persists.")
                self.safe_ui_call(show_error)
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            total_time = int(time.time() - start_time)
            print(f"Error in background thread: {e}")  # Debug print
            import traceback
            traceback.print_exc()
            
            self.safe_ui_call(lambda: self.hide_enterprise_progress())
            self.safe_ui_call(lambda: self.status_label.config(
                text=f"❌ Error after {total_time}s: {error_msg[:30]}...", 
                foreground="red"))
            def show_error():
                messagebox.showerror(
                    "Processing Error", 
                    f"An error occurred during resume optimization:\n\n{error_msg}\n\n" +
                    f"Processing time: {total_time}s\n\n" +
                    "Please try again or check the console for detailed error information.")
            self.safe_ui_call(show_error)
        finally:
            self.safe_ui_call(lambda: self.process_btn.config(state='normal'))
    
    def run(self):
        """Start the application"""
        # Check if templates directory exists
        if not os.path.exists(self.optimizer.templates_dir):
            messagebox.showwarning("Setup Required", 
                                 f"'{self.optimizer.templates_dir}' folder not found!\n\n" +
                                 "Creating the folder now. Please add your resume templates:\n" +
                                 "- new_grad_resume.tex (for new grad format)\n" +
                                 "- experienced_resume.tex or sde_resume.tex (for experienced format)")
            self.optimizer.setup_directories()
        elif not self.optimizer.available_templates:
            messagebox.showwarning("No Templates Found", 
                                 f"No .tex files found in '{self.optimizer.templates_dir}' folder!\n\n" +
                                 "Please add your resume templates:\n" +
                                 "- new_grad_resume.tex (for new grad format)\n" +
                                 "- experienced_resume.tex or sde_resume.tex (for experienced format)")
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        print("Starting GUI...")  # Debug print
        self.root.mainloop()
    
    def run(self):
        """Start the application"""
        # Check if templates directory exists
        if not os.path.exists(self.optimizer.templates_dir):
            messagebox.showwarning("Setup Required", 
                                 f"'{self.optimizer.templates_dir}' folder not found!\n\n" +
                                 "Creating the folder now. Please add your resume templates:\n" +
                                 "- new_grad_resume.tex (for new grad format)\n" +
                                 "- experienced_resume.tex or sde_resume.tex (for experienced format)")
            self.optimizer.setup_directories()
        elif not self.optimizer.available_templates:
            messagebox.showwarning("No Templates Found", 
                                 f"No .tex files found in '{self.optimizer.templates_dir}' folder!\n\n" +
                                 "Please add your resume templates:\n" +
                                 "- new_grad_resume.tex (for new grad format)\n" +
                                 "- experienced_resume.tex or sde_resume.tex (for experienced format)")
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.root.mainloop()

# Main execution
if __name__ == "__main__":
    print("LaTeX Resume Automation Tool")
    print("-" * 40)
    print("This tool generates ATS-optimized LaTeX resumes using Claude AI")
    print("Reading templates from: resume_templates/")
    print("Output PDFs saved to: generated_resumes/")
    print()
    
    # Check for LaTeX installation
    latex_installed = False
    print("Checking for LaTeX installation...")
    print(f"Current PATH: {os.environ.get('PATH', 'Not found')}\n")
    
    # Common MacTeX paths
    mactex_paths = [
        "/Library/TeX/texbin",
        "/usr/local/texlive/2024/bin/universal-darwin",
        "/usr/local/texlive/2023/bin/universal-darwin",
        "/usr/local/texlive/2022/bin/universal-darwin",
        "/opt/local/bin",
        "/usr/texbin"
    ]
    
    # Add MacTeX paths to PATH if they exist
    for path in mactex_paths:
        if os.path.exists(path) and path not in os.environ.get('PATH', ''):
            print(f"Adding {path} to PATH")
            os.environ['PATH'] = f"{path}:{os.environ.get('PATH', '')}"
    
    for compiler in ['pdflatex', 'xelatex', 'lualatex']:
        try:
            # Try to find the compiler
            which_result = subprocess.run(['which', compiler], capture_output=True, text=True)
            if which_result.returncode == 0:
                compiler_path = which_result.stdout.strip()
                print(f"Found {compiler} at: {compiler_path}")
            
            result = subprocess.run([compiler, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                latex_installed = True
                print(f"✓ {compiler} is working")
                version_lines = result.stdout.split('\n')[:2]
                for line in version_lines:
                    if line.strip():
                        print(f"  {line.strip()}")
                break
        except FileNotFoundError:
            print(f"✗ {compiler} not found")
            continue
    
    if not latex_installed:
        print("\nWarning: No LaTeX compiler found - PDF generation will not work")
        print("MacTeX might not be in your PATH. Try:")
        print("  1. Close and reopen the terminal/application")
        print("  2. Run: export PATH=\"/Library/TeX/texbin:$PATH\"")
        print("  3. Or reinstall MacTeX from https://tug.org/mactex/")
        print("\nYou can still use the tool to generate LaTeX code for Overleaf")
    else:
        print("\nLaTeX installation verified!")
    print()
    
    try:
        print("Starting application...")
        app = LaTeXResumeAutomationGUI()
        app.run()
    except Exception as e:
        print(f"\nCritical error starting application: {e}")
        import traceback
        traceback.print_exc()
        
        print("\nTroubleshooting steps:")
        print("1. Make sure Python 3.8+ is installed")
        print("2. Try running: pip install --upgrade pip")
        print("3. Then run: pip install anthropic")
        print("4. Check if tkinter is properly installed:")
        print("   python3 -c 'import tkinter; print(\"tkinter OK\")'")
        print("5. Create templates in resume_templates folder")
        print("6. If using virtual environment, make sure tkinter is available")
        print("\nFor macOS users:")
        print("- Try: brew install python-tk")
        print("- Or reinstall Python from python.org")
        print("\nPress Enter to exit...")
        input()