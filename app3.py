import streamlit as st
import pandas as pd
import requests
import time
import os
import re
import json
import uuid
import datetime
import hashlib
from io import BytesIO
from PIL import Image
from elevenlabs import ElevenLabs

# Set page configuration
st.set_page_config(
    page_title="AdGen AI Platform",
    page_icon="🎬",
    layout="wide"
)

# Directory for storing user data and sessions
DATA_DIR = "user_data"
SESSION_DIR = os.path.join(DATA_DIR, "sessions")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

# Initialize session state variables if they don't exist
if 'script' not in st.session_state:
    st.session_state.script = ""
if 'cleaned_summary' not in st.session_state:
    st.session_state.cleaned_summary = ""
if 'step' not in st.session_state:
    st.session_state.step = "start"
if 'replicas_df' not in st.session_state:
    st.session_state.replicas_df = None
if 'selected_replica' not in st.session_state:
    st.session_state.selected_replica = None
if 'selected_voice_id' not in st.session_state:
    st.session_state.selected_voice_id = None
if 'selected_voice_name' not in st.session_state:
    st.session_state.selected_voice_name = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'sessions' not in st.session_state:
    st.session_state.sessions = []

# API Keys (in a real app, these should be secured properly)
serper_api_key = st.secrets["SERPER_API_KEY"] if "SERPER_API_KEY" in st.secrets else "14b865cf1dae8d1149dea6a7d2c93f8ac0105970"
openai_api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else "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"
groq_api_key = st.secrets["GROQ_API_KEY"] if "GROQ_API_KEY" in st.secrets else "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"
tavus_api_key = st.secrets["TAVUS_API_KEY"] if "TAVUS_API_KEY" in st.secrets else "d57e6c687a894213aa87abad7c1c5f56"
gemini_api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "AIzaSyBLzfjImenFp60acvXgKygaEDKGqKfHyKI"
elevenlabs_api_key = st.secrets["ELEVENLABS_API_KEY"] if "ELEVENLABS_API_KEY" in st.secrets else "sk_457392759b066ebb9b695f4f7f3b85d177d04350c85e494a"

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)

# Set environment variables for API keys
os.environ["SERPER_API_KEY"] = serper_api_key
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["GROQ_API_KEY"] = groq_api_key

# Default script for demonstration
default_script = (
    "Hey there... Are you feeling overwhelmed by credit card debt? I was too... until I found something that changed everything. "
    "I used to dread every bill that came in... It felt like a never-ending cycle of stress. "
    "But then I discovered this debt relief program that helped consolidate my payments into one simple monthly fee. "
    "The best part? It barely impacted my credit score! I finally started to breathe again, knowing there was a way out. "
    "If you're ready to take that first step towards relief, check it out now! You deserve to feel free from debt..."
)

# --------------------------
# User and Session Management
# --------------------------

def generate_user_id(username, email):
    """Generate a unique user ID based on username and email"""
    combined = f"{username.lower()}:{email.lower()}"
    return hashlib.md5(combined.encode()).hexdigest()

def get_user_data_path(user_id):
    """Get the path to the user's data file"""
    return os.path.join(DATA_DIR, f"user_{user_id}.json")

def get_session_path(session_id):
    """Get the path to a session file"""
    return os.path.join(SESSION_DIR, f"session_{session_id}.json")

def save_user_data(user_id, user_data):
    """Save user data to file"""
    file_path = get_user_data_path(user_id)
    with open(file_path, 'w') as f:
        json.dump(user_data, f, indent=2)

def load_user_data(user_id):
    """Load user data from file"""
    file_path = get_user_data_path(user_id)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {"user_id": user_id, "sessions": []}

def save_session(session_data):
    """Save session data to file"""
    session_id = session_data["session_id"]
    file_path = get_session_path(session_id)
    with open(file_path, 'w') as f:
        json.dump(session_data, f, indent=2)

def load_session(session_id):
    """Load session data from file"""
    file_path = get_session_path(session_id)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def create_new_session(name="New Campaign"):
    """Create a new session with a unique ID"""
    session_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    session_data = {
        "session_id": session_id,
        "name": name,
        "created_at": timestamp,
        "updated_at": timestamp,
        "campaign_brief": "",
        "script": "",
        "selected_tools": [],
        "generated_content": {}
    }
    
    save_session(session_data)
    
    # Update user's session list
    if st.session_state.user_id:
        user_data = load_user_data(st.session_state.user_id)
        user_data["sessions"].append({
            "session_id": session_id,
            "name": name,
            "created_at": timestamp
        })
        save_user_data(st.session_state.user_id, user_data)
    
    return session_id

