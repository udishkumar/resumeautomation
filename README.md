# LaTeX Resume Automation Tool 🚀

> **AI-Powered Resume Optimization with Claude API**  
> Transform your resume with strategic keyword optimization while preserving your beautiful LaTeX formatting.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Claude API](https://img.shields.io/badge/Claude_API-Sonnet_4-orange.svg)](https://www.anthropic.com/claude)
[![LaTeX](https://img.shields.io/badge/LaTeX-ModernCV-green.svg)](https://www.ctan.org/pkg/moderncv)
[![GUI](https://img.shields.io/badge/GUI-Tkinter-red.svg)](https://docs.python.org/3/library/tkinter.html)

## ✨ Features

### 🎯 **Strategic Resume Optimization**
- **ATS-Optimized**: 90%+ keyword match with job descriptions
- **Role-Specific Positioning**: Automatically detects Senior, Mid-level, or New Grad positions
- **Specialization Detection**: API Engineer, Full Stack, Mobile, Product Manager targeting
- **Quantified Impact**: Emphasizes metrics and business results

### 🎨 **Template Preservation**
- **Format Retention**: Preserves your LaTeX template's exact structure and styling
- **ModernCV Support**: Full color support for moderncv templates
- **Multiple Templates**: Support for New Grad, Experienced, and custom templates
- **Content-Only Updates**: Only optimizes text content, keeps all formatting

### 🤖 **Advanced AI Integration**
- **Claude Sonnet 4 & Opus 4**: Latest AI models for superior optimization
- **Strategic Bold Formatting**: Highlights key metrics and technologies
- **Natural Language Flow**: No keyword stuffing, authentic content
- **Context-Aware**: Adapts language based on role seniority and specialization

### 💼 **Enterprise-Grade Interface**
- **Professional GUI**: Clean, modern interface with enterprise styling
- **Real-Time Progress**: Beautiful spinning wheel with detailed status updates
- **PDF Generation**: Local compilation with LaTeX color support
- **Template Management**: Easy template loading and organization

## 🛠️ Installation

### Prerequisites
- **Python 3.8+**
- **LaTeX Distribution** (for PDF generation)
  - macOS: [MacTeX](https://tug.org/mactex/)
  - Windows: [MiKTeX](https://miktex.org/) or [TeX Live](https://www.tug.org/texlive/)
  - Linux: `sudo apt-get install texlive-full`
- **Claude API Key** from [Anthropic](https://console.anthropic.com/)

### Quick Setup

```bash
# Clone or download the tool
git clone <repository-url>
cd resume-automation-tool

# Create virtual environment (recommended)
python3 -m venv resume_env
source resume_env/bin/activate  # On Windows: resume_env\Scripts\activate

# Install dependencies
pip install anthropic

# Run the tool
python3 resume_automation.py
```

### Verify LaTeX Installation
```bash
# Check if LaTeX is properly installed
pdflatex --version
xelatex --version    # Recommended for moderncv colors
```

## 🚀 Quick Start

### 1. **Setup Templates**
Place your LaTeX resume templates in the `resume_templates/` folder:
```
resume_templates/
├── new_grad_resume.tex          # For new graduate positions
├── experienced_resume.tex       # For experienced positions  
├── api_engineer_resume.tex      # Custom specialized templates
└── product_manager_resume.tex
```

### 2. **Configure API Key**
- Get your Claude API key from [Anthropic Console](https://console.anthropic.com/)
- Enter it in the GUI and click "Save Key" for future use

### 3. **Generate Optimized Resume**
1. **Load Template**: Select and load your desired template
2. **Enter Company**: Specify company name for filename
3. **Paste Job Description**: Copy the complete job posting
4. **Generate**: Click "Generate Optimized Resume"
5. **Review**: PDF opens automatically or copy LaTeX for Overleaf

## 📋 Template Requirements

### Supported Formats
- **ModernCV** (recommended) - Full color support
- **Custom LaTeX** templates with standard commands
- **New Grad** vs **Experienced** template detection

### Template Structure
Your templates should include:
```latex
\documentclass[11pt,a4paper,sans]{moderncv}
\moderncvstyle{banking}  % or casual, classic, etc.
\moderncvcolor{blue}     % Full color support

\name{Your}{Name}
\title{Your Title}
% ... rest of your template
```

### Template Types
- **`new_grad_*.tex`**: Education → Skills → Projects → Experience
- **`experienced_*.tex`**: Professional Summary → Skills → Experience → Education → Projects
- **Custom**: Manually specify template type during loading

## 🎯 Optimization Features

### Strategic Content Enhancement
- **Keyword Integration**: Natural incorporation of job-specific terms
- **Quantified Results**: Emphasis on metrics and business impact
- **Technical Skills**: Reorganized to match job requirements
- **Professional Summary**: Enhanced with top keywords and achievements
- **Bold Formatting**: Strategic highlighting of key information

### Role-Specific Adaptations
- **Senior Roles**: Leadership, architecture, business impact, team management
- **New Grad**: Projects, internship impact, modern tech stack, learning agility  
- **Specialized**: Domain expertise, certifications, specific technologies

### Industry Standards
- **ATS Compatibility**: Standard headers, consistent formatting
- **6-Second Scan**: Key information immediately visible
- **Modern Positioning**: Current tech stack and methodologies

## 📁 File Organization

```
resume-automation-tool/
├── resume_automation.py          # Main application
├── resume_templates/              # Your LaTeX templates
│   ├── new_grad_resume.tex
│   ├── experienced_resume.tex
│   └── custom_template.tex
├── generated_resumes/             # Output folder
│   ├── CANDIDATE_COMPANY_DATE.pdf
│   ├── CANDIDATE_COMPANY_DATE.tex
│   └── error_logs/
├── config.ini                     # Encrypted API key storage
└── README.md                      # This file
```

## 🎨 GUI Features

### Modern Interface
- **Tabbed Layout**: Setup & Input | Generated Output
- **Template Management**: Easy loading and switching
- **Real-Time Validation**: Input checking and error handling
- **Progress Tracking**: Enterprise-style progress indicators

### Progress System
- **Spinning Wheel**: Professional animation during processing
- **Status Updates**: "Connecting to Claude AI", "Optimizing Content", etc.
- **Time Tracking**: Elapsed time display
- **Error Handling**: Detailed troubleshooting information

### Output Management
- **PDF Viewer**: One-click PDF opening
- **LaTeX Editor**: Copy optimized code to clipboard
- **File Management**: Direct access to output folder
- **Version Control**: Date-stamped file naming

## ⚙️ Configuration

### API Settings
- **Model Selection**: Choose between Sonnet 4 ($3/$15) or Opus 4 ($15/$75)
- **Secure Storage**: API keys encrypted and stored locally
- **Usage Tracking**: Monitor processing time and costs

### Template Settings
- **Auto-Detection**: Automatic template type recognition
- **Custom Loading**: Load templates from anywhere
- **Format Preservation**: Maintains exact LaTeX structure

## 🔧 Troubleshooting

### Common Issues

#### **"No LaTeX compiler found"**
```bash
# macOS
brew install --cask mactex

# Ubuntu/Debian
sudo apt-get install texlive-full

# Windows
# Download and install MiKTeX from https://miktex.org/
```

#### **"ModernCV colors not working"**
- Install complete LaTeX distribution (not minimal)
- Use XeLaTeX or LuaLaTeX instead of pdfLaTeX
- Alternative: Copy LaTeX code to Overleaf

#### **"API authentication failed"**
- Verify API key is correct
- Check internet connection
- Ensure sufficient API credits

#### **"Template failed to load"**
- Check LaTeX syntax in template
- Ensure proper encoding (UTF-8)
- Verify template is in `resume_templates/` folder

### PDF Generation Issues
1. **Install Full LaTeX**: Minimal installations lack packages
2. **Check Compiler**: XeLaTeX recommended for moderncv
3. **Use Overleaf**: Guaranteed to work with generated LaTeX
4. **Check Logs**: Error details saved in `generated_resumes/`

## 📊 Performance

### Typical Processing Times
- **Claude Sonnet 4**: 15-30 seconds
- **Claude Opus 4**: 20-45 seconds (higher quality)
- **PDF Generation**: 5-15 seconds (local LaTeX)
- **Total**: ~30-60 seconds end-to-end

### Cost Estimates (Per Resume)
- **Sonnet 4**: ~$0.15-0.30
- **Opus 4**: ~$0.75-1.50
- **Monthly Usage**: 50 resumes ≈ $7.50-75

## 🔒 Privacy & Security

### Data Handling
- **Local Processing**: All data stays on your machine
- **API Communication**: Only resume content sent to Claude
- **No Storage**: Anthropic doesn't store conversation data
- **Encrypted Keys**: API keys stored securely with base64 encoding

### Best Practices
- Use specific company names in job descriptions for better targeting
- Review generated content before sending
- Keep templates updated with latest experience
- Regular API key rotation recommended

## 🤝 Contributing

### Feature Requests
- Template format support (Awesome-CV, etc.)
- Additional AI model integration
- Batch processing capabilities
- Web interface option

### Bug Reports
Please include:
- Python version and OS
- LaTeX distribution and version
- Template type being used
- Complete error logs

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **Anthropic** for Claude API
- **ModernCV** LaTeX package authors
- **Python/Tkinter** for GUI framework
- **Community** for template contributions

---

## 📞 Support

Having issues? Check our troubleshooting guide above or:
- 📧 Open an issue with detailed error logs
- 💬 Include template type and job description format
- 🔍 Check console output for detailed debugging

**Made with ❤️ for job seekers everywhere**
