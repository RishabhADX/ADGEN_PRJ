import streamlit as st
import pandas as pd
import requests
import time
import os
import re
import json
from io import BytesIO
from PIL import Image
from elevenlabs import ElevenLabs

# Set page configuration
st.set_page_config(
    page_title="AdGen AI Platform",
    page_icon="🎬",
    layout="wide"
)

# Initialize session state variables if they don't exist
if 'script' not in st.session_state:
    st.session_state.script = ""
if 'screenplay_script' not in st.session_state:
    st.session_state.screenplay_script = ""
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
if 'creatify_response' not in st.session_state:
    st.session_state.creatify_response = None

# API Keys (in a real app, these should be secured properly)
serper_api_key = st.secrets["SERPER_API_KEY"] if "SERPER_API_KEY" in st.secrets else "14b865cf1dae8d1149dea6a7d2c93f8ac0105970"
openai_api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else "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"
groq_api_key = st.secrets["GROQ_API_KEY"] if "GROQ_API_KEY" in st.secrets else "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"
tavus_api_key = st.secrets["TAVUS_API_KEY"] if "TAVUS_API_KEY" in st.secrets else "d57e6c687a894213aa87abad7c1c5f56"
gemini_api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "AIzaSyBLzfjImenFp60acvXgKygaEDKGqKfHyKI"
elevenlabs_api_key = st.secrets["ELEVENLABS_API_KEY"] if "ELEVENLABS_API_KEY" in st.secrets else "sk_457392759b066ebb9b695f4f7f3b85d177d04350c85e494a"
creatify_api_id = st.secrets["CREATIFY_API_ID"] if "CREATIFY_API_ID" in st.secrets else "5f8b3a5c-6e33-4e9f-b85c-71941d675270"
creatify_api_key = st.secrets["CREATIFY_API_KEY"] if "CREATIFY_API_KEY" in st.secrets else "c019dd017d22e2e40627f87bc86168b631b9a345"

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

# Default screenplay script for demonstration
default_screenplay_script = (
    "You're not alone... Financial stress is affecting so many. Real help for real debt. "
    "Professional, confidential support awaits. Take the first step... Start your free debt review today."
)

# Helper functions
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
                return f"✅ Video is ready! Video ID: {video_id}", stream_url

        return "⏳ Video is still processing. Please check back later.", None
        
    except Exception as e:
        return f"❌ Exception during video generation: {str(e)}", None

# New function for Creatify API video generation
def generate_screenplay_video(screenplay_script, name="AI TEST", target_platform="Facebook", 
                             target_audience="Debt Payers", language="en", video_length=30,
                             aspect_ratio="16x9", visual_style="GreenScreenEffectTemplate", 
                             avatar_id="a7a240e8-efbf-4ab5-a02d-0f367a810875"):
    url = "https://api.creatify.ai/api/link_to_videos/"
    
    payload = {
        "name": name,
        "target_platform": target_platform,
        "target_audience": target_audience,
        "language": language,
        "video_length": video_length,
        "aspect_ratio": aspect_ratio,
        "visual_style": visual_style,
        "override_avatar": avatar_id,
        "override_script": screenplay_script,
        "voiceover_volume": 0.5,
        "link": "9a98f404-f3d9-4f74-b452-f73013be938f",
        "no_background_music": True,
        "caption_style": "normal-black"
    }
    
    headers = {
        "X-API-ID": creatify_api_id,
        "X-API-KEY": creatify_api_key,
        "Content-Type": "application/json"
    }
    
    try:
        with st.spinner("Creating screenplay video..."):
            response = requests.post(url, json=payload, headers=headers)
            
        if response.status_code != 200:
            return f"❌ Error creating screenplay video: {response.status_code} - {response.text}", None
            
        response_data = response.json()
        
        # Check if we need to poll for completion
        if response_data.get("status") != "done":
            # Initialize progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Get the video ID for polling
            video_id = response_data.get("id")
            status_url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/"
            
            # Poll for completion
            for i in range(30):  # Up to ~5 minutes
                progress_percentage = min(response_data.get("progress", 0), 1.0)
                progress_bar.progress(progress_percentage)
                status_text.text(f"Video processing: {int(progress_percentage * 100)}% complete...")
                
                if response_data.get("status") == "done":
                    break
                    
                time.sleep(10)  # Check every 10 seconds
                status_response = requests.get(status_url, headers=headers)
                response_data = status_response.json()
            
            # Final status check
            if response_data.get("status") != "done":
                return "⏳ Screenplay video is still processing. Please check back later.", response_data
        
        # Return success with video URL
        video_url = response_data.get("video_output")
        return f"✅ Screenplay video is ready!", response_data
            
    except Exception as e:
        return f"❌ Exception during screenplay video generation: {str(e)}", None

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
    
    return script_result