def update_session(session_data):
    """Update an existing session"""
    session_data["updated_at"] = datetime.datetime.now().isoformat()
    save_session(session_data)
    
    # Update the session name in the user's session list if it changed
    if st.session_state.user_id:
        user_data = load_user_data(st.session_state.user_id)
        for session in user_data["sessions"]:
            if session["session_id"] == session_data["session_id"]:
                session["name"] = session_data["name"]
                break
        save_user_data(st.session_state.user_id, user_data)

def load_current_session():
    """Load the current session data"""
    if st.session_state.current_session_id:
        return load_session(st.session_state.current_session_id)
    return None

def save_current_session_state():
    """Save the current app state to the session"""
    if not st.session_state.current_session_id:
        return
    
    session_data = load_current_session()
    if not session_data:
        return
    
    # Update session data with current app state
    session_data["script"] = st.session_state.script
    session_data["campaign_brief"] = st.session_state.cleaned_summary
    
    # Add selected tools and content to the session
    if hasattr(st.session_state, 'selected_replica') and st.session_state.selected_replica:
        session_data["generated_content"]["selected_replica"] = st.session_state.selected_replica
    
    if hasattr(st.session_state, 'selected_voice_id') and st.session_state.selected_voice_id:
        session_data["generated_content"]["selected_voice"] = {
            "id": st.session_state.selected_voice_id,
            "name": st.session_state.selected_voice_name
        }
    
    if hasattr(st.session_state, 'image_prompts') and st.session_state.image_prompts:
        session_data["generated_content"]["image_prompts"] = st.session_state.image_prompts
    
    update_session(session_data)

def load_session_state(session_id):
    """Load a session into the app state"""
    session_data = load_session(session_id)
    if not session_data:
        st.error(f"Session {session_id} not found")
        return False
    
    # Update app state with session data
    st.session_state.current_session_id = session_id
    st.session_state.script = session_data.get("script", "")
    st.session_state.cleaned_summary = session_data.get("campaign_brief", "")
    
    # Load generated content if available
    generated_content = session_data.get("generated_content", {})
    
    if "selected_replica" in generated_content:
        st.session_state.selected_replica = generated_content["selected_replica"]
    
    if "selected_voice" in generated_content:
        st.session_state.selected_voice_id = generated_content["selected_voice"]["id"]
        st.session_state.selected_voice_name = generated_content["selected_voice"]["name"]
    
    if "image_prompts" in generated_content:
        st.session_state.image_prompts = generated_content["image_prompts"]
    
    return True

def delete_session(session_id):
    """Delete a session"""
    # Remove from user's session list
    if st.session_state.user_id:
        user_data = load_user_data(st.session_state.user_id)
        user_data["sessions"] = [s for s in user_data["sessions"] if s["session_id"] != session_id]
        save_user_data(st.session_state.user_id, user_data)
    
    # Delete the session file
    file_path = get_session_path(session_id)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Reset current session if it was the deleted one
    if st.session_state.current_session_id == session_id:
        st.session_state.current_session_id = None
        st.session_state.script = ""
        st.session_state.cleaned_summary = ""
        # Reset other session-specific state variables
        if 'selected_replica' in st.session_state:
            st.session_state.selected_replica = None
        if 'selected_voice_id' in st.session_state:
            st.session_state.selected_voice_id = None
        if 'selected_voice_name' in st.session_state:
            st.session_state.selected_voice_name = None
        if 'image_prompts' in st.session_state:
            st.session_state.image_prompts = None

# --------------------------
# Authentication Functions
# --------------------------

def render_login_page():
    """Render the login page"""
    st.title("🎬 AdGen AI Platform")
    st.subheader("Login or Create Account")
    
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if email and password:  # In a real app, verify credentials
                    # Generate user ID - in a real app, you would verify password
                    user_id = generate_user_id(email, email)
                    st.session_state.user_id = user_id
                    
                    # Load user data
                    user_data = load_user_data(user_id)
                    st.session_state.sessions = user_data.get("sessions", [])
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Please enter both email and password")
    
    with tab2:
        with st.form("signup_form"):
            st.subheader("Create Account")
            username = st.text_input("Username")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                if username and email and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        # Generate user ID
                        user_id = generate_user_id(username, email)
                        
                        # Create user data file
                        user_data = {
                            "user_id": user_id,
                            "username": username,
                            "email": email,
                            # In a real app, you would hash the password
                            "sessions": []
                        }
                        save_user_data(user_id, user_data)
                        
                        # Set session state
                        st.session_state.user_id = user_id
                        st.session_state.sessions = []
                        
                        st.success("Account created successfully!")
                        st.rerun()
                else:
                    st.error("Please fill out all fields")

