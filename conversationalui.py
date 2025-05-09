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
import requests
from PIL import Image as PILImage
from io import BytesIO

# Google Gemini imports for image generation
from google import genai
from google.genai import types
from imagekitio import ImageKit

# Initialize Groq client
os.environ["GROQ_API_KEY"] = "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"
client = Groq()

# Initialize the Google Gemini client
gemini_client = genai.Client(api_key="AIzaSyBLzfjImenFp60acvXgKygaEDKGqKfHyKI")

# Initialize the ImageKit client
imagekit = ImageKit(
    private_key='private_OGgux+C54n9PIYDlLdOrYysEWrw=',
    public_key='public_Qq9s197rBPKyx5eWhq+aN6TQ3Iw=',
    url_endpoint='https://ik.imagekit.io/b6pq3mgo7'
)

# Set page configuration
st.set_page_config(
    page_title="Creative Assistant",
    page_icon="🎨",
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
    .image-gallery {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin-top: 1rem;
    }
    .image-card {
        border-radius: 0.5rem;
        overflow: hidden;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        background-color: white;
        width: 100%;
        max-width: 320px;
    }
    .image-card img {
        width: 100%;
        height: auto;
        object-fit: cover;
        border-top-left-radius: 0.5rem;
        border-top-right-radius: 0.5rem;
    }
    .image-card .prompt {
        padding: 0.75rem;
        font-size: 0.875rem;
        color: #555;
    }
    .rating-buttons {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .rating-buttons button {
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
        border: 1px solid #ddd;
        background-color: white;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        transition: all 0.2s;
    }
    .rating-buttons button:hover {
        background-color: #4e8df5;
        color: white;
        border-color: #4e8df5;
    }
    .feature-tabs {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .feature-tab {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        background-color: #f1f1f1;
        cursor: pointer;
        transition: all 0.2s;
    }
    .feature-tab.active {
        background-color: #4e8df5;
        color: white;
    }
    .feature-tab:hover {
        background-color: #e0e0e0;
    }
    .feature-tab.active:hover {
        background-color: #3b7eea;
    }
</style>
""", unsafe_allow_html=True)

# Define directories
@st.cache_resource
def ensure_directories():
    directories = ["users", "sessions", "user_data", "output_audio", "generated_images"]
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
            "image_prompts": [],        # List of successful image prompts
            "image_ratings": {},        # image_prompt -> rating (1-5)
            "last_session": None,       # Timestamp
            "total_generations": 0,     # Count of audio generations
            "total_image_generations": 0 # Count of image generations
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
    
    def record_image_generation(self, prompt, image_url, success=True):
        """Record an image generation event"""
        # Increment total image generations
        self.preferences["total_image_generations"] += 1
        
        # Store successful image prompts for learning
        if success:
            # Store compact history entry
            history_entry = {
                "prompt": prompt,
                "image_url": image_url,
                "timestamp": datetime.now().isoformat()
            }
            self.preferences["image_prompts"].append(history_entry)
        
        # Save the updated data
        self.save_data()
    
    def record_rating(self, voice_id, rating):
        """Record a user's rating of a voice (1-5)"""
        if 1 <= rating <= 5:
            self.preferences["voice_ratings"][voice_id] = rating
            self.save_data()
            return True
        return False
    
    def record_image_rating(self, prompt, rating):
        """Record a user's rating of an image (1-5)"""
        if 1 <= rating <= 5:
            # Use the prompt as key since we don't have a stable image ID
            self.preferences["image_ratings"][prompt] = rating
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
        # Create output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = f"output_audio/output_{timestamp}.mp3"
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Generate audio
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=applied_settings
        )
        
        # Save audio to file
        with open(output_file, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        return {"status": "success", "file": output_file, "text_length": len(text)}
    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")
        return {"status": "error", "message": str(e)}

def get_audio_data_url(file_path):
    """Convert an audio file to a base64 data URL"""
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

# Image-related functions
def generate_images(prompts, create_collection=True):
    """Generate images using Google Gemini and upload to ImageKit"""
    if isinstance(prompts, str):
        prompts = [prompts]  # Convert single prompt to list
    
    # Create lists to store image information
    image_urls = []
    image_file_ids = []
    
    # Create directory for images if it doesn't exist
    os.makedirs("generated_images", exist_ok=True)
    
    # Create progress bar
    progress_bar = st.progress(0)
    total_prompts = len(prompts)
    
    # Process each prompt
    for i, prompt in enumerate(prompts):
        progress_text = st.empty()
        progress_text.text(f"Generating image {i+1}/{total_prompts}: {prompt}")
        
        try:
            # Generate image using Gemini
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=prompt
            )
            
            # Check for generated image
            image_found = False
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data.mime_type.startswith('image/'):
                    image_found = True
                    
                    # Save the image
                    image_data = base64.b64decode(part.inline_data.data)
                    filename = f"generated_images/image-{i+1:02d}-{uuid.uuid4().hex[:8]}.png"
                    
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    # Upload to ImageKit
                    try:
                        with open(filename, "rb") as img_file:
                            upload = imagekit.upload_file(
                                file=img_file,
                                file_name=os.path.basename(filename)
                            )
                        
                        image_urls.append(upload["response"]["url"])
                        image_file_ids.append(upload["response"]["fileId"])
                    except Exception as upload_error:
                        # If ImageKit upload fails, use the local file
                        st.error(f"Error uploading to ImageKit: {str(upload_error)}")
                        image_urls.append(filename)
                        image_file_ids.append(None)
            
            if not image_found:
                image_urls.append(None)
                image_file_ids.append(None)
                
        except Exception as e:
            st.error(f"Error generating image: {str(e)}")
            image_urls.append(None)
            image_file_ids.append(None)
        
        # Update progress
        progress = (i + 1) / total_prompts
        progress_bar.progress(progress)
    
    # Clear progress indicators
    progress_bar.empty()
    progress_text.empty()
    
    # Create collection link if requested
    collection_url = None
    if create_collection and any(url is not None for url in image_urls):
        try:
            collection_url = create_image_collection(image_urls, "Generated Images Collection")
        except Exception as e:
            st.error(f"Error creating collection: {str(e)}")
    
    # Prepare results
    results = []
    for i, prompt in enumerate(prompts):
        if i < len(image_urls) and image_urls[i]:
            file_id = image_file_ids[i] if i < len(image_file_ids) else None
            results.append({
                "prompt": prompt,
                "image_url": image_urls[i],
                "file_id": file_id,
                "collection_url": collection_url,
                "status": "success"
            })
        else:
            results.append({
                "prompt": prompt,
                "status": "error",
                "message": "Failed to generate or upload image"
            })
    
    return results

def create_image_collection(image_urls, title="Generated Images Collection"):
    """Create a collection link with Creatify API"""
    # Filter out any None values
    valid_image_urls = [url for url in image_urls if url is not None]
    
    if not valid_image_urls:
        return None
    
    # Prepare payload for Creatify API
    creatify_url = "https://api.creatify.ai/api/links/link_with_params/"
    
    payload = {
        "title": title,
        "description": "Images generated with Google Gemini",
        "image_urls": valid_image_urls,
        "video_urls": [],
        "reviews": "AI Generated Images"
    }
    
    headers = {
        "X-API-ID": "5f8b3a5c-6e33-4e9f-b85c-71941d675270",
        "X-API-KEY": "c019dd017d22e2e40627f87bc86168b631b9a345",
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request
        response = requests.request("POST", creatify_url, json=payload, headers=headers)
        
        # Check for success
        if response.status_code == 200:
            try:
                json_response = response.json()
                if 'url' in json_response:
                    return json_response['url']
            except ValueError:
                pass
        
        return None
    
    except Exception as e:
        st.error(f"Error creating collection link: {e}")
        return None

# Chat and conversation functions
def process_message(message, system_prompt, messages, elevenlabs_client, selected_voice_id=None):
    """Process a user message, get AI response, and optionally generate audio"""
    # Add user message to history
    messages.append({"role": "user", "content": message})
    
    # Define function specs
    function_specs = [
        {
            "name": "generate_elevenlabs_audio",
            "description": "Generate audio from text using ElevenLabs",
            "parameters": {
                "type": "object",
                "properties": {
                    "voice_id": {"type": "string"},
                    "text": {"type": "string"},
                    "voice_settings": {
                        "type": "object",
                        "properties": {
                            "stability": {"type": "number", "minimum": 0, "maximum": 1},
                            "similarity_boost": {"type": "number", "minimum": 0, "maximum": 1},
                            "style": {"type": "number", "minimum": 0, "maximum": 1},
                            "use_speaker_boost": {"type": "boolean"},
                            "speed": {"type": "number", "minimum": 0.7, "maximum": 1.2}
                        }
                    }
                },
                "required": ["voice_id", "text"]
            }
        },
        {
            "name": "generate_images",
            "description": "Generate images based on text prompts",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompts": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "create_collection": {"type": "boolean"}
                },
                "required": ["prompts"]
            }
        }
    ]
    
    # Get AI response
    try:
        # Manage conversation history for token efficiency
        if len(messages) > 12:  # Keep system prompt and last 10 messages
            system_message = messages[0]
            recent_messages = messages[-11:]
            messages_to_send = [system_message] + recent_messages
        else:
            messages_to_send = messages
        
        # Add system prompt if not present
        if messages_to_send[0]["role"] != "system":
            messages_to_send = [{"role": "system", "content": system_prompt}] + messages_to_send
        
        # Call Groq API
        chat_completion = client.chat.completions.create(
            model=""deepseek-r1-distill-llama-70b",
            messages=messages_to_send,
            temperature=0.7,
            max_tokens=1024,
            tools=function_specs,
            tool_choice="auto"
        )
        
        # Get the response
        response_message = chat_completion.choices[0].message
        
        # Check for tool calls
        audio_result = None
        images_result = None
        
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                if tool_name == "generate_elevenlabs_audio" and elevenlabs_client and selected_voice_id:
                    # Check for audio generation
                    should_generate_audio = True
                    
                    # Generate audio
                    text_to_speak = arguments.get("text", "")
                    voice_settings = arguments.get("voice_settings", {})
                    
                    audio_result = generate_elevenlabs_audio(
                        elevenlabs_client,
                        selected_voice_id,
                        text_to_speak,
                        voice_settings
                    )
                    
                elif tool_name == "generate_images":
                    # Check for image generation
                    prompts = arguments.get("prompts", [])
                    create_collection = arguments.get("create_collection", True)
                    
                    if prompts:
                        images_result = generate_images(prompts, create_collection)
        
        # Add assistant response to history
        messages.append({"role": "assistant", "content": response_message.content})
        
        return response_message.content, audio_result, images_result
    except Exception as e:
        st.error(f"Error getting response: {str(e)}")
        error_message = f"I'm sorry, I encountered an error: {str(e)}"
        messages.append({"role": "assistant", "content": error_message})
        return error_message, None, None

def display_message(message, is_user=False, audio_file=None, images=None):
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
        content_html = f"<p>{message}</p>"
        
        # Add audio player if audio is available
        if audio_file:
            content_html += f"""
            <div class="audio-message">
                <audio class="audio-player" controls>
                    <source src="{get_audio_data_url(audio_file)}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
            </div>
            """
        
        # Create message without images first
        st.markdown(f"""
        <div class="chat-message assistant">
            <div class="avatar">🤖</div>
            <div class="content">
                {content_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display images if available
        if images and len(images) > 0:
            st.markdown("<div class='image-gallery'>", unsafe_allow_html=True)
            cols = st.columns(min(3, len(images)))
            
            for i, image_info in enumerate(images):
                if image_info["status"] == "success":
                    col = cols[i % len(cols)]
                    with col:
                        st.image(image_info["image_url"], caption=image_info["prompt"][:50] + "..." if len(image_info["prompt"]) > 50 else image_info["prompt"])
                        
                        # Add rating buttons if needed
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.button("1★", key=f"rate_img_{i}_1", on_click=lambda prompt=image_info["prompt"], rating=1: rate_image(prompt, rating))
                        with col2:
                            st.button("2★", key=f"rate_img_{i}_2", on_click=lambda prompt=image_info["prompt"], rating=2: rate_image(prompt, rating))
                        with col3:
                            st.button("3★", key=f"rate_img_{i}_3", on_click=lambda prompt=image_info["prompt"], rating=3: rate_image(prompt, rating))
                        with col4:
                            st.button("4★", key=f"rate_img_{i}_4", on_click=lambda prompt=image_info["prompt"], rating=4: rate_image(prompt, rating))
                        with col5:
                            st.button("5★", key=f"rate_img_{i}_5", on_click=lambda prompt=image_info["prompt"], rating=5: rate_image(prompt, rating))
            
            # If we have a collection URL, show it
            if images[0].get("collection_url"):
                st.markdown(f"[View all images in collection]({images[0]['collection_url']})")
            
            st.markdown("</div>", unsafe_allow_html=True)

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
    
    # API keys and clients
    if "elevenlabs_api_key" not in st.session_state:
        st.session_state.elevenlabs_api_key = ""
        
    if "elevenlabs_client" not in st.session_state:
        st.session_state.elevenlabs_client = None
    
    # Voice options
    if "voices" not in st.session_state:
        st.session_state.voices = []
        
    if "selected_voice_id" not in st.session_state:
        st.session_state.selected_voice_id = None
        
    if "selected_voice_data" not in st.session_state:
        st.session_state.selected_voice_data = None
    
    if "voice_settings" not in st.session_state:
        st.session_state.voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True,
            "speed": 1.0
        }
    
    # Conversation state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    if "user_learning" not in st.session_state:
        st.session_state.user_learning = None
    
    # UI state
    if "show_voice_selection" not in st.session_state:
        st.session_state.show_voice_selection = False
        
    if "voice_search_query" not in st.session_state:
        st.session_state.voice_search_query = ""
        
    if "show_image_generation" not in st.session_state:
        st.session_state.show_image_generation = False
    
    if "image_prompts" not in st.session_state:
        st.session_state.image_prompts = [""]
        
    if "active_feature" not in st.session_state:
        st.session_state.active_feature = None

# Callback functions
def set_elevenlabs_api_key():
    api_key = st.session_state.elevenlabs_api_key_input
    if api_key:
        st.session_state.elevenlabs_api_key = api_key
        st.session_state.elevenlabs_client = ElevenLabs(api_key=api_key)
        # Load voices automatically
        load_voices()
    else:
        st.error("Please enter a valid API key")

def load_voices():
    if st.session_state.elevenlabs_client:
        with st.spinner("Loading voices..."):
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

def toggle_image_generation():
    st.session_state.show_image_generation = not st.session_state.show_image_generation

def add_image_prompt():
    st.session_state.image_prompts.append("")

def remove_image_prompt(index):
    if len(st.session_state.image_prompts) > 1:
        st.session_state.image_prompts.pop(index)

def update_image_prompt(index, value):
    st.session_state.image_prompts[index] = value

def generate_images_from_ui():
    prompts = [p for p in st.session_state.image_prompts if p.strip()]
    if not prompts:
        st.error("Please enter at least one prompt")
        return
    
    results = generate_images(prompts)
    
    # Record in user learning
    if st.session_state.user_learning:
        for result in results:
            if result["status"] == "success":
                st.session_state.user_learning.record_image_generation(
                    result["prompt"],
                    result["image_url"]
                )
    
    # Add to chat history
    if any(result["status"] == "success" for result in results):
        # Count successful images
        success_count = sum(1 for result in results if result["status"] == "success")
        
        # Create user message
        prompts_text = "\n".join([f"- {p}" for p in prompts])
        user_message = f"Generate images with these prompts:\n{prompts_text}"
        
        # Create assistant message
        assistant_message = f"I've generated {success_count} out of {len(prompts)} images based on your prompts."
        
        # Add to messages
        st.session_state.messages.append({"role": "user", "content": user_message})
        st.session_state.messages.append({"role": "assistant", "content": assistant_message, "images": results})
        
        # Reset prompts
        st.session_state.image_prompts = [""]
        st.session_state.show_image_generation = False
    else:
        st.error("Failed to generate any images. Please try different prompts.")

def rate_voice(voice_id, rating):
    if st.session_state.user_learning:
        if st.session_state.user_learning.record_rating(voice_id, rating):
            st.success(f"Voice rated {rating}/5!")
            return True
    return False

def rate_image(prompt, rating):
    if st.session_state.user_learning:
        if st.session_state.user_learning.record_image_rating(prompt, rating):
            st.success(f"Image rated {rating}/5!")
            return True
    return False

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

def set_active_feature(feature):
    st.session_state.active_feature = feature

# Define system prompt
def get_system_prompt(username, selected_voice_name=None, user_learning=None):
    base_prompt = """
You are a creative assistant specializing in helping users create high-quality audio content and generate images. You guide users through script creation, voice selection, audio generation, and image generation with a conversational, helpful approach.

CORE PRINCIPLES:
1. GATHER COMPLETE INFORMATION before suggesting function calls
2. CONFIRM CRITICAL DETAILS explicitly before generating final outputs
3. ASK FOR CLARIFICATION when user responses are ambiguous
4. ENSURE SCRIPTS HAVE NO PLACEHOLDERS before generating audio
5. BUILD TOWARDS COMPLETION step by step

AUDIO CAPABILITIES:
- You can generate audio from your responses when users ask you to "speak this" or "generate audio"
- You can help users create scripts for various purposes
- You can explain voice characteristics and suggest options

IMAGE CAPABILITIES:
- You can generate images based on text prompts using Google Gemini
- You help users create effective image prompts
- You can create collections of related images

CONVERSATION TIPS:
- Ask about the purpose of their content
- Help refine scripts and prompts
- Explain different voice and image options
- Be conversational and friendly
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
            personalization.append(f"- User has generated {user_learning.preferences['total_generations']} audio clips previously.")
        
        if user_learning.preferences["total_image_generations"] > 0:
            personalization.append(f"- User has generated {user_learning.preferences['total_image_generations']} images previously.")
        
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
        
        st.markdown("### 🎙️ ElevenLabs Connection")
        
        if not st.session_state.elevenlabs_client:
            st.text_input("ElevenLabs API Key", type="password", key="elevenlabs_api_key_input")
            st.button("Connect", on_click=set_elevenlabs_api_key)
            st.markdown("""
            <small>Don't have an API key? Get one at <a href="https://elevenlabs.io/sign-up" target="_blank">elevenlabs.io</a></small>
            """, unsafe_allow_html=True)
        else:
            st.success("Connected to ElevenLabs ✓")
            if st.button("Change API Key"):
                st.session_state.elevenlabs_api_key = ""
                st.session_state.elevenlabs_client = None
                st.rerun()
        
        # Only show these options if authenticated
        if st.session_state.authenticated:
            st.markdown("### ⚙️ Options")
            
            # Voice selection button
            if st.session_state.elevenlabs_client:
                voice_btn_label = "Change Voice" if st.session_state.selected_voice_id else "Select Voice"
                if st.button(voice_btn_label):
                    toggle_voice_selection()
                    set_active_feature("voice")
            
            # Image generation button
            if st.button("Create Images"):
                toggle_image_generation()
                set_active_feature("image")
            
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
            <div class="icon">🎨</div>
            <h1>Creative Assistant</h1>
        </div>
        """, unsafe_allow_html=True)
        st.info("Please log in or continue as a guest to start using the Creative Assistant")
    elif not st.session_state.elevenlabs_client:
        st.markdown("""
        <div class="chat-header">
            <div class="icon">🎨</div>
            <h1>Creative Assistant</h1>
        </div>
        """, unsafe_allow_html=True)
        st.info("Please provide your ElevenLabs API key to enable voice generation")
        
        # Still allow chat without voice features
        chat_container = st.container()
        
        # Display chat messages
        with chat_container:
            # Welcome message if no messages yet
            if not st.session_state.messages:
                display_system_message(
                    "👋 Welcome to the Creative Assistant! I can help you generate images and create audio content. "
                    "To use all features, please connect your ElevenLabs API key in the sidebar."
                )
            
            # Display all messages
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    display_message(message["content"], is_user=True)
                elif message["role"] == "assistant":
                    # Get images if available
                    images = message.get("images")
                    
                    display_message(message["content"], is_user=False, images=images)
                elif message["role"] == "system":
                    display_system_message(message["content"])
            
        # Chat input
        user_input = st.chat_input("Type your message here...")
        
        # Process user input
        if user_input:
            # Get system prompt
            system_prompt = get_system_prompt(
                st.session_state.username,
                None,
                st.session_state.user_learning
            )
            
            # Add user message to state and display
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Record in user learning system
            if st.session_state.user_learning and len(st.session_state.messages) >= 2:
                last_assistant_message = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"), None)
                if last_assistant_message:
                    st.session_state.user_learning.record_conversation_turn(user_input, last_assistant_message)
            
            # Rerun to display user message
            st.rerun()
    else:
        # Chat header
        st.markdown("""
        <div class="chat-header">
            <div class="icon">🎨</div>
            <h1>Creative Assistant</h1>
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
        
        # Feature tabs
        if st.session_state.active_feature == "voice":
            st.session_state.show_voice_selection = True
            st.session_state.show_image_generation = False
        elif st.session_state.active_feature == "image":
            st.session_state.show_voice_selection = False
            st.session_state.show_image_generation = True
        
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
                            st.session_state.active_feature = None
                            
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                # Close button
                if st.button("Close Voice Selection"):
                    st.session_state.show_voice_selection = False
                    st.session_state.active_feature = None
        
        # Image generation interface
        if st.session_state.show_image_generation:
            st.markdown("### Create Images")
            
            # Instructions
            st.info("Enter one or more image prompts and click 'Generate Images' to create visuals with Google Gemini.")
            
            # Prompt inputs
            for i, prompt in enumerate(st.session_state.image_prompts):
                col1, col2 = st.columns([10, 1])
                with col1:
                    new_prompt = st.text_area(f"Prompt {i+1}", value=prompt, height=70, key=f"prompt_{i}")
                    update_image_prompt(i, new_prompt)
                with col2:
                    if len(st.session_state.image_prompts) > 1:
                        st.button("✖", key=f"remove_{i}", on_click=remove_image_prompt, args=(i,))
            
            # Add prompt button
            if len(st.session_state.image_prompts) < 5:  # Limit to 5 prompts
                st.button("+ Add Prompt", on_click=add_image_prompt)
            
            # Generation button
            if st.button("Generate Images"):
                generate_images_from_ui()
            
            # Close button
            if st.button("Close Image Creation"):
                st.session_state.show_image_generation = False
                st.session_state.active_feature = None
        
        # Chat message container
        chat_container = st.container()
        
        # Display chat messages
        with chat_container:
            # Welcome message if no messages yet
            if not st.session_state.messages:
                display_system_message(
                    "👋 Welcome to the Creative Assistant! I can help you create voice content and generate images. "
                    "How can I help you today?"
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
                    for j in range(i+1, len(st.session_state.messages)):
                        if st.session_state.messages[j]["role"] == "system" and isinstance(st.session_state.messages[j]["content"], dict):
                            if "audio_file" in st.session_state.messages[j]["content"]:
                                audio_file = st.session_state.messages[j]["content"]["audio_file"]
                                break
                    
                    # Get images if available
                    images = message.get("images")
                    
                    display_message(message["content"], is_user=False, audio_file=audio_file, images=images)
                elif message["role"] == "system":
                    # Skip system messages with audio files
                    if isinstance(message["content"], dict) and "audio_file" in message["content"]:
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
            typing_indicator = st.empty()
            typing_indicator.markdown("""
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
            
            # Get system prompt
            system_prompt = get_system_prompt(
                st.session_state.username,
                selected_voice_name,
                st.session_state.user_learning
            )
            
            # Process message and get response
            user_message = st.session_state.messages[-1]["content"]
            response_text, audio_result, images_result = process_message(
                user_message,
                system_prompt,
                [m for m in st.session_state.messages if m["role"] != "system"],  # Exclude system messages
                st.session_state.elevenlabs_client,
                st.session_state.selected_voice_id
            )
            
            # Clear typing indicator
            typing_indicator.empty()
            
            # Add response to session state
            assistant_message = {"role": "assistant", "content": response_text}
            
            # Add images if available
            if images_result:
                assistant_message["images"] = images_result
                
                # Record in user learning system
                if st.session_state.user_learning:
                    for result in images_result:
                        if result["status"] == "success":
                            st.session_state.user_learning.record_image_generation(
                                result["prompt"],
                                result["image_url"]
                            )
            
            st.session_state.messages.append(assistant_message)
            
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
