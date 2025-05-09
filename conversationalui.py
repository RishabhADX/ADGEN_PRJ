import streamlit as st
import json
import re
import os
import hashlib
import uuid
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from collections import Counter
import base64
from elevenlabs import ElevenLabs, VoiceSettings
from pathlib import Path
import time

# Set page configuration
st.set_page_config(
    page_title="VoiceGen | ElevenLabs Voice Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .voice-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .voice-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .voice-name {
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 5px;
    }
    .voice-description {
        color: #555;
        font-size: 14px;
        margin-bottom: 10px;
    }
    .custom-header {
        color: #1D3557;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .custom-subheader {
        color: #457B9D;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .highlight-text {
        background-color: #F1FAEE;
        padding: 2px 5px;
        border-radius: 3px;
    }
    .audio-player {
        width: 100%;
        border-radius: 8px;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
    .stTextArea>div>div>textarea {
        border-radius: 8px;
    }
    .sidebar .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #1D3557;
        color: white;
    }
    .sidebar .stButton>button:hover {
        background-color: #2A4A6B;
    }
    .user-info {
        background-color: #E9F2FF;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .stProgress > div > div > div {
        background-color: #457B9D;
    }
    .rating-button {
        background-color: #f0f0f0;
        border: 1px solid #ddd;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin: 0 5px;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .rating-button:hover, .rating-button.selected {
        background-color: #457B9D;
        color: white;
    }
    .voice-filter {
        display: inline-block;
        background-color: #f0f0f0;
        border-radius: 15px;
        padding: 5px 10px;
        margin: 5px;
        cursor: pointer;
    }
    .voice-filter.active {
        background-color: #457B9D;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Define directories
@st.cache_resource
def ensure_directories():
    directories = ["users", "sessions", "user_data", "output_audio"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

ensure_directories()

# Initialize ElevenLabs client
def get_elevenlabs_client():
    # Try to get API key from session state or environment variable
    api_key = st.session_state.get("elevenlabs_api_key", os.getenv("ELEVENLABS_API_KEY", ""))
    
    if not api_key:
        return None
    
    return ElevenLabs(api_key=api_key)

# Helper class for user management
class UserManager:
    def __init__(self):
        self.users_dir = "users"
        self.sessions_dir = "sessions"
        
    def user_exists(self, username):
        """Check if a user exists"""
        return os.path.exists(f"{self.users_dir}/{username}.json")
    
    def create_user(self, username, password):
        """Create a new user"""
        if self.user_exists(username):
            return False, "User already exists"
        
        # Hash the password
        salt = os.urandom(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt, 
            100000
        )
        
        # Store user data
        user_data = {
            "username": username,
            "salt": salt.hex(),
            "password_hash": password_hash.hex(),
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        with open(f"{self.users_dir}/{username}.json", 'w') as f:
            json.dump(user_data, f)
        
        return True, "User created successfully"
    
    def verify_password(self, username, password):
        """Verify a user's password"""
        if not self.user_exists(username):
            return False
        
        # Load user data
        with open(f"{self.users_dir}/{username}.json", 'r') as f:
            user_data = json.load(f)
        
        # Verify password
        salt = bytes.fromhex(user_data["salt"])
        stored_password_hash = bytes.fromhex(user_data["password_hash"])
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt, 
            100000
        )
        
        return password_hash == stored_password_hash
    
    def login(self, username, password):
        """Log in a user"""
        if not self.verify_password(username, password):
            return False, "Invalid username or password"
        
        # Update last login time
        with open(f"{self.users_dir}/{username}.json", 'r') as f:
            user_data = json.load(f)
        
        user_data["last_login"] = datetime.now().isoformat()
        
        with open(f"{self.users_dir}/{username}.json", 'w') as f:
            json.dump(user_data, f)
        
        # Create a new session
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "username": username,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        with open(f"{self.sessions_dir}/{session_id}.json", 'w') as f:
            json.dump(session_data, f)
        
        return True, session_id

# User Learning System
class UserLearningSystem:
    def __init__(self, user_id="default_user"):
        self.user_id = user_id
        self.data_dir = "user_data"
        self.data_file = f"{self.data_dir}/{user_id}_preferences.json"
        
        # Default structure for preferences
        self.preferences = {
            "favorite_voices": [],      # List of voice_ids
            "voice_ratings": {},        # voice_id -> rating (1-5)
            "script_history": [],       # List of successful scripts
            "voice_traits": {},         # Traits -> count (accent, age, gender, etc.)
            "last_session": None,       # Timestamp
            "total_generations": 0      # Count of generations
        }
        
        # Default structure for conversation learning
        self.conversation_learning = {
            "effective_questions": {},  # Questions that led to progress
            "question_responses": {},   # How users respond to different questions
            "conversation_flows": [],   # Successful conversation paths
            "user_response_patterns": {}, # How user typically responds
            "topic_preferences": {},    # Topics user engages with most
            "engagement_metrics": {     # Metrics on user engagement
                "avg_response_length": 0,
                "avg_session_length": 0,
                "total_sessions": 0,
                "total_messages": 0
            }
        }
        
        # Load existing data if available
        self.load_data()
    
    def load_data(self):
        """Load all user data"""
        try:
            with open(self.data_file, 'r') as f:
                loaded_data = json.load(f)
                # Load preferences
                if "preferences" in loaded_data:
                    self.preferences.update(loaded_data["preferences"])
                # Load conversation learning
                if "conversation_learning" in loaded_data:
                    self.conversation_learning.update(loaded_data["conversation_learning"])
        except FileNotFoundError:
            # No previous data, using defaults
            pass
    
    def save_data(self):
        """Save all user data"""
        # Update last session timestamp
        self.preferences["last_session"] = datetime.now().isoformat()
        
        # Prepare complete data structure
        complete_data = {
            "preferences": self.preferences,
            "conversation_learning": self.conversation_learning
        }
        
        with open(self.data_file, 'w') as f:
            json.dump(complete_data, f, indent=2)
    
    def record_voice_selection(self, voice_id, voice_data):
        """Record that a user selected a particular voice"""
        # Add to favorite voices if not already there
        if voice_id not in self.preferences["favorite_voices"]:
            self.preferences["favorite_voices"].append(voice_id)
        
        # Track voice traits
        if "labels" in voice_data:
            for trait_type, trait_value in voice_data["labels"].items():
                if trait_value:
                    # Clean and normalize the trait value
                    trait_value = self.clean_label_value(trait_value)
                    trait_key = f"{trait_type}:{trait_value}"
                    
                    # Increment the trait counter
                    self.preferences["voice_traits"][trait_key] = self.preferences["voice_traits"].get(trait_key, 0) + 1
        
        # Save the updated data
        self.save_data()
    
    def record_script_generation(self, voice_id, script, success=True):
        """Record a script generation event"""
        # Increment total generations
        self.preferences["total_generations"] += 1
        
        # Store successful scripts for learning
        if success:
            # Store compact history entry
            history_entry = {
                "voice_id": voice_id,
                "script_length": len(script),
                "timestamp": datetime.now().isoformat(),
                "script_sample": script[:100] + "..." if len(script) > 100 else script
            }
            self.preferences["script_history"].append(history_entry)
        
        # Save the updated data
        self.save_data()
    
    def record_rating(self, voice_id, rating):
        """Record a user's rating of a voice (1-5)"""
        if 1 <= rating <= 5:
            self.preferences["voice_ratings"][voice_id] = rating
            self.save_data()
            return True
        return False
    
    def get_preferred_voices(self, limit=5):
        """Get the user's preferred voices based on history"""
        # Combine favorite voices and highly rated voices
        preferred_voice_ids = []
        
        # First add voices with high ratings (4-5)
        for voice_id, rating in self.preferences["voice_ratings"].items():
            if rating >= 4:
                preferred_voice_ids.append(voice_id)
        
        # Then add favorites not already included
        for voice_id in self.preferences["favorite_voices"]:
            if voice_id not in preferred_voice_ids:
                preferred_voice_ids.append(voice_id)
        
        # Return up to the limit
        return preferred_voice_ids[:limit]
    
    def get_preferred_traits(self, limit=3):
        """Get the user's preferred voice traits"""
        # Sort traits by count
        sorted_traits = sorted(
            self.preferences["voice_traits"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return the top traits
        return [trait_key for trait_key, _ in sorted_traits[:limit]]
    
    def clean_label_value(self, value):
        if not value:
            return ""
        # Replace underscores with hyphens
        value = value.replace("_", "-")
        return value

# Voice-related functions
def list_elevenlabs_voices(client, page_size=100, max_pages=10):
    voices_info = []
    next_page_token = ""

    for page_num in range(max_pages):
        try:
            response = client.voices.search(
                page_size=page_size,
                include_total_count=True,
                next_page_token=next_page_token
            )

            for voice in response.voices:
                voice_data = {
                    "name": voice.name,
                    "voice_id": voice.voice_id,
                    "language": voice.fine_tuning.language if hasattr(voice.fine_tuning, "language") else "Unknown",
                    "category": voice.category,
                    "preview_url": voice.preview_url,
                    "labels": voice.labels
                }
                voices_info.append(voice_data)

            next_page_token = response.next_page_token
            if not next_page_token:
                break
        except Exception as e:
            st.error(f"Error fetching voices: {str(e)}")
            break

    return voices_info

def get_audio_bytes_url(url):
    """Convert an audio URL to a base64 string for embedding"""
    import requests
    try:
        response = requests.get(url)
        audio_bytes = response.content
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        return f"data:audio/mpeg;base64,{audio_base64}"
    except Exception as e:
        st.error(f"Error fetching audio: {str(e)}")
        return None

def generate_elevenlabs_audio(client, voice_id, text, voice_settings=None):
    applied_settings = None
    if voice_settings:
        applied_settings = VoiceSettings(
            stability=voice_settings.get("stability", 0.5),
            similarity_boost=voice_settings.get("similarity_boost", 0.5),
            style=voice_settings.get("style", 0.0),
            use_speaker_boost=voice_settings.get("use_speaker_boost", False),
            speed=voice_settings.get("speed", 1.0)
        )

    try:
        # Show a progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Generating audio...")
        progress_bar.progress(30)
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = f"output_audio/output_{timestamp}.mp3"
        
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=applied_settings
        )
        
        progress_bar.progress(70)
        status_text.text("Processing audio...")
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        
        progress_bar.progress(100)
        status_text.text("Audio generated successfully!")
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()

        return {"status": "success", "file": output_file, "text_length": len(text)}
    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")
        return {"status": "error", "message": str(e)}

def get_audio_data_url(file_path):
    with open(file_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    return f"data:audio/mpeg;base64,{audio_base64}"

def get_voice_trait(voice_data, trait_name, default="Unknown"):
    """Extract a specific trait from voice labels"""
    if not voice_data or "labels" not in voice_data:
        return default
    
    labels = voice_data.get("labels", {})
    value = labels.get(trait_name, default)
    
    if not value:
        return default
        
    # Clean up formatting
    value = value.replace("_", " ").title()
    
    return value

def create_voice_card(voice, index, user_learning):
    """Create a styled card for a voice"""
    # Get preferred voices
    preferred_voice_ids = user_learning.get_preferred_voices() if user_learning else []
    
    # Check if this voice is preferred
    is_preferred = voice["voice_id"] in preferred_voice_ids
    
    # Get rating if available
    rating = user_learning.preferences["voice_ratings"].get(voice["voice_id"], None) if user_learning else None
    
    # Extract label information
    accent = get_voice_trait(voice, "accent")
    age = get_voice_trait(voice, "age") 
    gender = get_voice_trait(voice, "gender")
    use_case = get_voice_trait(voice, "use_case")
    
    # Get audio preview URL
    preview_url = voice.get("preview_url", "")
    
    # Create card column
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div class="voice-card" {'style="border-left: 4px solid #4CAF50;"' if is_preferred else ''}>
            <div class="voice-name">{'⭐ ' if is_preferred else ''}{index}. {voice["name"]}</div>
            <div class="voice-description">
                {gender} • {age} • {accent} • {use_case}
                {f'<br><small>Your rating: {"⭐" * rating}</small>' if rating else ''}
            </div>
        """, unsafe_allow_html=True)
        
        # Add audio player if preview available
        if preview_url:
            preview_data_url = get_audio_bytes_url(preview_url)
            if preview_data_url:
                st.markdown(f"""
                <audio class="audio-player" controls>
                    <source src="{preview_data_url}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Add select button
        if st.button(f"Select", key=f"select_{voice['voice_id']}"):
            return voice["voice_id"]
    
    return None

# Authentication functions
def login_form():
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if not username or not password:
                st.error("Please enter both username and password")
                return None
                
            user_manager = UserManager()
            success, session_id = user_manager.login(username, password)
            
            if success:
                return username, session_id
            else:
                st.error("Invalid username or password")
                return None
        return None

def signup_form():
    with st.form("signup_form"):
        username = st.text_input("Choose a username")
        password = st.text_input("Choose a password", type="password")
        confirm_password = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create Account")
        
        if submitted:
            if not username or not password:
                st.error("Please enter both username and password")
                return None
                
            if password != confirm_password:
                st.error("Passwords don't match")
                return None
                
            user_manager = UserManager()
            success, message = user_manager.create_user(username, password)
            
            if success:
                st.success(message)
                success, session_id = user_manager.login(username, password)
                if success:
                    return username, session_id
            else:
                st.error(message)
                return None
        return None

def guest_login():
    guest_id = f"guest_{uuid.uuid4().hex[:8]}"
    return guest_id, None

def init_session_state():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "username" not in st.session_state:
        st.session_state.username = None
        
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
        
    if "api_key_provided" not in st.session_state:
        st.session_state.api_key_provided = False
        
    if "elevenlabs_api_key" not in st.session_state:
        st.session_state.elevenlabs_api_key = ""
        
    if "elevenlabs_client" not in st.session_state:
        st.session_state.elevenlabs_client = None
        
    if "voices" not in st.session_state:
        st.session_state.voices = []
        
    if "selected_voice_id" not in st.session_state:
        st.session_state.selected_voice_id = None
        
    if "selected_voice_data" not in st.session_state:
        st.session_state.selected_voice_data = None
        
    if "script" not in st.session_state:
        st.session_state.script = ""
        
    if "generated_audio" not in st.session_state:
        st.session_state.generated_audio = None
        
    if "voice_settings" not in st.session_state:
        st.session_state.voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True,
            "speed": 1.0
        }
        
    if "user_learning" not in st.session_state:
        st.session_state.user_learning = None
        
    if "voice_filters" not in st.session_state:
        st.session_state.voice_filters = {
            "accents": [],
            "ages": [],
            "genders": []
        }
        
    if "applied_filters" not in st.session_state:
        st.session_state.applied_filters = {
            "accent": None,
            "age": None,
            "gender": None
        }
        
    if "history" not in st.session_state:
        st.session_state.history = []
        
    if "show_advanced" not in st.session_state:
        st.session_state.show_advanced = False

# Callback functions
def set_api_key():
    api_key = st.session_state.api_key_input
    if api_key:
        st.session_state.elevenlabs_api_key = api_key
        st.session_state.api_key_provided = True
        try:
            st.session_state.elevenlabs_client = ElevenLabs(api_key=api_key)
            st.success("API key set successfully!")
        except Exception as e:
            st.error(f"Error setting API key: {str(e)}")
            st.session_state.api_key_provided = False
    else:
        st.error("Please enter a valid API key")

def load_voices():
    if st.session_state.elevenlabs_client:
        with st.spinner("Loading voices..."):
            voices = list_elevenlabs_voices(st.session_state.elevenlabs_client)
            if voices:
                st.session_state.voices = voices
                
                # Extract unique values for filters
                accents = set()
                ages = set()
                genders = set()
                
                for voice in voices:
                    labels = voice.get("labels", {})
                    
                    accent = get_voice_trait(voice, "accent")
                    if accent != "Unknown":
                        accents.add(accent)
                        
                    age = get_voice_trait(voice, "age")
                    if age != "Unknown":
                        ages.add(age)
                        
                    gender = get_voice_trait(voice, "gender")
                    if gender != "Unknown":
                        genders.add(gender)
                
                st.session_state.voice_filters = {
                    "accents": sorted(list(accents)),
                    "ages": sorted(list(ages)),
                    "genders": sorted(list(genders))
                }
                
                st.success(f"Loaded {len(voices)} voices successfully!")
            else:
                st.error("No voices found or there was an error fetching voices")

def select_voice(voice_id):
    st.session_state.selected_voice_id = voice_id
    
    # Find the corresponding voice data
    for voice in st.session_state.voices:
        if voice["voice_id"] == voice_id:
            st.session_state.selected_voice_data = voice
            
            # Record this voice selection in user preferences
            if st.session_state.user_learning:
                st.session_state.user_learning.record_voice_selection(voice_id, voice)
            
            st.success(f"Selected voice: {voice['name']}")
            break

def generate_audio():
    if not st.session_state.selected_voice_id:
        st.error("Please select a voice first")
        return
        
    if not st.session_state.script:
        st.error("Please enter a script first")
        return
        
    # Check for placeholders in the script
    if re.search(r'\[.*?\]', st.session_state.script):
        st.error("Your script contains placeholders like [Company Name]. Please replace them before generating audio.")
        return
    
    # Generate audio
    result = generate_elevenlabs_audio(
        st.session_state.elevenlabs_client,
        st.session_state.selected_voice_id,
        st.session_state.script,
        st.session_state.voice_settings
    )
    
    if result["status"] == "success":
        st.session_state.generated_audio = result["file"]
        
        # Record generation in user preferences
        if st.session_state.user_learning:
            st.session_state.user_learning.record_script_generation(
                st.session_state.selected_voice_id,
                st.session_state.script
            )
            
        # Add to history
        voice_name = "Unknown"
        for voice in st.session_state.voices:
            if voice["voice_id"] == st.session_state.selected_voice_id:
                voice_name = voice["name"]
                break
                
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "voice_id": st.session_state.selected_voice_id,
            "voice_name": voice_name,
            "script": st.session_state.script,
            "audio_file": result["file"]
        }
        
        st.session_state.history.append(history_entry)
        st.success("Audio generated successfully!")
    else:
        st.error(f"Error generating audio: {result.get('message', 'Unknown error')}")

def rate_voice(voice_id, rating):
    if st.session_state.user_learning:
        if st.session_state.user_learning.record_rating(voice_id, rating):
            st.success(f"Thank you for rating this voice {rating}/5!")
        else:
            st.error("Failed to record rating")

def filter_voices():
    filtered_voices = st.session_state.voices.copy()
    
    accent_filter = st.session_state.applied_filters["accent"]
    age_filter = st.session_state.applied_filters["age"]
    gender_filter = st.session_state.applied_filters["gender"]
    
    if accent_filter:
        filtered_voices = [v for v in filtered_voices if get_voice_trait(v, "accent") == accent_filter]
        
    if age_filter:
        filtered_voices = [v for v in filtered_voices if get_voice_trait(v, "age") == age_filter]
        
    if gender_filter:
        filtered_voices = [v for v in filtered_voices if get_voice_trait(v, "gender") == gender_filter]
        
    return filtered_voices

def reset_filters():
    st.session_state.applied_filters = {
        "accent": None,
        "age": None,
        "gender": None
    }

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()
    st.rerun()

# Main app
def main():
    # Initialize session state
    init_session_state()
    
    # Display app header
    st.markdown("<h1 class='custom-header'>🎙️ VoiceGen</h1>", unsafe_allow_html=True)
    st.markdown("<p>Create lifelike voice audio with ElevenLabs AI</p>", unsafe_allow_html=True)
    
    # Sidebar for authentication and settings
    with st.sidebar:
        st.markdown("<h3 class='custom-subheader'>🔑 Account</h3>", unsafe_allow_html=True)
        
        if not st.session_state.authenticated:
            tabs = st.tabs(["Login", "Create Account", "Guest"])
            
            with tabs[0]:
                login_result = login_form()
                if login_result:
                    username, session_id = login_result
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.session_id = session_id
                    st.session_state.user_learning = UserLearningSystem(username)
                    st.rerun()
            
            with tabs[1]:
                signup_result = signup_form()
                if signup_result:
                    username, session_id = signup_result
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.session_id = session_id
                    st.session_state.user_learning = UserLearningSystem(username)
                    st.rerun()
            
            with tabs[2]:
                st.write("Continue without an account")
                if st.button("Continue as Guest"):
                    guest_id, _ = guest_login()
                    st.session_state.authenticated = True
                    st.session_state.username = guest_id
                    st.session_state.user_learning = UserLearningSystem(guest_id)
                    st.rerun()
        else:
            st.markdown(f"""
            <div class="user-info">
                <p><strong>Logged in as:</strong> {st.session_state.username}</p>
                <p><small>{'Active session' if st.session_state.session_id else 'Guest session'}</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Logout"):
                logout()
        
        st.markdown("<h3 class='custom-subheader'>🔌 API Connection</h3>", unsafe_allow_html=True)
        
        if not st.session_state.api_key_provided:
            st.text_input("ElevenLabs API Key", key="api_key_input", type="password")
            st.button("Set API Key", on_click=set_api_key)
            st.markdown("""
            <small>Don't have an API key? Get one at <a href="https://elevenlabs.io/sign-up" target="_blank">elevenlabs.io</a></small>
            """, unsafe_allow_html=True)
        else:
            st.success("API Key provided ✓")
            if st.button("Change API Key"):
                st.session_state.api_key_provided = False
                st.session_state.elevenlabs_api_key = ""
                st.session_state.elevenlabs_client = None
                st.rerun()
                
        if st.session_state.api_key_provided and not st.session_state.voices:
            st.button("Load Voices", on_click=load_voices)
        
        # Only show this section if authenticated
        if st.session_state.authenticated:
            st.markdown("<h3 class='custom-subheader'>⚙️ Settings</h3>", unsafe_allow_html=True)
            
            if st.checkbox("Show Advanced Settings", value=st.session_state.show_advanced):
                st.session_state.show_advanced = True
                st.markdown("<p>Voice Settings</p>", unsafe_allow_html=True)
                
                st.session_state.voice_settings["stability"] = st.slider(
                    "Stability", 0.0, 1.0, st.session_state.voice_settings["stability"], 0.01,
                    help="Higher stability makes the voice more consistent but less expressive"
                )
                
                st.session_state.voice_settings["similarity_boost"] = st.slider(
                    "Similarity Boost", 0.0, 1.0, st.session_state.voice_settings["similarity_boost"], 0.01,
                    help="Higher similarity makes the voice sound more like the original sample"
                )
                
                st.session_state.voice_settings["style"] = st.slider(
                    "Style", 0.0, 1.0, st.session_state.voice_settings["style"], 0.01,
                    help="Higher style value improves style transfer but may reduce clarity"
                )
                
                st.session_state.voice_settings["speed"] = st.slider(
                    "Speed", 0.7, 1.3, st.session_state.voice_settings["speed"], 0.01,
                    help="Adjust the speaking speed"
                )
                
                st.session_state.voice_settings["use_speaker_boost"] = st.checkbox(
                    "Speaker Boost", value=st.session_state.voice_settings["use_speaker_boost"],
                    help="Enhance voice clarity and reduce background noise"
                )
            else:
                st.session_state.show_advanced = False
    
    # Main content area
    if not st.session_state.authenticated:
        st.info("Please log in or continue as a guest to start using VoiceGen")
    elif not st.session_state.api_key_provided:
        st.info("Please provide your ElevenLabs API key to get started")
    else:
        tabs = st.tabs(["Create Audio", "Voice Library", "History"])
        
        # Create Audio Tab
        with tabs[0]:
            st.markdown("<h2 class='custom-subheader'>✏️ Create Audio</h2>", unsafe_allow_html=True)
            
            # Script input
            st.markdown("<h4>Step 1: Write Your Script</h4>", unsafe_allow_html=True)
            script = st.text_area(
                "Enter your script below",
                value=st.session_state.script,
                height=200,
                placeholder="Type or paste your script here. Make sure to remove any placeholders like [Company Name] before generating."
            )
            
            if script != st.session_state.script:
                st.session_state.script = script
            
            # Voice selection
            st.markdown("<h4>Step 2: Select a Voice</h4>", unsafe_allow_html=True)
            
            if not st.session_state.voices:
                st.warning("No voices loaded. Please click 'Load Voices' in the sidebar.")
            else:
                if st.session_state.selected_voice_id:
                    # Display selected voice
                    for voice in st.session_state.voices:
                        if voice["voice_id"] == st.session_state.selected_voice_id:
                            st.markdown(f"""
                            <div class="voice-card" style="border-left: 4px solid #1D3557;">
                                <div class="voice-name">Selected: {voice["name"]}</div>
                                <div class="voice-description">
                                    {get_voice_trait(voice, "gender")} • 
                                    {get_voice_trait(voice, "age")} • 
                                    {get_voice_trait(voice, "accent")} • 
                                    {get_voice_trait(voice, "use_case")}
                                </div>
                            """, unsafe_allow_html=True)
                            
                            preview_url = voice.get("preview_url")
                            if preview_url:
                                preview_data_url = get_audio_bytes_url(preview_url)
                                if preview_data_url:
                                    st.markdown(f"""
                                    <audio class="audio-player" controls>
                                        <source src="{preview_data_url}" type="audio/mpeg">
                                        Your browser does not support the audio element.
                                    </audio>
                                    """, unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            # Button to change voice
                            if st.button("Change Voice"):
                                st.session_state.selected_voice_id = None
                                st.session_state.selected_voice_data = None
                                st.rerun()
                            break
                else:
                    st.info("Please select a voice in the 'Voice Library' tab")
            
            # Generate audio
            st.markdown("<h4>Step 3: Generate Audio</h4>", unsafe_allow_html=True)
            
            if st.button("Generate Audio", disabled=not (st.session_state.script and st.session_state.selected_voice_id)):
                generate_audio()
            
            # Display generated audio
            if st.session_state.generated_audio:
                st.markdown("<h4>Your Generated Audio:</h4>", unsafe_allow_html=True)
                
                try:
                    audio_file = Path(st.session_state.generated_audio)
                    if audio_file.exists():
                        audio_data = get_audio_data_url(st.session_state.generated_audio)
                        st.markdown(f"""
                        <div style="padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin-top: 20px;">
                            <h4 style="margin-bottom: 15px;">🎵 Generated Audio</h4>
                            <audio class="audio-player" controls style="width: 100%;">
                                <source src="{audio_data}" type="audio/mpeg">
                                Your browser does not support the audio element.
                            </audio>
                            <p style="margin-top: 15px; font-size: 14px;">
                                File: {os.path.basename(st.session_state.generated_audio)}<br>
                                Characters: {len(st.session_state.script)}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Download button
                        with open(st.session_state.generated_audio, "rb") as file:
                            btn = st.download_button(
                                label="Download Audio",
                                data=file,
                                file_name=os.path.basename(st.session_state.generated_audio),
                                mime="audio/mpeg"
                            )
                        
                        # Rating section
                        st.markdown("<h4>How was this voice?</h4>", unsafe_allow_html=True)
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            if st.button("⭐", key="rate_1"):
                                rate_voice(st.session_state.selected_voice_id, 1)
                        with col2:
                            if st.button("⭐⭐", key="rate_2"):
                                rate_voice(st.session_state.selected_voice_id, 2)
                        with col3:
                            if st.button("⭐⭐⭐", key="rate_3"):
                                rate_voice(st.session_state.selected_voice_id, 3)
                        with col4:
                            if st.button("⭐⭐⭐⭐", key="rate_4"):
                                rate_voice(st.session_state.selected_voice_id, 4)
                        with col5:
                            if st.button("⭐⭐⭐⭐⭐", key="rate_5"):
                                rate_voice(st.session_state.selected_voice_id, 5)
                    else:
                        st.error(f"Audio file not found: {st.session_state.generated_audio}")
                except Exception as e:
                    st.error(f"Error displaying audio: {str(e)}")
        
        # Voice Library Tab
        with tabs[1]:
            st.markdown("<h2 class='custom-subheader'>🗣️ Voice Library</h2>", unsafe_allow_html=True)
            
            if not st.session_state.voices:
                st.warning("No voices loaded. Please click 'Load Voices' in the sidebar.")
            else:
                # Search and filters
                search_col, filter_col = st.columns([2, 1])
                
                with search_col:
                    search_query = st.text_input("Search voices", placeholder="Search by name...")
                
                with filter_col:
                    if st.button("Filters", use_container_width=True):
                        st.session_state.show_filters = not st.session_state.get("show_filters", False)
                
                # Filters section
                if st.session_state.get("show_filters", False):
                    st.markdown("<h4>Filter Voices</h4>", unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                    
                    with col1:
                        if st.session_state.voice_filters["accents"]:
                            accent_options = ["Any"] + st.session_state.voice_filters["accents"]
                            accent_filter = st.selectbox("Accent", accent_options)
                            if accent_filter != "Any":
                                st.session_state.applied_filters["accent"] = accent_filter
                            else:
                                st.session_state.applied_filters["accent"] = None
                    
                    with col2:
                        if st.session_state.voice_filters["ages"]:
                            age_options = ["Any"] + st.session_state.voice_filters["ages"]
                            age_filter = st.selectbox("Age", age_options)
                            if age_filter != "Any":
                                st.session_state.applied_filters["age"] = age_filter
                            else:
                                st.session_state.applied_filters["age"] = None
                    
                    with col3:
                        if st.session_state.voice_filters["genders"]:
                            gender_options = ["Any"] + st.session_state.voice_filters["genders"]
                            gender_filter = st.selectbox("Gender", gender_options)
                            if gender_filter != "Any":
                                st.session_state.applied_filters["gender"] = gender_filter
                            else:
                                st.session_state.applied_filters["gender"] = None
                    
                    with col4:
                        st.write(" ")  # Spacing
                        if st.button("Reset Filters"):
                            reset_filters()
                
                # Get filtered and searched voices
                voices_to_display = st.session_state.voices.copy()
                
                # Apply filters if any
                if any(st.session_state.applied_filters.values()):
                    voices_to_display = filter_voices()
                
                # Apply search if any
                if search_query:
                    voices_to_display = [
                        v for v in voices_to_display 
                        if search_query.lower() in v["name"].lower()
                    ]
                
                # Get preferred voices
                preferred_voice_ids = []
                if st.session_state.user_learning:
                    preferred_voice_ids = st.session_state.user_learning.get_preferred_voices()
                
                # Sort by preference
                if preferred_voice_ids:
                    preferred_voices = [v for v in voices_to_display if v["voice_id"] in preferred_voice_ids]
                    other_voices = [v for v in voices_to_display if v["voice_id"] not in preferred_voice_ids]
                    voices_to_display = preferred_voices + other_voices
                
                # Display voice count
                st.markdown(f"<p>Showing {len(voices_to_display)} voices</p>", unsafe_allow_html=True)
                
                # Display voices
                for i, voice in enumerate(voices_to_display, 1):
                    selected = create_voice_card(voice, i, st.session_state.user_learning)
                    if selected:
                        select_voice(selected)
                        st.rerun()
        
        # History Tab
        with tabs[2]:
            st.markdown("<h2 class='custom-subheader'>📜 History</h2>", unsafe_allow_html=True)
            
            if not st.session_state.history:
                st.info("Your audio generation history will appear here")
            else:
                for i, entry in enumerate(reversed(st.session_state.history)):
                    with st.expander(f"{entry['voice_name']} - {datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')}"):
                        st.markdown(f"**Script:**\n{entry['script']}")
                        
                        audio_file = Path(entry['audio_file'])
                        if audio_file.exists():
                            audio_data = get_audio_data_url(entry['audio_file'])
                            st.markdown(f"""
                            <audio class="audio-player" controls>
                                <source src="{audio_data}" type="audio/mpeg">
                                Your browser does not support the audio element.
                            </audio>
                            """, unsafe_allow_html=True)
                            
                            # Download button
                            with open(entry['audio_file'], "rb") as file:
                                btn = st.download_button(
                                    label="Download Audio",
                                    data=file,
                                    file_name=os.path.basename(entry['audio_file']),
                                    mime="audio/mpeg",
                                    key=f"download_{i}"
                                )
                        else:
                            st.error("Audio file not found")
                            
                        # Use this script/voice again buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Use this script", key=f"use_script_{i}"):
                                st.session_state.script = entry['script']
                                st.session_state.tab_index = 0  # Switch to Create Audio tab
                                st.rerun()
                        with col2:
                            if st.button("Use this voice", key=f"use_voice_{i}"):
                                select_voice(entry['voice_id'])
                                st.session_state.tab_index = 0  # Switch to Create Audio tab
                                st.rerun()

# Run the app
if __name__ == "__main__":
    main()
