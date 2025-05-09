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
from groq import Groq

# Initialize Groq client
os.environ["GROQ_API_KEY"] = "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"
client = Groq()

# Set page configuration
st.set_page_config(
    page_title="Voice Chat | AI Assistant",
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
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        gap: 0.75rem;
    }
    .chat-message.user {
        background-color: #e9ecef;
    }
    .chat-message.assistant {
        background-color: #f1f8ff;
        border-left: 5px solid #4e8df5;
    }
    .chat-message .avatar {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #d1e7ff;
        color: #4e8df5;
        font-size: 1.25rem;
        flex-shrink: 0;
    }
    .chat-message .user-avatar {
        background-color: #e9f5ff;
        color: #2c5282;
    }
    .chat-message .content {
        flex-grow: 1;
    }
    .chat-message .content p {
        margin: 0;
    }
    .voice-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 1rem;
    }
    .voice-info {
        flex-grow: 1;
    }
    .voice-name {
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 5px;
    }
    .voice-description {
        color: #555;
        font-size: 14px;
    }
    .voice-actions {
        display: flex;
        flex-direction: row;
        gap: 0.5rem;
    }
    .audio-player {
        width: 100%;
        border-radius: 8px;
        margin-top: 10px;
    }
    .chat-input {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-top: 1rem;
    }
    .chat-input textarea {
        border: none;
        box-shadow: none !important;
        padding: 0;
        resize: none !important;
    }
    .chat-input textarea:focus {
        border: none;
        box-shadow: none !important;
    }
    .send-button {
        border-radius: 1.5rem !important;
        padding: 0.5rem 1rem !important;
        background-color: #4e8df5 !important;
        color: white !important;
    }
    .send-button:hover {
        background-color: #3b7eea !important;
    }
    .send-button:active {
        background-color: #2c6cdf !important;
    }
    .voice-selection {
        margin-top: 1rem;
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .voice-preview {
        display: inline-block;
        margin-right: 10px;
        cursor: pointer;
    }
    .voice-preview.selected {
        font-weight: bold;
        text-decoration: underline;
    }
    .system-message {
        background-color: #e2f3ff;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        font-style: italic;
        color: #555;
    }
    .sidebar .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #4e8df5;
        color: white;
    }
    .sidebar .stButton>button:hover {
        background-color: #3b7eea;
    }
    .audio-message {
        margin-top: 0.5rem;
        padding: 0.75rem;
        background-color: #f8f8f8;
        border-radius: 0.5rem;
    }
    .user-info {
        background-color: #E9F2FF;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .chat-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .chat-header h1 {
        margin: 0;
        font-size: 1.75rem;
        color: #2c5282;
    }
    .chat-header .icon {
        font-size: 2rem;
        color: #4e8df5;
    }
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    .typing-dot {
        width: 0.5rem;
        height: 0.5rem;
        background-color: #4e8df5;
        border-radius: 50%;
        animation: typing-dot 1.4s infinite ease-in-out;
    }
    .typing-dot:nth-child(1) {
        animation-delay: 0s;
    }
    .typing-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    .typing-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes typing-dot {
        0%, 60%, 100% {
            transform: translateY(0);
        }
        30% {
            transform: translateY(-5px);
        }
    }
    .loading-voices {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #4e8df5;
        margin: 1rem 0;
    }
    .loading-voices .spinner {
        width: 1rem;
        height: 1rem;
        border: 2px solid rgba(78, 141, 245, 0.3);
        border-radius: 50%;
        border-top-color: #4e8df5;
        animation: spin 1s infinite linear;
    }
    @keyframes spin {
        0% {
            transform: rotate(0deg);
        }
        100% {
            transform: rotate(360deg);
        }
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
    
    def record_conversation_turn(self, user_message, assistant_message):
        """Record a conversation turn"""
        # Update engagement metrics
        metrics = self.conversation_learning["engagement_metrics"]
        metrics["total_messages"] += 1
        metrics["avg_response_length"] = (
            (metrics["avg_response_length"] * (metrics["total_messages"] - 1)) + len(user_message)
        ) / metrics["total_messages"]
        
        # Extract potential topics (simplified)
        words = re.findall(r'\b\w+\b', user_message.lower())
        common_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "are", "was", "were"]
        potential_topics = [word for word in words if word not in common_words and len(word) > 3]
        
        # Record topics
        for topic in potential_topics:
            self.conversation_learning["topic_preferences"][topic] = (
                self.conversation_learning["topic_preferences"].get(topic, 0) + 1
            )
        
        # Record response patterns
        response_type = "short" if len(user_message) < 20 else "medium" if len(user_message) < 100 else "long"
        self.conversation_learning["user_response_patterns"][response_type] = (
            self.conversation_learning["user_response_patterns"].get(response_type, 0) + 1
        )
        
        # Save data periodically (every 5 messages)
        if metrics["total_messages"] % 5 == 0:
            self.save_data()
        
    def clean_label_value(self, value):
        if not value:
            return ""
        # Replace underscores with spaces
        value = value.replace("_", " ").title()
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
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = f"output_audio/output_{timestamp}.mp3"
        
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=applied_settings
        )
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "wb") as f:
            for chunk in audio:
                f.write(chunk)

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