def render_user_dashboard():
    """Render the user dashboard with session management"""
    st.title("🎬 AdGen AI Platform")
    st.subheader("My Campaigns")
    
    # Add a sidebar for user info and session actions
    with st.sidebar:
        st.header("Account")
        user_data = load_user_data(st.session_state.user_id)
        st.write(f"Logged in as: {user_data.get('username', 'User')}")
        
        if st.button("Logout"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        st.header("Actions")
        campaign_name = st.text_input("New Campaign Name", "My Campaign")
        if st.button("Create New Campaign"):
            session_id = create_new_session(campaign_name)
            st.session_state.current_session_id = session_id
            st.session_state.step = "briefer"  # Start with the briefer
            st.rerun()
    
    # Display user's sessions
    if not st.session_state.sessions:
        st.info("You don't have any campaigns yet. Create one to get started!")
    else:
        for i in range(0, len(st.session_state.sessions), 3):
            cols = st.columns(3)
            for j in range(3):
                if i+j < len(st.session_state.sessions):
                    session = st.session_state.sessions[i+j]
                    with cols[j]:
                        st.markdown(f"### {session['name']}")
                        
                        # Get creation date and format it
                        created_at = datetime.datetime.fromisoformat(session['created_at']).strftime("%Y-%m-%d %H:%M")
                        st.write(f"Created: {created_at}")
                        
                        # Load session to get more details
                        session_data = load_session(session['session_id'])
                        if session_data:
                            has_brief = bool(session_data.get("campaign_brief"))
                            has_script = bool(session_data.get("script"))
                            has_video = "video" in session_data.get("generated_content", {})
                            
                            # Display progress indicators
                            progress_items = []
                            if has_brief:
                                progress_items.append("✅ Brief")
                            else:
                                progress_items.append("❌ Brief")
                                
                            if has_script:
                                progress_items.append("✅ Script")
                            else:
                                progress_items.append("❌ Script")
                                
                            if has_video:
                                progress_items.append("✅ Video")
                            else:
                                progress_items.append("❌ Video")
                                
                            st.write(" | ".join(progress_items))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Open", key=f"open_{session['session_id']}"):
                                if load_session_state(session['session_id']):
                                    if has_script:
                                        st.session_state.step = "edit_script"
                                    else:
                                        st.session_state.step = "briefer"
                                    st.rerun()
                        with col2:
                            if st.button("Delete", key=f"delete_{session['session_id']}"):
                                delete_session(session['session_id'])
                                # Refresh session list
                                user_data = load_user_data(st.session_state.user_id)
                                st.session_state.sessions = user_data.get("sessions", [])
                                st.rerun()

# --------------------------
# Helper functions
# --------------------------

def clean_summary(text):
    lines = text.strip().split('\n')
    cleaned = ["Cleaned Campaign Summary:\n"]
    for line in lines:
        line = line.strip()
        # Skip unwanted lines
        if not line or line.startswith("✅") or line == "=" or "To be determined" in line or line == "END OF CHAT":
            continue
        cleaned.append(line)
    return "\n".join(cleaned)

def get_replicas():
    url = "https://tavusapi.com/v2/replicas"
    headers = {"x-api-key": tavus_api_key}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            df = pd.json_normalize(data['data'])
            df_selected = df[['thumbnail_video_url', 'model_name', 'replica_id', 'replica_name']]
            return df_selected
        else:
            st.error(f"Error fetching replicas: {response.status_code} - {response.text}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Exception while fetching replicas: {e}")
        return pd.DataFrame()

def get_elevenlabs_voices():
    try:
        response = elevenlabs_client.voices.search(include_total_count=True, page_size=100)
        return response.voices
    except Exception as e:
        st.error(f"Error fetching ElevenLabs voices: {e}")
        return []

def generate_and_fetch_video(replica_id, video_name, script_text, audio_url=None, background_url=None):
    url = "https://tavusapi.com/v2/videos"
    headers = {
        "x-api-key": tavus_api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "replica_id": replica_id,
        "script": script_text,
        "video_name": video_name
    }
    
    if audio_url:
        payload["audio_url"] = audio_url
    if background_url:
        payload["background_url"] = background_url

    try:
        with st.spinner("Creating video..."):
            creation_response = requests.post(url, json=payload, headers=headers)

        if creation_response.status_code != 200:
            return f"❌ Error creating video: {creation_response.status_code} - {creation_response.text}", None

        video_id = creation_response.json().get("video_id")
        if not video_id:
            return "❌ No video ID returned by Tavus.", None

        # Save video ID to session
        session_data = load_current_session()
        if session_data:
            if "generated_content" not in session_data:
                session_data["generated_content"] = {}
            
            session_data["generated_content"]["video"] = {
                "video_id": video_id,
                "video_name": video_name,
                "created_at": datetime.datetime.now().isoformat()
            }
            update_session(session_data)

        # Polling until status is 'ready'
        status_url = f"https://tavusapi.com/v2/videos/{video_id}"
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(20):  # Up to ~60 seconds
            progress_bar.progress((i+1)/20)
            status_text.text(f"Checking video status ({i+1}/20)...")
            
            time.sleep(3)
            status_response = requests.get(status_url, headers=headers)
            status_data = status_response.json()
            
            if status_data.get("status") == "ready":
                progress_bar.progress(1.0)
                stream_url = status_data.get("stream_url")
                
                # Update session with stream URL
                session_data = load_current_session()
                if session_data and "generated_content" in session_data and "video" in session_data["generated_content"]:
                    session_data["generated_content"]["video"]["stream_url"] = stream_url
                    update_session(session_data)
                
                return f"✅ Video is ready! Video ID: {video_id}", stream_url

        return "⏳ Video is still processing. Please check back later.", None
        
    except Exception as e:
        return f"❌ Exception during video generation: {str(e)}", None

# Mock function for audio generation with ElevenLabs
def generate_audio_with_elevenlabs(voice_id, text, speed=1.0, stability=0.5):
    # In a real implementation, this would call the ElevenLabs API
    # For now, we'll simulate the process with a delay
    
    st.info(f"Generating audio with ElevenLabs... (Voice ID: {voice_id})")
    progress_bar = st.progress(0)
    
    # Simulate the API call with delay
    for i in range(5):
        progress_bar.progress((i+1)/5)
        time.sleep(1)  # Simulate work being done
    
    # Save to session
    session_data = load_current_session()
    if session_data:
        if "generated_content" not in session_data:
            session_data["generated_content"] = {}
        
        session_data["generated_content"]["audio"] = {
            "voice_id": voice_id,
            "speed": speed,
            "stability": stability,
            "created_at": datetime.datetime.now().isoformat()
        }
        update_session(session_data)
    
    # Placeholder for actual API response
    # In a real implementation, this would return the URL or bytes of the generated audio
    return "https://via.placeholder.com/300x50.mp3?text=Generated+Audio"

# Mock function for CrewAI script generation
def generate_script_with_crewai(campaign_summary):
    # In a real implementation, this would call your CrewAI workflow
    # For now, we'll simulate the process with a delay and return the default script
    
    st.info("Generating script with CrewAI... (This may take a few minutes)")
    progress_bar = st.progress(0)
    
    # Simulate the CrewAI process with delay
    for i in range(10):
        progress_bar.progress((i+1)/10)
        time.sleep(1)  # Simulate work being done
    
    # In the real implementation, this would be the actual result from CrewAI
    script_result = {
        "hook": "Hey there... Are you feeling overwhelmed by credit card debt? I was too... until I found something that changed everything.",
        "body": "I used to dread every bill that came in... It felt like a never-ending cycle of stress. But then I discovered this debt relief program that helped consolidate my payments into one simple monthly fee. The best part? It barely impacted my credit score!",
        "cta": "If you're ready to take that first step towards relief, check it out now! You deserve to feel free from debt...",
        "final_script": default_script
    }
    
    # Save to session
    session_data = load_current_session()
    if session_data:
        session_data["script"] = script_result["final_script"]
        session_data["generated_content"]["script_parts"] = {
            "hook": script_result["hook"],
            "body": script_result["body"],
            "cta": script_result["cta"]
        }
        update_session(session_data)
    
    return script_result

# --------------------------
# UI Components
# --------------------------

def render_start_page():
    st.title("🎬 AdGen AI Platform")
    st.subheader("Create compelling ad campaigns with AI")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Do you already have a script?")
        if st.button("Yes, I have a script", use_container_width=True):
            st.session_state.step = "edit_script"
            st.rerun()
    
    with col2:
        st.markdown("### Need to create a new script?")
        if st.button("No, help me create one", use_container_width=True):
            st.session_state.step = "briefer"
            st.rerun()

def render_session_navigation():
    """Render session navigation and save button in the sidebar"""
    with st.sidebar:
        st.header("Current Campaign")
        
        # Display current session info if available
        if st.session_state.current_session_id:
            session_data = load_current_session()
            if session_data:
                st.write(f"Name: {session_data['name']}")
                
                # Allow renaming the session
                new_name = st.text_input("Rename Campaign", session_data['name'])
                if new_name != session_data['name']:
                    session_data['name'] = new_name
                    update_session(session_data)
                    
                    # Update in user's session list too
                    user_data = load_user_data(st.session_state.user_id)
                    for session in user_data.get("sessions", []):
                        if session["session_id"] == st.session_state.current_session_id:
                            session["name"] = new_name
                            break
                    save_user_data(st.session_state.user_id, user_data)
                
                # Created at
                created_at = datetime.datetime.fromisoformat(session_data['created_at']).strftime("%Y-%m-%d %H:%M")
                st.write(f"Created: {created_at}")
                
                # Last updated
                updated_at = datetime.datetime.fromisoformat(session_data['updated_at']).strftime("%Y-%m-%d %H:%M")
                st.write(f"Last updated: {updated_at}")
                
                # Save button (automatically saves on each update, but provide manual option)
                if st.button("Save Campaign"):
                    save_current_session_state()
                    st.success("Campaign saved successfully!")
                
                st.markdown("---")
        
        # Navigation buttons
        st.header("Navigation")
        if st.button("Go to Dashboard"):
            save_current_session_state()  # Save before navigating away
            st.session_state.step = "dashboard"
            st.rerun()
        
        if st.session_state.step != "briefer" and st.button("Campaign Brief"):
            save_current_session_state()
            st.session_state.step = "briefer"
            st.rerun()
        
        if st.session_state.step != "edit_script" and st.button("Script Editor"):
            save_current_session_state()
            st.session_state.step = "edit_script"
            st.rerun()
        
        if st.session_state.step != "audio_generation" and st.button("Audio Generation"):
            save_current_session_state()
            st.session_state.step = "audio_generation"
            st.rerun()
        
        if st.session_state.step != "video_generation" and st.button("Video Generation"):
            save_current_session_state()
            st.session_state.step = "video_generation"
            st.rerun()
        
        if st.session_state.step != "image_generation" and st.button("Image Generation"):
            save_current_session_state()
            st.session_state.step = "image_generation"
            st.rerun()

def render_briefer_page():
    st.title("🧠 Campaign Briefer")
    st.subheader("Let's gather information about your campaign")
    
    # Add session navigation
    render_session_navigation()
    
    st.info("Chat with our AI assistant to create your campaign brief. The assistant will ask you questions about your campaign goals, target audience, and more.")
    
    # Simulate a conversation with the AI
    with st.form("briefer_form"):
        st.markdown("### Tell us about your campaign")
        campaign_goal = st.text_area("What is the goal of your campaign?", height=100)
        target_audience = st.text_area("Who is your target audience?", height=100)
        product_name = st.text_input("What is your product or service name?")
        key_benefits = st.text_area("What are the key benefits of your product/service?", height=100)
        preferred_style = st.selectbox("What style of ad do you prefer?", 
                                     ["Conversational", "Testimonial", "Educational", "Humorous", "Emotional"])
        
        submit_button = st.form_submit_button("Generate Campaign Brief")
        
        if submit_button:
            if not campaign_goal or not target_audience or not product_name or not key_benefits:
                st.error("Please fill out all fields")
            else:
                # Construct a summary from the form inputs
                summary = f"""
                Campaign Goal: {campaign_goal}
                Target Audience: {target_audience}
                Product/Service: {product_name}
                Key Benefits: {key_benefits}
                Preferred Style: {preferred_style}
                """
                
                st.session_state.cleaned_summary = clean_summary(summary)
                
                # Save to current session
                if st.session_state.current_session_id:
                    session_data = load_current_session()
                    if session_data:
                        session_data["campaign_brief"] = st.session_state.cleaned_summary
                        session_data["generated_content"]["brief_details"] = {
                            "campaign_goal": campaign_goal,
                            "target_audience": target_audience,
                            "product_name": product_name,
                            "key_benefits": key_benefits,
                            "preferred_style": preferred_style
                        }
                        update_session(session_data)
                
                st.session_state.step = "generate_script"
                st.rerun()
