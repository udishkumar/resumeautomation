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
        
        # Create directories if they don't exist
        self.setup_directories()
        
        # Load available templates
        self.load_available_templates()
        
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
            
            # Create temp directory for compilation
            with tempfile.TemporaryDirectory() as temp_dir:
                tex_path = os.path.join(temp_dir, f"{filename_base}.tex")
                
                # Write LaTeX content
                with open(tex_path, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                
                # Try different LaTeX compilers
                compilers = ['pdflatex', 'xelatex', 'lualatex']
                compiled = False
                
                for compiler in compilers:
                    try:
                        # Run compiler twice for references
                        for _ in range(2):
                            result = subprocess.run(
                                [compiler, '-interaction=nonstopmode', tex_path],
                                cwd=temp_dir,
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                        
                        pdf_temp_path = os.path.join(temp_dir, f"{filename_base}.pdf")
                        if os.path.exists(pdf_temp_path):
                            # Copy PDF to output directory
                            pdf_final_path = os.path.join(self.output_dir, f"{filename_base}.pdf")
                            shutil.copy2(pdf_temp_path, pdf_final_path)
                            compiled = True
                            return True, pdf_final_path
                            
                    except FileNotFoundError:
                        continue
                    except subprocess.TimeoutExpired:
                        print(f"Timeout with {compiler} - compilation took too long")
                        continue
                    except Exception as e:
                        print(f"Error with {compiler}: {e}")
                        continue
                
                if not compiled:
                    # Save LaTeX file even if compilation failed
                    tex_final_path = os.path.join(self.output_dir, f"{filename_base}.tex")
                    with open(tex_final_path, 'w', encoding='utf-8') as f:
                        f.write(latex_content)
                    return False, tex_final_path
                    
        except Exception as e:
            print(f"Error in compile_latex_to_pdf: {e}")
            return False, None
    
    def optimize_resume_latex(self, job_description, original_latex_content):
        """Send resume and job description to Claude for optimization"""
        
        # Determine section order based on template type
        if self.current_template_type == "new_grad":
            section_order = "Professional Summary → Education → Skills → Projects → Experience"
            template_type_desc = "NEW GRAD template"
        elif self.current_template_type == "experienced":
            section_order = "Professional Summary → Skills → Experience → Education → Projects"
            template_type_desc = "EXPERIENCED template"
        else:
            section_order = "Professional Summary → Skills → Experience → Education → Projects"
            template_type_desc = "GENERAL template (using experienced order)"
        
        prompt = f"""Expert ATS optimizer: Transform this LaTeX resume for 90%+ keyword match with the job description.

TEMPLATE TYPE: {template_type_desc}
REQUIRED SECTION ORDER: {section_order}

ANALYZE & OPTIMIZE:
1. Extract ALL keywords from job: technical skills, tools, certifications, soft skills, experience requirements
2. Gap analysis: Find missing keywords I likely have but haven't mentioned
3. Rewrite strategically:
   - Summary: Include top 8-10 job keywords
   - Skills: Reorganize to match job requirements exactly  
   - Experience: Incorporate keywords naturally with metrics and STAR method
   - Projects/Education: Highlight relevant technologies and coursework
4. Format for ATS: Standard headers, consistent dates, include acronyms+full forms (e.g., "Machine Learning (ML)")

CRITICAL FORMATTING RULES:
1. **Professional Summary**: MUST be 2-3 lines of continuous text with NO bullet points. Write as a paragraph.
2. **Section Order**: You MUST arrange sections in this exact order: {section_order}
3. Maintain all LaTeX formatting and packages from the original template

RULES:
- Maintain authenticity while optimizing
- Natural language flow, no filler words
- Confident, results-oriented tone
- Professional Summary must be a paragraph (2-3 lines), NOT bullet points

DELIVERABLES:
Return ONLY the complete optimized LaTeX code ready for Overleaf compilation. Maintain exact document structure and packages from the original, but sections MUST be in the order specified above.

Current LaTeX Resume:
```latex
{original_latex_content}
```

Job Description:
{job_description}

Return ONLY LaTeX code starting with \\documentclass and ending with \\end{{document}}."""

        try:
            # Use Claude to optimize
            message = self.client.messages.create(
                model=self.model_choice,  # Use selected model
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Extract LaTeX code from response
            # Remove any markdown code blocks if present
            latex_match = re.search(r'\\documentclass.*?\\end\{document\}', response_text, re.DOTALL)
            if latex_match:
                return latex_match.group(0)
            else:
                # If no match, assume the whole response is LaTeX
                return response_text
                
        except Exception as e:
            print(f"Error optimizing resume: {e}")
            return None

class LaTeXResumeAutomationGUI:
    """GUI for the LaTeX Resume Automation Tool"""
    
    def __init__(self):
        self.optimizer = LaTeXResumeOptimizer()
        self.notebook = None  # Will store reference to notebook
        self.current_pdf_path = None  # Store path to generated PDF
        self.template_mapping = {}  # Store display name to actual name mapping
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
        
        self.template_status = ttk.Label(template_frame, text="No template loaded", foreground="red")
        self.template_status.grid(row=1, column=0, columnspan=4, pady=(5,0))
        
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
        
        # Generate button
        button_frame = ttk.Frame(setup_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.process_btn = ttk.Button(button_frame, text="Generate Optimized Resume", 
                                     command=self.process_resume, 
                                     style='Accent.TButton')
        self.process_btn.pack()
        
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
        # Validate inputs
        if not self.api_key_entry.get():
            messagebox.showerror("Error", "Please enter your Claude API key")
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
        
        # Process in thread to keep UI responsive
        threading.Thread(target=self._process_resume_thread, daemon=True).start()
    
    def _process_resume_thread(self):
        """Process resume in background thread"""
        try:
            # Update UI
            self.root.after(0, lambda: self.status_label.config(text="Setting up API...", foreground="blue"))
            self.root.after(0, lambda: self.process_btn.config(state='disabled'))
            self.root.after(0, lambda: self.output_text.delete("1.0", tk.END))
            self.current_pdf_path = None
            
            # Setup API
            if not self.optimizer.setup_claude_api(self.api_key_entry.get()):
                self.root.after(0, lambda: self.status_label.config(text="API setup failed", foreground="red"))
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    "Failed to setup API. Please check your API key."))
                return
            
            # Set selected model
            self.optimizer.set_model(self.model_var.get())
            
            # Update status
            self.root.after(0, lambda: self.status_label.config(text="Optimizing resume with Claude AI...", 
                                                               foreground="blue"))
            
            # Get inputs
            job_description = self.job_desc.get("1.0", tk.END).strip()
            company_name = self.company_name_entry.get().strip()
            
            # Optimize resume
            optimized_latex = self.optimizer.optimize_resume_latex(
                job_description,
                self.optimizer.latex_template
            )
            
            if optimized_latex:
                # Display result
                self.root.after(0, lambda: self.output_text.insert("1.0", optimized_latex))
                self.root.after(0, lambda: self.copy_btn.config(state='normal'))
                self.root.after(0, lambda: self.save_btn.config(state='normal'))
                
                # Update status for PDF generation
                self.root.after(0, lambda: self.status_label.config(
                    text="Generating PDF...", 
                    foreground="blue"))
                
                # Try to compile to PDF
                pdf_success, output_path = self.optimizer.compile_latex_to_pdf(optimized_latex, company_name)
                
                if pdf_success:
                    self.current_pdf_path = output_path
                    filename = os.path.basename(output_path)
                    
                    self.root.after(0, lambda: self.open_pdf_btn.config(state='normal'))
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"✓ Resume optimized and PDF generated: {filename}", 
                        foreground="green"))
                    
                    # Switch to output tab
                    self.root.after(0, lambda: self.notebook.select(1))
                    
                    # Show success message
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Success", 
                        f"Resume optimization complete!\n\n" +
                        f"PDF saved as: {filename}\n" +
                        f"Location: {self.optimizer.output_dir}/\n\n" +
                        "Click 'Open PDF' to view it or 'Open Output Folder' to see all resumes."
                    ))
                else:
                    # PDF compilation failed but LaTeX saved
                    if output_path:
                        filename = os.path.basename(output_path)
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"✓ LaTeX saved: {filename} (PDF compilation failed)", 
                            foreground="orange"))
                        
                        # Switch to output tab
                        self.root.after(0, lambda: self.notebook.select(1))
                        
                        self.root.after(0, lambda: messagebox.showwarning(
                            "Partial Success", 
                            f"Resume optimized but PDF compilation failed.\n\n" +
                            f"LaTeX file saved as: {filename}\n" +
                            f"Location: {self.optimizer.output_dir}/\n\n" +
                            "You can copy the LaTeX code and compile it in Overleaf.\n\n" +
                            "To enable PDF generation, install a LaTeX distribution:\n" +
                            "• Windows: MiKTeX or TeX Live\n" +
                            "• Mac: MacTeX\n" +
                            "• Linux: texlive-full"
                        ))
                    else:
                        self.root.after(0, lambda: self.status_label.config(
                            text="✓ Resume optimized (use Overleaf for PDF)", 
                            foreground="green"))
                        self.root.after(0, lambda: self.notebook.select(1))
            else:
                self.root.after(0, lambda: self.status_label.config(text="Optimization failed", foreground="red"))
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    "Failed to optimize resume. Please check your API key and try again."))
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda: self.status_label.config(text=error_msg[:50] + "...", foreground="red"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.root.after(0, lambda: self.process_btn.config(state='normal'))
    
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
        app = LaTeXResumeAutomationGUI()
        app.run()
    except Exception as e:
        print(f"\nError starting application: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure Python is installed correctly")
        print("2. Try running: pip install --upgrade pip")
        print("3. Then run: pip install anthropic")
        print("4. Create templates in resume_templates folder")
        print("\nPress Enter to exit...")
        input()