# UI Components
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

def render_briefer_page():
    st.title("🧠 Campaign Briefer")
    st.subheader("Let's gather information about your campaign")
    
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
                st.session_state.step = "generate_script"
                st.rerun()

def render_script_generation_page():
    st.title("📝 Script Generation")
    st.subheader("Creating your ad script with AI")
    
    st.markdown("### Campaign Brief Summary")
    st.info(st.session_state.cleaned_summary)
    
    if st.button("Generate Script with CrewAI"):
        # In a real implementation, this would call your CrewAI workflow
        script_result = generate_script_with_crewai(st.session_state.cleaned_summary)
        
        st.session_state.script = script_result["final_script"]
        st.session_state.step = "edit_script"
        st.rerun()

def render_script_editor_page():
    st.title("✏️ Script Editor")
    
    # If there's no script yet (coming directly from start page)
    if not st.session_state.script:
        st.session_state.script = default_script
    
    # Script editing section
    st.subheader("Edit Your Script")
    new_script = st.text_area("Script", st.session_state.script, height=300)
    
    if st.button("Save Script"):
        st.session_state.script = new_script
        st.success("Script saved!")
    
    # Section to choose next steps
    st.subheader("What would you like to do next?")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Generate Audio", use_container_width=True):
            st.session_state.step = "audio_generation"
            st.rerun()
    
    with col2:
        if st.button("Generate Video", use_container_width=True):
            st.session_state.step = "video_generation"
            st.rerun()
    
    with col3:
        if st.button("Generate Images", use_container_width=True):
            st.session_state.step = "image_generation"
            st.rerun()
            
    with col4:
        if st.button("Generate Screenplay", use_container_width=True):
            st.session_state.step = "screenplay_generation"
            st.rerun()

