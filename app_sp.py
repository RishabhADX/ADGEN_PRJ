import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
from PIL import Image
import io
import time
import requests
import json
import uuid
from io import BytesIO

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
    
    .loading-spinner {{
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100px;
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
if 'screenplay_data' not in st.session_state:
    st.session_state.screenplay_data = None
if 'image_urls' not in st.session_state:
    st.session_state.image_urls = []
if 'creatify_link' not in st.session_state:
    st.session_state.creatify_link = None
if 'video_output_url' not in st.session_state:
    st.session_state.video_output_url = None
if 'video_job_id' not in st.session_state:
    st.session_state.video_job_id = None

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

# Actual AI functions (Implementation from your first code snippet)
def screen_crew():
    from pydantic import BaseModel
    from typing import List, Optional
    
    # This is where you'd put your crew agent code
    # For the purposes of this demonstration, we'll simulate the output
    
    # Simulated output structure
    class ScriptOutput:
        def __init__(self):
            self.title = "Finding Your Financial Freedom"
            self.style = "screenplay"
            self.hook = "A person overwhelmed by bills and financial stress."
            self.body = "They discover a professional debt solution service."
            self.cta = "Take the first step toward financial freedom."
            self.final_script = "You're not alone... Financial stress is affecting so many. Real help for real debt. Professional, confidential support awaits. Take the first step... Start your free debt review today."
            self.screenplay = """
FADE IN:

INT. LIVING ROOM - NIGHT

JANE (30s) sits at her kitchen table, surrounded by bills, her face etched with worry. She rubs her temples, overwhelmed.

JANE (V.O.)
You're not alone...

She looks at her phone showing overdue payment notifications.

JANE (V.O.)
Financial stress is affecting so many.

INT. PROFESSIONAL OFFICE - DAY

Jane sits across from a FINANCIAL ADVISOR, who reviews her documents with understanding and compassion.

JANE (V.O.)
Real help for real debt.

CLOSE ON: A computer screen showing a debt reduction plan.

JANE (V.O.)
Professional, confidential support awaits.

INT. LIVING ROOM - EVENING - WEEKS LATER

Jane at her table again, but now organized folders replace the scattered bills. She smiles as she checks off items on a financial plan.

JANE (V.O.)
Take the first step...

She closes her budget book with satisfaction.

JANE
(looking directly at camera)
Start your free debt review today.

FADE OUT.
            """
            self.image_prompts = [
                "Close-up of a worried woman in her 30s sitting at a kitchen table at night, surrounded by bills and notices, face illuminated by lamp light, shoulders slumped in stress",
                
                "Professional modern office setting with sunlight streaming through windows, a compassionate financial advisor in business attire reviewing documents with a relieved client, desk has organized folders and a computer",
                
                "Close-up of a computer screen showing a colorful debt reduction graph with downward trending lines, professional desktop setting, office environment",
                
                "Same woman from first scene, now sitting at a neat kitchen table with organized financial documents in labeled folders, checking items off a list, expression hopeful and relieved, warmer lighting"
            ]
            
    # Return simulated output
    return ScriptOutput()

# Function to generate images using Google Gemini (simplified)
def generate_gemini_images(prompts, api_key="AIzaSyBLzfjImenFp60acvXgKygaEDKGqKfHyKI"):
    from google import genai
    from google.genai import types
    
    # Initialize the Google Gemini client
    client = genai.Client(api_key=api_key)
    
    image_paths = []
    
    with st.spinner("Generating images from screenplay scenes..."):
        progress_bar = st.progress(0)
        
        for i, prompt in enumerate(prompts):
            status_text = st.empty()
            status_text.text(f"Processing image {i+1}/{len(prompts)}")
            
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
                    if hasattr(part, "inline_data"):
                        # Save the generated image
                        filename = f"scene-{i+1:02d}-gemini-image.png"
                        image_data = part.inline_data.data
                        
                        # Create PIL Image
                        image = Image.open(BytesIO(image_data))
                        
                        # Save to BytesIO for display in Streamlit
                        img_byte_arr = BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)
                        
                        # Display image in Streamlit
                        st.image(img_byte_arr, caption=f"Scene {i+1}", use_column_width=True)
                        
                        # Add to images list
                        image_paths.append((filename, img_byte_arr))
            
            except Exception as e:
                st.error(f"Error generating image {i+1}: {str(e)}")
                # Create a placeholder image instead
                placeholder = Image.new('RGB', (400, 300), color=(173, 216, 230))
                img_byte_arr = BytesIO()
                placeholder.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                image_paths.append((f"placeholder-{i+1}.png", img_byte_arr))
            
            # Update progress
            progress_bar.progress((i + 1) / len(prompts))
        
        progress_bar.empty()
        status_text.empty()
    
    return image_paths

# Function to upload images to ImageKit
def upload_to_imagekit(image_data_list):
    from imagekitio import ImageKit
    
    # Initialize the ImageKit client
    imagekit = ImageKit(
        private_key='private_OGgux+C54n9PIYDlLdOrYysEWrw=',
        public_key='public_Qq9s197rBPKyx5eWhq+aN6TQ3Iw=',
        url_endpoint='https://ik.imagekit.io/b6pq3mgo7'
    )
    
    image_urls = []
    file_ids = []
    
    with st.spinner("Uploading images to cloud storage..."):
        progress_bar = st.progress(0)
        
        for i, (filename, img_data) in enumerate(image_data_list):
            try:
                img_data.seek(0)
                upload = imagekit.upload(
                    file=img_data,
                    file_name=filename
                )
                
                image_urls.append(upload.url)
                file_ids.append(upload.file_id)
                
                progress_bar.progress((i + 1) / len(image_data_list))
                
            except Exception as e:
                st.error(f"Error uploading image {filename}: {str(e)}")
                image_urls.append(None)
                file_ids.append(None)
        
        progress_bar.empty()
    
    return image_urls, file_ids

# Function to create Creatify link
def create_creatify_link(image_urls, title="AI Generated Screenplay Images"):
    # API credentials
    headers = {
        "X-API-ID": "5f8b3a5c-6e33-4e9f-b85c-71941d675270",
        "X-API-KEY": "c019dd017d22e2e40627f87bc86168b631b9a345",
        "Content-Type": "application/json"
    }
    
    # Filter out None values
    valid_urls = [url for url in image_urls if url is not None]
    
    if not valid_urls:
        st.error("No valid image URLs to create a link")
        return None
    
    # Prepare payload
    creatify_url = "https://api.creatify.ai/api/links/link_with_params/"
    payload = {
        "title": title,
        "description": "Screenplay scenes generated with AI",
        "image_urls": valid_urls,
        "video_urls": [],
        "reviews": title  # Using title as reviews
    }
    
    try:
        with st.spinner("Creating link to images..."):
            response = requests.request("POST", creatify_url, json=payload, headers=headers)
            if response.status_code == 200:
                json_response = response.json()
                if 'url' in json_response:
                    return json_response
            else:
                st.error(f"Error creating link: {response.text}")
                return None
    except Exception as e:
        st.error(f"Error making API request: {str(e)}")
        return None

# Function to create video from screenplay and images
def create_creatify_video(screenplay_script, override_avatar=None):
    # API credentials
    headers = {
        "X-API-ID": "5f8b3a5c-6e33-4e9f-b85c-71941d675270",
        "X-API-KEY": "c019dd017d22e2e40627f87bc86168b631b9a345",
        "Content-Type": "application/json"
    }
    
    # For the link ID, use the link from the previous step or a default one
    link_id = "9a98f404-f3d9-4f74-b452-f73013be938f"  # Default, replace with actual link ID if available
    if st.session_state.creatify_link and 'id' in st.session_state.creatify_link.get('link', {}):
        link_id = st.session_state.creatify_link['link']['id']
    
    # Set the avatar ID or use default
    avatar_id = override_avatar if override_avatar else "a7a240e8-efbf-4ab5-a02d-0f367a810875"
    
    # Prepare the payload
    url = "https://api.creatify.ai/api/link_to_videos/"
    payload = {
        "name": "AI Generated Screenplay",
        "target_platform": "Facebook",
        "target_audience": "General Audience",
        "language": "en",
        "video_length": 30,
        "aspect_ratio": "16x9",
        "visual_style": "GreenScreenEffectTemplate",
        "override_avatar": avatar_id,
        "override_script": screenplay_script,
        "voiceover_volume": 0.5,
        "link": link_id,
        "no_background_music": True,
        "caption_style": "normal-black",
    }
    
    try:
        with st.spinner("Initiating video creation..."):
            response = requests.request("POST", url, json=payload, headers=headers)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                st.error(f"Error creating video: {response.text}")
                return None
    except Exception as e:
        st.error(f"Error making API request: {str(e)}")
        return None

# Function to check video status
def check_video_status(video_id):
    # API credentials
    headers = {
        "X-API-ID": "5f8b3a5c-6e33-4e9f-b85c-71941d675270",
        "X-API-KEY": "c019dd017d22e2e40627f87bc86168b631b9a345",
    }
    
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/"
    
    try:
        response = requests.request("GET", url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error checking video status: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error making API request: {str(e)}")
        return None

# Function to render the video
def render_video(video_id):
    # API credentials
    headers = {
        "X-API-ID": "5f8b3a5c-6e33-4e9f-b85c-71941d675270",
        "X-API-KEY": "c019dd017d22e2e40627f87bc86168b631b9a345",
    }
    
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/render/"
    
    try:
        with st.spinner("Rendering final video..."):
            response = requests.request("POST", url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error rendering video: {response.text}")
                return None
    except Exception as e:
        st.error(f"Error making API request: {str(e)}")
        return None

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

# Dummy function for generating script
def generate_script(prompt):
    # In a real implementation, this would call your AI API
    with st.spinner("Generating script with AI agents..."):
        # Simulate calling the screen_crew function
        time.sleep(2)  # Simulate processing time
        
        # Get results from the AI crew
        screenplay_data = screen_crew()
        
        # Store in session state
        st.session_state.screenplay_data = screenplay_data
        
        # Return the final script
        return screenplay_data.screenplay

# Mock function to get a placeholder image
def get_placeholder_image(width, height, text="Preview"):
    image = Image.new('RGB', (width, height), color=(173, 216, 230))
    return image

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
            "Images": "✅" if st.session_state.screenplay_images else "❌",
            "Video": "✅" if st.session_state.video_output_url else "❌"
        }
        
        for item, status in progress_items.items():
            st.markdown(f"{status} {item}")

def render_home():
    st.markdown("<h1 class='main-header'>AI Creative Suite</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; margin-bottom: 40px;'>Transform your ideas into professional scripts, videos, and images with AI</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-title">AI Script Generator</div>
            <p>Create professional scripts using our AI agents. Start with a simple prompt and get a fully-formed screenplay.</p>
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
            <p>Create professional screenplays with our AI-powered tools. Visualize your story with AI-generated images and convert to video.</p>
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
            <p>Generate a professional script using our multi-agent AI system or upload your own.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-title">2. Generate Images</div>
            <p>Our AI analyzes your screenplay and generates images for each scene using Google's Gemini.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-title">3. Create Video</div>
            <p>Generate a professional video with your script and generated images using Creatify AI.</p>
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
                                  placeholder="Example: A 30-second commercial for a debt solution service targeting people with financial stress...")
        
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
                
            if st.button("Generate Images from Script", key="proceed_to_images"):
                go_to_screenplay_generator()
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
