import streamlit as st
import os
import json
import hashlib
import uuid
from datetime import datetime
from PIL import Image as PILImage
import re
from typing import List, Dict, Any, Optional, Union
from io import BytesIO
import base64
import requests
from collections import Counter

# Import the necessary libraries
# from openai import OpenAI
from elevenlabs import ElevenLabs, VoiceSettings
from groq import Groq
from google import genai
from google.genai import types
from imagekitio import ImageKit

# Set page config
st.set_page_config(
    page_title="AI Content Creator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API clients based on environment variables or secrets
@st.cache_resource
def initialize_clients():
    # ElevenLabs
    elevenlabs_api_key = st.secrets.get("ELEVENLABS_API_KEY", "sk_d2f56a18a10228e786474237a7c303dbef9c977359622f29")
    elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)
    
    # Groq
    groq_api_key = st.secrets.get("GROQ_API_KEY", "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")
    os.environ["GROQ_API_KEY"] = groq_api_key
    groq_client = Groq()
    
    # Google Gemini
    gemini_api_key = st.secrets.get("GEMINI_API_KEY", "AIzaSyBLzfjImenFp60acvXgKygaEDKGqKfHyKI")
    gemini_client = genai.Client(api_key=gemini_api_key)
    
    # ImageKit
    imagekit = ImageKit(
        private_key=st.secrets.get("IMAGEKIT_PRIVATE_KEY", 'private_OGgux+C54n9PIYDlLdOrYysEWrw='),
        public_key=st.secrets.get("IMAGEKIT_PUBLIC_KEY", 'public_Qq9s197rBPKyx5eWhq+aN6TQ3Iw='),
        url_endpoint=st.secrets.get("IMAGEKIT_URL", 'https://ik.imagekit.io/b6pq3mgo7')
    )
    
    return {
        "elevenlabs": elevenlabs_client,
        "groq": groq_client,
        "gemini": gemini_client,
        "imagekit": imagekit
    }

# Initialize our clients
clients = initialize_clients()

# Create data directories
os.makedirs("users", exist_ok=True)
os.makedirs("sessions", exist_ok=True)
os.makedirs("user_data", exist_ok=True)
os.makedirs("generated_images", exist_ok=True)

# ====================== USER MANAGEMENT SYSTEM ======================
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
        
        # Hash the password (never store plaintext passwords)
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