# Chat and conversation functions
def process_message(message, system_prompt, messages, elevenlabs_client, selected_voice_id=None):
    """Process a user message, get AI response, and optionally generate audio"""
    # Add user message to history
    messages.append({"role": "user", "content": message})
    
    # Get AI response
    try:
        chat_completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                *messages
            ],
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=False
        )
        
        # Get the response text
        response_text = chat_completion.choices[0].message.content
        
        # Add assistant response to history
        messages.append({"role": "assistant", "content": response_text})
        
        # Check if we should generate audio
        audio_result = None
        if elevenlabs_client and selected_voice_id:
            # Check for explicit audio generation command
            should_generate_audio = (
                "generate audio" in message.lower() or
                "speak this" in message.lower() or
                "say this" in message.lower() or
                "read this" in message.lower()
            )
            
            if should_generate_audio:
                # Generate audio from the response
                audio_result = generate_elevenlabs_audio(
                    elevenlabs_client,
                    selected_voice_id,
                    response_text
                )
        
        return response_text, audio_result
    except Exception as e:
        st.error(f"Error getting response: {str(e)}")
        return f"I'm sorry, I encountered an error: {str(e)}", None

def display_message(message, is_user=False, audio_file=None):
    """Display a chat message"""
    if is_user:
        st.markdown(f"""
        <div class="chat-message user">
            <div class="avatar user-avatar">👤</div>
            <div class="content">
                <p>{message}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant">
            <div class="avatar">🤖</div>
            <div class="content">
                <p>{message}</p>
                {f'<div class="audio-message"><audio class="audio-player" controls><source src="{get_audio_data_url(audio_file)}" type="audio/mpeg">Your browser does not support the audio element.</audio></div>' if audio_file else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_system_message(message):
    """Display a system message"""
    st.markdown(f"""
    <div class="system-message">
        <p>{message}</p>
    </div>
    """, unsafe_allow_html=True)

def display_typing_indicator():
    """Display a typing indicator"""
    st.markdown("""
    <div class="chat-message assistant">
        <div class="avatar">🤖</div>
        <div class="content">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    if "user_learning" not in st.session_state:
        st.session_state.user_learning = None
        
    if "voice_settings" not in st.session_state:
        st.session_state.voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True,
            "speed": 1.0
        }
    
    if "voice_search_query" not in st.session_state:
        st.session_state.voice_search_query = ""
        
    if "show_voice_selection" not in st.session_state:
        st.session_state.show_voice_selection = False

# Callback functions
def set_api_key():
    api_key = st.session_state.api_key_input
    if api_key:
        st.session_state.elevenlabs_api_key = api_key
        st.session_state.api_key_provided = True
        try:
            st.session_state.elevenlabs_client = ElevenLabs(api_key=api_key)
            # Load voices automatically
            load_voices()
        except Exception as e:
            st.error(f"Error setting API key: {str(e)}")
            st.session_state.api_key_provided = False
    else:
        st.error("Please enter a valid API key")

