import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
from PIL import Image
import io
import time

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
    .play-button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border-radius: 50%;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        margin: 10px auto;
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

# Simulated functions for AI features
def generate_script(prompt):
    # In a real implementation, this would call your AI API
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
    # In a real implementation, this would call your AI API
    time.sleep(2)  # Simulate API call
    return "generated_audio.mp3"  # This would be a file path or base64 data

def generate_video(script, style_id, audio=None):
    # In a real implementation, this would call your AI API
    time.sleep(3)  # Simulate API call
    return "generated_video.mp4"  # This would be a file path or base64 data

def generate_screenplay_images(screenplay):
    # In a real implementation, this would parse the screenplay and generate images
    time.sleep(2)  # Simulate API call
    # Return mock image data
    return ["image1.jpg", "image2.jpg", "image3.jpg"]

# Mock function to simulate playing audio
def play_audio_sample(sample_id):
    st.audio(f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{sample_id}.mp3")

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
            "Voice": "✅" if st.session_state.selected_voice else "❌",
            "Audio": "✅" if st.session_state.generated_audio else "❌",
            "Video": "✅" if st.session_state.generated_video else "❌"
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
            if st.session_state.script:
                go_to_audio_generator()
            else:
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
    
    st.markdown("---")
    
    st.markdown("<h2 class='sub-header'>How It Works</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
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
                
                st.experimental_rerun()
    
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
            # Check if this voice is selected
            is_selected = st.session_state.selected_voice == voice["id"]
            card_class = "card card-selected" if is_selected else "card"
            
            st.markdown(f"""
            <div class="{card_class}">
                <div class="card-title">{voice["name"]}</div>
                <p><strong>Gender:</strong> {voice["gender"]}</p>
                <p><strong>Style:</strong> {voice["style"]}</p>
                <p><strong>Language:</strong> {voice["language"]}</p>
                <div class="play-button">▶</div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Play Sample", key=f"play_{voice['id']}"):
                    play_audio_sample(voice["id"])
            with col2:
                if st.button("Select" if not is_selected else "Selected", key=f"select_{voice['id']}"):
                    select_voice(voice["id"])
                    st.experimental_rerun()
    
    # Pagination controls
    st.markdown("<div class='pagination'>", unsafe_allow_html=True)
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if st.session_state.voice_page > 1:
            if st.button("← Previous", key="prev_voice_page"):
                st.session_state.voice_page -= 1
                st.experimental_rerun()
                
    with cols[1]:
        st.markdown(f"<p style='text-align: center;'>Page {st.session_state.voice_page} of {total_pages}</p>", unsafe_allow_html=True)
        
    with cols[2]:
        if st.session_state.voice_page < total_pages:
            if st.button("Next →", key="next_voice_page"):
                st.session_state.voice_page += 1
                st.experimental_rerun()
    
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
            
            # Create placeholder preview image
            placeholder = get_placeholder_image(300, 200, f"Style {style['id']}")
            
            st.markdown(f"""
            <div class="{card_class}">
                <div class="card-title">{style["name"]}</div>
                <p>{style["description"]}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.image(placeholder, use_column_width=True)
            
            if st.button("Select" if not is_selected else "Selected", key=f"select_video_{style['id']}"):
                select_video_style(style["id"])
                st.experimental_rerun()
    
    # Pagination controls
    st.markdown("<div class='pagination'>", unsafe_allow_html=True)
    cols = st.columns([1, 4, 1])
    with cols[0]:
        if st.session_state.video_page > 1:
            if st.button("← Previous", key="prev_video_page"):
                st.session_state.video_page -= 1
                st.experimental_rerun()
                
    with cols[1]:
        st.markdown(f"<p style='text-align: center;'>Page {st.session_state.video_page} of {total_pages}</p>", unsafe_allow_html=True)
        
    with cols[2]:
        if st.session_state.video_page < total_pages:
            if st.button("Next →", key="next_video_page"):
                st.session_state.video_page += 1
                st.experimental_rerun()
    
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
            # In a real implementation, you would play the audio here
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
                # In a real implementation, this would parse the screenplay and generate relevant images
                images = generate_screenplay_images(screenplay)
                st.session_state.screenplay_images = images
                st.session_state.script = screenplay  # Save the screenplay
                st.success("Images generated successfully!")
    
    with col2:
        st.markdown("<h3>Preview</h3>", unsafe_allow_html=True)
        
        if st.session_state.screenplay_images:
            for i, img in enumerate(st.session_state.screenplay_images):
                # Create placeholder images
                placeholder = get_placeholder_image(400, 225, f"Scene {i+1}")
                st.image(placeholder, caption=f"Scene {i+1}", use_column_width=True)
        else:
            st.info("Generate images from your screenplay to see previews here.")
        
        if st.session_state.screenplay_images and st.button("Proceed to Audio", key="screenplay_to_audio"):
            go_to_audio_generator()

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

if __name__ == "__main__":
    main()
