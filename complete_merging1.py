import streamlit as st
import requests
import json
import base64
import time
import os
import pandas as pd
import re
from PIL import Image
from io import BytesIO
import uuid

# API credentials and configuration
API_KEYS = {
    "CREATIFY_API_ID": "5f8b3a5c-6e33-4e9f-b85c-71941d675270",
    "CREATIFY_API_KEY": "c019dd017d22e2e40627f87bc86168b631b9a345",
    "GEMINI_API_KEY": "AIzaSyBLzfjImenFp60acvXgKygaEDKGqKfHyKI",
    "IMAGEKIT_PRIVATE_KEY": "private_OGgux+C54n9PIYDlLdOrYysEWrw=",
    "IMAGEKIT_PUBLIC_KEY": "public_Qq9s197rBPKyx5eWhq+aN6TQ3Iw=",
    "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/b6pq3mgo7",
    "SERPER_API_KEY": "14b865cf1dae8d1149dea6a7d2c93f8ac0105970",
    "OPENAI_API_KEY": "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",
    "GROQ_API_KEY": "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",
    "ELEVENLABS_API_KEY": "your_elevenlabs_api_key",
    "TAVUS_API_KEY": "d57e6c687a894213aa87abad7c1c5f56"
}

# Set page configuration
st.set_page_config(
    page_title="AI Creative Suite",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define color scheme
PRIMARY_COLOR = "#2196F3"  # Blue
SECONDARY_COLOR = "#e6f3ff"  # Light blue
TEXT_COLOR = "#2C3E50"  # Dark blue/gray

# Apply custom CSS
st.markdown(f"""
<style>
    .stApp {{
        background-color: white;
    }}
    .stButton > button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border-radius: 6px;
        border: 1px solid {PRIMARY_COLOR};
        padding: 0.5rem 1rem;
        font-weight: 500;
    }}
    .stButton > button:hover {{
        background-color: #1976D2;
        border: 1px solid #1976D2;
    }}
    .card {{
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #e0e0e0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
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
    .header {{
        background-color: {PRIMARY_COLOR};
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }}
    .voice-card {{
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: white;
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
        color: white;
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
    .video-container {{
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }}
    .chat-message {{
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }}
    .user-message {{
        background-color: #e6f7ff;
        border-left: 4px solid #1890ff;
    }}
    .ai-message {{
        background-color: #f6f6f6;
        border-left: 4px solid #d9d9d9;
    }}
    .chat-name {{
        font-weight: bold;
        margin-bottom: 0.5rem;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'script' not in st.session_state:
    st.session_state.script = ""
if 'screenplay_data' not in st.session_state:
    st.session_state.screenplay_data = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'selected_voice' not in st.session_state:
    st.session_state.selected_voice = None
if 'selected_voice_name' not in st.session_state:
    st.session_state.selected_voice_name = ""
if 'selected_avatar' not in st.session_state:
    st.session_state.selected_avatar = None
if 'selected_video_style' not in st.session_state:
    st.session_state.selected_video_style = None
if 'generated_audio' not in st.session_state:
    st.session_state.generated_audio = None
if 'generated_video' not in st.session_state:
    st.session_state.generated_video = None
if 'voice_pagination' not in st.session_state:
    st.session_state.voice_pagination = {}
if 'voice_page' not in st.session_state:
    st.session_state.voice_page = 1
if 'video_page' not in st.session_state:
    st.session_state.video_page = 1
if 'image_urls' not in st.session_state:
    st.session_state.image_urls = []
if 'link_data' not in st.session_state:
    st.session_state.link_data = None
if 'video_data' not in st.session_state:
    st.session_state.video_data = None
if 'campaign_brief' not in st.session_state:
    st.session_state.campaign_brief = {}
if 'brief_conversation' not in st.session_state:
    st.session_state.brief_conversation = []
if 'brief_stage' not in st.session_state:
    st.session_state.brief_stage = "initial"

# API Headers
headers = {
    "X-API-ID": API_KEYS["CREATIFY_API_ID"],
    "X-API-KEY": API_KEYS["CREATIFY_API_KEY"],
    "Content-Type": "application/json"
}

# Navigation functions
def go_to_home():
    st.session_state.page = "home"

def go_to_brief_generator():
    st.session_state.page = "brief_generator"

def go_to_script_generator():
    st.session_state.page = "script_generator"

def go_to_audio_generator():
    st.session_state.page = "audio_generator"

def go_to_video_generator():
    st.session_state.page = "video_generator"

def go_to_screenplay_generator():
    st.session_state.page = "screenplay_generator"

def go_to_image_generator():
    st.session_state.page = "image_generator"

def go_to_video_results():
    st.session_state.page = "video_results"

def set_script(script_text):
    st.session_state.script = script_text
    go_to_audio_generator()

def select_voice(voice_id, voice_name=""):
    st.session_state.selected_voice = voice_id
    st.session_state.selected_voice_name = voice_name

def select_avatar(avatar_id):
    st.session_state.selected_avatar = avatar_id

def select_video_style(style_id):
    st.session_state.selected_video_style = style_id

# API Functions
@st.cache_data(ttl=3600)
def get_personas():
    """Get available personas from the Creatify API"""
    url = "https://api.creatify.ai/api/personas/paginated/"
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        st.error(f"Error fetching personas: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_voices():
    """Get available voices from the Creatify API"""
    url = "https://api.creatify.ai/api/voices/"
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        st.error(f"Error fetching voices: {str(e)}")
        # Return a fallback list of voices
        return [
            {"voice_id": "en-US-Wavenet-A", "name": "US Male", "gender": "Male", "language": "English (US)"},
            {"voice_id": "en-US-Wavenet-C", "name": "US Female", "gender": "Female", "language": "English (US)"},
            {"voice_id": "en-GB-Wavenet-B", "name": "UK Male", "gender": "Male", "language": "English (UK)"},
            {"voice_id": "en-GB-Wavenet-C", "name": "UK Female", "gender": "Female", "language": "English (UK)"}
        ]

@st.cache_data(ttl=3600)
def get_tavus_replicas():
    """Get available replicas from the Tavus API"""
    url = "https://tavusapi.com/v2/replicas"
    headers = {"x-api-key": API_KEYS["TAVUS_API_KEY"]}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        df = pd.json_normalize(data['data'])
        df_selected = df[['thumbnail_video_url', 'model_name', 'replica_id', 'replica_name']]
        return df_selected.to_dict('records')
    except Exception as e:
        st.error(f"Error fetching Tavus replicas: {str(e)}")
        return []

def generate_screenplay(campaign_brief, tone, target_audience, product_details, num_scenes):
    """Generate screenplay using Gemini"""
    from google import genai
    
    # Initialize Gemini client
    try:
        client = genai.Client(api_key=API_KEYS["GEMINI_API_KEY"])
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {str(e)}")
        return None, str(e)
    
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

        # Generate content
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=prompt
        )
        
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

def generate_image(prompt):
    """Generate image with Gemini"""
    from google import genai
    from google.genai import types
    
    # Initialize Gemini client
    try:
        client = genai.Client(api_key=API_KEYS["GEMINI_API_KEY"])
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {str(e)}")
        return None, str(e)
    
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

def upload_to_imagekit(image_data, filename):
    """Upload image to ImageKit"""
    try:
        # Convert image to bytes if it's not already
        if isinstance(image_data, Image.Image):
            buffer = BytesIO()
            image_data.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
        else:
            image_bytes = image_data
            
        # Create a file-like object
        file_like = BytesIO(image_bytes)
        
        # Prepare the upload
        url = f"https://upload.imagekit.io/api/v1/files/upload"
        
        # Create authentication header
        auth_str = base64.b64encode(f"{API_KEYS['IMAGEKIT_PRIVATE_KEY']}:".encode()).decode()
        
        headers_upload = {
            "Authorization": f"Basic {auth_str}"
        }
        
        files = {
            'file': (filename, file_like, 'image/png'),
            'fileName': (None, filename),
            'publicKey': (None, API_KEYS["IMAGEKIT_PUBLIC_KEY"]),
        }
        
        response = requests.post(url, files=files, headers=headers_upload)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("url"), result.get("fileId"), None
        else:
            return None, None, f"Upload failed with status {response.status_code}: {response.text}"
            
    except Exception as e:
        return None, None, str(e)

def create_creatify_link(image_urls, title, description):
    """Create Creatify link"""
    url = "https://api.creatify.ai/api/links/link_with_params/"
    
    payload = {
        "title": title,
        "description": description,
        "image_urls": image_urls,
        "video_urls": [],
        "reviews": "Generated with AI Creative Suite"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json(), None
    except Exception as e:
        return None, f"Error creating link: {str(e)}"

def create_video(link_id, name, script, avatar_id, **kwargs):
    """Create video"""
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

def get_video_status(video_id):
    """Get video status"""
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/"
    
    try:
        response = requests.get(url, headers=headers)
        return response.json(), None
    except Exception as e:
        return None, f"Error getting video status: {str(e)}"

def render_video(video_id):
    """Render video"""
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/render/"
    
    try:
        response = requests.post(url, headers=headers)
        return response.json(), None
    except Exception as e:
        return None, f"Error rendering video: {str(e)}"

def generate_tavus_video(replica_name, video_name, script_text, audio_url, background_url, replicas_df):
    """Generate video with Tavus API"""
    url = "https://tavusapi.com/v2/videos"
    replica_id_map = dict(zip(replicas_df["replica_name"], replicas_df["replica_id"]))
    
    headers = {
        "x-api-key": API_KEYS["TAVUS_API_KEY"],
        "Content-Type": "application/json"
    }

    payload = {
        "background_url": background_url,
        "replica_id": replica_id_map[replica_name] if replica_name in replica_id_map else "",
        "script": script_text,
        "audio_url": audio_url,
        "video_name": video_name
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            return f"Error creating video: {response.status_code} - {response.text}", None

        video_id = response.json().get("video_id")
        if not video_id:
            return "No video ID returned by Tavus.", None

        # Polling until status is 'ready'
        status_url = f"https://tavusapi.com/v2/videos/{video_id}"
        for i in range(10):  # Up to ~30 seconds
            time.sleep(3)
            status_response = requests.get(status_url, headers=headers)
            status_data = status_response.json()
            if status_data.get("status") == "ready":
                stream_url = status_data.get("stream_url")
                return f"Video is ready! Video ID: {video_id}", stream_url

        return "Video is still processing. Please check back later.", None
    except Exception as e:
        return f"Error: {str(e)}", None

def simulate_brief_generation(user_input):
    """Simulate brief generation using Groq"""
    # This would integrate with your actual brief generation code
    time.sleep(2)  # Simulate processing time
    
    # Generate a mock brief based on the input
    brief = {
        "campaign_objective": "Generate awareness and leads for financial services",
        "target_audience": "Adults 30-55 struggling with debt",
        "product_details": "Debt resolution services with personalized plans",
        "tone": "Empathetic but professional",
        "key_message": "Take control of your finances with expert help",
        "call_to_action": "Start your free debt review today"
    }
    
    return brief

def simulate_script_generation(brief):
    """Simulate script generation"""
    # This would integrate with your actual script crew functionality
    time.sleep(3)  # Simulate processing time
    
    return f"""Hey there... Are you feeling overwhelmed by credit card debt? I was too... until I found something that changed everything.

I used to dread every bill that came in... It felt like a never-ending cycle of stress.

But then I discovered this debt relief program that helped consolidate my payments into one simple monthly fee.

The best part? It barely impacted my credit score! I finally started to breathe again, knowing there was a way out.

If you're ready to take that first step towards relief, check it out now! You deserve to feel free from debt..."""

def simulate_audio_generation(script, voice_id):
    """Simulate audio generation"""
    # This would integrate with your actual audio generation
    time.sleep(2)  # Simulate processing time
    
    # In a real implementation, this would return an audio file URL
    return "simulated_audio.mp3"

# UI Components
def render_sidebar():
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=AI+Suite", width=150)
        st.markdown("### Navigation")
        
        if st.button("🏠 Home", key="nav_home"):
            go_to_home()
            
        if st.button("📝 Brief Generator", key="nav_brief"):
            go_to_brief_generator()
            
        if st.button("📜 Script Generator", key="nav_script"):
            go_to_script_generator()
        
        if st.button("🎭 Screenplay Generator", key="nav_screenplay"):
            go_to_screenplay_generator()
            
        if st.session_state.script or st.session_state.screenplay_data:
            if st.button("🎙️ Audio Generator", key="nav_audio"):
                go_to_audio_generator()
                
            if st.button("🖼️ Image Generator", key="nav_image"):
                go_to_image_generator()
                
            if st.button("🎬 Video Generator", key="nav_video"):
                go_to_video_generator()
                
        if st.session_state.video_data:
            if st.button("🎥 View Results", key="nav_results"):
                go_to_video_results()
            
        st.markdown("---")
        st.markdown("### Current Progress")
        
        progress_items = {
            "Brief": "✅" if st.session_state.campaign_brief else "❌",
            "Script/Screenplay": "✅" if st.session_state.script or st.session_state.screenplay_data else "❌",
            "Voice": "✅" if st.session_state.selected_voice else "❌",
            "Audio": "✅" if st.session_state.generated_audio else "❌",
            "Images": "✅" if st.session_state.image_urls else "❌",
            "Video": "✅" if st.session_state.video_data else "❌"
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
            if st.session_state.script or st.session_state.screenplay_data:
                go_to_audio_generator()
            else:
                go_to_brief_generator()
    
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-title">1. Create Brief</div>
            <p>Generate a detailed campaign brief using our AI assistant to capture your objectives.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-title">2. Generate Script</div>
            <p>Create a professional script or screenplay using AI or upload your own content.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-title">3. Add Audio & Images</div>
            <p>Select from AI voices and generate visuals to bring your script to life.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown("""
        <div class="card">
            <div class="card-title">4. Create Video</div>
            <p>Choose a video style and generate a professional video with your assets.</p>
        </div>
        """, unsafe_allow_html=True)

def render_brief_generator():
    st.markdown("<h1 class='main-header'>Campaign Brief Generator</h1>", unsafe_allow_html=True)
    
    # Brief interaction area
    st.markdown("""
    <div class="card">
        <p>Let our AI assistant help you define your campaign objectives. Answer a series of questions to generate a detailed brief.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display conversation history
    for i, message in enumerate(st.session_state.brief_conversation):
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <div class="chat-name">You:</div>
                <div>{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message ai-message">
                <div class="chat-name">AI:</div>
                <div>{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Initial prompt if conversation hasn't started
    if not st.session_state.brief_conversation and st.session_state.brief_stage == "initial":
        st.session_state.brief_conversation.append({
            "role": "assistant",
            "content": "Hi there! I'm your campaign brief assistant. Let's create a detailed brief for your ad campaign. What type of product or service are you looking to promote today?"
        })
        st.rerun()
    
    # User input for brief generation
    user_input = st.text_input("Your response:", key="brief_input")
    
    if st.button("Send", key="send_brief") and user_input:
        # Add user message to conversation
        st.session_state.brief_conversation.append({
            "role": "user",
            "content": user_input
        })
        
        # Process based on conversation stage
        if st.session_state.brief_stage == "initial":
            # First question about product/service
            response = "Great! Could you tell me about your target audience? Who would benefit most from this product/service?"
            st.session_state.brief_stage = "audience"
            
        elif st.session_state.brief_stage == "audience":
            # Second question about target audience
            response = "Perfect. What tone would you like your campaign to have? (Examples: Professional, Emotional, Humorous, Serious, Inspirational)"
            st.session_state.brief_stage = "tone"
            
        elif st.session_state.brief_stage == "tone":
            # Third question about tone
            response = "What's the key message or benefit you want to highlight in this campaign?"
            st.session_state.brief_stage = "message"
            
        elif st.session_state.brief_stage == "message":
            # Fourth question about key message
            response = "What call-to-action would you like to include?"
            st.session_state.brief_stage = "cta"
            
        elif st.session_state.brief_stage == "cta":
            # Process final input and generate brief
            with st.spinner("Generating campaign brief..."):
                # In a real implementation, this would call your brief generation function
                
                # Extract information from conversation
                product_info = st.session_state.brief_conversation[1]["content"] if len(st.session_state.brief_conversation) > 1 else ""
                audience_info = st.session_state.brief_conversation[3]["content"] if len(st.session_state.brief_conversation) > 3 else ""
                tone_info = st.session_state.brief_conversation[5]["content"] if len(st.session_state.brief_conversation) > 5 else ""
                message_info = st.session_state.brief_conversation[7]["content"] if len(st.session_state.brief_conversation) > 7 else ""
                cta_info = user_input
                
                # Create brief summary
                st.session_state.campaign_brief = {
                    "product_details": product_info,
                    "target_audience": audience_info,
                    "tone": tone_info,
                    "key_message": message_info,
                    "call_to_action": cta_info
                }
                
                response = f"""
                ## Campaign Brief Summary
                
                **Product/Service Details:** {product_info}
                
                **Target Audience:** {audience_info}
                
                **Tone:** {tone_info}
                
                **Key Message:** {message_info}
                
                **Call-to-Action:** {cta_info}
                
                Great! I've created your campaign brief. You can now proceed to script generation or screenplay creation.
                """
                
                st.session_state.brief_stage = "completed"
                
        else:
            # Default response for any other stage
            response = "Your brief is now complete. Would you like to generate a script or screenplay based on this brief?"
        
        # Add assistant response to conversation
        st.session_state.brief_conversation.append({
            "role": "assistant",
            "content": response
        })
        
        st.rerun()
    
    # Brief completed, show next step buttons
    if st.session_state.brief_stage == "completed":
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Script", key="gen_script_from_brief"):
                go_to_script_generator()
        
        with col2:
            if st.button("Create Screenplay", key="gen_screenplay_from_brief"):
                go_to_screenplay_generator()

def render_script_generator():
    st.markdown("<h1 class='main-header'>Script Generator</h1>", unsafe_allow_html=True)
    
    # Two options: Generate with AI or Upload
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3>Generate with AI</h3>", unsafe_allow_html=True)
        
        # If we have a campaign brief, use it
        if st.session_state.campaign_brief:
            st.markdown("""
            <div class="card">
                <div class="card-title">Using Campaign Brief</div>
            """, unsafe_allow_html=True)
            
            for key, value in st.session_state.campaign_brief.items():
                st.markdown(f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Otherwise, allow direct prompt
        else:
            st.markdown("""
            <div class="card">
                <p>No campaign brief found. Please describe what kind of script you want to create.</p>
            </div>
            """, unsafe_allow_html=True)
            
        user_prompt = st.text_area("Additional instructions or modifications:", 
                                  height=100, 
                                  placeholder="Example: Add more emotional appeal, emphasize the affordability, focus on long-term benefits...")
        
        if st.button("Generate Script", key="gen_script_btn"):
            with st.spinner("Generating your script..."):
                if st.session_state.campaign_brief:
                    # In a real implementation, you would use the campaign brief
                    script = simulate_script_generation(st.session_state.campaign_brief)
                else:
                    # Use the direct prompt
                    script = simulate_script_generation({"prompt": user_prompt})
                
                st.session_state.script = script
                st.success("Script generated successfully!")
                st.rerun()
                
        # Chat interface for refining the script
        if st.session_state.script:
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
            script_text = st.text_area("Your script:", value=st.session_state.script, height=400, key="script_preview")
            
            # Update script if edited
            if script_text != st.session_state.script:
                st.session_state.script = script_text
                
            if st.button("Proceed to Audio Generation", key="proceed_to_audio"):
                go_to_audio_generator()
        else:
            st.info("No script available yet. Generate or upload a script to see preview.")

def render_screenplay_generator():
    st.markdown("<h1 class='main-header'>Screenplay Generator</h1>", unsafe_allow_html=True)
    
    # Two columns layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<h3>Generate Ad Screenplay</h3>", unsafe_allow_html=True)
        
        # Form for screenplay generation
        with st.form("screenplay_form"):
            # If we have a campaign brief, use it and allow edits
            if st.session_state.campaign_brief:
                campaign_brief = st.text_area(
                    "Campaign Brief", 
                    value=st.session_state.campaign_brief.get("product_details", ""), 
                    height=100
                )
                
                target_audience = st.text_area(
                    "Target Audience", 
                    value=st.session_state.campaign_brief.get("target_audience", ""), 
                    height=100
                )
                
                tone = st.selectbox(
                    "Tone", 
                    ["Professional", "Emotional", "Humorous", "Serious", "Inspirational", "Conversational"],
                    index=["Professional", "Emotional", "Humorous", "Serious", "Inspirational", "Conversational"].index(
                        st.session_state.campaign_brief.get("tone", "Professional")
                    ) if st.session_state.campaign_brief.get("tone", "") in ["Professional", "Emotional", "Humorous", "Serious", "Inspirational", "Conversational"] else 0
                )
                
                product_details = st.text_area(
                    "Product/Service Details", 
                    value=st.session_state.campaign_brief.get("key_message", ""), 
                    height=100
                )
            else:
                # No brief, let user input everything
                campaign_brief = st.text_area(
                    "Campaign Brief", 
                    "A financial service helping people manage and reduce their debt through personalized plans and expert guidance.",
                    height=100
                )
                
                target_audience = st.text_area(
                    "Target Audience", 
                    "Adults 30-55 who are struggling with debt and seeking reliable solutions to regain financial stability.",
                    height=100
                )
                
                tone = st.selectbox(
                    "Tone", 
                    ["Professional", "Emotional", "Humorous", "Serious", "Inspirational", "Conversational"]
                )
                
                product_details = st.text_area(
                    "Product/Service Details", 
                    "Debt resolution services with personalized plans, expert financial advisors, and a track record of helping clients reduce debt by an average of 30%.",
                    height=100
                )
            
            num_scenes = st.slider("Number of Scenes", 2, 5, 3)
            
            submitted = st.form_submit_button("Generate Screenplay")
            
            if submitted:
                with st.spinner("Generating screenplay..."):
                    # This would be the real API call in your implementation
                    screenplay_data, error = generate_screenplay(
                        campaign_brief, tone, target_audience, product_details, num_scenes
                    )
                    
                    if error:
                        st.error(f"Error generating screenplay: {error}")
                    else:
                        st.session_state.screenplay_data = screenplay_data
                        st.session_state.script = screenplay_data.get("final_script", "")
                        st.success("Screenplay generated successfully!")
                        st.rerun()
    
    with col2:
        # Information and tips
        st.markdown("""
        <div class="card">
            <div class="card-title">About Screenplay Generation</div>
            <p>Our AI creates professional, visually-driven screenplays for effective ads.</p>
            <ul>
                <li>Scene-by-scene structure with visual details</li>
                <li>Professional formatting with scene headings</li>
                <li>Generated image prompts for each scene</li>
                <li>Complete voiceover script for narration</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card">
            <div class="card-title">Tips for Great Results</div>
            <ul>
                <li>Be specific about your target audience</li>
                <li>Clearly describe your product's benefits</li>
                <li>Choose a tone that matches your brand</li>
                <li>Focus on visual storytelling opportunities</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Display screenplay result if available
    if st.session_state.screenplay_data:
        st.markdown("---")
        st.markdown("<h3>Generated Screenplay</h3>", unsafe_allow_html=True)
        
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
        
        # Next steps buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Generate Images", key="gen_images_btn"):
                go_to_image_generator()
        
        with col2:
            if st.button("Create Audio", key="create_audio_btn"):
                go_to_audio_generator()
        
        with col3:
            if st.button("Generate Video", key="gen_video_from_screenplay"):
                go_to_video_generator()

def render_audio_generator():
    st.markdown("<h1 class='main-header'>Audio Generator</h1>", unsafe_allow_html=True)
    
    if not st.session_state.script and not st.session_state.screenplay_data:
        st.warning("You need a script or screenplay first. Please generate or upload content.")
        if st.button("Go to Script Generator"):
            go_to_script_generator()
        return
    
    # Voice selection area
    st.markdown("<h3>Select a Voice</h3>", unsafe_allow_html=True)
    
    # Get voices with their preview URLs
    voices = get_voices()
    
    # Create tabs for different audio services
    tabs = st.tabs(["Creatify Voices", "Tavus Replicas", "Upload Your Audio"])
    
    with tabs[0]:  # Creatify Voices
        # Group voices by language for better organization
        voice_by_language = {}
        for voice in voices:
            lang = voice.get("language", "Other")
            if lang not in voice_by_language:
                voice_by_language[lang] = []
            voice_by_language[lang].append(voice)
        
        # Sort languages alphabetically
        sorted_languages = sorted(voice_by_language.keys())
        
        # Initialize pagination for any new languages
        for lang in sorted_languages:
            if lang not in st.session_state.voice_pagination:
                st.session_state.voice_pagination[lang] = 0
        
        # Create tabs for different language groups
        if sorted_languages:
            lang_tabs = st.tabs(sorted_languages)
            
            for tab_idx, lang in enumerate(sorted_languages):
                with lang_tabs[tab_idx]:
                    lang_voices = voice_by_language[lang]
                    
                    # Pagination settings
                    voices_per_page = 3  # Show 3 voices per page
                    total_pages = (len(lang_voices) + voices_per_page - 1) // voices_per_page
                    
                    # Start and end indices for current page
                    current_page = st.session_state.voice_pagination[lang]
                    start_idx = current_page * voices_per_page
                    end_idx = min(start_idx + voices_per_page, len(lang_voices))
                    
                    # Display current page range info
                    st.markdown(f"**Showing voices {start_idx+1}-{end_idx} of {len(lang_voices)}**")
                    
                    # Display only the voices for the current page
                    for voice_idx in range(start_idx, end_idx):
                        voice = lang_voices[voice_idx]
                        voice_id = voice.get("voice_id")
                        voice_name = voice.get("name", "Unnamed")
                        voice_gender = voice.get("gender", "Unspecified")
                        
                        # Get preview URL from the accents list if available
                        preview_url = ""
                        accent_name = ""
                        accents = voice.get("accents", [])
                        if accents and len(accents) > 0:
                            preview_url = accents[0].get("preview_url", "")
                            accent_name = accents[0].get("accent_name", "")
                        
                        # Check if this voice is currently selected
                        is_selected = st.session_state.selected_voice == voice_id
                        
                        # Create a card for each voice
                        with st.container():
                            # Voice card with name and properties
                            title_col, status_col = st.columns([3, 1])
                            with title_col:
                                st.markdown(f"### {voice_name}")
                            with status_col:
                                if is_selected:
                                    st.markdown("✅ **Selected**")
                            
                            # Show voice characteristics as bubbles
                            bubbles = [
                                f"Gender: {voice_gender}",
                                f"Language: {lang}"
                            ]
                            
                            if accent_name:
                                bubbles.append(f"Accent: {accent_name}")
                                
                            bubble_html = "<div>"
                            for bubble in bubbles:
                                bubble_html += f'<span class="bubble">{bubble}</span> '
                            bubble_html += "</div>"
                            
                            st.markdown(bubble_html, unsafe_allow_html=True)
                            
                            # Two column layout: audio player and selection button
                            col1, col2 = st.columns([2, 1])
                            
                            # Display audio player if we have a preview URL
                            with col1:
                                if preview_url:
                                    st.audio(preview_url, format="audio/mp3")
                                else:
                                    st.info("Voice preview not available")
                            
                            # Select button with unique key - with different text if already selected
                            with col2:
                                button_text = "Selected" if is_selected else "Use This Voice"
                                button_disabled = is_selected
                                
                                if st.button(button_text, key=f"select_{lang}_{voice_idx}", disabled=button_disabled):
                                    # Save both the voice_id and name in session state
                                    select_voice(voice_id, voice_name)
                                    st.rerun()  # Refresh to show the updated selection
                            
                            # Add separator between voices
                            st.markdown("---")
                    
                    # Pagination navigation
                    if total_pages > 1:
                        col1, col2, col3 = st.columns([1, 3, 1])
                        
                        with col1:
                            if current_page > 0:
                                if st.button("← Previous", key=f"prev_{lang}"):
                                    st.session_state.voice_pagination[lang] = current_page - 1
                                    st.rerun()
                        
                        with col2:
                            # Page selector - dropdown to jump to specific page
                            page_options = [f"Page {i+1} of {total_pages}" for i in range(total_pages)]
                            selected_page = st.selectbox(
                                "Go to page:", 
                                page_options, 
                                index=current_page,
                                key=f"page_select_{lang}"
                            )
                            # Extract page number from selection and update if changed
                            selected_page_num = int(selected_page.split()[1]) - 1
                            if selected_page_num != current_page:
                                st.session_state.voice_pagination[lang] = selected_page_num
                                st.rerun()
                        
                        with col3:
                            if current_page < total_pages - 1:
                                if st.button("Next →", key=f"next_{lang}"):
                                    st.session_state.voice_pagination[lang] = current_page + 1
                                    st.rerun()
    
    with tabs[1]:  # Tavus Replicas
        # Get Tavus replicas
        replicas = get_tavus_replicas()
        
        if not replicas:
            st.warning("No Tavus replicas available.")
        else:
            # Display replicas in a grid
            cols = st.columns(3)
            for i, replica in enumerate(replicas[:6]):  # Show first 6 replicas
                with cols[i % 3]:
                    replica_name = replica.get("replica_name", "Unnamed")
                    preview_url = replica.get("thumbnail_video_url", "")
                    
                    # Check if this replica is currently selected
                    is_selected = st.session_state.selected_voice == f"tavus_{replica.get('replica_id')}"
                    
                    st.markdown(f"### {replica_name}")
                    
                    if preview_url:
                        st.video(preview_url)
                    else:
                        st.info("Preview not available")
                    
                    # Select button
                    button_text = "Selected" if is_selected else "Use This Replica"
                    button_disabled = is_selected
                    
                    if st.button(button_text, key=f"select_tavus_{i}", disabled=button_disabled):
                        select_voice(f"tavus_{replica.get('replica_id')}", replica_name)
                        st.rerun()
    
    with tabs[2]:  # Upload your own audio
        st.markdown("### Upload Your Own Audio")
        
        uploaded_audio = st.file_uploader("Upload an audio file", type=["mp3", "wav", "ogg"])
        
        if uploaded_audio is not None:
            st.audio(uploaded_audio)
            st.session_state.generated_audio = uploaded_audio
            st.success("Audio uploaded successfully!")
    
    # Display currently selected voice
    if st.session_state.selected_voice:
        st.success(f"Currently selected voice: {st.session_state.selected_voice_name}")
        
        # Voice volume slider
        voice_volume = st.slider("Voice Volume", 0.0, 1.0, 0.5, 0.1)
        st.session_state.voice_volume = voice_volume
    
    # Generate audio button
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Button to generate audio
        if st.button("Generate Audio", key="gen_audio_btn", disabled=not st.session_state.selected_voice and not st.session_state.generated_audio):
            if st.session_state.selected_voice:
                with st.spinner("Generating audio..."):
                    # In a real implementation, this would call your audio generation function
                    script_text = st.session_state.script
                    if st.session_state.screenplay_data:
                        script_text = st.session_state.screenplay_data.get("final_script", script_text)
                    
                    generated_audio = simulate_audio_generation(script_text, st.session_state.selected_voice)
                    st.session_state.generated_audio = generated_audio
                    st.success("Audio generated successfully!")
                    st.rerun()
    
    with col2:
        # Proceed to next step
        if st.session_state.generated_audio:
            if st.session_state.screenplay_data and not st.session_state.image_urls:
                # If we have a screenplay but no images, suggest image generation
                if st.button("Generate Images for Scenes", key="gen_images_after_audio"):
                    go_to_image_generator()
            else:
                # Otherwise proceed to video generation
                if st.button("Proceed to Video Generation", key="proceed_to_video"):
                    go_to_video_generator()
    
    # Preview area for the script
    st.markdown("---")
    st.markdown("<h3>Script Preview</h3>", unsafe_allow_html=True)
    
    # Display the appropriate script content
    script_content = st.session_state.script
    if st.session_state.screenplay_data:
        script_content = st.session_state.screenplay_data.get("final_script", script_content)
    
    with st.expander("View Script", expanded=False):
        st.markdown(script_content)

def render_image_generator():
    st.markdown("<h1 class='main-header'>Image Generator</h1>", unsafe_allow_html=True)
    
    if not st.session_state.screenplay_data:
        st.warning("You need a screenplay to generate scene images. Please create one first.")
        if st.button("Go to Screenplay Generator"):
            go_to_screenplay_generator()
        return
    
    screenplay_data = st.session_state.screenplay_data
    image_prompts = screenplay_data.get("image_prompts", [])
    
    if not image_prompts:
        st.error("No image prompts found in the screenplay data.")
        return
    
    st.markdown("<h3>Generate Scene Images</h3>", unsafe_allow_html=True)
    
    # Display the prompts for each scene
    for i, prompt in enumerate(image_prompts):
        st.markdown(f'<div class="card"><h4>Scene {i+1}</h4>{prompt}</div>', unsafe_allow_html=True)
    
    # Generate images button
    if st.button("Generate All Scene Images"):
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
                    filename = f"scene-{i+1:02d}-{uuid.uuid4()}.png"
                    
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
                    screenplay_data.get("title", "Generated Screenplay")
                )
                
                if link_error:
                    st.error(link_error)
                else:
                    st.session_state.image_urls = image_urls
                    st.session_state.link_data = link_data
                    status_text.empty()
                    st.success("All images generated and uploaded! Link created successfully.")
                    
                    # Show next steps
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Create Audio"):
                            go_to_audio_generator()
                    with col2:
                        if st.button("Proceed to Video Creation"):
                            go_to_video_generator()
            else:
                st.error("No images were successfully generated and uploaded. Please try again.")

def render_video_generator():
    st.markdown("<h1 class='main-header'>Video Generator</h1>", unsafe_allow_html=True)
    
    # Check if we have the necessary assets
    script_ready = st.session_state.script or (st.session_state.screenplay_data and st.session_state.screenplay_data.get("final_script"))
    
    if not script_ready:
        st.warning("You need a script or screenplay first. Please generate or upload one.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Script Generator"):
                go_to_script_generator()
        with col2:
            if st.button("Go to Screenplay Generator"):
                go_to_screenplay_generator()
        return
    
    # Get the script text
    script_text = st.session_state.script
    if st.session_state.screenplay_data:
        script_text = st.session_state.screenplay_data.get("final_script", script_text)
    
    # Display the script preview
    with st.expander("Script Preview", expanded=False):
        st.markdown(script_text)
    
    # Display the images if available
    if st.session_state.image_urls:
        st.subheader("Images for Your Video")
        cols = st.columns(min(len(st.session_state.image_urls), 3))
        for i, url in enumerate(st.session_state.image_urls):
            with cols[i % len(cols)]:
                st.image(url, caption=f"Scene {i+1}", use_column_width=True)
    elif st.session_state.screenplay_data and st.session_state.screenplay_data.get("image_prompts"):
        st.warning("You have scene prompts but no generated images. It's recommended to generate images first.")
        if st.button("Generate Images First"):
            go_to_image_generator()
    
    # Tabs for different video generation methods
    tabs = st.tabs(["Creatify (Avatar-based)", "Tavus (Real Person)"])
    
    with tabs[0]:  # Creatify video generation
        # Get available personas
        personas = get_personas()
        
        if personas:
            st.subheader("Select Avatar")
            
            # Display personas in a grid
            persona_cols = st.columns(3)
            
            for i, persona in enumerate(personas[:6]):  # Limit to first 6 personas
                with persona_cols[i % 3]:
                    persona_id = persona.get("id")
                    preview_img = persona.get("preview_image_1_1")
                    
                    # Check if this avatar is currently selected
                    is_selected = st.session_state.selected_avatar == persona_id
                    
                    if preview_img:
                        st.image(preview_img, width=150)
                    else:
                        st.markdown("*Preview not available*")
                    
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
                    
                    # Selection button
                    button_text = "Selected" if is_selected else "Select Avatar"
                    button_disabled = is_selected
                    
                    if st.button(button_text, key=f"select_avatar_{i}", disabled=button_disabled):
                        select_avatar(persona_id)
                        st.rerun()
            
            # Video settings
            st.subheader("Video Settings")
            
            col1, col2 = st.columns(2)
            with col1:
                platform = st.selectbox("Target Platform", ["Facebook", "Instagram", "YouTube", "TikTok", "LinkedIn"])
                language = st.selectbox("Language", ["en", "es", "fr", "de"])
                audience = st.text_input("Target Audience", "General")
            
            with col2:
                video_length = st.slider("Video Length (seconds)", 15, 60, 30)
                aspect_ratio = st.selectbox("Aspect Ratio", ["16x9", "1x1", "9x16"])
                caption_style = st.selectbox("Caption Style", ["normal-black", "normal-white", "highlight-yellow", "none"])
            
            # Select voice section
            st.subheader("Voice Settings")
            
            if st.session_state.selected_voice:
                st.success(f"Using voice: {st.session_state.selected_voice_name}")
                voice_volume = st.slider("Voice Volume", 0.0, 1.0, st.session_state.voice_volume if 'voice_volume' in st.session_state else 0.5, 0.1)
                st.session_state.voice_volume = voice_volume
            else:
                st.warning("No voice selected. Please select a voice in the Audio Generator section.")
                if st.button("Go to Audio Generator"):
                    go_to_audio_generator()
            
            # Create video button
            if st.button("Create Video", disabled=not st.session_state.selected_avatar or not st.session_state.link_data):
                if not st.session_state.link_data:
                    st.error("No images available. Please generate images first.")
                elif not st.session_state.selected_avatar:
                    st.error("Please select an avatar first.")
                else:
                    with st.spinner("Creating video..."):
                        link_id = st.session_state.link_data.get("id")
                        if not link_id:
                            link_id = st.session_state.link_data.get("link", {}).get("id")
                        
                        video_name = st.session_state.screenplay_data.get("title", "AI Generated Video") if st.session_state.screenplay_data else "AI Generated Video"
                        
                        video_data, video_error = create_video(
                            link_id,
                            video_name,
                            script_text,
                            st.session_state.selected_avatar,
                            platform=platform,
                            audience=audience,
                            language=language,
                            length=video_length,
                            ratio=aspect_ratio,
                            voice_id=st.session_state.selected_voice,
                            volume=st.session_state.voice_volume,
                            caption_style=caption_style
                        )
                        
                        if video_error:
                            st.error(video_error)
                        else:
                            st.session_state.video_data = video_data
                            st.success("Video creation initiated!")
                            if st.button("View Results"):
                                go_to_video_results()
                                st.rerun()
        else:
            st.error("No personas available. Please check your API connection.")
    
    with tabs[1]:  # Tavus video generation
        st.subheader("Tavus Video Creation")
        
        # Get Tavus replicas
        replicas = get_tavus_replicas()
        replica_names = [r.get("replica_name") for r in replicas] if replicas else []
        
        if not replicas:
            st.warning("No Tavus replicas available.")
        else:
            # Form for Tavus video settings
            with st.form("tavus_form"):
                # Select replica
                selected_replica = st.selectbox("Select a Replica", replica_names)
                
                # Video settings
                col1, col2 = st.columns(2)
                with col1:
                    video_name = st.text_input("Video Name", "AI Generated Video")
                    audio_url = st.text_input("Audio URL (.wav/.mp3)", "")
                
                with col2:
                    background_url = st.text_input("Background Video URL", "")
                
                # Submit button
                tavus_submitted = st.form_submit_button("Generate Video")
            
            # Handle form submission
            if tavus_submitted:
                with st.spinner("Generating video with Tavus..."):
                    status, stream_url = generate_tavus_video(
                        selected_replica,
                        video_name,
                        script_text,
                        audio_url,
                        background_url,
                        pd.DataFrame(replicas)
                    )
                    
                    if stream_url:
                        st.success(status)
                        st.video(stream_url)
                        # Store the URL in session state
                        video_data = {"status": "done", "video_output": stream_url}
                        st.session_state.video_data = video_data
                    else:
                        st.warning(status)

def render_video_results():
    st.markdown("<h1 class='main-header'>Video Results</h1>", unsafe_allow_html=True)
    
    if not st.session_state.video_data:
        st.error("No video data available. Please go back and create a video.")
        st.button("Go to Video Generator", on_click=go_to_video_generator)
        return
    
    # Get current status for Creatify videos
    video_data = st.session_state.video_data
    
    # Check if we're using Tavus (simplified data structure)
    if "video_output" in video_data and video_data.get("status") == "done":
        # Display Tavus video
        st.success("Your video is ready!")
        st.video(video_data["video_output"])
        st.markdown("---")
        
        # Show script for reference
        st.subheader("Script")
        script_text = st.session_state.script
        if st.session_state.screenplay_data:
            script_text = st.session_state.screenplay_data.get("final_script", script_text)
        
        st.markdown(f"""
        <div class="card">
            <p>{script_text}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Creatify video - check status and update
        video_id = video_data.get("id")
        status, status_error = get_video_status(video_id)
        
        if status_error:
            st.error(status_error)
        else:
            # Update session state
            st.session_state.video_data = status
            video_status = status
            
            # Display status card
            current_status = video_status.get("status", "unknown")
            progress = video_status.get("progress", 0)
            
            st.markdown(f"""
                <div class="card">
                    <h3>Video Status</h3>
                    <p><strong>Project:</strong> {video_status.get('name', 'Unnamed')}</p>
                    <p><strong>Status:</strong> {current_status}</p>
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
            if current_status == "pending" or current_status == "running":
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
                            <a href="{preview_url}" target="_blank">
                                <button>Open Preview</button>
                            </a>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Render button
                if st.button("Render Final Video"):
                    with st.spinner("Rendering video..."):
                        render_result, render_error = render_video(video_id)
                        
                        if render_error:
                            st.error(render_error)
                        else:
                            st.session_state.video_data = render_result
                            st.success("Rendering started!")
                            st.rerun()
            
            elif current_status == "done":
                st.success("Your video is ready!")
                
                # Display the video
                video_url = video_status.get("video_output")
                if video_url:
                    st.subheader("Your Video")
                    st.video(video_url)
                    
                    # Download button
                    st.download_button(
                        label="Download Video",
                        data=requests.get(video_url).content,
                        file_name=f"{video_status.get('name', 'video').replace(' ', '_')}.mp4",
                        mime="video/mp4"
                    )
                    
                    # Show script for reference
                    st.subheader("Script")
                    script_text = st.session_state.script
                    if st.session_state.screenplay_data:
                        script_text = st.session_state.screenplay_data.get("final_script", script_text)
                    
                    st.markdown(f"""
                        <div class="card">
                            <p>{script_text}</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Video URL not available. There might be an issue with the video.")
            
            elif current_status == "failed":
                st.error("Video creation failed.")
                failed_reason = video_status.get("failed_reason", "Unknown reason")
                st.write(f"Reason: {failed_reason}")
                
                # Option to try again
                if st.button("Try Again"):
                    go_to_video_generator()
                    st.rerun()

# Main app logic
def main():
    render_sidebar()
    
    if st.session_state.page == "home":
        render_home()
    elif st.session_state.page == "brief_generator":
        render_brief_generator()
    elif st.session_state.page == "script_generator":
        render_script_generator()
    elif st.session_state.page == "audio_generator":
        render_audio_generator()
    elif st.session_state.page == "video_generator":
        render_video_generator()
    elif st.session_state.page == "screenplay_generator":
        render_screenplay_generator()
    elif st.session_state.page == "image_generator":
        render_image_generator()
    elif st.session_state.page == "video_results":
        render_video_results()

if __name__ == "__main__":
    main(),