def load_voices():
    if st.session_state.elevenlabs_client:
        voices = list_elevenlabs_voices(st.session_state.elevenlabs_client)
        if voices:
            st.session_state.voices = voices
            return True
    return False

def select_voice(voice_id, voice_name):
    st.session_state.selected_voice_id = voice_id
    
    # Find the corresponding voice data
    for voice in st.session_state.voices:
        if voice["voice_id"] == voice_id:
            st.session_state.selected_voice_data = voice
            
            # Record this voice selection in user preferences
            if st.session_state.user_learning:
                st.session_state.user_learning.record_voice_selection(voice_id, voice)
            
            # Add system message to chat
            st.session_state.messages.append({
                "role": "system", 
                "content": f"Voice '{voice_name}' selected. You can now ask the assistant to generate audio responses."
            })
            
            st.session_state.show_voice_selection = False
            break

def toggle_voice_selection():
    st.session_state.show_voice_selection = not st.session_state.show_voice_selection

def search_voices():
    st.session_state.voice_search_query = st.session_state.voice_search_input

def reset_conversation():
    st.session_state.messages = []
    st.rerun()

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()
    st.rerun()

# Define system prompt
def get_system_prompt(username, selected_voice_name=None, user_learning=None):
    base_prompt = """
You are an AI assistant specializing in voice content creation through ElevenLabs. Your primary goal is to help users create high-quality voice content in a conversational manner.

CORE PRINCIPLES:
1. CONVERSATIONAL & HELPFUL - Guide users through their voice content needs naturally
2. GATHER INFORMATION - Ask questions to understand what the user wants to create
3. PROVIDE GUIDANCE - Help users improve their scripts for optimal audio quality
4. EXPLAIN VOICE SELECTION - Help users understand different voice characteristics
5. SUGGEST IMPROVEMENTS - Offer constructive suggestions for script improvement

VOICE GENERATION CAPABILITIES:
- When users ask you to "generate audio", "speak this", "say this", or "read this", you'll convert your response to audio
- You can suggest voice options based on content type (e.g., narration, character voices)
- You provide guidance on script length, pacing, and pronunciation

CONVERSATION TIPS:
- Ask about the purpose of their audio content
- Help refine scripts by suggesting improvements
- Offer to generate audio when the script seems polished
- Explain different voice characteristics when relevant
"""

    # Add personalization if available
    if user_learning:
        # Get preferred voices info
        preferred_voice_ids = user_learning.get_preferred_voices()
        preferred_traits = user_learning.get_preferred_traits()
        
        # Get user conversation patterns
        metrics = user_learning.conversation_learning["engagement_metrics"]
        response_patterns = user_learning.conversation_learning["user_response_patterns"]
        
        # Build personalization section
        personalization = ["USER PREFERENCES:"]
        
        if user_learning.preferences["total_generations"] > 0:
            personalization.append(f"- User has generated {user_learning.preferences['total_generations']} audio clips")
        
        if preferred_traits:
            trait_text = ", ".join(preferred_traits)
            personalization.append(f"- Preferred voice traits: {trait_text}")
        
        if metrics["total_messages"] > 5:
            response_style = max(response_patterns.items(), key=lambda x: x[1])[0] if response_patterns else "medium"
            personalization.append(f"- Communication style: {response_style} responses")
        
        # Add current voice if selected
        if selected_voice_name:
            personalization.append(f"- Current voice: {selected_voice_name}")
            
        personalized_prompt = base_prompt + "\n\n" + "\n".join(personalization)
        return personalized_prompt
    
    # Add selected voice if available
    if selected_voice_name:
        return base_prompt + f"\n\nCURRENT VOICE: {selected_voice_name}"
        
    return base_prompt

