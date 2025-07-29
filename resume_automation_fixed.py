"""
Resume Automation Tool - LaTeX Version
Generates LaTeX code for tailored resumes using Claude API
Automatically reads from input_resume.tex
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import re
import threading

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
        self.available_templates = {}
        self.current_template_type = None
        
        # Create templates directory if it doesn't exist
        self.setup_templates_directory()
        
        # Load available templates
        self.load_available_templates()
        
    def setup_templates_directory(self):
        """Create templates directory if it doesn't exist"""
        if not os.path.exists(self.templates_dir):
            try:
                os.makedirs(self.templates_dir)
                print(f"✓ Created {self.templates_dir} directory")
            except Exception as e:
                print(f"Error creating {self.templates_dir}: {e}")
    
    def load_available_templates(self):
        """Load all .tex files from templates directory"""
        self.available_templates = {}
        if os.path.exists(self.templates_dir):
            for file in os.listdir(self.templates_dir):
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
            
            print(f"✓ Found {len(self.available_templates)} templates in {self.templates_dir}")
        else:
            print(f"⚠ Warning: {self.templates_dir} directory not found")
        
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
    
    def load_latex_template(self, file_path):
        """Load LaTeX template from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.latex_template = f.read()
            return True
        except Exception as e:
            print(f"Error loading LaTeX template: {e}")
            return False
    
    def load_template_by_name(self, template_name):
        """Load a specific template by name"""
        if template_name in self.available_templates:
            template_info = self.available_templates[template_name]
            try:
                with open(template_info['path'], 'r', encoding='utf-8') as f:
                    self.latex_template = f.read()
                self.current_template_type = template_info['type']
                return True
            except Exception as e:
                print(f"Error loading template {template_name}: {e}")
                return False
        return False
    
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
        job_frame = ttk.LabelFrame(setup_frame, text="Job Description", padding="10")
        job_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=5)
        setup_frame.grid_rowconfigure(3, weight=1)
        
        self.job_desc = scrolledtext.ScrolledText(job_frame, height=15, width=70, wrap=tk.WORD)
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
        
        # Style
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 12, 'bold'))
        
        # Populate templates
        self.refresh_templates()
        
    def refresh_templates(self):
        """Refresh the templates dropdown"""
        self.optimizer.load_available_templates()
        
        if self.optimizer.available_templates:
            # Create display names with type indicators
            template_names = []
            for name, info in self.optimizer.available_templates.items():
                if info['type'] == 'new_grad':
                    display_name = f"{name} [New Grad]"
                elif info['type'] == 'experienced':
                    display_name = f"{name} [Experienced]"
                else:
                    display_name = f"{name} [General]"
                template_names.append(display_name)
            
            self.template_dropdown['values'] = template_names
            if template_names:
                self.template_dropdown.current(0)
            
            self.status_label.config(text=f"Found {len(template_names)} templates", foreground="green")
        else:
            self.template_dropdown['values'] = []
            self.status_label.config(text=f"No templates found in {self.optimizer.templates_dir}", 
                                   foreground="orange")
            messagebox.showwarning("No Templates", 
                                 f"No .tex files found in '{self.optimizer.templates_dir}' folder.\n\n" +
                                 "Please add your resume templates there.")
    
    def load_selected_template(self):
        """Load the selected template"""
        if not self.template_var.get():
            messagebox.showerror("Error", "Please select a template first")
            return
        
        # Extract actual template name (remove type indicator)
        display_name = self.template_var.get()
        template_name = display_name.split(' [')[0]
        
        if self.optimizer.load_template_by_name(template_name):
            template_type = self.optimizer.current_template_type
            type_display = template_type.replace('_', ' ').title()
            self.template_status.config(
                text=f"✓ Loaded: {template_name} ({type_display} format)", 
                foreground="green"
            )
            self.status_label.config(text="Template loaded successfully", foreground="green")
        else:
            self.template_status.config(text="Failed to load template", foreground="red")
            self.status_label.config(text="Error loading template", foreground="red")
    
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
            
            # Get job description
            job_description = self.job_desc.get("1.0", tk.END).strip()
            
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
                self.root.after(0, lambda: self.status_label.config(
                    text="✓ Resume optimized successfully! Check the 'Generated Output' tab.", 
                    foreground="green"))
                
                # Switch to output tab
                self.root.after(0, lambda: self.notebook.select(1))
                
                # Show success message
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    "Resume optimization complete!\n\n" +
                    "You can now:\n" +
                    "1. Copy the LaTeX code to clipboard\n" +
                    "2. Save as a .tex file\n" +
                    "3. Paste into Overleaf to generate PDF"
                ))
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
            self.optimizer.setup_templates_directory()
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
    print("Reading resume from: input_resume.tex")
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
        print("4. Create input_resume.tex with your resume content")
        print("\nPress Enter to exit...")
        input()