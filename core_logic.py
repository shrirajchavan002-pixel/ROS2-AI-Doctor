import os
import sys
from dotenv import load_dotenv
from google import genai

# Setup API
load_dotenv()
my_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=my_key)

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
    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt_instructions
        )
        return response.text
    except Exception as e:
        return f"\n⚠️ [API ERROR]: Google's AI servers are currently too busy. Please wait a few seconds and try again.\n(Details: {e})"

print("🤖 ROS2 Error Explainer (Fast CLI Mode) is ready!")
print("-" * 50)

while True:
    print("\n📥 Paste your ROS2 error below.")
    print("   (Press ENTER on an empty line to start analyzing)")
    print("   (Type 'QUIT' to exit)")
    print("👇--------------------------------------------------👇")
    
    lines = []
    
    while True:
        line = input()
        
        # If user types quit
        if line.strip().upper() == 'QUIT':
            print("\nGoodbye! Keep coding! 💻\n")
            sys.exit()
            
        # The Magic "Double Enter" trick: 
        # If the line is completely empty (they just pressed Enter), break the loop and analyze!
        if line == "":
            break
            
        lines.append(line)
        
    user_error = "\n".join(lines)
    
    if user_error.strip() == "":
        continue
        
    print("\n🚀 Analyzing error...\n")
    final_explanation = explain_ros2_error(user_error)
    print(final_explanation)
    print("\n" + "=" * 50)
