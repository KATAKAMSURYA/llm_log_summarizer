"""
LLM-Based Build/Error-Log Summarization
AI-powered software error analysis using Google Gemini.

Author: Katakam Surya Teja
USN: 24BTRAO017
Department: CSE – AI Driven DevOps
"""

import os
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

MAX_LOG_SIZE_BYTES = 50_000  # 50 KB limit

SAMPLE_LOGS = {
    "-- Select a sample log --": "",
    "Python ModuleNotFoundError": "sample_logs/python_error.log",
    "Dependency Installation Failure": "sample_logs/dependency_error.log",
    "TypeScript Build Failure": "sample_logs/build_failure.log",
}

SUPPORTED_EXTENSIONS = {".log", ".txt", ".out"}

# ---------------------------------------------------------------------------
# Gemini helpers
# ---------------------------------------------------------------------------

def get_gemini_client():
    """Create and return a configured Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. "
            "Please add your Gemini API key to the .env file."
        )
    return genai.Client(api_key=api_key)


def get_model_name():
    """Return the Gemini model name from env or fall back to a safe default."""
    return os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()


def build_prompt(log_text: str) -> str:
    """Build the structured prompt sent to Gemini."""
    return f"""You are an expert software build engineer and debugging assistant.

Analyze ONLY the following software build / error log and produce a concise,
structured report. Do NOT invent information that is not supported by the log.
If the root cause cannot be confirmed with certainty, say so clearly.

LOG:
\"\"\"
{log_text}
\"\"\"

Respond EXACTLY in the following six sections (use the exact headings):

## 1. Build Status
State whether the build/run succeeded or failed and in one sentence why.

## 2. Main Error
Quote the primary error message(s) found in the log.

## 3. Root Cause
Explain the most probable root cause of the failure.
If uncertain, say "Root cause cannot be confirmed from the log alone."

## 4. Explanation in Simple Words
Explain what went wrong in plain English that a beginner developer can understand.
Avoid jargon.

## 5. Suggested Fix
Give concrete, step-by-step fix instructions a beginner can follow.

## 6. Prevention Tips
List 2–4 tips the developer can follow to avoid this error in the future.
"""


def summarize_log(log_text: str) -> str:
    """
    Send the log to Gemini and return the structured summary.
    Retries once on transient HTTP 429 / 503 errors.
    """
    client = get_gemini_client()
    model = get_model_name()
    prompt = build_prompt(log_text)

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=1024,
                ),
            )
            return response.text

        except Exception as exc:
            error_str = str(exc)

            # Transient errors – retry once after a short pause
            if attempt == 0 and any(
                code in error_str for code in ("429", "503", "quota", "overloaded")
            ):
                time.sleep(5)
                continue

            # Classify and re-raise with a friendly message
            if "API_KEY_INVALID" in error_str or "API key not valid" in error_str:
                raise RuntimeError(
                    "Invalid Gemini API key. "
                    "Please check the GEMINI_API_KEY value in your .env file."
                ) from exc
            if "429" in error_str or "quota" in error_str.lower():
                raise RuntimeError(
                    "Gemini API quota exceeded. "
                    "Please wait a moment and try again, "
                    "or check your API usage limits."
                ) from exc
            if "503" in error_str or "overloaded" in error_str.lower():
                raise RuntimeError(
                    "Gemini service is temporarily unavailable. "
                    "Please try again in a few seconds."
                ) from exc
            if "timeout" in error_str.lower() or "timed out" in error_str.lower():
                raise RuntimeError(
                    "The request to Gemini timed out. "
                    "Please check your internet connection and try again."
                ) from exc
            if "network" in error_str.lower() or "connection" in error_str.lower():
                raise RuntimeError(
                    "A network error occurred while contacting Gemini. "
                    "Please check your internet connection."
                ) from exc

            raise RuntimeError(f"Gemini API error: {error_str}") from exc

    raise RuntimeError("Request failed after retries. Please try again later.")


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def validate_log(log_text: str) -> str | None:
    """
    Validate the log text.
    Returns an error message string if invalid, or None if valid.
    """
    if not log_text or not log_text.strip():
        return "Please provide a build / error log before summarizing."

    if len(log_text.encode("utf-8")) > MAX_LOG_SIZE_BYTES:
        size_kb = MAX_LOG_SIZE_BYTES // 1024
        return (
            f"The log is too large (limit: {size_kb} KB). "
            "Please paste a smaller portion of the log."
        )

    return None


def load_sample_log(path: str) -> str:
    """Read and return the contents of a sample log file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

