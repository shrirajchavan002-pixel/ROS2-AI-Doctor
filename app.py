import os
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai

# --- PAGE CONFIGURATION (Must be at the very top) ---
st.set_page_config(page_title="ROS2 Analyzer", page_icon="🦾", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS ---
# This hides the Streamlit menu and footer to make it look like a real app
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 1. Setup API key and client
load_dotenv()
my_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=my_key)

# 2. AI Function
def explain_ros2_error(error_text):
    prompt_instructions = f"""
    You are an expert ROS2 coding mentor. The student encountered this error:
    {error_text}

    NEVER give long paragraphs. Be extremely concise. 
    Always use this exact format:

    ❌ Error:
    (One-line summary)

    📌 Cause:
    • (Point 1)
    • (Point 2)

    ✅ Fix:
    1. (Step 1)
    2. (Step 2)

    💻 Commands:
    ```bash
    # Exact commands only
    ```
    """
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=prompt_instructions
    )
    return response.text

# --- SIDEBAR (Robotics Dashboard Theme) ---
with st.sidebar:
    # Adding the official ROS logo from the internet!
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/b2/ROS_logo.svg", width=150)
    st.title("⚙️ Diagnostics")

    # Cool fake metrics to make it look like a real system monitor
    st.metric(label="API Status", value="Online", delta="Connected")
    st.metric(label="AI Core", value="Flash-Latest", delta="High Speed")

    st.markdown("---")
    st.markdown("### 👨‍💻 Lead Engineer")
    st.markdown("**Shriraj**")
    st.caption("BTech Robotics & Automation")
    st.markdown("---")
    st.info("System Ready. Waiting for trace logs...")

# --- MAIN PAGE UI ---
st.title("🦾 Advanced ROS2 Error Analyzer")
st.markdown("> **Automated Debugging Terminal for Robotics Engineers**")
st.divider()

# Split the screen into two columns
col1, col2 = st.columns(2)

# LEFT COLUMN: INPUT
with col1:
    with st.container(border=True):
        st.subheader("📥 Input Terminal")
        st.caption("Paste your ROS2, CMake, Colcon, or Python traceback:")

        # 'label_visibility="collapsed"' hides the default label for a cleaner look
        user_error = st.text_area("Traceback Log:", height=300, label_visibility="collapsed")

        # A button that stretches across the whole column
        analyze_button = st.button("🚀 Execute Analysis", type="primary", use_container_width=True)

# RIGHT COLUMN: OUTPUT
with col2:
    with st.container(border=True):
        st.subheader("📤 AI Output Engine")

        if analyze_button:
            if user_error.strip() == "":
                st.error("⚠️ [SYS_ERROR]: Input terminal is empty.")
            else:
                # Cool fake progress bar sequence
                progress_text = "Initializing AI analysis sequence..."
                my_bar = st.progress(0, text=progress_text)
                for percent_complete in range(100):
                    time.sleep(0.01) # Makes the bar load smoothly
                    my_bar.progress(percent_complete + 1, text="Extracting trace logs and querying Gemini Core...")
                my_bar.empty() # Hides the bar when done

                with st.spinner("Compiling fix sequence..."):
                    explanation = explain_ros2_error(user_error)
                    st.success("✅ Analysis Complete")
                    st.markdown(explanation)
        else:
            # This shows a gray placeholder text before the user clicks the button
            st.markdown("<br><br><br><br><br><center><p style='color:gray;'><i>Awaiting input trace...</i></p></center>", unsafe_allow_html=True)
