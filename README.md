# LLM-Build-Error-Log-Summarizer

> **AI-powered software build and error log analysis using Google Gemini**

---

## Project Overview

**LLM-Build-Error-Log-Summarizer** is a web application that accepts software build logs and error logs and uses the Google Gemini large language model to summarize, explain, and suggest fixes for the errors found inside those logs.

The application is designed to help beginner developers understand complex terminal errors without manually reading lengthy and confusing log output.

---

## Problem Statement

Software developers — especially beginners — frequently encounter cryptic error messages during development, dependency installation, and build processes. Reading and understanding these messages requires experience and time. This project automates that analysis using a large language model, making error understanding accessible to everyone.

---

## Objectives

- Accept real-world build and error logs as input.
- Use Google Gemini to analyze the log and return a structured report.
- Display the report in a beginner-friendly format covering:
  1. Build Status
  2. Main Error
  3. Root Cause
  4. Explanation in Simple Words
  5. Suggested Fix
  6. Prevention Tips
- Provide a simple and professional user interface built with Streamlit.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3 | Core programming language |
| Streamlit | Web application framework |
| Google Gemini API | Large language model for log analysis |
| google-genai SDK | Official Python client for Gemini |
| python-dotenv | Load API key from `.env` file |
| Git + GitHub | Version control and code hosting |

---

## Features

- 📂 Upload `.log`, `.txt`, or `.out` log files directly.
- 📋 Choose from three built-in sample error logs for quick testing.
- ✏️ Paste any error log into the text area.
- 🤖 AI-powered analysis using Google Gemini (gemini-2.0-flash by default).
- 🔍 Structured six-section result display with expandable panels.
- ⚠️ Friendly error messages for missing API key, quota errors, and network issues.
- 🛡️ No API keys stored or displayed in the UI.

---

## Project Folder Structure

```
LLM-Build-Error-Log-Summarizer/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env                        # API key (not committed to Git)
├── .env.example                # Template for .env
├── .gitignore                  # Files excluded from Git
├── README.md                   # This documentation file
├── sample_logs/
│   ├── python_error.log        # Python ModuleNotFoundError sample
│   ├── dependency_error.log    # pip dependency build failure sample
│   └── build_failure.log       # TypeScript build error sample
└── tests/
    └── test_app.py             # Automated unit tests (unittest)
```

---

## Installation Instructions

### Prerequisites

- macOS (or Linux)
- Python 3.10 or later
- A Google Gemini API key (free tier available at [Google AI Studio](https://aistudio.google.com/app/apikey))

---

### Step 1 – Clone or Download the Repository

```bash
git clone https://github.com/<your-username>/LLM-Build-Error-Log-Summarizer.git
cd LLM-Build-Error-Log-Summarizer
```

---

### Step 2 – Create a Virtual Environment (macOS)

```bash
python3 -m venv venv
```

---

### Step 3 – Activate the Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` appear at the start of your terminal prompt.

---

### Step 4 – Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5 – Configure the Gemini API Key

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` in any text editor and replace the placeholder with your real API key:

```
GEMINI_API_KEY=your_actual_api_key_here
```

> ⚠️ **Never share or commit your `.env` file.** It is listed in `.gitignore` and will not be uploaded to GitHub.

---

## How to Run the Application

```bash
source venv/bin/activate
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`).  
Open that URL in your web browser to use the application.

---

## How to Run Automated Tests

```bash
source venv/bin/activate
python -m unittest discover -s tests -v
```

All tests mock the Gemini API, so **no live API key is required** to run the tests.

---

## Python Syntax Validation

```bash
python -m py_compile app.py && echo "Syntax OK"
```

---

## Example Usage

1. Open the application in your browser.
2. Choose **"Python ModuleNotFoundError"** from the sample log dropdown.
3. Click **"Summarize Error Log"**.
4. Review the six-section AI analysis result.

---

## Limitations

- Log size is limited to 50 KB per request.
- Only `.log`, `.txt`, and `.out` file formats are supported.
- Gemini API responses depend on internet connectivity.
- Free-tier API keys have usage quotas and rate limits.
- AI analysis accuracy depends on the quality and completeness of the log.

---

## Conclusion

LLM-Build-Error-Log-Summarizer demonstrates the practical application of large language models in AI-driven DevOps. By combining Streamlit's rapid UI development with Google Gemini's natural language understanding, this project delivers a tool that makes software debugging more accessible for beginner developers.

---

**Student:** Katakam Surya Teja  
**USN:** 24BTRAO017  
**Department:** CSE – AI Driven DevOps  
**Academic Year:** 2026–2027