# ====================== USER LEARNING SYSTEM ======================
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
            # No previous data, use defaults
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
    
    # ==== Voice Preference Methods ====
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
                    trait_value = clean_label_value(trait_value)
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
    
    # ==== Conversation Learning Methods ====
    def normalize_question(self, question):
        """Normalize a question for storage/comparison"""
        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r'\s+', ' ', question.lower().strip())
        
        # Remove specific details but keep the structure
        normalized = re.sub(r'\b\d+\b', 'NUM', normalized)  # Replace numbers
        
        return normalized
    
    def record_question_effectiveness(self, question, was_effective, context=None):
        """Record whether a question was effective at advancing the conversation"""
        # Normalize the question for storage
        norm_question = self.normalize_question(question)
        
        # Initialize if first time seeing this question
        if norm_question not in self.conversation_learning["effective_questions"]:
            self.conversation_learning["effective_questions"][norm_question] = {
                "effective_count": 0,
                "ineffective_count": 0,
                "contexts": {}
            }
        
        # Update effectiveness counters
        if was_effective:
            self.conversation_learning["effective_questions"][norm_question]["effective_count"] += 1
        else:
            self.conversation_learning["effective_questions"][norm_question]["ineffective_count"] += 1
        
        # If context is provided, track effectiveness in this context
        if context:
            context_key = context[:50]  # Use first 50 chars as key
            if context_key not in self.conversation_learning["effective_questions"][norm_question]["contexts"]:
                self.conversation_learning["effective_questions"][norm_question]["contexts"][context_key] = {
                    "effective_count": 0,
                    "ineffective_count": 0
                }
            
            if was_effective:
                self.conversation_learning["effective_questions"][norm_question]["contexts"][context_key]["effective_count"] += 1
            else:
                self.conversation_learning["effective_questions"][norm_question]["contexts"][context_key]["ineffective_count"] += 1
        
        # Save the updated data
        self.save_data()
    
    def record_user_response(self, question, response):
        """Record user's response to a question to learn patterns"""
        # Normalize the question
        norm_question = self.normalize_question(question)
        
        # Initialize if first time
        if norm_question not in self.conversation_learning["question_responses"]:
            self.conversation_learning["question_responses"][norm_question] = {
                "response_count": 0,
                "avg_length": 0,
                "sentiment": {"positive": 0, "negative": 0, "neutral": 0},
                "common_phrases": {},
                "examples": []
            }
        
        data = self.conversation_learning["question_responses"][norm_question]
        
        # Update counters and metrics
        data["response_count"] += 1
        
        # Update average length
        curr_avg = data["avg_length"]
        curr_count = data["response_count"] - 1  # Subtract 1 because we already incremented
        new_length = len(response)
        data["avg_length"] = (curr_avg * curr_count + new_length) / data["response_count"]
        
        # Simple sentiment analysis (very basic)
        sentiment = "neutral"
        positive_words = ["yes", "good", "great", "thanks", "helpful", "like", "perfect"]
        negative_words = ["no", "bad", "not", "don't", "wrong", "terrible", "unhelpful"]
        
        response_lower = response.lower()
        pos_count = sum(1 for word in positive_words if word in response_lower)
        neg_count = sum(1 for word in negative_words if word in response_lower)
        
        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        
        data["sentiment"][sentiment] += 1
        
        # Extract and count common phrases (simple version)
        words = re.findall(r'\b\w+\b', response_lower)
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            data["common_phrases"][phrase] = data["common_phrases"].get(phrase, 0) + 1
        
        # Store example (limited to 5)
        if len(data["examples"]) < 5:
            data["examples"].append(response[:100])  # Store first 100 chars
        
        # Save the updated data
        self.save_data()
    
    def record_conversation_turn(self, question, response, next_question, context=None):
        """Record a complete conversation turn to learn flow patterns"""
        # Add to conversation flows
        flow_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question[:100],  # Truncate for storage
            "response": response[:100],  # Truncate for storage
            "next_question": next_question[:100],  # Truncate for storage
            "context": context[:100] if context else None  # Truncate for storage
        }
        
        # Add to the flows (limit to last 50 for storage reasons)
        self.conversation_learning["conversation_flows"].append(flow_entry)
        if len(self.conversation_learning["conversation_flows"]) > 50:
            self.conversation_learning["conversation_flows"] = self.conversation_learning["conversation_flows"][-50:]
        
        # Update response patterns
        response_type = "short" if len(response) < 20 else "medium" if len(response) < 100 else "long"
        self.conversation_learning["user_response_patterns"][response_type] = self.conversation_learning["user_response_patterns"].get(response_type, 0) + 1
        
        # Extract potential topics
        topics = extract_topics(question + " " + response)
        for topic in topics:
            self.conversation_learning["topic_preferences"][topic] = self.conversation_learning["topic_preferences"].get(topic, 0) + 1
        
        # Update engagement metrics
        metrics = self.conversation_learning["engagement_metrics"]
        metrics["total_messages"] += 1
        metrics["avg_response_length"] = ((metrics["avg_response_length"] * (metrics["total_messages"]-1)) + len(response)) / metrics["total_messages"]
        
        # Save the updated data
        self.save_data()
    
    def get_question_recommendations(self, context, limit=3):
        """Get recommended questions based on past effectiveness"""
        # Find questions that were effective in similar contexts
        effective_questions = []
        
        # Extract potential topics from context
        topics = extract_topics(context)
        
        # For each question in our database
        for question, data in self.conversation_learning["effective_questions"].items():
            effectiveness_ratio = 0
            if data["effective_count"] + data["ineffective_count"] > 0:
                effectiveness_ratio = data["effective_count"] / (data["effective_count"] + data["ineffective_count"])
            
            # Check if question contains any topics from context
            topic_match = any(topic in question for topic in topics)
            
            # If question was generally effective or matches topics
            if effectiveness_ratio > 0.6 or topic_match:
                effective_questions.append((question, effectiveness_ratio))
        
        # Sort by effectiveness ratio
        effective_questions.sort(key=lambda x: x[1], reverse=True)
        
        # Return top recommendations
        return [q for q, _ in effective_questions[:limit]]
    
    def get_preferred_response_style(self):
        """Get the user's preferred response style based on their patterns"""
        if not self.conversation_learning["user_response_patterns"]:
            return "medium"  # Default if no data
        
        # Find the most common response type
        response_type, _ = max(
            self.conversation_learning["user_response_patterns"].items(),
            key=lambda x: x[1]
        )
        
        return response_type
    
    def get_favorite_topics(self, limit=3):
        """Get the user's favorite topics based on conversation history"""
        if not self.conversation_learning["topic_preferences"]:
            return []
        
        # Sort topics by frequency
        sorted_topics = sorted(
            self.conversation_learning["topic_preferences"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return top topics
        return [topic for topic, _ in sorted_topics[:limit]]
    
    def generate_personalized_prompt_addition(self):
        """Generate personalized additions to the system prompt based on learning"""
        prompt_parts = []
        
        # Add voice preferences if available
        if self.preferences["total_generations"] > 0:
            preferred_traits = self.get_preferred_traits()
            trait_text = ", ".join(preferred_traits) if preferred_traits else "No strong voice preferences yet"
            prompt_parts.append(f"This user has generated {self.preferences['total_generations']} audio clips previously. Their preferred voice traits appear to be: {trait_text}")
        
        # Add image generation info if available
        if self.preferences["total_image_generations"] > 0:
            prompt_parts.append(f"This user has generated {self.preferences['total_image_generations']} images previously.")
        
        # Add conversation style preferences if available
        if self.conversation_learning["user_response_patterns"]:
            response_style = self.get_preferred_response_style()
            prompt_parts.append(f"This user tends to give {response_style} responses. Adjust your questioning style accordingly.")
        
        # Add topic preferences if available
        favorite_topics = self.get_favorite_topics()
        if favorite_topics:
            topics_text = ", ".join(favorite_topics)
            prompt_parts.append(f"This user has shown interest in these topics: {topics_text}")
        
        # Add engagement level information
        metrics = self.conversation_learning["engagement_metrics"]
        if metrics["total_messages"] > 10:
            avg_length = round(metrics["avg_response_length"])
            prompt_parts.append(f"This user's average response is {avg_length} characters long.")
        
        # Combine all parts
        if prompt_parts:
            return "PERSONALIZATION:\n" + "\n".join(prompt_parts)
        
        return ""

# ====================== CORE FUNCTIONS ======================

# Function to list ElevenLabs voices
def list_elevenlabs_voices(page_size=100, max_pages=10):
    elevenlabs_client = clients["elevenlabs"]
    voices_info = []
    next_page_token = ""

    for page_num in range(max_pages):
        response = elevenlabs_client.voices.search(
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

    return voices_info

# Function to generate audio
def generate_elevenlabs_audio(voice_id, text, voice_settings=None):
    elevenlabs_client = clients["elevenlabs"]
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
        audio = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=applied_settings
        )
        
        # In Streamlit, we'll keep the audio in memory instead of writing to disk
        audio_bytes = b""
        for chunk in audio:
            audio_bytes += chunk
            
        return {
            "status": "success", 
            "audio_bytes": audio_bytes, 
            "text_length": len(text)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Function to generate images
def generate_images(prompts, create_collection=True):
    """Generate images using Google Gemini and upload to ImageKit"""
    gemini_client = clients["gemini"]
    imagekit = clients["imagekit"]

    if isinstance(prompts, str):
        prompts = [prompts]  # Convert single prompt to list

    # Create lists to store image information
    image_urls = []
    image_file_ids = []
    image_bytes_list = []
    error_messages = []

    # Process each prompt
    for i, prompt in enumerate(prompts):
        try:
            print(f"Processing prompt {i+1}/{len(prompts)}: {prompt[:50]}...")

            # Generate content using Gemini API
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )

            print(f"Received response for prompt {i+1}")

            # Check if we have a valid response
            if not response.candidates or not response.candidates[0].content.parts:
                error_msg = f"No valid content in response for prompt {i+1}"
                print(error_msg)
                error_messages.append(error_msg)
                image_urls.append(None)
                image_file_ids.append(None)
                image_bytes_list.append(None)
                continue

            # Process results
            image_found = False
            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None):
                    image_found = True
                    print(f"Found image data in response for prompt {i+1}")

                    # Get image data
                    image_data = BytesIO(part.inline_data.data)
                    image_bytes_list.append(image_data.getvalue())

                    # Upload to ImageKit
                    try:
                        print(f"Uploading image {i+1} to ImageKit")
                        upload = imagekit.upload(
                            file=image_data,
                            file_name=f"image-{uuid.uuid4().hex[:8]}.png"
                        )

                        print(f"Successfully uploaded image {i+1}")
                        image_urls.append(upload.url)
                        image_file_ids.append(upload.file_id)
                    except Exception as upload_error:
                        error_msg = f"Error uploading to ImageKit for prompt {i+1}: {str(upload_error)}"
                        print(error_msg)
                        error_messages.append(error_msg)
                        image_urls.append(None)
                        image_file_ids.append(None)

            if not image_found:
                error_msg = f"No image found in response for prompt {i+1}"
                print(error_msg)
                error_messages.append(error_msg)
                image_urls.append(None)
                image_file_ids.append(None)
                image_bytes_list.append(None)

        except Exception as general_error:
            error_msg = f"Error in image generation for prompt {i+1}: {str(general_error)}"
            print(error_msg)
            error_messages.append(error_msg)
            image_urls.append(None)
            image_file_ids.append(None)
            image_bytes_list.append(None)

    collection_url = None
    # Create a collection link if requested and we have images
    if create_collection and any(url is not None for url in image_urls):
        try:
            print("Creating image collection")
            collection_url = create_image_collection(image_urls, "Generated Images Collection")
            print(f"Collection created with URL: {collection_url}")
        except Exception as collection_error:
            error_msg = f"Error creating collection: {str(collection_error)}"
            print(error_msg)
            error_messages.append(error_msg)

    # Return results
    results = []
    for i, prompt in enumerate(prompts):
        if i < len(image_urls) and image_urls[i]:
            file_id = image_file_ids[i] if i < len(image_file_ids) else None
            image_bytes = image_bytes_list[i] if i < len(image_bytes_list) else None

            results.append({
                "prompt": prompt,
                "image_url": image_urls[i],
                "image_bytes": image_bytes,
                "file_id": file_id,
                "collection_url": collection_url,
                "status": "success"
            })
            print(f"Successfully generated image for prompt {i+1}")
        else:
            results.append({
                "prompt": prompt,
                "status": "error",
                "message": error_messages[i] if i < len(error_messages) else "Failed to generate or upload image"
            })
            print(f"Failed to generate image for prompt {i+1}")

    return results


# Function to create image collection
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

# ====================== HELPER FUNCTIONS ======================

# Function to manage conversation history
def manage_conversation_history(messages, max_turns=10):
    """Keep conversation history manageable to control token usage"""
    if len(messages) <= max_turns + 2:  # +2 for system and first user message
        return messages
    
    # Keep system prompt, first user message, and last max_turns messages
    system_prompt = messages[0]
    first_user_message = next((m for m in messages if m["role"] == "user"), None)
    recent_messages = messages[-(max_turns):]
    
    # Create a summary message for context
    conversation_summary = {
        "role": "system",
        "content": f"Previous conversation contained {len(messages) - len(recent_messages) - 2} turns that have been summarized to save tokens."
    }
    
    # Build new messages array
    pruned_messages = [system_prompt]
    if first_user_message:
        pruned_messages.append(first_user_message)
    pruned_messages.append(conversation_summary)
    pruned_messages.extend(recent_messages)
    
    return pruned_messages

# Function to extract voice ID from user input
def extract_voice_id(user_input, stored_voices):
    """Extract voice ID based on user input (either by name or number)"""
    if not stored_voices:
        return None
    
    # Check if user mentioned a voice by name
    for voice in stored_voices:
        if voice["name"].lower() in user_input.lower():
            return voice["voice_id"]
    
    # Check if user mentioned a number
    number_match = re.search(r'\b(\d+)\b', user_input)
    if number_match:
        number = int(number_match.group(1))
        # Convert to 0-based index
        index = number - 1
        if 0 <= index < len(stored_voices):
            return stored_voices[index]["voice_id"]
    
    return None

# Helper function to extract potential topics from text
def extract_topics(text):
    """Extract potential topics from text (simple version)"""
    # A simple implementation - in production you'd use NLP
    common_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "are", "was", "were"]
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out common words and count occurrences
    word_counts = Counter(word for word in words if word not in common_words and len(word) > 3)
    
    # Return top words as potential topics
    return [word for word, _ in word_counts.most_common(5)]