def render_result(result_text: str):
    """Render the Gemini response in a readable format."""
    st.markdown("---")
    st.subheader("📋 Analysis Result")

    sections = [
        "## 1. Build Status",
        "## 2. Main Error",
        "## 3. Root Cause",
        "## 4. Explanation in Simple Words",
        "## 5. Suggested Fix",
        "## 6. Prevention Tips",
    ]

    # Split result into named sections for nicer rendering
    parts = {}
    current_key = None
    buffer = []

    for line in result_text.splitlines():
        matched = False
        for section in sections:
            if line.strip().startswith(section):
                if current_key is not None:
                    parts[current_key] = "\n".join(buffer).strip()
                current_key = section
                buffer = []
                matched = True
                break
        if not matched and current_key is not None:
            buffer.append(line)

    if current_key is not None:
        parts[current_key] = "\n".join(buffer).strip()

    icon_map = {
        "## 1. Build Status": "🔴",
        "## 2. Main Error": "⚠️",
        "## 3. Root Cause": "🔍",
        "## 4. Explanation in Simple Words": "💡",
        "## 5. Suggested Fix": "🔧",
        "## 6. Prevention Tips": "🛡️",
    }

    if parts:
        for section in sections:
            if section in parts and parts[section]:
                icon = icon_map.get(section, "•")
                label = section.replace("## ", "")
                with st.expander(f"{icon} {label}", expanded=True):
                    st.markdown(parts[section])
    else:
        # Fallback: render raw markdown if parsing failed
        st.markdown(result_text)


def main():
    st.set_page_config(
        page_title="LLM Build/Error-Log Summarizer",
        page_icon="🛠️",
        layout="centered",
    )

    # ---- Header ----
    st.title("🛠️ LLM-Based Build/Error-Log Summarization")
    st.markdown(
        "**AI-powered software error analysis using Google Gemini.**  \n"
        "Paste your build or error log below and get an instant, "
        "beginner-friendly explanation."
    )
    st.markdown("---")

    # ---- Session state ----
    if "log_content" not in st.session_state:
        st.session_state["log_content"] = ""
    if "result" not in st.session_state:
        st.session_state["result"] = ""

    # ---- Sidebar ----
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown(
            "This tool uses **Google Gemini** to analyze software build logs "
            "and explain errors in simple language."
        )
        st.markdown("**Student:** Katakam Surya Teja")
        st.markdown("**USN:** 24BTRAO017")
        st.markdown("**Dept:** CSE – AI Driven DevOps")
        st.markdown("---")
        st.markdown("**Supported formats:** `.log`, `.txt`, `.out`")
        st.markdown(f"**Max log size:** {MAX_LOG_SIZE_BYTES // 1024} KB")

    # ---- Input Section ----
    st.subheader("📂 Input Log")

    # 1. File uploader
    uploaded_file = st.file_uploader(
        "Upload a log file (.log, .txt, .out)",
        type=["log", "txt", "out"],
        help="Upload your build or error log file here.",
    )

    if uploaded_file is not None:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            st.error(
                f"Unsupported file type: `{ext}`. "
                f"Please upload a `.log`, `.txt`, or `.out` file."
            )
        else:
            raw = uploaded_file.read()
            if len(raw) > MAX_LOG_SIZE_BYTES:
                st.error(
                    f"File is too large ({len(raw) // 1024} KB). "
                    f"Limit is {MAX_LOG_SIZE_BYTES // 1024} KB."
                )
            else:
                st.session_state["log_content"] = raw.decode("utf-8", errors="replace")
                st.success(f"✅ File loaded: `{uploaded_file.name}`")

    st.markdown(" ")

    # 2. Sample log dropdown
    selected_sample = st.selectbox(
        "Or choose a sample log to test:",
        options=list(SAMPLE_LOGS.keys()),
    )

    if selected_sample and selected_sample != "-- Select a sample log --":
        sample_path = SAMPLE_LOGS[selected_sample]
        sample_content = load_sample_log(sample_path)
        if sample_content:
            st.session_state["log_content"] = sample_content
            st.info(f"📄 Sample log loaded: **{selected_sample}**")
        else:
            st.warning(f"Sample file not found: `{sample_path}`")

    st.markdown(" ")

    # 3. Text area
    log_input = st.text_area(
        "Or paste your error log here:",
        value=st.session_state["log_content"],
        height=280,
        placeholder="Paste your build output or error log here…",
        key="log_textarea",
    )
    # Keep session state in sync with manual edits
    st.session_state["log_content"] = log_input

    # ---- Action Buttons ----
    col1, col2 = st.columns([2, 1])

    with col1:
        summarize_clicked = st.button(
            "🔍 Summarize Error Log",
            type="primary",
            use_container_width=True,
        )

    with col2:
        clear_clicked = st.button(
            "🗑️ Clear Input",
            use_container_width=True,
        )

    if clear_clicked:
        st.session_state["log_content"] = ""
        st.session_state["result"] = ""
        st.rerun()

    # ---- Summarize ----
    if summarize_clicked:
        log_text = st.session_state["log_content"].strip()
        error_msg = validate_log(log_text)

        if error_msg:
            st.error(f"⚠️ {error_msg}")
        else:
            st.session_state["result"] = ""
            with st.spinner("🤖 Analyzing log with Google Gemini…"):
                try:
                    result = summarize_log(log_text)
                    st.session_state["result"] = result
                except RuntimeError as exc:
                    st.error(f"❌ {exc}")
                except Exception:
                    st.error(
                        "An unexpected error occurred. "
                        "Please check your API key and internet connection."
                    )

    # ---- Display Result ----
    if st.session_state.get("result"):
        render_result(st.session_state["result"])


if __name__ == "__main__":
    main()