# Main app
def main():
    # Initialize session state
    init_session_state()
    
    # Sidebar for authentication and settings
    with st.sidebar:
        st.markdown("### 🔑 Account")
        
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
        
        st.markdown("### 🔌 API Connection")
        
        if not st.session_state.api_key_provided:
            st.text_input("ElevenLabs API Key", key="api_key_input", type="password")
            st.button("Connect API", on_click=set_api_key)
            st.markdown("""
            <small>Don't have an API key? Get one at <a href="https://elevenlabs.io/sign-up" target="_blank">elevenlabs.io</a></small>
            """, unsafe_allow_html=True)
        else:
            st.success("Connected to ElevenLabs ✓")
            if st.button("Change API Key"):
                st.session_state.api_key_provided = False
                st.session_state.elevenlabs_api_key = ""
                st.session_state.elevenlabs_client = None
                st.rerun()
        
        # Only show these options if authenticated
        if st.session_state.authenticated:
            st.markdown("### ⚙️ Chat Options")
            
            # Voice selection button
            voice_btn_label = "Change Voice" if st.session_state.selected_voice_id else "Select Voice"
            if st.button(voice_btn_label):
                toggle_voice_selection()
            
            # Reset conversation button
            if st.button("New Conversation"):
                reset_conversation()
                
            # Voice settings (collapsible)
            with st.expander("Voice Settings"):
                st.slider(
                    "Stability", 0.0, 1.0, st.session_state.voice_settings["stability"], 0.01,
                    help="Higher stability makes the voice more consistent but less expressive"
                )
                
                st.slider(
                    "Similarity Boost", 0.0, 1.0, st.session_state.voice_settings["similarity_boost"], 0.01,
                    help="Higher similarity makes the voice sound more like the original sample"
                )
                
                st.slider(
                    "Speed", 0.7, 1.3, st.session_state.voice_settings["speed"], 0.01,
                    help="Adjust the speaking speed"
                )
    
    # Main chat interface
    if not st.session_state.authenticated:
        st.markdown("""
        <div class="chat-header">
            <div class="icon">🎙️</div>
            <h1>Voice Chat Assistant</h1>
        </div>
        """, unsafe_allow_html=True)
        st.info("Please log in or continue as a guest to start using Voice Chat")
    elif not st.session_state.api_key_provided:
        st.markdown("""
        <div class="chat-header">
            <div class="icon">🎙️</div>
            <h1>Voice Chat Assistant</h1>
        </div>
        """, unsafe_allow_html=True)
        st.info("Please provide your ElevenLabs API key to get started")
    else:
        # Chat header
        st.markdown("""
        <div class="chat-header">
            <div class="icon">🎙️</div>
            <h1>Voice Chat</h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Get the selected voice name if available
        selected_voice_name = None
        if st.session_state.selected_voice_data:
            selected_voice_name = st.session_state.selected_voice_data["name"]
        
        # Display current voice if selected
        if selected_voice_name:
            st.markdown(f"""
            <div style="display: inline-block; background-color: #e2f3ff; padding: 5px 10px; border-radius: 20px; margin-bottom: 10px;">
                <span style="font-weight: bold;">🎤 {selected_voice_name}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Voice selection interface
        if st.session_state.show_voice_selection:
            st.markdown("### Select a Voice")
            
            if not st.session_state.voices:
                with st.spinner("Loading voices..."):
                    if load_voices():
                        st.success(f"Loaded {len(st.session_state.voices)} voices")
                    else:
                        st.error("Failed to load voices. Please try again.")
            else:
                # Voice search
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text_input("Search voices", key="voice_search_input")
                with col2:
                    st.button("Search", on_click=search_voices)
                
                # Filter voices by search query
                filtered_voices = st.session_state.voices
                if st.session_state.voice_search_query:
                    query = st.session_state.voice_search_query.lower()
                    filtered_voices = [
                        v for v in filtered_voices 
                        if query in v["name"].lower() or 
                        query in get_voice_trait(v, "accent").lower() or
                        query in get_voice_trait(v, "gender").lower()
                    ]
                
                # Get preferred voices
                preferred_voice_ids = []
                if st.session_state.user_learning:
                    preferred_voice_ids = st.session_state.user_learning.get_preferred_voices()
                
                # Sort by preference
                if preferred_voice_ids:
                    preferred_voices = [v for v in filtered_voices if v["voice_id"] in preferred_voice_ids]
                    other_voices = [v for v in filtered_voices if v["voice_id"] not in preferred_voice_ids]
                    filtered_voices = preferred_voices + other_voices
                
                # Show voice cards in a grid
                voice_cols = st.columns(2)
                for i, voice in enumerate(filtered_voices[:10]):  # Limit to 10 voices
                    with voice_cols[i % 2]:
                        st.markdown(f"""
                        <div class="voice-card">
                            <div class="voice-info">
                                <div class="voice-name">{"⭐ " if voice["voice_id"] in preferred_voice_ids else ""}{voice["name"]}</div>
                                <div class="voice-description">
                                    {get_voice_trait(voice, "gender")} • 
                                    {get_voice_trait(voice, "age")} • 
                                    {get_voice_trait(voice, "accent")}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Add audio preview
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
                        
                        # Selection button
                        if st.button(f"Select", key=f"select_{voice['voice_id']}"):
                            select_voice(voice["voice_id"], voice["name"])
                            
                        st.markdown("</div>", unsafe_allow_html=True)
        
        # Chat message container
        chat_container = st.container()
        
        # Display chat messages
        with chat_container:
            # Welcome message if no messages yet
            if not st.session_state.messages:
                display_system_message(
                    "👋 Welcome to Voice Chat! I'm your AI assistant for creating voice content. "
                    "How can I help you today? You can ask me to write scripts, suggest voice options, "
                    "or generate audio from text."
                )
                
                if not selected_voice_name:
                    display_system_message(
                        "📢 No voice selected yet. Click the 'Select Voice' button in the sidebar to choose a voice for audio generation."
                    )
            
            # Display all messages
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    display_message(message["content"], is_user=True)
                elif message["role"] == "assistant":
                    # Check if we have an audio file for this message
                    audio_file = None
                    if i > 0 and i+1 < len(st.session_state.messages) and st.session_state.messages[i+1]["role"] == "system" and "audio_file" in st.session_state.messages[i+1]["content"]:
                        audio_file = st.session_state.messages[i+1]["content"]["audio_file"]
                    
                    display_message(message["content"], is_user=False, audio_file=audio_file)
                elif message["role"] == "system":
                    if isinstance(message["content"], dict) and "audio_file" in message["content"]:
                        # This is an audio file system message, skip displaying it
                        continue
                    else:
                        display_system_message(message["content"])
            
        # Chat input
        user_input = st.chat_input("Type your message here...")
        
        # Process user input
        if user_input:
            # Get system prompt
            system_prompt = get_system_prompt(
                st.session_state.username,
                selected_voice_name,
                st.session_state.user_learning
            )
            
            # Add user message to state
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Record in user learning system
            if st.session_state.user_learning and len(st.session_state.messages) >= 2:
                last_assistant_message = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"), None)
                if last_assistant_message:
                    st.session_state.user_learning.record_conversation_turn(user_input, last_assistant_message)
            
            # Show typing indicator (rerun to display user message first)
            st.rerun()
        
        # Process assistant response after rerun if there's a user message
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            # Show typing indicator
            display_typing_indicator()
            
            # Get system prompt
            system_prompt = get_system_prompt(
                st.session_state.username,
                selected_voice_name,
                st.session_state.user_learning
            )
            
            # Process message and get response
            user_message = st.session_state.messages[-1]["content"]
            response_text, audio_result = process_message(
                user_message,
                system_prompt,
                [m for m in st.session_state.messages if m["role"] != "system"],  # Exclude system messages
                st.session_state.elevenlabs_client,
                st.session_state.selected_voice_id
            )
            
            # Add response to session state
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            # Add audio result if available
            if audio_result and audio_result["status"] == "success":
                st.session_state.messages.append({
                    "role": "system", 
                    "content": {"audio_file": audio_result["file"]}
                })
                
                # Record in user learning system
                if st.session_state.user_learning:
                    st.session_state.user_learning.record_script_generation(
                        st.session_state.selected_voice_id,
                        response_text
                    )
            
            # Rerun to display assistant message
            st.rerun()

# Run the app
if __name__ == "__main__":
    main()