# Helper function to clean a label value
def clean_label_value(value):
    if not value:
        return ""
    # Replace underscores with hyphens
    value = value.replace("_", "-")
    return value

# ====================== UI COMPONENTS ======================

# Custom message container for displaying audio/image content
def display_message(role, content, voice_data=None, image_data=None):
    """Display a chat message with optional audio or image content"""
    if role == "user":
        # User message - right side
        with st.chat_message("user"):
            st.write(content)
    else:
        # Assistant message - left side with possible media
        with st.chat_message("assistant"):
            st.write(content)
            
            # Display audio if available
            if voice_data:
                if "preview_url" in voice_data:
                    st.audio(voice_data["preview_url"])
                    st.caption(f"👆 Preview of {voice_data.get('name', 'the voice')}")
                
                if "audio_bytes" in voice_data:
                    st.audio(voice_data["audio_bytes"])
                    st.caption(f"👆 Generated audio with {voice_data.get('name', 'the selected voice')}")
            
            # Display image if available
            if image_data:
                for img in image_data:
                    if img.get("status") == "success" and img.get("image_url"):
                        st.image(img["image_url"])
                        st.caption(f"Prompt: {img.get('prompt', 'No prompt provided')}")
                
                # Display collection link if available
                collection_url = next((img.get("collection_url") for img in image_data if img.get("collection_url")), None)
                if collection_url:
                    st.markdown(f"[View all images in collection]({collection_url})")

