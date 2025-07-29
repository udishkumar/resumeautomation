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
        self.input_resume_path = "input_resume.tex"
        
        # Automatically load the input resume on initialization
        self.auto_load_resume()
        
    def auto_load_resume(self):
        """Automatically load the input_resume.tex file"""
        if os.path.exists(self.input_resume_path):
            try:
                with open(self.input_resume_path, 'r', encoding='utf-8') as f:
                    self.latex_template = f.read()
                print(f"✓ Automatically loaded resume from {self.input_resume_path}")
                return True
            except Exception as e:
                print(f"Error loading {self.input_resume_path}: {e}")
                return False
        else:
            print(f"⚠ Warning: {self.input_resume_path} not found")
            print("Please create this file with your resume content")
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
    
    def load_latex_template(self, file_path):
        """Load LaTeX template from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.latex_template = f.read()
            return True
        except Exception as e:
            print(f"Error loading LaTeX template: {e}")
            return False
    
    def reload_input_resume(self):
        """Reload the input resume file"""
        return self.auto_load_resume()
    
    def optimize_resume_latex(self, job_description, original_latex_content):
        """Send resume and job description to Claude for optimization"""
        
        prompt = f"""Expert ATS optimizer: Transform this LaTeX resume for 90%+ keyword match with the job description.

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
2. **Section Order**:
   - For NEW GRAD (less than 3 years experience): Professional Summary → Education → Skills → Projects → Experience
   - For EXPERIENCED (3+ years): Professional Summary → Skills → Experience → Education → Projects
3. Determine if candidate is new grad or experienced based on their work experience duration in the resume

RULES:
- Distinguish New Grad vs experienced roles based on years of experience
- Maintain authenticity while optimizing
- Natural language flow, no filler words
- Confident, results-oriented tone
- Professional Summary must be a paragraph (2-3 lines), NOT bullet points

