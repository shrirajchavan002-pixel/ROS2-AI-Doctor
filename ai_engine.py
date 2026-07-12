import os
import re
from dotenv import load_dotenv
from groq import Groq
from diagnostics import scan_workspace_files, get_error_database_context
from history import get_past_memory_context

load_dotenv(override=True)

def analyze_error(error_text, workspace_scan_context=""):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY not found in .env file."

    client = Groq(api_key=api_key)
    
    internal_db = get_error_database_context()
    ai_memory = get_past_memory_context()

    system_prompt = (
        "You are an Elite Senior ROS2 Debugging AI Doctor.\n"
        "Analyze the error, workspace scan data, and past AI memory.\n\n"
        "CRITICAL RULES:\n"
        "1. NEVER GUESS as confirmed truth. You must distinguish between (✓ Confirmed, ⚠ Likely, ❓ Possible).\n"
        "2. EVERY conclusion needs Evidence.\n"
        "3. Calculate Confidence Score dynamically based ONLY on verified evidence.\n"
        "4. Any actionable command MUST be wrapped in ONE Markdown bash block.\n\n"
        "You MUST strictly output in this format:\n\n"
        "## 🎯 Confidence Score\n"
        "**Confidence:** [X]%\n"
        "**Reason:**\n"
        "✓ [Evidence present]\n"
        "✗ [Evidence missing]\n\n"
        "## 🔍 Evidence-Based Diagnosis\n"
        "**Evidence:**\n"
        "✓ [Confirmed fact 1]\n"
        "✗ [Unverified aspect]\n\n"
        "## 🚨 File-Level Diagnosis\n"
        "**File:** [Name] | **Line:** [Number] (Or N/A if not applicable)\n"
        "**Statement:** [Code snippet that failed]\n"
        "**Why it failed:** [Deep explanation]\n\n"
        "## ⚠️ Ranked Root Causes\n"
        "- ★★★★★ [Confirmed cause if evidence proves it, else Highly Likely]\n"
        "  - **Status:** [CONFIRMED / LIKELY / POSSIBLE]\n"
        "  - **Reason:** [Explain using evidence]\n"
        "- ★★★☆☆ [Possible secondary cause]\n\n"
        "## ⚙️ Diagnosis Timeline\n"
        "[E.g. Build -> CMake -> find_package() -> Missing -> Crash]\n\n"
        "## 🧠 Internal Explanation\n"
        "- [Step-by-step ROS2 internal breakdown]\n\n"
        "## 🛠️ Suggested File Changes\n"
        "**File:** `[Filename]`\n"
        "**Action:** [Add/Modify]\n"
        "```diff\n"
        "- Before\n"
        "+ After\n"
        "```\n\n"
        "## 📋 Recovery Plan\n"
        "**Step 1:** [Action]\n"
        "**Step 2:** [Action]\n\n"
        "## 💻 Actionable Fix Commands\n"
        "```bash\n"
        "[Single block of safe terminal commands]\n"
        "```\n\n"
        "## ✅ Intelligent Verification\n"
        "- `[command 1]`: [Expected specific output]\n\n"
        "## 🛡️ Prevention Tips\n"
        "- [Pro tip for future prevention]\n\n"
        "## 📚 Learning Section\n"
        "- [Internal ROS2 engineering concept related to this]\n\n"
        "## 🔗 Related Errors\n"
        "- [Same category errors e.g., PackageNotFoundError, etc.]"
    )

    user_content = f"{internal_db}\n\n{ai_memory}\n\n[Workspace Deep Scan]:\n{workspace_scan_context}\n\n[User Error Log]:\n{error_text}"

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2, # Keep it extremely logical and strictly factual
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"❌ Groq AI Error: {str(e)}"

def extract_command(analysis_text):
    match = re.search(r"```bash\n(.*?)\n```", analysis_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None
