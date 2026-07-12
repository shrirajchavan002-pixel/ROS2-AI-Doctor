import sqlite3
import os
import json
import re
from datetime import datetime

BASE_DIR = os.path.expanduser("~/ros2_error_explainer")
DB_PATH = os.path.join(BASE_DIR, "history.db")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  error_log TEXT,
                  analysis TEXT,
                  status TEXT DEFAULT 'Resolved')''')
    conn.commit()
    conn.close()

def save_to_history(error_log, analysis):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO history (timestamp, error_log, analysis) VALUES (?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error_log, analysis))
        history_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Save persistent logs
        save_persistent_logs(history_id, error_log, analysis)
    except Exception:
        pass

def save_persistent_logs(history_id, error_log, analysis):
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = os.path.join(LOGS_DIR, f"diagnosis_{history_id:03d}_{timestamp_str}.md")
    json_path = os.path.join(LOGS_DIR, f"diagnosis_{history_id:03d}_{timestamp_str}.json")
    
    # Save Markdown
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# ROS2 AI Diagnosis Log\n\n**Timestamp:** {timestamp_str}\n\n")
        f.write(f"## Error Log\n```\n{error_log}\n```\n\n")
        f.write(f"## Analysis\n{analysis}\n")
        
    # Try to extract confidence for JSON
    conf_match = re.search(r"\*\*Confidence:\*\*\s*(\d+)%", analysis)
    confidence = int(conf_match.group(1)) if conf_match else 0
    
    # Save JSON
    log_data = {
        "id": history_id,
        "timestamp": timestamp_str,
        "error": error_log,
        "confidence_score": confidence,
        "analysis_raw": analysis,
        "status": "Archived"
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=4)

def get_past_memory_context():
    """AI Learning Memory: Fetch past errors to avoid repeating mistakes and learn from them."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT timestamp, error_log, analysis FROM history ORDER BY id DESC LIMIT 2")
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return "No previous learning memory available."
            
        memory_str = "[AI LEARNING MEMORY - Previous Diagnoses]:\n"
        for row in rows:
            memory_str += f"Occurred: {row[0]}\nError Snippet: {row[1][:150]}...\nStatus: Resolved\n---\n"
        return memory_str
    except Exception:
        return ""

def export_reports():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM history")
        rows = c.fetchall()
        conn.close()
        
        report_path = os.path.join(BASE_DIR, "report.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(f"--- {row[1]} ---\nError:\n{row[2]}\n\nAnalysis:\n{row[3]}\n\n")
        return report_path, f"Report exported successfully to {report_path}"
    except Exception as e:
        return "", f"Export failed: {e}"
