from imagekitio import ImageKit
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
from PIL import Image
import io
import time
# Add at the top with other imports
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import base64
import uuid
import requests
import json

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
</style>
""", unsafe_allow_html=True)
# Add after st.set_page_config()
# Initialize the Google Gemini client
client = genai.Client(api_key="AIzaSyBLzfjImenFp60acvXgKygaEDKGqKfHyKI")

# Initialize the ImageKit client
imagekit = ImageKit(
    private_key='private_OGgux+C54n9PIYDlLdOrYysEWrw=',
    public_key='public_Qq9s197rBPKyx5eWhq+aN6TQ3Iw=',
    url_endpoint='https://ik.imagekit.io/b6pq3mgo7'
)

# Creatify API headers
creatify_headers = {
    "X-API-ID": "5f8b3a5c-6e33-4e9f-b85c-71941d675270",
    "X-API-KEY": "c019dd017d22e2e40627f87bc86168b631b9a345",
    "Content-Type": "application/json"
}

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
# Add to the session state initialization
if 'image_prompts' not in st.session_state:
    st.session_state.image_prompts = []
if 'generated_image_urls' not in st.session_state:
    st.session_state.generated_image_urls = []
if 'creatify_link' not in st.session_state:
    st.session_state.creatify_link = None
if 'creatify_video_id' not in st.session_state:
    st.session_state.creatify_video_id = None
if 'brief' not in st.session_state:
    st.session_state.brief = ""

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
# Copy the entire screen_crew() function definition from paste.txt
def screen_crew():
    from pydantic import BaseModel
    from typing import List, Optional
    
    class ScriptOutput(BaseModel):
        title: str
        style: str
        hook: str = None
        body: str = None
        cta: str = None
        final_script: str = None
        screenplay: str = None
        image_prompts: List[str] = None  # List of prompts for the scenes

    # Define the Task planning Agent
    task_planning = Agent(
        role = "Workflow Architect for Ad Creation",
        goal = "transform a clean campaign summary into a detailed workflow and instructions for research and script writing agents.",
        backstory = """An experienced workflow architect specializing in streamlining creative processes for advertising campaigns. They excel at dissecting campaign objectives and translating them into clear, sequential tasks for specialized agents. With a deep understanding of the content creation lifecycle, they ensure that research and scripting are aligned and contribute effectively to the overall campaign goals. They focus on providing precise guidance to each agent, maximizing efficiency and creative output.""",
        memory = True,
        verbose = True,
        delegation = False,
        # llm = llm1,
        tools=[SerperDevTool()]  # Still useful for the architect to understand the landscape
    )
    
    # ... (rest of the crew system code from paste.txt)
    
    # For simulation purposes in the Streamlit app, let's return a mock output
    return {
        "title": "Financial Freedom Ad",
        "style": "screenplay",
        "final_script": "You're not alone... Financial stress is affecting so many. Real help for real debt. Professional, confidential support awaits. Take the first step... Start your free debt review today.",
        "screenplay": "EXT. CITY STREET - DAY\n\nA PERSON sits alone on a bench, looking stressed about bills.\n\nNARRATOR\nYou're not alone...\n\nINT. LIVING ROOM - DAY\n\nSeveral PEOPLE look at financial documents with worried expressions.\n\nNARRATOR\nFinancial stress is affecting so many.\n\nINT. OFFICE - DAY\n\nA FINANCIAL ADVISOR greets a client warmly.\n\nNARRATOR\nReal help for real debt.\n\nINT. CONSULTATION ROOM - DAY\n\nThe ADVISOR and CLIENT review documents together.\n\nNARRATOR\nProfessional, confidential support awaits.\n\nEXT. OFFICE BUILDING - DAY\n\nA PERSON walks confidently toward the entrance.\n\nNARRATOR\nTake the first step...\n\nON SCREEN TEXT: \"Start your free debt review today.\"",
        "image_prompts": [
            "A stressed person sitting alone on a bench in a city street, looking at bills, concern on their face, daytime scene",
            "Interior living room with several diverse people looking at financial documents with worried expressions",
            "Professional financial advisor in business attire greeting a client warmly in a modern office",
            "Financial advisor and client reviewing documents together in a professional consultation room",
            "Person walking confidently toward the entrance of a professional office building, bright daylight"
        ]
    }
# Sample data (would be replaced with actual API calls)
def get_voice_samples(page=1, per_page=6):
    # Mock data
    all_voices = [
        {"id": i, "name": f"Voice {i}", "gender": "Female" if i % 2 == 0 else "Male", 
         "style": ["Friendly", "Professional"][i % 2], "language": "English",
         "sample": f"sample_audio_{i}.mp3"} for i in range(1, 21)
    ]
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    return all_voices[start_idx:end_idx], len(all_voices)

def get_video_styles(page=1, per_page=6):
    # Mock data
    all_styles = [
        {"id": i, "name": f"Style {i}", 
         "description": f"Creative video style {i} with unique visual elements",
         "preview": f"video_preview_{i}.mp4"} for i in range(1, 21)
    ]
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    return all_styles[start_idx:end_idx], len(all_styles)

# Simulated functions for AI features
def generate_script(prompt):
    # Store the prompt as the brief
    st.session_state.brief = prompt
    
    # Simulate calling the crew system (in production, you'd use the actual crew system)
    time.sleep(2)  # Simulate processing time
    
    # Get result from screen_crew function
    result = screen_crew()
    
    # Store the results in session state
    st.session_state.screenplay_script = result["final_script"]
    st.session_state.image_prompts = result["image_prompts"]
    
    # Return the formatted screenplay for display
    return result["screenplay"]

def generate_audio(script, voice_id):
    # In a real implementation, this would call your AI API
    time.sleep(2)  # Simulate API call
    return "generated_audio.mp3"  # This would be a file path or base64 data

def generate_video(script, style_id, audio=None):
    # In a real implementation, this would call your AI API
    time.sleep(3)  # Simulate API call
    return "generated_video.mp4"  # This would be a file path or base64 data

def generate_screenplay_images(screenplay):
    # In a real implementation, this would parse the screenplay and generate images
    time.sleep(2)  # Simulate API call
    # Return mock image data
    return ["image1.jpg", "image2.jpg", "image3.jpg"]
def generate_images():
    """Generate images from the image prompts"""
    image_urls = []
    
    for i, prompt in enumerate(st.session_state.image_prompts):
        try:
            # Generate content using Gemini API
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )
            
            # Process response
            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None):
                    # Save the generated image
                    image = Image.open(BytesIO(part.inline_data.data))
                    filename = f"scene-{i+1:02d}-gemini-image.png"
                    image.save(filename)
                    
                    # Upload the image to ImageKit
                    upload = imagekit.upload(
                        file=open(filename, "rb"),
                        file_name=filename
                    )
                    
                    # Store the URL
                    image_urls.append(upload.url)
                    break
        except Exception as e:
            st.error(f"Error generating image {i+1}: {str(e)}")
    
    st.session_state.generated_image_urls = image_urls
    return image_urls
    
def create_creatify_link(image_urls):
    """Create a Creatify link with the generated images"""
    creatify_url = "https://api.creatify.ai/api/links/link_with_params/"
    
    payload = {
        "title": "Generated Images Collection",
        "description": "Images generated with Google Gemini",
        "image_urls": image_urls,
        "video_urls": [],
        "reviews": "Finding Your Way to Financial Freedom"
    }
    
    response = requests.request("POST", creatify_url, json=payload, headers=creatify_headers)
    
    if response.status_code == 200:
        json_response = response.json()
        st.session_state.creatify_link = json_response.get('url')
        return json_response
    else:
        st.error(f"Error creating Creatify link: {response.text}")
        return None

# Mock function to simulate playing audio
def play_audio_sample(sample_id):
    st.audio(f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{sample_id}.mp3")

# Mock function to get a placeholder image
def get_placeholder_image(width, height, text="Preview"):
    image = Image.new('RGB', (width, height), color=(173, 216, 230))
    return image
def create_creatify_video(script):
    """Create a video using Creatify API"""
    url = "https://api.creatify.ai/api/link_to_videos/"
    
    payload = {
        "name": "AI Generated Video",
        "target_platform": "Facebook",
        "target_audience": "Debt Payers",
        "language": "en",
        "video_length": 30,
        "aspect_ratio": "16x9",
        "visual_style": "GreenScreenEffectTemplate",
        "override_avatar": "a7a240e8-efbf-4ab5-a02d-0f367a810875",
        "override_script": script,
        "voiceover_volume": 0.5,
        "link": "9a98f404-f3d9-4f74-b452-f73013be938f",
        "no_background_music": True,
        "caption_style": "normal-black",
    }
    
    response = requests.request("POST", url, json=payload, headers=creatify_headers)
    
    if response.status_code == 200:
        json_response = response.json()
        st.session_state.creatify_video_id = json_response.get('id')
        return json_response
    else:
        st.error(f"Error creating Creatify video: {response.text}")
        return None
def check_video_status(video_id):
    """Check the status of a Creatify video"""
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/"
    response = requests.request("GET", url, headers=creatify_headers)
    return response.json() if response.status_code == 200 else None

def render_creatify_video(video_id):
    """Render the Creatify video"""
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/render/"
    response = requests.request("POST", url, headers=creatify_headers)
    return response.json() if response.status_code == 200 else None
    
# UI Components
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
        
        user_prompt = st.text_area("Describe what kind of script you want to create:", 
                                  height=100, 
                                  placeholder="Example: A 30-second commercial for a new coffee brand targeting young professionals...")
        
        if st.button("Generate Script", key="gen_script_btn"):
            with st.spinner("Generating your script..."):
                generated_script = generate_script(user_prompt)
                st.session_state.script = generated_script
                st.success("Script generated successfully!")
                
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
    
    # Get paginated voice samples
    voices, total_voices = get_voice_samples(page=st.session_state.voice_page)
    total_pages = (total_voices + 5) // 6  # 6 items per page, rounded up
    
    # Display voice cards in a grid
    cols = st.columns(3)

    cols = st.columns(3)

    for i, voice in enumerate(voices):
        with cols[i % 3]:
            is_selected = st.session_state.selected_voice == voice["id"]
            card_id = f"voice_card_{voice['id']}"
    
            # Create the card
            card_html = f"""
            <div class="voice-card {'selected' if is_selected else ''}">
                <div class="card-header">
                    <div class="card-title">{voice["name"]}</div>
                    <div class="selection-indicator">{'✓' if is_selected else ''}</div>
                </div>
                <div class="card-tags">
                    <span class="bubble">{voice["gender"]}</span>
                    <span class="bubble">{voice["style"]}</span>
                    <span class="bubble">{voice["language"]}</span>
                </div>
                <audio controls style="width: 100%; margin-bottom: 10px;">
                    <source src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{voice['id']}.mp3" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
            </div>
            """
    
            st.markdown(card_html, unsafe_allow_html=True)
    
            # Button to select this voice
            if st.button(f"Select {voice['name']}", key=f"select_btn_{voice['id']}"):
                st.session_state.selected_voice = voice["id"]
                st.rerun()


    
    # Add CSS to style the tick-box
    st.markdown("""
    <style>
    .voice-card {
        position: relative;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
        background-color: #fff;
    }
    
    .voice-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    .tick-box {
        position: absolute;
        top: 10px;
        right: 10px;
        width: 24px;
        height: 24px;
        background-color: #f0f0f0;
        border: 2px solid #4CAF50;
        border-radius: 4px;
        font-size: 16px;
        color: #4CAF50;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-weight: bold;
    }
    
    .voice-card .tick-box:hover {
        background-color: #e0ffe0;
    }
    .card-title {
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 10px;
    }
    .bubble {
        background-color: #f0f0f0;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        margin-right: 5px;
    }
    .card-tags {
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    
    # Add CSS for the voice cards
    st.markdown("""
    <style>
    .voice-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
    }
    
    .voice-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    .voice-card.selected {
        border: 2px solid #4CAF50;
        background-color: rgba(76, 175, 80, 0.05);
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    
    .card-title {
        font-weight: bold;
        font-size: 1.1em;
    }
    
    .selection-indicator {
        color: #4CAF50;
        font-weight: bold;
        font-size: 1.2em;
    }
    
    .card-tags {
        margin-bottom: 15px;
    }
    
    .bubble {
        background-color: #f0f0f0;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        margin-right: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
                    generated_audio = generate_audio(st.session_state.script, st.session_state.selected_voice)
                    st.session_state.generated_audio = generated_audio
                    st.success("Audio generated successfully!")
    
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
    
    # Generate video button
    st.markdown("---")
    
    if st.button("Generate Video", key="gen_video_btn", disabled=not st.session_state.selected_video_style or not st.session_state.generated_audio):
        if st.session_state.selected_video_style and st.session_state.generated_audio:
            with st.spinner("Generating video... This may take a few moments."):
                generated_video = generate_video(
                    st.session_state.script, 
                    st.session_state.selected_video_style,
                    st.session_state.generated_audio
                )
                st.session_state.generated_video = generated_video
                st.success("Video generated successfully!")
                
                # Display a placeholder for the video
                placeholder = get_placeholder_image(640, 360, "Video Preview")
                st.image(placeholder, use_column_width=True)
                
                # Download button (in a real implementation, this would be a link to the actual video)
                st.download_button(
                    label="Download Video",
                    data=io.BytesIO().getvalue(),  # Placeholder
                    file_name="generated_video.mp4",
                    mime="video/mp4")

    def render_video_generator():
    
        # Add a section for AI-generated video
        st.markdown("---")
        st.markdown("<h3>AI-Generated Video</h3>", unsafe_allow_html=True)
        
        if st.session_state.screenplay_script:
            if not st.session_state.creatify_video_id:
                if st.button("Generate AI Video", key="gen_ai_video"):
                    with st.spinner("Creating video with Creatify..."):
                        result = create_creatify_video(st.session_state.screenplay_script)
                        if result:
                            st.success(f"Video creation started!")
                            st.rerun()
            else:
                # Check video status
                if st.button("Check Video Status", key="check_status"):
                    with st.spinner("Checking video status..."):
                        status = check_video_status(st.session_state.creatify_video_id)
                        if status:
                            st.write(f"Status: {status.get('status')}")
                            
                            if status.get("status") == "done" and status.get("video_output"):
                                st.video(status["video_output"])
                                
                                # Download button
                                video_url = status["video_output"]
                                st.markdown(f"[Download Video]({video_url})")
                            else:
                                st.info(f"Video is still processing. Progress: {status.get('progress', 0) * 100:.0f}%")
                                
                                # Show preview if available
                                if status.get("preview"):
                                    st.markdown(f"[Preview Link]({status['preview']})")
                
                # Render video button
                if st.button("Render Video", key="render_video"):
                    with st.spinner("Rendering video..."):
                        result = render_creatify_video(st.session_state.creatify_video_id)
                        if result:
                            st.success("Video rendering started!")
                            st.write(result)    

def render_screenplay_generator():
    st.markdown("<h1 class='main-header'>Screenplay Generator</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("<h3>Write Your Screenplay</h3>", unsafe_allow_html=True)
        
        # Add input field for the campaign brief
        campaign_brief = st.text_area("Enter campaign brief:", height=100, 
                               placeholder="A 30-second ad about financial freedom...",
                               key="campaign_brief")
        
        if st.button("Generate with AI Crew", key="gen_screenplay_btn"):
            with st.spinner("AI crew is working on your screenplay..."):
                st.session_state.brief = campaign_brief
                result = screen_crew()  # This would be your actual crew system
                st.session_state.script = result["screenplay"]
                st.session_state.screenplay_script = result["final_script"]
                st.session_state.image_prompts = result["image_prompts"]
                st.success("Screenplay and image prompts generated!")
                st.rerun()
        
        # Display the screenplay if available
        if st.session_state.script:
            screenplay = st.text_area("Generated screenplay:", height=400, 
                                   value=st.session_state.script,
                                   key="screenplay_display")
        
        # Display image prompts if available
        if st.session_state.image_prompts:
            st.markdown("<h3>Generated Image Prompts</h3>", unsafe_allow_html=True)
            for i, prompt in enumerate(st.session_state.image_prompts):
                st.markdown(f"**Scene {i+1}:** {prompt}")
    
    with col2:
        st.markdown("<h3>Generated Images</h3>", unsafe_allow_html=True)
        
        # Generate images button if we have prompts but no images
        if st.session_state.image_prompts and not st.session_state.generated_image_urls:
            if st.button("Generate Images", key="gen_images"):
                with st.spinner("Generating images... This may take a moment."):
                    image_urls = generate_images()
                    if image_urls:
                        st.success(f"Generated {len(image_urls)} images!")
                        st.rerun()
        
        # Display generated images if available
        if st.session_state.generated_image_urls:
            for i, url in enumerate(st.session_state.generated_image_urls):
                st.image(url, caption=f"Scene {i+1}", use_column_width=True)
            
            # Create Creatify link button
            if not st.session_state.creatify_link:
                if st.button("Create Creatify Link", key="create_link"):
                    with st.spinner("Creating Creatify link..."):
                        result = create_creatify_link(st.session_state.generated_image_urls)
                        if result:
                            st.success(f"Creatify link created!")
                            st.rerun()
            else:
                st.success(f"Creatify link: {st.session_state.creatify_link}")
        
        # Create video button if we have a script
        if st.session_state.screenplay_script:
            if not st.session_state.creatify_video_id:
                if st.button("Create Video", key="create_video"):
                    with st.spinner("Creating video with Creatify..."):
                        result = create_creatify_video(st.session_state.screenplay_script)
                        if result:
                            st.success(f"Video creation started!")
                            st.rerun()
            else:
                # Check video status
                if st.button("Check Video Status", key="check_status"):
                    with st.spinner("Checking video status..."):
                        status = check_video_status(st.session_state.creatify_video_id)
                        if status:
                            st.write(status)
                            
                            if status.get("status") == "done" and status.get("video_output"):
                                st.video(status["video_output"])
                            else:
                                st.info(f"Video status: {status.get('status')}")
                
                # Render video button
                if st.button("Render Video", key="render_video"):
                    with st.spinner("Rendering video..."):
                        result = render_creatify_video(st.session_state.creatify_video_id)
                        if result:
                            st.success("Video rendering started!")
                            st.rerun()
        
        if st.session_state.script and st.button("Proceed to Audio", key="screenplay_to_audio"):
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