# Function to create a rating interface
def display_rating_interface(item_type, item_id, item_name=None):
    """Display a rating interface for voice or image"""
    item_desc = item_name if item_name else f"this {item_type}"
    
    st.write(f"How would you rate {item_desc}? (1-5 stars)")
    cols = st.columns(5)
    rating = None
    
    for i, col in enumerate(cols, 1):
        if col.button(f"⭐ {i}", key=f"rating_{item_type}_{item_id}_{i}"):
            rating = i
    
    return rating

# Function to display voice selection interface
def display_voice_selection(voices):
    """Display a grid of voice options with audio previews"""
    st.write("Select a voice for your content:")
    
    # Display voices in a grid
    cols = st.columns(3)
    selected_voice_id = None
    
    for i, voice in enumerate(voices):
        col = cols[i % 3]
        with col:
            st.subheader(voice["name"])
            
            # Display labels if available
            labels = voice.get("labels", {})
            accent = clean_label_value(labels.get("accent", ""))
            age = clean_label_value(labels.get("age", ""))
            gender = clean_label_value(labels.get("gender", ""))
            
            description_parts = []
            if accent:
                description_parts.append(accent)
            if age:
                description_parts.append(age)
            if gender:
                description_parts.append(gender)
            
            description = ", ".join(description_parts) if description_parts else "No description available"
            st.caption(description)
            
            # Display preview if available
            if voice.get("preview_url"):
                st.audio(voice["preview_url"])
            
            # Button to select this voice
            if st.button(f"Select {voice['name']}", key=f"select_voice_{voice['voice_id']}"):
                selected_voice_id = voice["voice_id"]
    
    return selected_voice_id

# ====================== STREAMLIT APP SETUP ======================

# Initialize session state
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False
    st.session_state.username = None
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.conversation_state = {
        "last_assistant_message": None,
        "last_user_message": None,
        "current_context": None,
        "script_development_stage": "initial",  # initial, developing, finalizing
        "voice_selection_stage": "not_started",  # not_started, showing, selected
        "image_generation_stage": "not_started"  # not_started, prompting, generated
    }
    st.session_state.stored_voices = None
    st.session_state.function_call_history = {
        "list_elevenlabs_voices": False,
        "generate_elevenlabs_audio": False,
        "generate_images": False
    }
    st.session_state.last_generated_audio = {
        "voice_id": None,
        "text": None
    }
    st.session_state.last_generated_images = {
        "prompts": []
    }
    st.session_state.pending_feedback = {
        "needed": False,
        "type": None,  # "voice" or "image"
        "voice_id": None,
        "voice_name": None,
        "image_prompt": None
    }
    st.session_state.user_learning = None

# Initialize user manager
user_manager = UserManager()