def render_audio_generation_page():
    st.title("🔊 Audio Generation")
    st.subheader("Generate voice audio for your ad")
    
    # Display the current script
    st.markdown("### Current Script")
    st.info(st.session_state.script)
    
    # ElevenLabs voice selection (integrated from second snippet)
    st.subheader("Select Voice from ElevenLabs")
    
    # Fetch voices if not already in session state
    if 'elevenlabs_voices' not in st.session_state:
        with st.spinner("Loading ElevenLabs voices..."):
            st.session_state.elevenlabs_voices = get_elevenlabs_voices()
    
    # Display voices in a grid
    if st.session_state.elevenlabs_voices:
        cards_per_row = 3
        
        for i in range(0, len(st.session_state.elevenlabs_voices), cards_per_row):
            cols = st.columns(cards_per_row)
            for j, col in enumerate(cols):
                if i + j < len(st.session_state.elevenlabs_voices):
                    voice = st.session_state.elevenlabs_voices[i + j]
                    name = voice.name
                    accent = voice.labels.get("accent", "Unknown")
                    gender = voice.labels.get("gender", "Unknown")
                    age = voice.labels.get("age", "Unknown")
                    use_case = voice.labels.get("use_case", "Unknown")
                    preview_url = voice.preview_url
                    voice_id = voice.voice_id
                    
                    with col:
                        st.markdown(f"**{name}**")
                        st.markdown(
                            f"Accent: {accent} | Gender: {gender} | Age: {age} | Use Case: {use_case}"
                        )
                        # Preview the voice
                        st.audio(preview_url)
                        # Select button for this voice
                        if st.button(f"Select {name}", key=f"voice_{voice_id}"):
                            st.session_state.selected_voice_id = voice_id
                            st.session_state.selected_voice_name = name
                            st.success(f"Selected voice: {name}")
    else:
        st.error("Could not load ElevenLabs voices. Please check your API key or try again later.")
    
    # Generation options
    st.subheader("Generate Audio")
    
    with st.form("audio_generation_form"):
        if 'selected_voice_id' in st.session_state:
            st.info(f"Selected voice: {st.session_state.selected_voice_name}")
        else:
            st.warning("Please select a voice first")
        
        speed = st.slider("Speed", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
        stability = st.slider("Stability", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
        
        submit = st.form_submit_button("Generate Audio")
        
        if submit and 'selected_voice_id' in st.session_state:
            # Call the audio generation function
            audio_url = generate_audio_with_elevenlabs(
                st.session_state.selected_voice_id,
                st.session_state.script,
                speed,
                stability
            )
            
            # Play the generated audio
            st.audio(audio_url, format="audio/mp3")
            
            # Download button for the generated audio
            st.download_button(
                label="Download Audio",
                data=b"placeholder",  # This would be the actual audio data
                file_name="generated_audio.mp3",
                mime="audio/mp3"
            )
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Back to Script", use_container_width=True):
            st.session_state.step = "edit_script"
            st.rerun()
    
    with col2:
        if st.button("Generate Video", use_container_width=True):
            st.session_state.step = "video_generation"
            st.rerun()
    
    with col3:
        if st.button("Generate Images", use_container_width=True):
            st.session_state.step = "image_generation"
            st.rerun()
            
    with col4:
        if st.button("Generate Screenplay", use_container_width=True):
            st.session_state.step = "screenplay_generation"
            st.rerun()

def render_video_generation_page():
    st.title("🎥 Video Generation")
    st.subheader("Create videos with AI avatars")
    
    # Display the current script
    st.markdown("### Current Script")
    st.info(st.session_state.script)
    
    # Choose video platform
    st.subheader("Select Video Platform")
    
    video_platform = st.radio(
        "Choose a platform:",
        ["Tavus", "HeyGen", "Veed.io"],
        horizontal=True
    )
    
    if video_platform == "Tavus":
        # Load Tavus replicas if not already loaded
        if st.session_state.replicas_df is None:
            with st.spinner("Loading Tavus models..."):
                st.session_state.replicas_df = get_replicas()
        
        if not st.session_state.replicas_df.empty:
            st.subheader("Select Tavus Replica")
            
            # Initialize the page index if it doesn't exist
            if 'page' not in st.session_state:
                st.session_state.page = 0

            # Paginate and display replicas in chunks
            items_per_page = 6  # Set the number of replicas per page
            total_pages = len(st.session_state.replicas_df) // items_per_page + (1 if len(st.session_state.replicas_df) % items_per_page != 0 else 0)
            current_page = st.session_state.page

            # Display replicas for the current page
            start_idx = current_page * items_per_page
            end_idx = start_idx + items_per_page
            replicas_to_display = st.session_state.replicas_df.iloc[start_idx:end_idx]

            cols = st.columns(3)
            for i, (index, row) in enumerate(replicas_to_display.iterrows()):
                with cols[i % 3]:
                    st.markdown(f"### {row['replica_name']}")
                    
                    # If there is a video thumbnail, show it; otherwise, show a placeholder
                    if 'thumbnail_video_url' in row and row['thumbnail_video_url']:
                        st.video(row['thumbnail_video_url'])
                    else:
                        # Fallback to a placeholder if there's no video thumbnail
                        st.image("https://via.placeholder.com/150", caption=f"Thumbnail of {row['replica_name']}")

                    if st.button(f"Select {row['replica_name']}", key=f"replica_{row['replica_id']}"):
                        st.session_state.selected_replica = {
                            'id': row['replica_id'],
                            'name': row['replica_name']
                        }
                        st.success(f"Selected replica: {row['replica_name']}")

            # Pagination Controls
            col1, col2 = st.columns(2)
            with col1:
                if current_page > 0 and st.button("Previous", use_container_width=True):
                    st.session_state.page = current_page - 1
                    st.rerun()

            with col2:
                if current_page < total_pages - 1 and st.button("Next", use_container_width=True):
                    st.session_state.page = current_page + 1
                    st.rerun()

            # Video generation form
            st.subheader("Generate Video")
            
            with st.form("video_generation_form"):
                if 'selected_replica' in st.session_state:
                    st.info(f"Selected replica: {st.session_state.selected_replica['name']}")
                else:
                    st.warning("Please select a replica first")
                
                video_name = st.text_input("Video Name", "My Ad Campaign")
                background_url = st.text_input("Background Video URL (optional)")
                audio_url = st.text_input("Audio URL (optional)")
                
                submit = st.form_submit_button("Generate Video")
                
                if submit and 'selected_replica' in st.session_state:
                    status_msg, video_url = generate_and_fetch_video(
                        st.session_state.selected_replica['id'],
                        video_name,
                        st.session_state.script,
                        audio_url,
                        background_url
                    )
                    
                    st.markdown(status_msg)
                    
                    if video_url:
                        st.video(video_url)
        else:
            st.error("Could not load Tavus replicas. Please check your API key or try again later.")
    
    elif video_platform == "HeyGen":
        st.info("HeyGen integration is coming soon!")
        
        # Placeholder UI for HeyGen
        st.subheader("HeyGen Models")
        cols = st.columns(3)
        for i in range(3):
            with cols[i]:
                st.markdown(f"### Model {i+1}")
                st.image("https://via.placeholder.com/150", caption=f"HeyGen Model {i+1}")
                st.button(f"Select Model {i+1}", key=f"heygen_model_{i}")
    
    elif video_platform == "Veed.io":
        st.info("Veed.io integration is coming soon!")
        
        # Placeholder UI for Veed.io
        st.subheader("Veed.io Templates")
        cols = st.columns(3)
        for i in range(3):
            with cols[i]:
                st.markdown(f"### Template {i+1}")
                st.image("https://via.placeholder.com/150", caption=f"Veed.io Template {i+1}")
                st.button(f"Select Template {i+1}", key=f"veed_template_{i}")
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Back to Script", use_container_width=True):
            st.session_state.step = "edit_script"
            st.rerun()
    
    with col2:
        if st.button("Generate Audio", use_container_width=True):
            st.session_state.step = "audio_generation"
            st.rerun()
    
    with col3:
        if st.button("Generate Images", use_container_width=True):
            st.session_state.step = "image_generation"
            st.rerun()
            
    with col4:
        if st.button("Generate Screenplay", use_container_width=True):
            st.session_state.step = "screenplay_generation"
            st.rerun()
            
def render_image_generation_page():
    st.title("🖼️ Image Generation")
    st.subheader("Create AI-generated images for your ad campaign")
    
    # Display the current script
    st.markdown("### Current Script")
    st.info(st.session_state.script)
    
    # Image prompt generation
    st.subheader("Generate Image Prompts")
    
    if st.button("Generate Prompts Based on Script"):
        # Simulate AI prompt generation (in real app, this would use your prompt_writer agent)
        with st.spinner("Generating image prompts..."):
            time.sleep(2)  # Simulating API call delay
            
            # These would be generated by your prompt_writer agent in a real implementation
            generated_prompts = [
                {
                    "id": "scene_1",
                    "prompt": "A person looking stressed while sorting through bills and credit card statements, dramatic lighting, shallow depth of field"
                },
                {
                    "id": "scene_2",
                    "prompt": "Close-up of a relaxed face with a relieved expression, soft natural lighting, symbolizing freedom from financial stress"
                },
                {
                    "id": "scene_3",
                    "prompt": "A clean, organized desk with a single bill and a calculator showing reduced numbers, representing financial organization"
                }
            ]
            
            st.session_state.image_prompts = generated_prompts
            st.success("Prompts generated successfully!")
    
    # Display generated prompts if available
    if 'image_prompts' in st.session_state:
        st.subheader("Generated Prompts")
        
        for i, prompt in enumerate(st.session_state.image_prompts):
            st.markdown(f"### Scene {i+1}")
            st.text_area(f"Prompt {i+1}", prompt["prompt"], key=f"prompt_{i}", height=100)
            
            if st.button(f"Generate Image for Scene {i+1}", key=f"gen_image_{i}"):
                # This would integrate with Gemini in a real implementation
                with st.spinner("Generating image..."):
                    time.sleep(3)  # Simulate API call
                    
                    # Placeholder image (would be replaced with actual generated image)
                    st.image("https://via.placeholder.com/512x512", caption=f"Generated image for Scene {i+1}")
                    st.download_button(
                        label=f"Download Image {i+1}",
                        data=BytesIO(b"placeholder"),  # Would be actual image data
                        file_name=f"scene_{i+1}.png",
                        mime="image/png"
                    )
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Back to Script", use_container_width=True):
            st.session_state.step = "edit_script"
            st.rerun()
    
    with col2:
        if st.button("Generate Audio", use_container_width=True):
            st.session_state.step = "audio_generation"
            st.rerun()
    
    with col3:
        if st.button("Generate Video", use_container_width=True):
            st.session_state.step = "video_generation"
            st.rerun()
            
    with col4:
        if st.button("Generate Screenplay", use_container_width=True):
            st.session_state.step = "screenplay_generation"
            st.rerun()

# New function to render the screenplay generation page
def render_screenplay_generation_page():
    st.title("🎬 Screenplay Generation")
    st.subheader("Create professional screenplay videos with AI")
    
    # If there's no screenplay script yet, initialize with a default
    if not st.session_state.screenplay_script:
        st.session_state.screenplay_script = default_screenplay_script
    
    # Script editing section
    st.subheader("Edit Your Screenplay Script")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_screenplay_script = st.text_area("Screenplay Script", st.session_state.screenplay_script, height=200)
        
        if st.button("Save Screenplay Script"):
            st.session_state.screenplay_script = new_screenplay_script
            st.success("Screenplay script saved!")
    
    with col2:
        st.markdown("### Tips for Effective Scripts")
        st.info("""
        - Keep it concise (30-60 words)
        - Use emotional language
        - Include a clear call to action
        - Break complex ideas into simple sentences
        - Use pauses (...) for emphasis
        """)
    
    # Creatify API Integration
    st.subheader("Generate Screenplay Video with Creatify.ai")
    
    with st.form("screenplay_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            video_name = st.text_input("Video Name", "AI Debt Relief Campaign")
            target_platform = st.selectbox("Target Platform", ["Facebook", "Instagram", "YouTube", "TikTok", "LinkedIn"])
            target_audience = st.text_input("Target Audience", "Debt Payers")
            language = st.selectbox("Language", ["en", "es", "fr", "de", "it"])
        
        with col2:
            video_length = st.slider("Video Length (seconds)", min_value=15, max_value=60, value=30, step=5)
            aspect_ratio = st.selectbox("Aspect Ratio", ["16x9", "9x16", "1x1", "4x5"])
            visual_style = st.selectbox("Visual Style", ["GreenScreenEffectTemplate", "ModernCorporate", "Casual", "Professional", "Energetic"])
            
            # In a real application, you would fetch avatars from Creatify API
            # For now, we'll use a hardcoded one
            avatar_selection = st.selectbox("Select Avatar", ["Default Avatar", "Professional Male", "Professional Female", "Casual Male", "Casual Female"])
            avatar_mapping = {
                "Default Avatar": "a7a240e8-efbf-4ab5-a02d-0f367a810875",
                "Professional Male": "a7a240e8-efbf-4ab5-a02d-0f367a810875",
                "Professional Female": "a7a240e8-efbf-4ab5-a02d-0f367a810875",
                "Casual Male": "a7a240e8-efbf-4ab5-a02d-0f367a810875",
                "Casual Female": "a7a240e8-efbf-4ab5-a02d-0f367a810875"
            }
            selected_avatar_id = avatar_mapping[avatar_selection]
        
        # Display preview of selected avatar (would be real images in production)
        cols = st.columns(5)
        with cols[2]:
            st.image("https://via.placeholder.com/200x300?text=Avatar", caption=avatar_selection)
        
        # Additional options
        st.subheader("Additional Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            no_background_music = st.checkbox("No Background Music", value=True)
            caption_style = st.selectbox("Caption Style", ["normal-black", "normal-white", "highlight", "none"])
        
        with col2:
            no_caption = st.checkbox("No Captions", value=False)
            no_emotion = st.checkbox("No Emotion", value=False)
        
        with col3:
            no_cta = st.checkbox("No Call to Action", value=False)
            no_stock_broll = st.checkbox("No Stock B-Roll", value=False)
        
        # Submit button
        submit_button = st.form_submit_button("Generate Screenplay Video")
        
        if submit_button:
            # Call the Creatify API function
            status_msg, response_data = generate_screenplay_video(
                screenplay_script=st.session_state.screenplay_script,
                name=video_name,
                target_platform=target_platform,
                target_audience=target_audience,
                language=language,
                video_length=video_length,
                aspect_ratio=aspect_ratio,
                visual_style=visual_style,
                avatar_id=selected_avatar_id
            )
            
            # Store the response in session state
            st.session_state.creatify_response = response_data
            
            # Display status message
            st.markdown(status_msg)
            
            # Display the video if available
            if response_data and "video_output" in response_data and response_data["video_output"]:
                st.video(response_data["video_output"])
                
                # Display additional information about the generated video
                with st.expander("Video Details"):
                    # Format the JSON for readability
                    formatted_json = json.dumps(response_data, indent=2)
                    st.code(formatted_json, language="json")
    
    # Display previously generated video if available
    if "creatify_response" in st.session_state and st.session_state.creatify_response:
        st.subheader("Previously Generated Video")
        
        # Extract video details
        video_data = st.session_state.creatify_response
        
        if "video_output" in video_data and video_data["video_output"]:
            st.video(video_data["video_output"])
            
            # Add download button for the video
            st.markdown(f"[Download Video]({video_data['video_output']})")
            
            # Display thumbnail if available
            if "video_thumbnail" in video_data and video_data["video_thumbnail"]:
                st.image(video_data["video_thumbnail"], caption="Video Thumbnail")
    
    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Back to Script", use_container_width=True):
            st.session_state.step = "edit_script"
            st.rerun()
    
    with col2:
        if st.button("Generate Audio", use_container_width=True):
            st.session_state.step = "audio_generation"
            st.rerun()
    
    with col3:
        if st.button("Generate Video", use_container_width=True):
            st.session_state.step = "video_generation"
            st.rerun()

# Main app logic based on current step
if st.session_state.step == "start":
    render_start_page()
elif st.session_state.step == "briefer":
    render_briefer_page()
elif st.session_state.step == "generate_script":
    render_script_generation_page()
elif st.session_state.step == "edit_script":
    render_script_editor_page()
elif st.session_state.step == "audio_generation":
    render_audio_generation_page()
elif st.session_state.step == "video_generation":
    render_video_generation_page()
elif st.session_state.step == "image_generation":
    render_image_generation_page()
elif st.session_state.step == "screenplay_generation":
    render_screenplay_generation_page()

# Add footer
st.markdown("---")
st.markdown("#### AdGen AI Platform v0.2 | Beta Testing")
