import streamlit as st
import pandas as pd
import requests
import time
import os
import re
from io import BytesIO
from PIL import Image
from elevenlabs import ElevenLabs
from crewai import Agent, Task, Crew
from langchain_groq import ChatGroq
from langchain_community.tools import SerperDevTool
from pydantic import BaseModel
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.schema import SystemMessage

# Set page configuration
st.set_page_config(
    page_title="AdGen AI Platform",
    page_icon="🎬",
    layout="wide"
)

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
def process_briefer_input(user_input):
    # Initialize the briefer components if not already initialized
    if not st.session_state.breifer_initialized:
        try:
            # Initialize Groq LLM
            st.session_state.llm = ChatGroq(
                model="groq/gemma2-9b-it",
                temperature=0.7,
                max_tokens=2048
            )
            
            # Load prompt from file or just define it directly if needed
            system_prompt = SystemMessage(content="Your system prompt content here")
            
            # Set up memory
            st.session_state.memory = ConversationBufferMemory(return_messages=True)
            st.session_state.memory.chat_memory.add_message(system_prompt)
            
            # Create conversation chain
            st.session_state.conversation_chain = ConversationChain(
                llm=st.session_state.llm,
                memory=st.session_state.memory,
                verbose=False
            )
            
            st.session_state.breifer_initialized = True
            
        except Exception as e:
            st.error(f"Error initializing briefer: {e}")
            return "I'm having trouble initializing. Let's continue with a simpler approach. What's your campaign about?"
    
    try:
        # Get response from the conversation chain
        response = st.session_state.conversation_chain.predict(input=user_input)
        return response
        
    except Exception as e:
        st.error(f"Error processing with Groq LLM: {e}")
        return "I'm having trouble processing your request. Could you tell me about your campaign goal?"
      
def render_script_generation_page():
    st.title("📝 Script Generation")
    st.subheader("Creating your ad script with AI")
    
    st.markdown("### Campaign Brief Summary")
    st.info(st.session_state.cleaned_summary)
    
    if 'script_generated' not in st.session_state:
        st.session_state.script_generated = False
    
    if not st.session_state.script_generated:
        if st.button("Generate Script with CrewAI"):
            with st.spinner("Generating script with CrewAI... (This may take several minutes)"):
                try:
                    # Define the crew() function with access to cleaned_summary
                    def crew():
                        # Access the cleaned summary from session state
                        cleaned_summary = st.session_state.cleaned_summary
                        
                        # Your existing script generator code
                        class Script(BaseModel):
                            hook: str
                            body: str
                            cta: str
                            final_script: str
                        
                        # The rest of your crew() function with task_planning, researcher, writer, etc.
                        # Make sure all f-strings that reference {cleaned_summary} can access it
                        
                        # Define your agents and tasks (from your paste.txt)
                        
                        # Run the crew workflow
                        result = crew.kickoff()
                        return result
                    
                    # Run the crew function
                    script_result = crew()
                    
                    # Store the script in session state
                    st.session_state.script = script_result.final_script
                    st.session_state.script_generated = True
                    
                except Exception as e:
                    st.error(f"Error generating script: {e}")
                    # Use default script as fallback
                    st.session_state.script = default_script
                    st.session_state.script_generated = True
                    st.rerun()
    
    if st.session_state.script_generated:
        st.markdown("### Generated Script")
        st.success("Script generated successfully!")
        st.text_area("Generated Script", st.session_state.script, height=300)
        
        if st.button("Edit Script"):
            st.session_state.step = "edit_script"
            st.rerun()
    
    # Add a back button
    if st.button("Back to Briefer"):
        st.session_state.step = "briefer"
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
    
    col1, col2, col3 = st.columns(3)
    
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
    col1, col2, col3 = st.columns(3)
    
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
        if st.button("Generate Images", use_container_width=True):
            st.session_state.step = "image_generation"
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
# Main app logic stays the same, you just need to update the implementations
# of render_briefer_page() and render_script_generation_page()
if st.session_state.step == "start":
    render_start_page()
elif st.session_state.step == "briefer":
    render_briefer_page()  # This is now chat-based
elif st.session_state.step == "generate_script":
    render_script_generation_page()  # This now uses your crew() function
elif st.session_state.step == "edit_script":
    render_script_editor_page()
elif st.session_state.step == "audio_generation":
    render_audio_generation_page()
elif st.session_state.step == "video_generation":
    render_video_generation_page()
elif st.session_state.step == "image_generation":
    render_image_generation_page()

# Add footer
st.markdown("---")
st.markdown("#### AdGen AI Platform v0 | Beta Testing")