# Authentication UI
if not st.session_state.user_authenticated:
    st.title("AI Content Creator")
    st.subheader("Welcome! Please log in or create an account")
    
    with st.expander("Login", expanded=True):
        auth_tab1, auth_tab2, auth_tab3 = st.tabs(["Login", "Create Account", "Continue as Guest"])
        
        with auth_tab1:
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", key="login_button"):
                if login_username and login_password:
                    success, result = user_manager.login(login_username, login_password)
                    if success:
                        st.session_state.user_authenticated = True
                        st.session_state.username = login_username
                        st.session_state.session_id = result
                        st.session_state.user_learning = UserLearningSystem(login_username)
                        st.success(f"Welcome back, {login_username}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
        
        with auth_tab2:
            new_username = st.text_input("Choose a username", key="new_username")
            new_password = st.text_input("Choose a password", type="password", key="new_password")
            confirm_password = st.text_input("Confirm password", type="password", key="confirm_password")
            
            if st.button("Create Account", key="create_account_button"):
                if new_username and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Passwords don't match")
                    else:
                        success, message = user_manager.create_user(new_username, new_password)
                        if success:
                            # Auto-login
                            success, result = user_manager.login(new_username, new_password)
                            if success:
                                st.session_state.user_authenticated = True
                                st.session_state.username = new_username
                                st.session_state.session_id = result
                                st.session_state.user_learning = UserLearningSystem(new_username)
                                st.success(f"Account created! Welcome, {new_username}!")
                                st.rerun()
                        else:
                            st.error(message)
                else:
                    st.warning("Please fill out all fields")
        
        with auth_tab3:
            if st.button("Continue as Guest", key="guest_button"):
                guest_id = f"guest_{uuid.uuid4().hex[:8]}"
                st.session_state.user_authenticated = True
                st.session_state.username = guest_id
                st.session_state.user_learning = UserLearningSystem(guest_id)
                st.success(f"Continuing as Guest ({guest_id})")
                st.rerun()

else:
    # Main application UI after authentication
    st.title("AI Content Creator")
    st.subheader(f"Hello, {st.session_state.username}!")
    
    # Initialize system prompt
    if "system_prompt" not in st.session_state:
        base_system_prompt = """
You are a creative assistant specializing in helping users create high-quality audio content and generate images. You guide users through script creation, voice selection, audio generation, and image generation with a conversational, helpful approach.

CORE PRINCIPLES:
1. GATHER COMPLETE INFORMATION before suggesting function calls
2. CONFIRM CRITICAL DETAILS explicitly before generating final outputs
3. ASK FOR CLARIFICATION when user responses are ambiguous
4. USE AUDIO PREVIEWS when showing voice options
5. ENSURE SCRIPTS HAVE NO PLACEHOLDERS before generating audio
6. BUILD TOWARDS COMPLETION step by step

AUDIO CAPABILITIES:
- Guide users through script creation for audio content
- Help users select appropriate voices for their content
- Generate audio content with selected voices

IMAGE CAPABILITIES:
- Generate images based on user's text prompts
- Create image collections for multiple generated images
- Provide shareable links for image collections

FUNCTION USAGE:
- list_elevenlabs_voices: Call ONLY ONCE unless explicitly asked to show voices again
- generate_elevenlabs_audio: Call ONLY after confirming both script and voice
- generate_images: Call when the user asks for image generation with clear prompts

Remember that brief user responses like "ok" or "sounds good" are often acknowledgments, not requests for action. Always clarify ambiguous responses before calling functions.
"""
        # Add personalization if available
        personalized_prompt = st.session_state.user_learning.generate_personalized_prompt_addition()
        if personalized_prompt:
            st.session_state.system_prompt = base_system_prompt + "\n\n" + personalized_prompt
        else:
            st.session_state.system_prompt = base_system_prompt
        
        # Initialize messages with system prompt
        st.session_state.messages = [{"role": "system", "content": st.session_state.system_prompt}]
    
    # Sidebar for settings and history
    with st.sidebar:
        st.header("Settings")
        
        # Voice settings slider
        st.subheader("Voice Settings")
        voice_stability = st.slider("Stability", 0.0, 1.0, 0.5, 0.01)
        similarity_boost = st.slider("Similarity Boost", 0.0, 1.0, 0.5, 0.01)
        style = st.slider("Style", 0.0, 1.0, 0.0, 0.01)
        speed = st.slider("Speed", 0.7, 1.2, 1.0, 0.01)
        speaker_boost = st.checkbox("Speaker Boost", False)
        
        # Option to clear chat history
        if st.button("Clear Chat History"):
            st.session_state.messages = [{"role": "system", "content": st.session_state.system_prompt}]
            st.session_state.conversation_state = {
                "last_assistant_message": None,
                "last_user_message": None,
                "current_context": None,
                "script_development_stage": "initial",
                "voice_selection_stage": "not_started",
                "image_generation_stage": "not_started"
            }
            st.session_state.function_call_history = {
                "list_elevenlabs_voices": False,
                "generate_elevenlabs_audio": False,
                "generate_images": False
            }
            st.rerun()
        
        # Logout button
        if st.button("Logout"):
            # Save user data before logout
            if st.session_state.user_learning:
                st.session_state.user_learning.save_data()
            
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            st.rerun()
        
        # Show user preferences summary
        if st.session_state.user_learning:
            st.subheader("Your Preferences")
            
            # Show voice preferences
            voice_count = st.session_state.user_learning.preferences["total_generations"]
            st.write(f"Total audio generations: {voice_count}")
            
            preferred_traits = st.session_state.user_learning.get_preferred_traits()
            if preferred_traits:
                st.write("Preferred voice traits:")
                for trait in preferred_traits:
                    st.write(f"- {trait}")
            
            # Show image preferences
            image_count = st.session_state.user_learning.preferences["total_image_generations"]
            st.write(f"Total image generations: {image_count}")
    
    # Display chat history
    for message in st.session_state.messages:
        if message["role"] != "system" and message["role"] != "function":
            display_message(message["role"], message["content"])
            
    #show json
    if st.button("Show Chat Session JSON"):
        st.json(st.session_state.messages)

    # Check for and process pending feedback
    if st.session_state.pending_feedback["needed"]:
        with st.container():
            feedback_type = st.session_state.pending_feedback["type"]
            
            if feedback_type == "voice":
                voice_id = st.session_state.pending_feedback["voice_id"]
                voice_name = st.session_state.pending_feedback["voice_name"]
                
                st.write(f"How would you rate {voice_name}'s voice? (1-5)")
                cols = st.columns(5)
                for i, col in enumerate(cols):
                    if col.button(f"{i+1} ⭐", key=f"voice_rating_{i+1}"):
                        st.session_state.user_learning.record_rating(voice_id, i+1)
                        st.session_state.pending_feedback["needed"] = False
                        st.rerun()
            
            elif feedback_type == "image":
                image_prompt = st.session_state.pending_feedback["image_prompt"]
                
                st.write("How would you rate the generated image? (1-5)")
                cols = st.columns(5)
                for i, col in enumerate(cols):
                    if col.button(f"{i+1} ⭐", key=f"image_rating_{i+1}"):
                        st.session_state.user_learning.record_image_rating(image_prompt, i+1)
                        st.session_state.pending_feedback["needed"] = False
                        st.rerun()
    
    # User input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Update conversation state
        st.session_state.conversation_state["last_user_message"] = user_input
        
        # Record user response for learning if we have a previous assistant message
        if st.session_state.conversation_state["last_assistant_message"]:
            st.session_state.user_learning.record_user_response(
                st.session_state.conversation_state["last_assistant_message"],
                user_input
            )
        
        # Check if user is selecting a voice by name or number
        selected_voice_id = extract_voice_id(user_input, st.session_state.stored_voices)
        if selected_voice_id and st.session_state.stored_voices:
            # Find the corresponding voice data
            selected_voice = next((v for v in st.session_state.stored_voices if v["voice_id"] == selected_voice_id), None)
            if selected_voice:
                # Record this voice selection in user preferences
                st.session_state.user_learning.record_voice_selection(selected_voice_id, selected_voice)
                
                # Update conversation state
                st.session_state.conversation_state["voice_selection_stage"] = "selected"
        
        # Check if this is a request to see voices again
        is_voice_request = re.search(r'(show|list|hear|voice|preview).*(voice|again)', user_input.lower()) is not None
        
        # Check if this is a request to generate images
        is_image_request = re.search(r'(generate|create|make).*(image|picture|photo)', user_input.lower()) is not None
        if is_image_request:
            st.session_state.conversation_state["image_generation_stage"] = "prompting"
        
        # Display user message in chat
        display_message("user", user_input)
        
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Prepare function specifications for the LLM
        function_specs = [
            {
                "name": "list_elevenlabs_voices",
                "description": "List available ElevenLabs voices with preview URLs. Only call this ONCE per conversation unless the user explicitly asks to see the voices again.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_size": {"type": "integer"},
                        "max_pages": {"type": "integer"}
                    }
                }
            },
            {
                "name": "generate_elevenlabs_audio",
                "description": "Generate audio from text using ElevenLabs. Only call this when you have confirmed the final script (with no placeholders) and specific voice selection with the user.",
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
                "description": "Generate images based on text prompts using Google Gemini. Only call this when the user has explicitly requested image generation and has provided clear prompts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompts": {
                            "type": "array",
                            "description": "List of prompts to generate images for (1-5 prompts recommended)",
                            "items": {
                                "type": "string"
                            }
                        },
                        "create_collection": {
                            "type": "boolean",
                            "description": "Whether to create a collection link for all generated images"
                        }
                    },
                    "required": ["prompts"]
                }
            }
        ]
        
        # Apply token-saving conversation history management
        temp_messages = manage_conversation_history(st.session_state.messages)
        
        # Add guidance for function calls if needed
        if st.session_state.function_call_history["list_elevenlabs_voices"] and not is_voice_request:
            guidance_message = {
                "role": "system", 
                "content": "NOTE: Voice list has already been provided once in this conversation. Only call list_elevenlabs_voices again if the user explicitly asks to see the voices again."
            }
            temp_messages = temp_messages + [guidance_message]
            
        # Add learning-based recommendations if appropriate
        if st.session_state.conversation_state["script_development_stage"] == "developing":
            # Get question recommendations for script development
            recommendations = st.session_state.user_learning.get_question_recommendations(
                user_input,  # Use the latest user input as context
                limit=2
            )
            
            if recommendations:
                rec_msg = "Based on what has worked well in the past, consider asking: " + " OR ".join(recommendations)
                temp_messages.append({
                    "role": "system",
                    "content": rec_msg
                })
        
        # Show a spinner while processing
        with st.spinner("Thinking..."):
            # Call the LLM
            groq_client = clients["groq"]
            response = groq_client.chat.completions.create(
                model="deepseek-r1-distill-llama-70b",
                messages=temp_messages,
                functions=function_specs,
                function_call="auto",
                max_tokens=4096
            )
            
            response_message = response.choices[0].message
            
            # Check if the assistant wants to call a function
            if hasattr(response_message, "function_call") and response_message.function_call:
                function_name = response_message.function_call.name
                arguments = json.loads(response_message.function_call.arguments)
                
                # Handle assistant's text response (if any)
                if response_message.content:
                    display_message("assistant", response_message.content)
                    
                    # Update conversation state
                    st.session_state.conversation_state["last_assistant_message"] = response_message.content
                    
                    # Add to session state message history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_message.content
                    })
                
                # Validation for function calls
                should_block_call = False
                block_reason = ""
                
                if function_name == "list_elevenlabs_voices":
                    if st.session_state.function_call_history[function_name] and not is_voice_request:
                        should_block_call = True
                        block_reason = "Voice list already provided. Using cached data instead."
                    else:
                        # Update conversation state
                        st.session_state.conversation_state["voice_selection_stage"] = "showing"
                
                elif function_name == "generate_elevenlabs_audio":
                    # Check for placeholders
                    script_has_placeholders = bool(re.search(r'\[.*?\]', arguments["text"]))
                    
                    if script_has_placeholders:
                        should_block_call = True
                        block_reason = "Script contains placeholders that need to be replaced."
                    
                    # Check for duplicate audio generation
                    if (st.session_state.last_generated_audio["voice_id"] == arguments["voice_id"] and 
                        st.session_state.last_generated_audio["text"] == arguments["text"] and
                        st.session_state.function_call_history[function_name]):
                        should_block_call = True
                        block_reason = "This exact audio has already been generated."
                
                elif function_name == "generate_images":
                    # Check if we have prompts
                    if not arguments.get("prompts") or len(arguments["prompts"]) == 0:
                        should_block_call = True
                        block_reason = "No image prompts provided."
                    
                    # Check for duplicate image generation
                    prompts = arguments.get("prompts", [])
                    if all(prompt in st.session_state.last_generated_images["prompts"] for prompt in prompts):
                        should_block_call = True
                        block_reason = "These exact images have already been generated."
                
                # Handle function call or blocking
                if should_block_call:
                    if function_name == "list_elevenlabs_voices" and st.session_state.function_call_history[function_name]:
                        # Use stored voice data for display
                        if st.session_state.stored_voices:
                            voices_intro = "Here are the available voices for your project. Please let me know which voice number or name you'd like to use."
                            display_message("assistant", voices_intro)
                            
                            # Maybe add a more interactive UI here to redisplay voices
                            voice_previews = []
                            for i, voice in enumerate(st.session_state.stored_voices):
                                if voice.get("preview_url"):
                                    voice_previews.append({
                                        "name": voice["name"],
                                        "preview_url": voice["preview_url"]
                                    })
                            
                            if voice_previews:
                                with st.container():
                                    cols = st.columns(3)
                                    for i, preview in enumerate(voice_previews[:6]):  # Limit to 6 previews for UI space
                                        with cols[i % 3]:
                                            st.caption(f"{i+1}. {preview['name']}")
                                            st.audio(preview["preview_url"])
                            
                            # Update state
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": voices_intro
                            })
                            st.session_state.conversation_state["last_assistant_message"] = voices_intro
                        else:
                            assistant_message = "I have voice information available. Would you like me to show it to you?"
                            display_message("assistant", assistant_message)
                            
                            # Update state
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": assistant_message
                            })
                            st.session_state.conversation_state["last_assistant_message"] = assistant_message
                    else:
                        # Add error message to messages for LLM context
                        st.session_state.messages.append({
                            "role": "function",
                            "name": function_name,
                            "content": json.dumps({
                                "error": block_reason,
                                "status": "blocked"
                            })
                        })
                        
                        # Display error to user
                        error_message = f"I couldn't complete that action: {block_reason}"
                        display_message("assistant", error_message)
                        
                        # Update state
                        st.session_state.conversation_state["last_assistant_message"] = error_message
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_message
                        })
                else:
                    # Execute the function
                    if function_name == "list_elevenlabs_voices":
                        # Get voices with a progress indicator
                        with st.status("Fetching voices..."):
                            page_size = arguments.get("page_size", 100)
                            max_pages = arguments.get("max_pages", 10)
                            
                            voices = list_elevenlabs_voices(page_size=page_size, max_pages=max_pages)
                            st.session_state.stored_voices = voices
                            st.session_state.function_call_history[function_name] = True
                        
                        # Check if we have preferred voices to highlight
                        preferred_voice_ids = st.session_state.user_learning.get_preferred_voices()
                        
                        # Create a personalized message if user has preferences
                        if preferred_voice_ids and len(preferred_voice_ids) > 0:
                            # Find preferred voice names
                            preferred_names = []
                            for voice in voices:
                                if voice["voice_id"] in preferred_voice_ids:
                                    preferred_names.append(voice["name"])
                            
                            if preferred_names:
                                preferred_text = ", ".join(preferred_names)
                                assistant_message = f"I've found {len(voices)} voices that you can use. Based on your previous choices, you might like these voices: {preferred_text}. They're listed first in the selection."
                            else:
                                assistant_message = f"I've found {len(voices)} voices that you can use for your audio content. Please let me know which voice you'd like to use."
                        else:
                            assistant_message = f"I've found {len(voices)} voices that you can use for your audio content. Please let me know which voice number or name you'd like to use."
                        
                        # Display message
                        display_message("assistant", assistant_message)
                        
                        # Display voice selection interface
                        with st.container():
                            st.write("Voice options (preview first few):")
                            
                            # Show a subset of voices with previews
                            display_voices = voices[:9]  # Show first 9 voices
                            
                            # Prioritize preferred voices if available
                            if preferred_voice_ids:
                                # Move preferred voices to the front
                                preferred_voices = [v for v in voices if v["voice_id"] in preferred_voice_ids]
                                other_voices = [v for v in voices if v["voice_id"] not in preferred_voice_ids]
                                display_voices = preferred_voices + other_voices
                                display_voices = display_voices[:9]  # Still limit to 9
                            
                            # Display in a grid
                            cols = st.columns(3)
                            for i, voice in enumerate(display_voices):
                                with cols[i % 3]:
                                    st.subheader(f"{i+1}. {voice['name']}")
                                    
                                    # Display labels if available
                                    labels = voice.get("labels", {})
                                    accent = clean_label_value(labels.get("accent", ""))
                                    age = clean_label_value(labels.get("age", ""))
                                    gender = clean_label_value(labels.get("gender", ""))
                                    
                                    description_parts = []
                                    if accent:
                                        description_parts.append(accent)
                                    if age:
                                        description_parts.append(age)
                                    if gender:
                                        description_parts.append(gender)
                                    
                                    description = ", ".join(description_parts) if description_parts else "No description available"
                                    st.caption(description)
                                    
                                    # Display preview if available
                                    if voice.get("preview_url"):
                                        st.audio(voice["preview_url"])
                        
                        # Add to state
                        st.session_state.messages.append({
                            "role": "function",
                            "name": function_name,
                            "content": json.dumps({
                                "voices": voices,
                                "count": len(voices)
                            })
                        })
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": assistant_message
                        })
                        
                        st.session_state.conversation_state["last_assistant_message"] = assistant_message
                    
                    elif function_name == "generate_elevenlabs_audio":
                        # Update script development stage
                        st.session_state.conversation_state["script_development_stage"] = "finalizing"
                        
                        # Get voice settings from sidebar
                        voice_settings = {
                            "stability": voice_stability,
                            "similarity_boost": similarity_boost,
                            "style": style,
                            "use_speaker_boost": speaker_boost,
                            "speed": speed
                        }
                        
                        # Generate the audio
                        with st.status("Generating audio..."):
                            result = generate_elevenlabs_audio(
                                voice_id=arguments["voice_id"],
                                text=arguments["text"],
                                voice_settings=voice_settings
                            )
                        
                        # Update tracking
                        st.session_state.function_call_history[function_name] = True
                        st.session_state.last_generated_audio["voice_id"] = arguments["voice_id"]
                        st.session_state.last_generated_audio["text"] = arguments["text"]
                        
                        # Find voice name
                        voice_name = "Unknown"
                        selected_voice = None
                        for voice in st.session_state.stored_voices or []:
                            if voice["voice_id"] == arguments["voice_id"]:
                                voice_name = voice["name"]
                                selected_voice = voice
                                break
                        
                        # Format response message
                        if result["status"] == "success":
                            assistant_message = f"Great! I've generated the audio using {voice_name}'s voice."
                            
                            # Record generation in user preferences
                            st.session_state.user_learning.record_script_generation(
                                arguments["voice_id"],
                                arguments["text"]
                            )
                            
                            # Record voice selection
                            if selected_voice:
                                st.session_state.user_learning.record_voice_selection(
                                    arguments["voice_id"],
                                    selected_voice
                                )
                            
                            # Mark question as effective since we reached audio generation
                            if st.session_state.conversation_state["last_assistant_message"]:
                                st.session_state.user_learning.record_question_effectiveness(
                                    st.session_state.conversation_state["last_assistant_message"],
                                    True,
                                    context=st.session_state.conversation_state["current_context"]
                                )
                            
                            # Set feedback collection for the next message
                            st.session_state.pending_feedback = {
                                "needed": True,
                                "type": "voice",
                                "voice_id": arguments["voice_id"],
                                "voice_name": voice_name,
                                "image_prompt": None
                            }
                        else:
                            assistant_message = f"I encountered an error while generating audio: {result.get('message', 'Unknown error')}."
                        
                        # Display message and audio
                        voice_data = {"name": voice_name}
                        if result["status"] == "success":
                            voice_data["audio_bytes"] = result["audio_bytes"]
                        
                        display_message("assistant", assistant_message, voice_data=voice_data)
                        
                        # Add to state
                        st.session_state.messages.append({
                            "role": "function",
                            "name": function_name,
                            "content": json.dumps({
                                "status": result["status"],
                                "message": result.get("message", ""),
                                "text_length": result.get("text_length", 0)
                            })
                        })
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": assistant_message
                        })
                        
                        st.session_state.conversation_state["last_assistant_message"] = assistant_message
                    
                    elif function_name == "generate_images":
                        # Update image generation stage
                        st.session_state.conversation_state["image_generation_stage"] = "generated"
                        
                        # Get prompts
                        prompts = arguments.get("prompts", [])
                        create_collection = arguments.get("create_collection", True)
                        
                        # Generate images
                        with st.status(f"Generating {len(prompts)} images..."):
                            results = generate_images(prompts, create_collection)
                        
                        # Update tracking
                        st.session_state.function_call_history[function_name] = True
                        st.session_state.last_generated_images["prompts"] = prompts
                        
                        # Format response message
                        if any(result["status"] == "success" for result in results):
                            # Count successful images
                            success_count = sum(1 for result in results if result["status"] == "success")
                            collection_url = next((result["collection_url"] for result in results if result.get("collection_url")), None)
                            
                            # Create message
                            message_parts = [f"I've successfully generated {success_count} out of {len(prompts)} images based on your prompts."]
                            
                            # Add collection URL if available
                            if collection_url:
                                message_parts.append(f"You can view all the images in this collection: {collection_url}")
                            else:
                                message_parts.append("The images are available to view individually.")
                            
                            # Combine message parts
                            assistant_message = " ".join(message_parts)
                            
                            # Record successful generations in user preferences
                            for result in results:
                                if result["status"] == "success":
                                    st.session_state.user_learning.record_image_generation(
                                        result["prompt"],
                                        result["image_url"]
                                    )
                            
                            # Set feedback collection for the next message (using first prompt)
                            if results and results[0]["status"] == "success":
                                st.session_state.pending_feedback = {
                                    "needed": True,
                                    "type": "image",
                                    "voice_id": None,
                                    "voice_name": None,
                                    "image_prompt": results[0]["prompt"]
                                }
                        else:
                            assistant_message = "I encountered an error while generating the images. Please try different prompts or try again later."
                        
                        # Display message with images
                        display_message("assistant", assistant_message, image_data=results)
                        
                        # Add to state
                        st.session_state.messages.append({
                            "role": "function",
                            "name": function_name,
                            "content": json.dumps({
                                "results": [
                                    {
                                        "prompt": r["prompt"],
                                        "status": r["status"],
                                        "image_url": r.get("image_url"),
                                        "collection_url": r.get("collection_url")
                                    } for r in results
                                ]
                            })
                        })
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": assistant_message
                        })
                        
                        st.session_state.conversation_state["last_assistant_message"] = assistant_message
            else:
                # Regular text response
                assistant_message = response_message.content
                display_message("assistant", assistant_message)
                
                # Update state
                st.session_state.conversation_state["last_assistant_message"] = assistant_message
                
                # If we're not at the script development stage yet, update
                if st.session_state.conversation_state["script_development_stage"] == "initial" and len(st.session_state.messages) > 3:
                    st.session_state.conversation_state["script_development_stage"] = "developing"
                    st.session_state.conversation_state["current_context"] = assistant_message
                
                # Add to state
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": assistant_message
                })
        
        # Record conversation turn for learning
        if len(st.session_state.messages) >= 4:  # We have at least 2 turns
            last_assistant_question = st.session_state.messages[-4]["content"] if len(st.session_state.messages) >= 4 and st.session_state.messages[-4]["role"] == "assistant" else ""
            user_response = st.session_state.messages[-3]["content"] if len(st.session_state.messages) >= 3 else ""
            next_question = st.session_state.messages[-1]["content"]
            
            st.session_state.user_learning.record_conversation_turn(
                last_assistant_question,
                user_response,
                next_question,
                context=st.session_state.conversation_state["current_context"]
            )

        
        # Periodically save learning data (every 5 messages)
        if len(st.session_state.messages) % 5 == 0:
            st.session_state.user_learning.save_data()
            
