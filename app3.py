import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
from PIL import Image
import io
import time
import requests
import os
from typing import List, Optional
from pydantic import BaseModel

# For the CrewAI components (these would be imported in your actual implementation)
# from langchain.chat_models import ChatGroq
# from langchain.schema import SystemMessage
# from langchain.memory import ConversationBufferMemory
# from langchain.chains import ConversationChain
# from crewai import Agent, Task, Crew
# from crewai_tools import SerperDevTool
# from google import genai

# Set page configuration
st.set_page_config(
    page_title="AI Creative Suite",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define color scheme
PRIMARY_COLOR = "#ADD8E6"  # Light blue
SECONDARY_COLOR = "#F0F8FF"  # AliceBlue
TEXT_COLOR = "#2C3E50"  # Dark blue/gray

# Apply custom CSS
st.markdown(f"""
<style>
    .stApp {{
        background-color: white;
    }}
    .stButton>button {{
        background-color: {PRIMARY_COLOR};
        color: {TEXT_COLOR};
        border-radius: 6px;
        border: 1px solid {PRIMARY_COLOR};
        padding: 0.5rem 1rem;
        font-weight: 500;
    }}
    .stButton>button:hover {{
        background-color: white;
        color: {PRIMARY_COLOR};
        border: 1px solid {PRIMARY_COLOR};
    }}
    .card {{
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin: 10px;
        border: 1px solid #e0e0e0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
    }}
    .card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        border: 1px solid {PRIMARY_COLOR};
    }}
    .card-selected {{
        border: 2px solid {PRIMARY_COLOR};
        background-color: {SECONDARY_COLOR};
    }}
    .card-title {{
        font-weight: 600;
        font-size: 1.2rem;
        margin-bottom: 10px;
        color: {TEXT_COLOR};
    }}
    .bubble {{
        display: inline-block;
        background-color: {SECONDARY_COLOR};
        color: {TEXT_COLOR};
        border-radius: 16px;
        padding: 4px 12px;
        margin-right: 8px;
        margin-bottom: 8px;
        font-size: 0.85rem;
        font-weight: 500;
    }}
    .audio-preview {{
        width: 100%;
        margin: 10px 0;
    }}
    .pagination {{
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }}
    .pagination-button {{
        margin: 0 5px;
        cursor: pointer;
        padding: 5px 10px;
        border-radius: 4px;
        background-color: {PRIMARY_COLOR};
        color: {TEXT_COLOR};
    }}
    .main-header {{
        color: {TEXT_COLOR};
        text-align: center;
        margin-bottom: 30px;
        font-size: 2.5rem;
        font-weight: 700;
    }}
    .sub-header {{
        color: {TEXT_COLOR};
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 20px;
    }}
    .voice-card {{
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
    }}
    
    .voice-card:hover {{
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }}
    
    .voice-card.selected {{
        border: 2px solid #4CAF50;
        background-color: rgba(76, 175, 80, 0.05);
    }}
    
    .card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}
    
    .card-title {{
        font-weight: bold;
        font-size: 1.1em;
    }}
    
    .selection-indicator {{
        color: #4CAF50;
        font-weight: bold;
        font-size: 1.2em;
    }}
    
    .card-tags {{
        margin-bottom: 15px;
    }}
    
    .bubble {{
        background-color: #f0f0f0;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        margin-right: 5px;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'script' not in st.session_state:
    st.session_state.script = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'selected_voice' not in st.session_state:
    st.session_state.selected_voice = None
if 'selected_video_style' not in st.session_state:
    st.session_state.selected_video_style = None
if 'generated_audio' not in st.session_state:
    st.session_state.generated_audio = None
if 'generated_video' not in st.session_state:
    st.session_state.generated_video = None
if 'voice_page' not in st.session_state:
    st.session_state.voice_page = 1
if 'video_page' not in st.session_state:
    st.session_state.video_page = 1
if 'screenplay_images' not in st.session_state:
    st.session_state.screenplay_images = []
if 'campaign_summary' not in st.session_state:
    st.session_state.campaign_summary = ""
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

# Navigation functions
def go_to_home():
    st.session_state.page = "home"

def go_to_script_generator():
    st.session_state.page = "script_generator"

def go_to_audio_generator():
    st.session_state.page = "audio_generator"

def go_to_video_generator():
    st.session_state.page = "video_generator"

def go_to_screenplay_generator():
    st.session_state.page = "screenplay_generator"

def set_script(script_text):
    st.session_state.script = script_text
    go_to_audio_generator()

def select_voice(voice_id):
    st.session_state.selected_voice = voice_id

def select_video_style(style_id):
    st.session_state.selected_video_style = style_id

# ============================================================================
# Backend AI Functions (Adapted from the workflow code)
# ============================================================================

def initialize_llm():
    """Initialize the Groq LLM"""
    # In a production environment, you'd want to handle API keys securely
    # For example, using st.secrets or environment variables
    api_key = st.secrets.get("GROQ_API_KEY", "your_default_key")
    
    # This is a mock implementation
    # In your actual code, you would use:
    # return ChatGroq(
    #     model="gemma2-9b-it",
    #     temperature=0.7,
    #     max_tokens=2048
    # )
    return {"model": "gemma2-9b-it", "api_key": api_key}

def run_breifer(user_prompt):
    """
    Adapted from the breifer() function to work with Streamlit
    Instead of using input(), it takes a prompt parameter and returns the result
    """
    # In your actual implementation, you would initialize these components
    # llm = initialize_llm()
    # system_prompt = SystemMessage(content=prompt_text)
    # memory = ConversationBufferMemory(return_messages=True)
    # memory.chat_memory.add_message(system_prompt)
    # conversation_chain = ConversationChain(llm=llm, memory=memory, verbose=False)
    
    # This is a simulated implementation for demonstration
    time.sleep(2)  # Simulate API call
    
    # For demo purposes, we'll generate a mock response
    marker = "========== Final Brief =========="
    response = f"""Based on your prompt: "{user_prompt}", I've analyzed your campaign needs.

{marker}

Campaign Type: Social Media Advertisement
Target Audience: Young adults (18-35)
Primary Goal: Increase brand awareness and drive sales
Key Message: The product offers a unique solution to a common problem
Tone: Casual and friendly
Special Requirements: Include a clear call-to-action
Platform Focus: Instagram and TikTok
"""
    
    # Extract the summary part after the marker
    if marker in response:
        summary = response.split(marker, 1)[1].strip()
        return summary
    
    return response

def clean_campaign_summary(text):
    """
    Clean the summary from the breifer output
    Adapted from clean_summary() in the original code
    """
    lines = text.strip().split('\n')
    cleaned = ["Cleaned Campaign Summary:\n"]
    for line in lines:
        line = line.strip()
        # Skip unwanted lines
        if not line or line.startswith("✅") or line == "=" or "To be determined" in line or line == "END OF CHAT":
            continue
        cleaned.append(line)

    return "\n".join(cleaned)

def run_crew(cleaned_summary):
    """
    Run the CrewAI workflow to generate script
    Adapted from the crew() function
    """
    # This is a simulated implementation for demonstration
    time.sleep(3)  # Simulate API call
    
    # Mock response structure
    script_result = {
        "title": "Product Awareness Campaign",
        "style": "ugc",
        "hook": "Hey! Ever struggled with [common problem]? I know I have...",
        "body": "I discovered [product] last month and it's been a game changer. Not only does it [benefit 1], but it also [benefit 2]. The best part? It's affordable and easy to use!",
        "cta": "Check out their website to get 20% off your first purchase. Trust me, you won't regret it!",
        "final_script": "Hey! Ever struggled with [common problem]? I know I have...\n\nI discovered [product] last month and it's been a game changer. Not only does it [benefit 1], but it also [benefit 2]. The best part? It's affordable and easy to use!\n\nCheck out their website to get 20% off your first purchase. Trust me, you won't regret it!"
    }
    
    return script_result

def run_screen_crew(cleaned_summary, script_style="screenplay"):
    """
    Run the screenplay generation workflow
    Adapted from the screen_crew() function
    """
    # This is a simulated implementation for demonstration
    time.sleep(4)  # Simulate API call
    
    # Mock response with screenplay and image prompts
    if script_style == "screenplay":
        result = {
            "title": "Brand Story",
            "style": "screenplay",
            "screenplay": """FADE IN:

EXT. CITY STREET - DAY

A YOUNG PROFESSIONAL (28) hurries down a busy sidewalk, looking stressed.

YOUNG PROFESSIONAL
(to phone)
I'm going to be late again!

They accidentally bump into a FRIENDLY STRANGER (30s) who is using [product].

FRIENDLY STRANGER
Whoa, careful there!

The Young Professional notices the product.

YOUNG PROFESSIONAL
Sorry! What's that you're using?

FRIENDLY STRANGER
This? It's changed my whole routine.
Let me show you...

MONTAGE - PRODUCT IN USE

The product solving various problems effortlessly.

CUT TO:

EXT. CITY STREET - LATER

The Young Professional smiles, now relaxed, using the product.

YOUNG PROFESSIONAL
(to camera)
Why didn't I discover this sooner?

FADE OUT.

TEXT ON SCREEN: "[Product Name]. Available Now."
""",
            "image_prompts": [
                "A busy city street with young professionals hurrying, mid-day lighting, shallow depth of field, cinematic composition",
                "Close-up of two people looking at a sleek modern product, with interested expressions, soft lighting, urban background",
                "Montage of product being used in different settings - office, home, and outdoors, bright vibrant colors",
                "Same city street as beginning, but person looking relaxed and confident using the product, golden hour lighting"
            ]
        }
    else:
        # UGC style as fallback
        result = run_crew(cleaned_summary)
        
    return result

def get_replicas():
    """
    Get voice replicas from Tavus API
    Adapted from get_replicas() in original code
    """
    # In a production environment, use proper API key management
    api_key = st.secrets.get("TAVUS_API_KEY", "d57e6c687a894213aa87abad7c1c5f56")
    
    try:
        url = "https://tavusapi.com/v2/replicas"
        headers = {"x-api-key": api_key}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            df_extracted = pd.json_normalize(data['data'])
            df_selected = df_extracted[['thumbnail_video_url', 'model_name', 'replica_id', 'replica_name']]
            return df_selected
        else:
            # If API call fails, return mock data for demonstration
            return get_mock_voice_samples()
    except Exception as e:
        st.error(f"Error fetching voice replicas: {str(e)}")
        return get_mock_voice_samples()

def call_tavus(background_url, replica_id, script, audio_url, video_name):
    """
    Generate a video using Tavus API
    Adapted from call_tavus() in original code
    """
    # In a production environment, use proper API key management
    api_key = st.secrets.get("TAVUS_API_KEY", "d57e6c687a894213aa87abad7c1c5f56")
    
    url = "https://tavusapi.com/v2/videos"
    payload = {
        "background_url": background_url,
        "replica_id": replica_id,
        "script": script,
        "audio_url": audio_url,
        "video_name": video_name
    }
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        st.error(f"Error calling Tavus API: {str(e)}")
        return {"error": str(e)}

def generate_images_from_prompts(image_prompts):
    """
    Generate images using Google Gemini API
    Adapted from the image generation code in the original workflow
    """
    # In a production environment, use proper API key management
    api_key = st.secrets.get("GEMINI_API_KEY", "AIzaSyBLzfjImenFp60acvXgKygaEDKGqKfHyKI")
    
    # This is a simulated implementation for demonstration
    generated_images = []
    
    # In your actual implementation, you would use:
    # client = genai.Client(api_key=api_key)
    
    for i, prompt in enumerate(image_prompts):
        time.sleep(1)  # Simulate API call
        
        # Create a placeholder image
        img = Image.new('RGB', (640, 360), color=(173, 216, 230))
        
        # Save to a BytesIO object
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        
        # Add to results
        generated_images.append({
            "prompt": prompt,
            "image": img_byte_arr.getvalue()
        })
    
    return generated_images

# ============================================================================
# Mock Data Functions (For demonstration when APIs are not available)
# ============================================================================

def get_mock_voice_samples(page=1, per_page=6):
    """Generate mock voice data for demonstration"""
    # This would be replaced with actual API calls to get_replicas()
    all_voices = [
        {"id": i, "name": f"Voice {i}", "gender": "Female" if i % 2 == 0 else "Male", 
         "style": ["Friendly", "Professional"][i % 2], "language": "English",
         "sample": f"sample_audio_{i}.mp3", "replica_id": f"replica_{i}"} for i in range(1, 21)
    ]
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    return all_voices[start_idx:end_idx], len(all_voices)

def get_video_styles(page=1, per_page=6):
    """Generate mock video style data for demonstration"""
    all_styles = [
        {"id": i, "name": f"Style {i}", 
         "description": f"Creative video style {i} with unique visual elements",
         "preview": f"video_preview_{i}.mp4"} for i in range(1, 21)
    ]
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    return all_styles[start_idx:end_idx], len(all_styles)

# ============================================================================
# Streamlit UI Components
# ============================================================================

def render_sidebar():
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=AI+Suite", width=150)
        st.markdown("### Navigation")
        
        if st.button("🏠 Home", key="nav_home"):
            go_to_home()
            
        if st.button("📝 Script Generator", key="nav_script"):
            go_to_script_generator()
            
        if st.session_state.script:
            if st.button("🎙️ Audio Generator", key="nav_audio"):
                go_to_audio_generator()
                
            if st.button("🎬 Video Generator", key="nav_video"):
                go_to_video_generator()
                
        if st.button("🎭 Screenplay Generator", key="nav_screenplay"):
            go_to_screenplay_generator()
            
        st.markdown("---")
        st.markdown("### Current Progress")
        
        progress_items = {
            "Script": "✅" if st.session_state.script else "❌",
            "Voice": "✅" if st.session_state.selected_voice else "❌",
            "Audio": "✅" if st.session_state.generated_audio else "❌",
            "Video": "✅" if st.session_state.generated_video else "❌"
        }
        
        for item, status in progress_items.items():
            st.markdown(f"{status} {item}")

def render_home():
    st.markdown("<h1 class='main-header'>AI Creative Suite</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; margin-bottom: 40px;'>Transform your ideas into professional scripts, audio, and videos with AI</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-title">AI Creative Generator</div>
            <p>Create professional scripts, audio, and videos using our AI tools. Start from scratch or use your existing script.</p>
            <p>Perfect for content creators, marketers, and storytellers.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Start Creating", key="start_creating"):
            if st.session_state.script:
                go_to_audio_generator()
            else:
                go_to_script_generator()
    
    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-title">Screenplay Generator</div>
            <p>Create professional screenplays with our AI-powered tools. Visualize your story with generated images.</p>
            <p>Perfect for screenwriters, filmmakers, and visual storytellers.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Create Screenplay", key="create_screenplay"):
            go_to_screenplay_generator()
    
    st.markdown("---")
    
    st.markdown("<h2 class='sub-header'>How It Works</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-title">1. Create Script</div>
            <p>Generate a professional script using our AI chat interface or upload your own.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-title">2. Generate Audio</div>
            <p>Select from a variety of AI voices or upload your own audio recording.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-title">3. Create Video</div>
            <p>Choose a video style and generate a professional video with your script and audio.</p>
        </div>
        """, unsafe_allow_html=True)

def render_script_generator():
    st.markdown("<h1 class='main-header'>Script Generator</h1>", unsafe_allow_html=True)
    
    # Two options: Generate with AI or Upload
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3>Generate with AI</h3>", unsafe_allow_html=True)
        
        script_style = st.radio(
            "Choose script style:",
            ["UGC (User Generated Content)", "Screenplay (Cinematic)"],
            key="script_style"
        )
        
        user_prompt = st.text_area("Describe what kind of script you want to create:", 
                                  height=100, 
                                  placeholder="Example: A 30-second commercial for a new coffee brand targeting young professionals...")
        
        if st.button("Generate Script", key="gen_script_btn"):
            if user_prompt:
                with st.spinner("Generating your script..."):
                    # In real implementation, call your AI workflow
                    st.session_state.is_processing = True
                    
                    # First run the breifer to get campaign summary
                    summary = run_breifer(user_prompt)
                    cleaned_summary = clean_campaign_summary(summary)
                    st.session_state.campaign_summary = cleaned_summary
                    
                    # Then run the crew or screen_crew based on the selected style
                    if "Screenplay" in script_style:
                        result = run_screen_crew(cleaned_summary, "screenplay")
                        st.session_state.script = result["screenplay"]
                        
                        # Store image prompts for later use
                        if "image_prompts" in result:
                            st.session_state.screenplay_images = result["image_prompts"]
                    else:
                        result = run_crew(cleaned_summary)
                        st.session_state.script = result["final_script"]
                    
                    st.session_state.is_processing = False
                    st.success("Script generated successfully!")
                    st.rerun()
            else:
                st.warning("Please provide a description of the script you want to create.")
                
        # Chat interface for refining the script
        st.markdown("---")
        st.markdown("<h3>Refine with Chat</h3>", unsafe_allow_html=True)
        
        for message in st.session_state.chat_history:
            role = "🧑‍💼 You" if message["role"] == "user" else "🤖 AI"
            st.markdown(f"**{role}**: {message['content']}")
        
        user_message = st.text_input("Ask for changes or refinements:", key="chat_input")
        
        if st.button("Send", key="send_chat"):
            if user_message:
                # Add user message to chat history
                st.session_state.chat_history.append({"role": "user", "content": user_message})
                
                # Simulate AI response
                with st.spinner("AI is thinking..."):
                    time.sleep(1.5)
                    ai_response = f"I've refined the script based on your request: '{user_message}'. The changes have been applied."
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                    
                    # In a real implementation, you would update the script here
                    if st.session_state.script:
                        st.session_state.script += "\n\n[Updated based on user feedback]"
                
                st.rerun()
    
    with col2:
        st.markdown("<h3>Upload Your Script</h3>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Upload a script file", type=["txt", "docx", "pdf"])
        
        if uploaded_file is not None:
            # In a real implementation, you would parse the file content
            file_content = uploaded_file.getvalue().decode("utf-8") if uploaded_file.type == "text/plain" else "Script content from uploaded file"
            st.session_state.script = file_content
            st.success(f"Uploaded script: {uploaded_file.name}")
        
        # Preview area
        st.markdown("---")
        st.markdown("<h3>Script Preview</h3>", unsafe_allow_html=True)
        
        if st.session_state.script:
            st.text_area("Your script:", value=st.session_state.script, height=400, key="script_preview")
            
            if st.button("Edit Script", key="edit_script"):
                # Enable editing
                pass
                
            if st.button("Proceed to Audio Generation", key="proceed_to_audio"):
                go_to_audio_generator()
        else:
            st.info("No script available yet. Generate or upload a script to see preview.")

def render_audio_generator():
    st.markdown("<h1 class='main-header'>Audio Generator</h1>", unsafe_allow_html=True)
    
    if not st.session_state.script:
        st.warning("You need a script first. Please generate or upload a script.")
        if st.button("Go to Script Generator"):
            go_to_script_generator()
        return
    
    # Voice selection area
    st.markdown("<h3>Select a Voice</h3>", unsafe_allow_html=True)
    
    # Get actual voices from Tavus API instead of mock data
    try:
        replicas_df = get_replicas()
        voices = []
        
        for i, row in replicas_df.iterrows():
            voices.append({
                "id": i,
                "name": row["replica_name"],
                "gender": "Female" if i % 2 == 0 else "Male",  # This would need to be derived from actual data
                "style": "Professional",  # This would need to be derived from actual data
                "language": "English",  # This would need to be derived from actual data
                "sample": row["thumbnail_video_url"],
                "replica_id": row["replica_id"]
            })
            
        total_voices = len(voices)
        page = st.session_state.voice_page
        per_page = 6
        
        # Paginate the voices
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_voices)
        displayed_voices = voices[start_idx:end_idx]
        total_pages = (total_voices + per_page - 1) // per_page
        
    except Exception as e:
        st.error(f"Error fetching voices: {str(e)}")
        displayed_voices, total_voices = get_mock_voice_samples(page=st.session_state.voice_page)
        total_pages = (total_voices + 5) // 6
    
    # Display voice cards in a grid
    cols = st.columns(3)
    for i, voice in enumerate(displayed_voices):
        with cols[i % 3]:
            is_selected = st.session_state.selected_voice == voice["id"]
            card_class = "voice-card selected" if is_selected else "voice-card"
            
            st.markdown(f"""
            <div class="{card_class}">
                <div class="card-header">
                    <div class="card-title">{voice["name"]}</div>
                    <div class="selection-indicator">{'✓' if is_selected else ''}</div>
                </div>
                <div class="card-tags">
                    <span class="bubble">{voice["gender"]}</span>
                    <span class="bubble">{voice["style"]}</span>
                    <span class="bubble">{voice["language"]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # For demonstration, we'll use a placeholder or the actual video URL if available
            if "sample" in voice and voice["sample"]:
                st.video(voice["sample"])
            else:
                # Fallback to audio sample
                st.audio(f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{voice['id']}.mp3")
            
            # Button to select this voice
            if st.button(f"Select {voice['name']}", key=f"select_btn_{voice['id']}"):
                st.session_state.selected_voice = voice["id"]
                # Store the actual replica_id for API calls
                if "replica_id" in voice:
                    st.session_state.selected_replica_id = voice["replica_id"]
                st.rerun()
    
    # Pagination controls
    st.markdown("<div class='pagination'>", unsafe_allow_html=True)
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if st.session_state.voice_page > 1:
            if st.button("← Previous", key="prev_voice_page"):
                st.session_state.voice_page -= 1
                st.rerun()
                
    with cols[1]:
        st.markdown(f"<p style='text-align: center;'>Page {st.session_state.voice_page} of {total_pages}</p>", unsafe_allow_html=True)
        
    with cols[2]:
        if st.session_state.voice_page < total_pages:
            if st.button("Next →", key="next_voice_page"):
                st.session_state.voice_page += 1
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Upload own audio option
    st.markdown("---")
    st.markdown("<h3>Or Upload Your Own Audio</h3>", unsafe_allow_html=True)
    
    uploaded_audio = st.file_uploader("Upload an audio file", type=["mp3", "wav", "ogg"])
    
    if uploaded_audio is not None:
        st.audio(uploaded_audio)
        st.session_state.generated_audio = uploaded_audio
        st.success("Audio uploaded successfully!")
    
    # Generate audio button
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Generate Audio", key="gen_audio_btn", disabled=not st.session_state.selected_voice and not uploaded_audio):
            if st.session_state.selected_voice:
                with st.spinner("Generating audio..."):
                    # In a real implementation, this would call ElevenLabs or another audio generation API
                    # You would adapt your audio_generation() function to work with the Streamlit UI
                    
                    # Simulate audio generation
                    time.sleep(2)
                    
                    # For demonstration, we'll use a placeholder audio
                    audio_file = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
                    st.session_state.generated_audio = audio_file
                    st.success("Audio generated successfully!")
                    st.audio(audio_file)
    
    with col2:
        if st.session_state.generated_audio and st.button("Proceed to Video Generation", key="proceed_to_video"):
            go_to_video_generator()
    
    # Preview area for the script
    st.markdown("---")
    st.markdown("<h3>Script Preview</h3>", unsafe_allow_html=True)
    
    with st.expander("View Script", expanded=False):
        st.markdown(st.session_state.script)

def render_video_generator():
    st.markdown("<h1 class='main-header'>Video Generator</h1>", unsafe_allow_html=True)
    
    if not st.session_state.script:
        st.warning("You need a script first. Please generate or upload a script.")
        if st.button("Go to Script Generator"):
            go_to_script_generator()
        return
    
    # Video style selection area
    st.markdown("<h3>Select a Video Style</h3>", unsafe_allow_html=True)
    
    # Get paginated video styles
    video_styles, total_styles = get_video_styles(page=st.session_state.video_page)
    total_pages = (total_styles + 5) // 6  # 6 items per page, rounded up
    
    # Display video style cards in a grid
    cols = st.columns(3)
    for i, style in enumerate(video_styles):
        with cols[i % 3]:
            # Check if this style is selected
            is_selected = st.session_state.selected_video_style == style["id"]
            card_class = "card card-selected" if is_selected else "card"
            
            # Extract characteristic tags from description
            characteristics = [
                f"Cinematic", 
                f"HD Quality", 
                f"{['Modern', 'Vintage', 'Futuristic'][i % 3]}"
            ]
            
            st.markdown(f"""
            <div class="{card_class}">
                <div class="card-title">{style["name"]}</div>
                <div>
                    <span class="bubble">{characteristics[0]}</span>
                    <span class="bubble">{characteristics[1]}</span>
                    <span class="bubble">{characteristics[2]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Create placeholder preview image
            placeholder = get_placeholder_image(300, 200, f"Style {style['id']}")
            st.image(placeholder, use_column_width=True)
            
            if st.button("Select" if not is_selected else "Selected", key=f"select_video_{style['id']}"):
                select_video_style(style["id"])
                st.rerun()
    
    # Pagination controls
    st.markdown("<div class='pagination'>", unsafe_allow_html=True)
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if st.session_state.video_page > 1:
            if st.button("← Previous", key="prev_video_page"):
                st.session_state.video_page -= 1
                st.rerun()
                
    with cols[1]:
        st.markdown(f"<p style='text-align: center;'>Page {st.session_state.video_page} of {total_pages}</p>", unsafe_allow_html=True)
        
    with cols[2]:
        if st.session_state.video_page < total_pages:
            if st.button("Next →", key="next_video_page"):
                st.session_state.video_page += 1
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Video background URL
    st.markdown("---")
    st.markdown("<h3>Video Background</h3>", unsafe_allow_html=True)
    
    background_url = st.text_input("Enter background video URL (optional):", 
                                placeholder="https://example.com/background-video.mp4")
    
    # Audio selection for the video
    st.markdown("---")
    st.markdown("<h3>Audio Selection</h3>", unsafe_allow_html=True)
    
    audio_option = st.radio(
        "Choose audio source:",
        ["Use Generated Audio", "Upload New Audio"]
    )
    
    if audio_option == "Use Generated Audio":
        if st.session_state.generated_audio:
            st.success("Using previously generated audio")
            # In a real implementation, you would play the audio here
            if isinstance(st.session_state.generated_audio, str) and st.session_state.generated_audio.startswith("http"):
                st.audio(st.session_state.generated_audio)
        else:
            st.warning("No generated audio found. Please generate audio first.")
            if st.button("Go to Audio Generator"):
                go_to_audio_generator()
    else:
        uploaded_audio = st.file_uploader("Upload an audio file for the video", type=["mp3", "wav", "ogg"], key="video_audio_upload")
        if uploaded_audio is not None:
            st.audio(uploaded_audio)
            st.session_state.generated_audio = uploaded_audio
            st.success("Audio uploaded successfully!")
    
    # Video name
    video_name = st.text_input("Enter a name for your video:", placeholder="My AI Video")
    
    # Generate video button
    st.markdown("---")
    
    if st.button("Generate Video", key="gen_video_btn", disabled=not st.session_state.selected_video_style or not st.session_state.generated_audio):
        if st.session_state.selected_video_style and st.session_state.generated_audio and video_name:
            with st.spinner("Generating video... This may take a few moments."):
                # Call the Tavus API to generate the video
                # In a real implementation, you would use the proper call_tavus() function
                
                # Get the replica_id for the selected voice
                replica_id = st.session_state.get("selected_replica_id", "default_replica_id")
                
                # Prepare audio_url (in a real implementation, you'd need to upload the audio file and get a URL)
                audio_url = ""
                if isinstance(st.session_state.generated_audio, str) and st.session_state.generated_audio.startswith("http"):
                    audio_url = st.session_state.generated_audio
                
                # Call Tavus API
                result = call_tavus(
                    background_url=background_url,
                    replica_id=replica_id,
                    script=st.session_state.script,
                    audio_url=audio_url,
                    video_name=video_name
                )
                
                if "error" in result:
                    st.error(f"Error generating video: {result['error']}")
                else:
                    # In a real implementation, you would handle the Tavus API response properly
                    # For now, we'll simulate a successful response
                    st.session_state.generated_video = "generated_video.mp4"
                    st.success("Video generation initiated! Check back in a few minutes for the final result.")
                    
                    # Display a placeholder for the video
                    placeholder = get_placeholder_image(640, 360, "Video Processing")
                    st.image(placeholder, use_column_width=True)
                    
                    st.info("The video is being processed by Tavus. Once complete, you'll be able to download it.")
        else:
            if not video_name:
                st.warning("Please provide a name for your video.")

def render_screenplay_generator():
    st.markdown("<h1 class='main-header'>Screenplay Generator</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("<h3>Write Your Screenplay</h3>", unsafe_allow_html=True)
        
        user_prompt = st.text_area("Describe what kind of screenplay you want:", height=100, 
                              placeholder="Example: A short film about a person discovering a hidden talent...",
                              key="screenplay_prompt")
        
        screenplay = st.text_area("Or directly write/edit your screenplay:", height=300, 
                                placeholder="EXT. FOREST - DAY\n\nA small clearing in a dense forest. Sunlight filters through the canopy...",
                                value=st.session_state.script if st.session_state.script else "")
        
        generate_screenplay = st.button("Generate New Screenplay", key="gen_screenplay")
        generate_images = st.button("Generate Images from Screenplay", key="gen_screenplay_images")
        
        if generate_screenplay:
            if user_prompt:
                with st.spinner("Generating screenplay from your description..."):
                    # In a real implementation, call your AI screenplay generator
                    # This would use the screen_crew() function from your workflow
                    st.session_state.is_processing = True
                    
                    # Run the screenplay generation workflow
                    result = run_screen_crew(user_prompt, "screenplay")
                    
                    if "screenplay" in result:
                        st.session_state.script = result["screenplay"]
                        
                    # Store image prompts for later use
                    if "image_prompts" in result:
                        st.session_state.screenplay_images = result["image_prompts"]
                    
                    st.session_state.is_processing = False
                    st.success("Screenplay generated successfully!")
                    st.rerun()
            else:
                st.warning("Please provide a description for your screenplay.")
        
        if generate_images and screenplay:
            with st.spinner("Analyzing screenplay and generating images..."):
                st.session_state.script = screenplay  # Save the screenplay
                
                # If we already have image prompts from a generated screenplay
                if st.session_state.screenplay_images:
                    image_prompts = st.session_state.screenplay_images
                else:
                    # In a real implementation, you would parse the screenplay to create image prompts
                    # For now, we'll create some simple prompts based on the screenplay length
                    scenes = [s for s in screenplay.split("EXT.") if s.strip()]
                    if not scenes:
                        scenes = [s for s in screenplay.split("INT.") if s.strip()]
                    
                    if not scenes:
                        # Just create generic prompts
                        image_prompts = [
                            "A cinematic scene from the screenplay, high quality, dramatic lighting",
                            "A character close-up from the screenplay, emotional, detailed",
                            "A wide establishing shot from the screenplay, cinematic composition"
                        ]
                    else:
                        # Create prompts based on scenes
                        image_prompts = [f"A cinematic shot of {scene[:50]}..." for scene in scenes[:3]]
                        
                        # Ensure we have at least 3 prompts
                        while len(image_prompts) < 3:
                            image_prompts.append("A cinematic scene from the screenplay, dramatic lighting")
                
                # Generate images using the prompts
                generated_images = generate_images_from_prompts(image_prompts)
                
                # Store results
                st.session_state.screenplay_images = image_prompts
                st.session_state.generated_screenplay_images = generated_images
                
                st.success("Images generated successfully!")
                st.rerun()
    
    with col2:
        st.markdown("<h3>Scene Previews</h3>", unsafe_allow_html=True)
        
        if hasattr(st.session_state, 'generated_screenplay_images') and st.session_state.generated_screenplay_images:
            for i, img_data in enumerate(st.session_state.generated_screenplay_images):
                st.markdown(f"**Scene {i+1}**")
                st.markdown(f"*Prompt: {img_data['prompt']}*")
                
                # Display the image
                st.image(img_data['image'], caption=f"Scene {i+1}", use_column_width=True)
        elif st.session_state.screenplay_images:
            for i, prompt in enumerate(st.session_state.screenplay_images):
                st.markdown(f"**Scene {i+1}**")
                st.markdown(f"*Prompt: {prompt}*")
                
                # Create a placeholder image
                placeholder = get_placeholder_image(400, 225, f"Scene {i+1}")
                st.image(placeholder, caption=f"Scene {i+1}", use_column_width=True)
        else:
            st.info("Generate images from your screenplay to see previews here.")
        
        if (hasattr(st.session_state, 'generated_screenplay_images') and st.session_state.generated_screenplay_images) or st.session_state.screenplay_images:
            if st.button("Proceed to Audio", key="screenplay_to_audio"):
                go_to_audio_generator()

# Main app logic
def main():
    render_sidebar()
    
    if st.session_state.page == "home":
        render_home()
    elif st.session_state.page == "script_generator":
        render_script_generator()
    elif st.session_state.page == "audio_generator":
        render_audio_generator()
    elif st.session_state.page == "video_generator":
        render_video_generator()
    elif st.session_state.page == "screenplay_generator":
        render_screenplay_generator()

if __name__ == "__main__":
    main()