DELIVERABLES:
Return ONLY the complete optimized LaTeX code ready for Overleaf compilation. Maintain exact document structure and packages from the original, but reorder sections according to the rules above.

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
        self.setup_gui()
        
    def setup_gui(self):
        """Create GUI elements"""
        self.root = tk.Tk()
        self.root.title("LaTeX Resume Automation Tool")
        self.root.geometry("900x700")
        
        # Main frame with scrollbar
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(main_frame, text="LaTeX Resume Automation Tool", font=('Arial', 18, 'bold'))
        title.pack(pady=10)
        
        description = ttk.Label(main_frame, text="Generate ATS-optimized LaTeX resumes using Claude AI", 
                               font=('Arial', 10))
        description.pack(pady=5)
        
        # API Key Section
        api_frame = ttk.LabelFrame(main_frame, text="API Configuration", padding="10")
        api_frame.pack(fill=tk.X, pady=10)
        
        api_inner = ttk.Frame(api_frame)
        api_inner.pack(fill=tk.X)
        ttk.Label(api_inner, text="Claude API Key:").pack(side=tk.LEFT)
        self.api_key_entry = ttk.Entry(api_inner, width=50, show="*")
        self.api_key_entry.pack(side=tk.LEFT, padx=5)
        
        # Model Selection
        model_frame = ttk.Frame(api_frame)
        model_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT)
        
        self.model_var = tk.StringVar(value="claude-sonnet-4-20250514")
        models = [
            ("Claude Sonnet 4 (Balanced - $3/$15)", "claude-sonnet-4-20250514"),
            ("Claude Opus 4 (Most Powerful - $15/$75)", "claude-opus-4-20250514"),
            ("Claude 3.5 Sonnet (Legacy - $3/$15)", "claude-3-5-sonnet-20241022")
        ]
        
        for i, (label, value) in enumerate(models):
            ttk.Radiobutton(model_frame, text=label, variable=self.model_var, 
                           value=value).pack(side=tk.LEFT, padx=5)
        
        # Resume Status Section
        resume_frame = ttk.LabelFrame(main_frame, text="Resume Status", padding="10")
        resume_frame.pack(fill=tk.X, pady=10)
        
        resume_status_frame = ttk.Frame(resume_frame)
        resume_status_frame.pack(fill=tk.X)
        
        # Check if input_resume.tex exists and show status
        if self.optimizer.latex_template:
            status_text = f"✓ Loaded from input_resume.tex"
            status_color = "green"
        else:
            status_text = "✗ input_resume.tex not found - please create this file"
            status_color = "red"
            
        self.resume_status = ttk.Label(resume_status_frame, text=status_text, foreground=status_color)
        self.resume_status.pack(side=tk.LEFT, padx=5)
        
        # Reload button
        self.reload_btn = ttk.Button(resume_status_frame, text="Reload Resume", 
                                    command=self.reload_resume)
        self.reload_btn.pack(side=tk.LEFT, padx=10)
        
        # Optional: Load different template button
        self.load_other_btn = ttk.Button(resume_status_frame, text="Load Different Template", 
                                        command=self.load_template)
        self.load_other_btn.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = ttk.Label(resume_frame, 
                               text="The tool automatically reads your resume from 'input_resume.tex'.\n" +
                                    "Make sure to update that file with your actual resume content.",
                               font=('Arial', 9), foreground="gray")
        instructions.pack(pady=(5, 0))
        
        # Job Info Section
        job_frame = ttk.LabelFrame(main_frame, text="Job Information", padding="10")
        job_frame.pack(fill=tk.X, pady=10)
        
        # Job Description
        ttk.Label(job_frame, text="Paste the job description below:").pack(anchor=tk.W, pady=(5, 5))
        self.job_desc = scrolledtext.ScrolledText(job_frame, height=12, width=80, wrap=tk.WORD)
        self.job_desc.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Output Section
        output_frame = ttk.LabelFrame(main_frame, text="Generated LaTeX Code", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=80, wrap=tk.NONE)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(output_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.copy_btn = ttk.Button(button_frame, text="Copy LaTeX to Clipboard", 
                                  command=self.copy_to_clipboard, state='disabled')
        self.copy_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(button_frame, text="Save as .tex File", 
                                  command=self.save_latex_file, state='disabled')
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Process button
        self.process_btn = ttk.Button(main_frame, text="Generate Optimized LaTeX Resume", 
                                     command=self.process_resume, 
                                     style='Accent.TButton')
        self.process_btn.pack(pady=10)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Ready", foreground="green")
        self.status_label.pack(pady=5)
        
        # Pack canvas and scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Style
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 12, 'bold'))
        
    def reload_resume(self):
        """Reload the input_resume.tex file"""
        if self.optimizer.reload_input_resume():
            self.resume_status.config(text="✓ Reloaded from input_resume.tex", foreground="green")
            self.status_label.config(text="Resume reloaded successfully", foreground="green")
        else:
            self.resume_status.config(text="✗ Failed to reload input_resume.tex", foreground="red")
            self.status_label.config(text="Error reloading resume", foreground="red")
            messagebox.showerror("Error", 
                               "Could not load input_resume.tex.\n" +
                               "Please make sure the file exists in the same directory as this script.")
    
    def load_template(self):
        """Load a different LaTeX template file"""
        file_path = filedialog.askopenfilename(
            title="Select LaTeX Template",
            filetypes=[("LaTeX Files", "*.tex"), ("All Files", "*.*")]
        )
        if file_path:
            if self.optimizer.load_latex_template(file_path):
                self.resume_status.config(text=f"✓ Loaded: {os.path.basename(file_path)}", foreground="green")
                self.status_label.config(text="LaTeX template loaded successfully", foreground="green")
            else:
                self.resume_status.config(text="Failed to load template", foreground="red")
                self.status_label.config(text="Error loading template", foreground="red")
    
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
                               "No resume loaded!\n\n" +
                               "Please create 'input_resume.tex' with your resume content,\n" +
                               "or use 'Load Different Template' to select another file.")
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
                    text="✓ Resume optimized successfully! Copy the LaTeX code or save as file.", 
                    foreground="green"))
                
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
        # Check if input_resume.tex exists on startup
        if not os.path.exists("input_resume.tex"):
            messagebox.showwarning("Setup Required", 
                                 "input_resume.tex not found!\n\n" +
                                 "Please create this file with your resume content.\n" +
                                 "You can also run simple_setup.py to create a template.")
        
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