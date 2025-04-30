import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import json
import base64
from PIL import Image
from io import BytesIO
import uuid
import time
import io
import re
from google import genai
from google.genai import types

# Set page configuration
st.set_page_config(
    page_title="AI Creative Suite",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API credentials from the video pipeline
API_ID = "5f8b3a5c-6e33-4e9f-b85c-71941d675270"
API_KEY = "c019dd017d22e2e40627f87bc86168b631b9a345"
GEMINI_API_KEY = "AIzaSyBLzfjImenFp60acvXgKygaEDKGqKfHyKI"
IMAGEKIT_PRIVATE_KEY = "private_OGgux+C54n9PIYDlLdOrYysEWrw="
IMAGEKIT_PUBLIC_KEY = "public_Qq9s197rBPKyx5eWhq+aN6TQ3Iw="
IMAGEKIT_URL_ENDPOINT = "https://ik.imagekit.io/b6pq3mgo7"

# Headers for API requests
headers = {
    "X-API-ID": API_ID,
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

# Initialize Gemini client
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"Failed to initialize Gemini: {str(e)}")

# Define color scheme
PRIMARY_COLOR = "#ADD8E6"  # Light blue
SECONDARY_COLOR = "#F0F8FF"  # AliceBlue
TEXT_COLOR = "#2C3E50"  # Dark blue/gray

# Apply custom CSS (combining both styles)
st.markdown(f"""
<style>
    .stApp {{
        background-color: white;
    }}
    .main {{
        padding: 2rem;
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
    .screenplay {{
        font-family: 'Courier New', monospace;
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 5px;
        white-space: pre-wrap;
    }}
    .scene-heading {{
        font-weight: bold;
        text-transform: uppercase;
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
    
    .selection-indicator {{
        color: #4CAF50;
        font-weight: bold;
        font-size: 1.2em;
    }}
    
    .video-container {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
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
if 'link_data' not in st.session_state:
    st.session_state.link_data = None
if 'video_data' not in st.session_state:
    st.session_state.video_data = None
if 'project_name' not in st.session_state:
    st.session_state.project_name = "My AI Project"

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

def go_to_video_pipeline():
    st.session_state.page = "video_pipeline"

def set_script(script_text):
    st.session_state.script = script_text
    go_to_audio_generator()

def select_voice(voice_id):
    st.session_state.selected_voice = voice_id

def select_video_style(style_id):
    st.session_state.selected_video_style = style_id

# API Functions from the video pipeline
# Function to get available personas
@st.cache_data(ttl=3600)
def get_personas():
    url = "https://api.creatify.ai/api/personas/paginated/"
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        st.error(f"Error fetching personas: {str(e)}")
        return []

# Function to get available voices
@st.cache_data(ttl=3600)
def get_voices():
    url = "https://api.creatify.ai/api/voices/"
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        st.error(f"Error fetching voices: {str(e)}")
        # Return a fallback list of voices in case the API call fails
        return [
            {"voice_id": "en-US-Wavenet-A", "name": "US Male", "gender": "Male", "language": "English (US)"},
            {"voice_id": "en-US-Wavenet-C", "name": "US Female", "gender": "Female", "language": "English (US)"},
            {"voice_id": "en-GB-Wavenet-B", "name": "UK Male", "gender": "Male", "language": "English (UK)"},
            {"voice_id": "en-GB-Wavenet-C", "name": "UK Female", "gender": "Female", "language": "English (UK)"},
            {"voice_id": "es-ES-Wavenet-B", "name": "Spanish Male", "gender": "Male", "language": "Spanish"},
            {"voice_id": "fr-FR-Wavenet-C", "name": "French Female", "gender": "Female", "language": "French"}
        ]

# Function to generate screenplay using Gemini
def generate_screenplay(campaign_brief, tone, target_audience, product_details, num_scenes):
    try:
        prompt = f"""Generate a captivating screenplay-style ad creative for the following brief:

Campaign Brief: {campaign_brief}
Tone: {tone}
Target Audience: {target_audience}
Product/Service Details: {product_details}
Number of Scenes: {num_scenes} (keep it concise)

Create the screenplay in proper format with:
1. SCENE HEADINGS in all caps
2. Action descriptions in present tense
3. Minimal dialogue (if needed)
4. Clear visual storytelling

The structure should include:
- A HOOK scene that grabs attention
- BODY scenes that develop the message
- A CTA (call-to-action) scene

Additionally, FOR EACH SCENE, create one detailed image prompt that could be used for AI image generation.
Format your response as a JSON object with these fields:
- title: A descriptive ad title
- style: "screenplay"
- screenplay: The full formatted screenplay content
- image_prompts: An array with one detailed image prompt per scene
- final_script: The complete voiceover content/narration text for the ad

Keep the total word count under 200 words for the script portion.
"""

        # Use the generate_content method instead of generate_text
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=prompt        )
        
        # Get the response text from the response object
        response_text = response.candidates[0].content.parts[0].text
        
        try:
            # Try to parse as JSON
            screenplay_data = json.loads(response_text)
            return screenplay_data, None
        except json.JSONDecodeError:
            # If not valid JSON, extract useful info using regex
            title_match = re.search(r'"title":\s*"([^"]+)"', response_text)
            title = title_match.group(1) if title_match else "Untitled Screenplay"
            
            screenplay_match = re.search(r'"screenplay":\s*"([^"]*)"', response_text, re.DOTALL)
            screenplay = screenplay_match.group(1) if screenplay_match else response_text
            
            # Extract image prompts using regex
            image_prompts_text = re.search(r'"image_prompts":\s*\[(.*?)\]', response_text, re.DOTALL)
            if image_prompts_text:
                # Clean up and split the prompts
                prompts_text = image_prompts_text.group(1)
                # Split by commas that are followed by a quote
                image_prompts = re.findall(r'"(.*?)"', prompts_text)
            else:
                # Fallback: Try to find lines that look like image prompts
                image_prompts = re.findall(r'Image prompt.*?:\s*(.*?)(?:\n|$)', response_text)
            
            script_match = re.search(r'"final_script":\s*"([^"]*)"', response_text, re.DOTALL)
            final_script = script_match.group(1) if script_match else ""
            
            # Construct JSON-like structure
            screenplay_data = {
                "title": title,
                "style": "screenplay",
                "screenplay": screenplay.replace('\\n', '\n').replace('\\"', '"'),
                "image_prompts": image_prompts[:num_scenes],  # Limit to requested number of scenes
                "final_script": final_script.replace('\\n', '\n').replace('\\"', '"')
            }
            
            return screenplay_data, None
    except Exception as e:
        return None, str(e)

# Function to generate a voice preview
def generate_voice_preview(voice_id, text="This is a sample of how this voice sounds."):
    url = "https://api.creatify.ai/api/tts/"
    
    payload = {
        "text": text,
        "voice_id": voice_id
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        return data.get("audio_url"), None
    except Exception as e:
        return None, f"Error generating voice preview: {str(e)}"
        
# Function to generate image with Gemini
def generate_image(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )
        
        if not response.candidates or not response.candidates[0].content.parts:
            return None, "No content generated"
            
        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None):
                return part.inline_data.data, None
        
        return None, "No image found in response"
    except Exception as e:
        return None, str(e)

# Function to upload image to ImageKit
def upload_to_imagekit(image_data, filename):
    try:
        # Convert image to bytes if it's not already
        if isinstance(image_data, Image.Image):
            buffer = io.BytesIO()
            image_data.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
        else:
            image_bytes = image_data
            
        # Create a file-like object
        file_like = io.BytesIO(image_bytes)
        
        # Prepare the upload
        url = f"https://upload.imagekit.io/api/v1/files/upload"
        
        # Create authentication header
        auth_str = base64.b64encode(f"{IMAGEKIT_PRIVATE_KEY}:".encode()).decode()
        
        headers_upload = {
            "Authorization": f"Basic {auth_str}"
        }
        
        files = {
            'file': (filename, file_like, 'image/png'),
            'fileName': (None, filename),
            'publicKey': (None, IMAGEKIT_PUBLIC_KEY),
        }
        
        response = requests.post(url, files=files, headers=headers_upload)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("url"), result.get("fileId"), None
        else:
            return None, None, f"Upload failed with status {response.status_code}: {response.text}"
            
    except Exception as e:
        return None, None, str(e)

# Function to create Creatify link
def create_creatify_link(image_urls, title, description):
    url = "https://api.creatify.ai/api/links/link_with_params/"
    
    payload = {
        "title": title,
        "description": description,
        "image_urls": image_urls,
        "video_urls": [],
        "reviews": "Generated with AI Video Pipeline"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json(), None
    except Exception as e:
        return None, f"Error creating link: {str(e)}"

# Function to create video
def create_video(link_id, name, script, avatar_id, **kwargs):
    url = "https://api.creatify.ai/api/link_to_videos/"
    
    payload = {
        "name": name,
        "target_platform": kwargs.get("platform", "Facebook"),
        "target_audience": kwargs.get("audience", "General"),
        "language": kwargs.get("language", "en"),
        "video_length": kwargs.get("length", 30),
        "aspect_ratio": kwargs.get("ratio", "16x9"),
        "visual_style": kwargs.get("style", "GreenScreenEffectTemplate"),
        "override_avatar": avatar_id,
        "override_script": script,
        "override_voice": kwargs.get("voice_id"),
        "voiceover_volume": kwargs.get("volume", 0.5),
        "link": link_id,
        "no_background_music": kwargs.get("no_music", True),
        "caption_style": kwargs.get("caption_style", "normal-black"),
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json(), None
    except Exception as e:
        return None, f"Error creating video: {str(e)}"

# Function to get video status
def get_video_status(video_id):
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/"
    
    try:
        response = requests.get(url, headers=headers)
        return response.json(), None
    except Exception as e:
        return None, f"Error getting video status: {str(e)}"

# Function to render video
def render_video(video_id):
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/render/"
    
    try:
        response = requests.post(url, headers=headers)
        return response.json(), None
    except Exception as e:
        return None, f"Error rendering video: {str(e)}"

# Function to format screenplay for display
def format_screenplay_display(screenplay_text):
    # Replace scene headings with styled versions
    formatted = re.sub(r'(INT\.|EXT\.)(.*?)(?=\n)', r'<div class="scene-heading">\1\2</div>', screenplay_text)
    # Replace double line breaks with paragraph breaks
    formatted = formatted.replace('\n\n', '</p><p>')
    return f'<p>{formatted}</p>'

# Sample data functions (for Creative Suite functionality)
def get_voice_samples(page=1, per_page=6):
    # Get real voices from API if possible
    try:
        voices = get_voices()
        # Paginate the voices
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        return voices[start_idx:end_idx], len(voices)
    except:
        # Fallback to mock data
        all_voices = [
            {"id": i, "voice_id": f"voice-{i}", "name": f"Voice {i}", "gender": "Female" if i % 2 == 0 else "Male", 
             "style": ["Friendly", "Professional"][i % 2], "language": "English",
             "sample": f"sample_audio_{i}.mp3"} for i in range(1, 21)
        ]
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        return all_voices[start_idx:end_idx], len(all_voices)

def get_video_styles(page=1, per_page=6):
    # Mock data for video styles
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
    # Try using Gemini for script generation
    try:
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=f"""Write a creative script based on the following prompt: {prompt}. 
            Include scene directions, character dialogue if appropriate, 
            and format it professionally as a screenplay."""
        )
        return response.candidates[0].content.parts[0].text
    except:
        # Fallback to simulated response
        time.sleep(2)  # Simulate API call
        return f"""# Sample Script: {prompt}

FADE IN:

EXT. CITY STREET - DAY

A bustling city street with people hurrying about their day.

NARRATOR (V.O.)
In a world where technology and humanity intersect...

[Character descriptions and additional scenes would follow...]

FADE OUT.
"""

def generate_audio(script, voice_id):
    # Try using real TTS API
    try:
        url = "https://api.creatify.ai/api/tts/"
        payload = {
            "text": script,
            "voice_id": voice_id
        }
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        return data.get("audio_url")
    except:
        # Fallback to mock data
        time.sleep(2)  # Simulate API call
        return "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"  # Mock audio URL

def generate_video(script, style_id, audio=None):
    # In a real implementation, this would call your AI API
    time.sleep(3)  # Simulate API call
    return "generated_video.mp4"  # This would be a file path or base64 data

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
            
        # Add the new Video Pipeline option
        if st.button("🎬 Advanced Video Pipeline", key="nav_video_pipeline"):
            go_to_video_pipeline()
            
        st.markdown("---")
        st.markdown("### Current Progress")
        
        progress_items = {
            "Script": "✅" if st.session_state.script else "❌",
            "Voice": "✅" if st.session_state.selected_voice else "❌",
            "Audio": "✅" if st.session_state.generated_audio else "❌",
            "Video": "✅" if st.session_state.generated_video else "❌",
            "Screenplay": "✅" if st.session_state.screenplay_data else "❌"
        }
        
        for item, status in progress_items.items():
            st.markdown(f"{status} {item}")

def render_home():
    st.markdown("<h1 class='main-header'>AI Creative Suite</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; margin-bottom: 40px;'>Transform your ideas into professional scripts, audio, and videos with AI</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-title">AI Script Generator</div>
            <p>Create professional scripts using our AI tools. Start from scratch or use your existing script.</p>
            <p>Perfect for content creators, marketers, and storytellers.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Create Script", key="start_scripting"):
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
            
    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-title">Advanced Video Pipeline</div>
            <p>Generate complete ad videos with our advanced video pipeline. From brief to final video.</p>
            <p>Includes AI-generated screenplay, images, and professional avatars.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Launch Pipeline", key="launch_pipeline"):
            go_to_video_pipeline()
    
    st.markdown("---")
    
    st.markdown("<h2 class='sub-header'>How It Works</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
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
        
    with col4:
        st.markdown("""
        <div class="card">
            <div class="card-title">4. Advanced Options</div>
            <p>Use our advanced video pipeline for complete control over avatars, scenes, and more.</p>
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
    
    for i, voice in enumerate(voices):
        with cols[i % 3]:
            voice_id = voice.get("voice_id", voice.get("id", f"voice-{i}"))
            is_selected = st.session_state.selected_voice == voice_id
            card_id = f"voice_card_{voice_id}"
    
            # Create the card
            card_html = f"""
            <div class="voice-card {'selected' if is_selected else ''}">
                <div class="card-header">
                    <div class="card-title">{voice.get("name", "Voice")}</div>
                    <div class="selection-indicator">{'✓' if is_selected else ''}</div>
                </div>
                <div class="card-tags">
                    <span class="bubble">{voice.get("gender", "Unknown")}</span>
                    <span class="bubble">{voice.get("style", voice.get("language", "Standard"))}</span>
                    <span class="bubble">{voice.get("language", "English")}</span>
                </div>
            </div>
            """
    
            st.markdown(card_html, unsafe_allow_html=True)
    
            # Button to select this voice
            if st.button(f"Select", key=f"select_btn_{voice_id}"):
                st.session_state.selected_voice = voice_id
                st.rerun()
                
            # Button to preview voice
            if st.button("Preview", key=f"preview_btn_{voice_id}"):
                with st.spinner("Generating preview..."):
                    preview_url, error = generate_voice_preview(voice_id)
                    if error:
                        st.error(error)
                    elif preview_url:
                        st.audio(preview_url, format="audio/mp3")
                    else:
                        sample_id = i % 10 + 1
                        st.audio(f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{sample_id}.mp3")
    
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
                    st.audio(generated_audio)
    
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
            if isinstance(st.session_state.generated_audio, str) and st.session_state.generated_audio.startswith("http"):
                st.audio(st.session_state.generated_audio)
            else:
                # For uploaded files
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
                    mime="video/mp4"
                )

def render_screenplay_generator():
    st.markdown("<h1 class='main-header'>Screenplay Generator</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("<h3>Write Your Screenplay</h3>", unsafe_allow_html=True)
        
        screenplay = st.text_area("Enter your screenplay:", height=400, 
                                placeholder="EXT. FOREST - DAY\n\nA small clearing in a dense forest. Sunlight filters through the canopy...",
                                value=st.session_state.script if st.session_state.script else "")
        
        if st.button("Generate Images from Screenplay", key="gen_screenplay_images"):
            with st.spinner("Analyzing screenplay and generating images..."):
                # Use the real image generation if possible
                st.session_state.script = screenplay  # Save the screenplay
                
                # Parse the screenplay into scenes
                scenes = [scene.strip() for scene in re.split(r'(INT\.|EXT\.)', screenplay) if scene.strip()]
                
                # Generate image prompts for each scene (up to 3 scenes)
                image_prompts = []
                for i, scene in enumerate(scenes[:3]):
                    prompt = f"Generate a cinematic image for this screenplay scene: {scene}"
                    image_prompts.append(prompt)
                
                # Generate images
                images = []
                for i, prompt in enumerate(image_prompts):
                    image_data, error = generate_image(prompt)
                    if not error and image_data:
                        # Convert to PIL Image
                        image = Image.open(BytesIO(image_data))
                        images.append(image)
                
                st.session_state.screenplay_images = images
                st.success("Images generated successfully!")
    
    with col2:
        st.markdown("<h3>Preview</h3>", unsafe_allow_html=True)
        
        if st.session_state.screenplay_images:
            for i, img in enumerate(st.session_state.screenplay_images):
                if isinstance(img, str):  # URL or filename
                    st.image(img, caption=f"Scene {i+1}", use_column_width=True)
                else:  # PIL Image
                    st.image(img, caption=f"Scene {i+1}", use_column_width=True)
        else:
            st.info("Generate images from your screenplay to see previews here.")
        
        if st.session_state.screenplay_images and st.button("Proceed to Audio", key="screenplay_to_audio"):
            go_to_audio_generator()
# Video Pipeline UI (from the first file)
def render_video_pipeline():
    st.markdown('<h1 class="main-header">🎬 Advanced Video Pipeline: From Brief to Video</h1>', unsafe_allow_html=True)

    # Initialize session state for storing data between steps
    if 'pipeline_step' not in st.session_state:
        st.session_state.pipeline_step = 1
        
    # Sidebar for navigation and status in the pipeline
    with st.sidebar:
        st.header("Pipeline Workflow")
        
        # Show workflow steps
        steps = [
            "1. Enter Campaign Details",
            "2. Generate Screenplay",
            "3. Generate & Upload Images",
            "4. Create Video",
            "5. View Results"
        ]
        
        for i, step in enumerate(steps):
            if i + 1 < st.session_state.pipeline_step:
                st.success(step)
            elif i + 1 == st.session_state.pipeline_step:
                st.info(step + " (Current)")
            else:
                st.write(step)
        
        # Reset button
        if st.button("Start Over Pipeline"):
            st.session_state.pipeline_step = 1
            st.session_state.screenplay_data = None
            st.session_state.image_urls = []
            st.session_state.link_data = None
            st.session_state.video_data = None
            st.rerun()

    # Step 1: Enter Campaign Details
    if st.session_state.pipeline_step == 1:
        st.header("Enter Campaign Details")
        
        with st.form("campaign_form"):
            project_name = st.text_input("Project Name", "My AI Video")
            
            col1, col2 = st.columns(2)
            with col1:
                campaign_brief = st.text_area("Campaign Brief", "A financial service helping people manage and reduce their debt through personalized plans and expert guidance.")
                tone = st.selectbox("Tone", ["Professional", "Emotional", "Humorous", "Serious", "Inspirational", "Conversational"])
            
            with col2:
                target_audience = st.text_area("Target Audience", "Adults 30-55 who are struggling with debt and seeking reliable solutions to regain financial stability.")
                product_details = st.text_area("Product/Service Details", "Debt resolution services with personalized plans, expert financial advisors, and a track record of helping clients reduce debt by an average of 30%.")
            
            num_scenes = st.slider("Number of Scenes", 2, 5, 3)
            
            submitted = st.form_submit_button("Generate Screenplay")
            
            if submitted:
                with st.spinner("Generating screenplay..."):
                    screenplay_data, error = generate_screenplay(
                        campaign_brief, tone, target_audience, product_details, num_scenes
                    )
                    if error:
                        st.error(f"Error generating screenplay: {error}")
                    else:
                        st.session_state.screenplay_data = screenplay_data
                        st.session_state.project_name = project_name
                        st.session_state.pipeline_step = 2
                        st.rerun()

    # Step 2: Display Screenplay and Confirm
    elif st.session_state.pipeline_step == 2:
        st.header("Review Generated Screenplay")
        
        screenplay_data = st.session_state.screenplay_data
        
        # Display the title
        st.subheader(screenplay_data["title"])
        
        # Display tabs for different views
        tab1, tab2, tab3 = st.tabs(["Screenplay", "Final Script", "Image Prompts"])
        
        with tab1:
            st.markdown(f'<div class="screenplay">{screenplay_data["screenplay"]}</div>', unsafe_allow_html=True)
        
        with tab2:
            st.markdown(f'<div class="card">{screenplay_data["final_script"]}</div>', unsafe_allow_html=True)
        
        with tab3:
            for i, prompt in enumerate(screenplay_data["image_prompts"]):
                st.markdown(f'<div class="card"><h4>Scene {i+1}</h4>{prompt}</div>', unsafe_allow_html=True)
        
        # Edit screenplay if needed
        if st.button("Edit Screenplay"):
            st.session_state.pipeline_step = 1
            st.rerun()
        
        # Proceed to image generation
        if st.button("Generate Images from Prompts"):
            st.session_state.pipeline_step = 3
            st.rerun()

    # Step 3: Generate and Upload Images
    elif st.session_state.pipeline_step == 3:
        st.header("Generate & Upload Images")
        
        screenplay_data = st.session_state.screenplay_data
        image_prompts = screenplay_data["image_prompts"]
        
        with st.spinner("Generating and uploading images..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            image_urls = []
            image_file_ids = []
            
            cols = st.columns(min(len(image_prompts), 3))
            
            for i, prompt in enumerate(image_prompts):
                status_text.text(f"Processing scene {i+1}/{len(image_prompts)}: Generating image...")
                
                # Generate image
                image_data, error = generate_image(prompt)
                
                if error:
                    st.error(f"Error generating image for scene {i+1}: {error}")
                    continue
                
                # Display image
                with cols[i % len(cols)]:
                    image = Image.open(BytesIO(image_data))
                    st.image(image, caption=f"Scene {i+1}", use_column_width=True)
                    
                    # Upload to ImageKit
                    status_text.text(f"Processing scene {i+1}/{len(image_prompts)}: Uploading to ImageKit...")
                    filename = f"scene-{i+1:02d}-{st.session_state.project_name.replace(' ', '-')}.png"
                    
                    url, file_id, upload_error = upload_to_imagekit(image_data, filename)
                    
                    if upload_error:
                        st.error(f"Error uploading image {i+1}: {upload_error}")
                    else:
                        image_urls.append(url)
                        image_file_ids.append(file_id)
                        st.success(f"Image {i+1} uploaded!")
                
                progress_bar.progress((i + 1) / len(image_prompts))
            
            # Create Creatify link
            if image_urls:
                status_text.text("Creating Creatify link with uploaded images...")
                
                link_data, link_error = create_creatify_link(
                    image_urls,
                    st.session_state.project_name,
                    f"Images for {st.session_state.project_name}"
                )
                
                if link_error:
                    st.error(link_error)
                else:
                    st.session_state.image_urls = image_urls
                    st.session_state.link_data = link_data
                    st.session_state.pipeline_step = 4
                    status_text.empty()
                    st.success("All images generated and uploaded! Link created successfully.")
                    st.button("Continue to Video Creation", on_click=lambda: st.rerun())
            else:
                st.error("No images were successfully generated and uploaded. Please try again.")

    # Step 4: Create Video
    elif st.session_state.pipeline_step == 4:
        st.header("Create Video")
        
        # Display images that will be used
        st.subheader("Images for Your Video")
        cols = st.columns(min(len(st.session_state.image_urls), 3))
        for i, url in enumerate(st.session_state.image_urls):
            with cols[i % len(cols)]:
                st.image(url, caption=f"Scene {i+1}", use_column_width=True)
        
        # Get available personas
        personas = get_personas()
        
        if personas:
            st.subheader("Select Avatar")
            
            # Display personas in a grid
            persona_cols = st.columns(3)
            selected_persona = None
            
            for i, persona in enumerate(personas[:6]):  # Limit to first 6 personas
                with persona_cols[i % 3]:
                    persona_id = persona.get("id")
                    preview_img = persona.get("preview_image_1_1")
                    
                    if preview_img:
                        st.image(preview_img, width=150)
                    
                    # Show persona characteristics as bubbles
                    gender = persona.get("gender", "unknown")
                    age = persona.get("age_range", "adult")
                    style = persona.get("style", "professional")
                    
                    characteristics = [
                        f"Gender: {gender}",
                        f"Age: {age}",
                        f"Style: {style}"
                    ]
                    
                    bubble_html = "<div>"
                    for char in characteristics:
                        bubble_html += f'<div class="bubble">{char}</div> '
                    bubble_html += "</div>"
                    
                    st.markdown(bubble_html, unsafe_allow_html=True)
                    
                    # Selection radio button
                    if st.radio("Select", ["No", "Yes"], key=f"persona_{i}") == "Yes":
                        selected_persona = persona_id
            
            # Video settings
            st.subheader("Video Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                platform = st.selectbox("Target Platform", ["Facebook", "Instagram", "YouTube", "TikTok", "LinkedIn"])
                language = st.selectbox("Language", ["en", "es", "fr", "de"])
            
            with col2:
                video_length = st.slider("Video Length (seconds)", 15, 60, 30)
                aspect_ratio = st.selectbox("Aspect Ratio", ["16x9", "1x1", "9x16"])
                
                # Get available voices
                voices = get_voices()
                
                # Display voice selection
                st.subheader("Select Voice")
                
                # Display voices in a scrollable container with preview functionality
                st.write("Click on a voice to preview how it sounds")
                
                # Create a container with fixed height for scrolling
                voice_container = st.container()
                with voice_container:
                    # Group voices by language for better organization
                    voice_by_language = {}
                    for voice in voices:
                        lang = voice.get("language", "Other")
                        if lang not in voice_by_language:
                            voice_by_language[lang] = []
                        voice_by_language[lang].append(voice)
                    
                    # Sort languages alphabetically
                    sorted_languages = sorted(voice_by_language.keys())
                    
                    # Create tabs for different language groups
                    if sorted_languages:
                        tabs = st.tabs(sorted_languages)
                        
                        for i, lang in enumerate(sorted_languages):
                            with tabs[i]:
                                lang_voices = voice_by_language[lang]
                                
                                # Use a single-level column layout
                                for j, voice in enumerate(lang_voices):
                                    voice_id = voice.get("voice_id")
                                    voice_name = voice.get("name", "Unnamed")
                                    voice_gender = voice.get("gender", "Unspecified")
                                    
                                    # Create an expander for each voice - this is more space-efficient
                                    with st.expander(f"{voice_name} ({voice_gender})"):
                                        # Preview button
                                        if st.button("Preview Voice", key=f"preview_{voice_id}"):
                                            with st.spinner("Generating preview..."):
                                                preview_url, error = generate_voice_preview(voice_id)
                                                if error:
                                                    st.error(error)
                                                elif preview_url:
                                                    st.audio(preview_url, format="audio/mp3")
                                                else:
                                                    st.warning("No preview available")
                                        
                                        # Select button
                                        if st.button("Use This Voice", key=f"select_{voice_id}"):
                                            st.session_state.selected_voice = voice_id
                                            st.session_state.selected_voice_name = voice_name
                                            st.success(f"Selected voice: {voice_name}")
                    else:
                        st.warning("No voices available")
                
                # Show the currently selected voice
                if 'selected_voice' in st.session_state:
                    st.info(f"Currently selected voice: {st.session_state.get('selected_voice_name', 'Unknown')}")
                    
                    # Voice volume slider
                    voice_volume = st.slider("Voice Volume", 0.0, 1.0, 0.5, 0.1)
                    
                    # Store in session state
                    st.session_state.voice_volume = voice_volume
                else:
                    st.info("No voice selected yet. Default voice will be used.")
                    st.session_state.selected_voice = ""
                    st.session_state.voice_volume = 0.5
            
            # Create video button
            if st.button("Create Video") and selected_persona and st.session_state.link_data:
                with st.spinner("Creating video..."):
                    link_id = st.session_state.link_data.get("id")
                    script = st.session_state.screenplay_data.get("final_script")
                    
                    # Create the video using the API
                    video_data, video_error = create_video(
                        link_id,
                        st.session_state.project_name,
                        script,
                        selected_persona,
                        platform=platform,
                        language=language,
                        length=video_length,
                        ratio=aspect_ratio,
                        voice_id=st.session_state.selected_voice,
                        volume=st.session_state.voice_volume
                    )
                    
                    if video_error:
                        st.error(video_error)
                    else:
                        st.session_state.video_data = video_data
                        st.session_state.pipeline_step = 5
                        st.success("Video creation initiated!")
                        st.button("View Results", on_click=lambda: st.rerun())
        else:
            st.error("No personas available. Please check your API connection.")

    # Step 5: View Results
    elif st.session_state.pipeline_step == 5:
        st.header("Video Results")
        
        if not st.session_state.video_data:
            st.error("No video data available. Please go back and create a video.")
            st.session_state.pipeline_step = 4
            st.button("Go Back", on_click=lambda: st.rerun())
        else:
            # Get current status
            video_id = st.session_state.video_data.get("id")
            video_status, status_error = get_video_status(video_id)
            
            if status_error:
                st.error(status_error)
            else:
                # Update session state
                st.session_state.video_data = video_status
                
                # Display status card
                status = video_status.get("status", "unknown")
                progress = video_status.get("progress", 0)
                
                st.markdown(f"""
                    <div class="card">
                        <h3>Video Status</h3>
                        <p><strong>Project:</strong> {st.session_state.project_name}</p>
                        <p><strong>Status:</strong> {status}</p>
                        <p><strong>Progress:</strong> {progress*100:.0f}%</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.progress(progress)
                
                # Show characteristics in bubbles
                st.subheader("Video Characteristics")
                
                characteristics = [
                    f"Platform: {video_status.get('target_platform', 'unknown')}",
                    f"Audience: {video_status.get('target_audience', 'unknown')}",
                    f"Length: {video_status.get('video_length', 0)} seconds",
                    f"Aspect Ratio: {video_status.get('aspect_ratio', 'unknown')}",
                    f"Language: {video_status.get('language', 'unknown')}",
                    f"Style: {video_status.get('visual_style', 'unknown')}"
                ]
                
                bubble_html = "<div>"
                for char in characteristics:
                    bubble_html += f'<div class="bubble">{char}</div> '
                bubble_html += "</div>"
                
                st.markdown(bubble_html, unsafe_allow_html=True)
                
                # Check status and show appropriate content
                if status == "pending" or status == "running":
                    st.info("Your video is being processed. This may take a few minutes.")
                    
                    # Show refresh button
                    if st.button("Refresh Status"):
                        st.rerun()
                    
                    # Show preview if available
                    preview_url = video_status.get("preview")
                    if preview_url:
                        st.subheader("Preview")
                        st.markdown(f"""
                            <div class="card">
                                <p>View your video preview:</p>
                                <a href="{preview_url}" target="_blank" class="stButton">
                                    <button>Open Preview</button>
                                </a>
                            </div>
                        """, unsafe_allow_html=True)
                
                elif status == "done":
                    st.success("Your video is ready!")
                    
                    # Display the video
                    video_url = video_status.get("video_output")
                    if video_url:
                        st.subheader("Your Video")
                        st.markdown(f"""
                            <div class="video-container">
                                <video width="100%" controls>
                                    <source src="{video_url}" type="video/mp4">
                                    Your browser does not support video playback.
                                </video>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Download button
                        st.download_button(
                            label="Download Video",
                            data=requests.get(video_url).content,
                            file_name=f"{st.session_state.project_name.replace(' ', '_')}.mp4",
                            mime="video/mp4"
                        )
                        
                        # Show script for reference
                        st.subheader("Script")
                        st.markdown(f"""
                            <div class="card">
                                <p>{st.session_state.screenplay_data.get('final_script')}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("Video URL not available. There might be an issue with the video.")
                
                elif status == "failed":
                    st.error("Video creation failed.")
                    failed_reason = video_status.get("failed_reason", "Unknown reason")
                    st.write(f"Reason: {failed_reason}")
                    
                    # Option to try again
                    if st.button("Try Again"):
                        st.session_state.pipeline_step = 4
                        st.rerun()
                
                # Render button (for pending/running status)
                if status != "done" and status != "failed":
                    if st.button("Render Final Video"):
                        with st.spinner("Rendering video..."):
                            render_result, render_error = render_video(video_id)
                            
                            if render_error:
                                st.error(render_error)
                            else:
                                st.session_state.video_data = render_result
                                st.success("Rendering started!")
                                st.rerun()

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
    elif st.session_state.page == "video_pipeline":
        render_video_pipeline()

if __name__ == "__main__":
    main()
