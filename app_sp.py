import streamlit as st
import requests
import json
import base64
from PIL import Image
from io import BytesIO
import uuid
import time
from google import genai
from google.genai import types

# Page configuration
st.set_page_config(
    page_title="Creatify AI Video Generator",
    page_icon="🎬",
    layout="wide",
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .card {
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .bubble {
        display: inline-block;
        background-color: #e6f3ff;
        border-radius: 20px;
        padding: 8px 16px;
        margin: 5px;
        font-size: 14px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .header {
        background-color: #4CAF50;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .video-container {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# API credentials
API_ID = "5f8b3a5c-6e33-4e9f-b85c-71941d675270"
API_KEY = "c019dd017d22e2e40627f87bc86168b631b9a345"
GEMINI_API_KEY = "AIzaSyBLzfjImenFp60acvXgKygaEDKGqKfHyKI"
IMAGEKIT_PRIVATE_KEY = "private_OGgux+C54n9PIYDlLdOrYysEWrw="
IMAGEKIT_PUBLIC_KEY = "public_Qq9s197rBPKyx5eWhq+aN6TQ3Iw="
IMAGEKIT_URL_ENDPOINT = "https://ik.imagekit.io/b6pq3mgo7"

# Initialize Gemini
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"Failed to initialize Gemini: {str(e)}")

# Headers for API requests
headers = {
    "X-API-ID": API_ID,
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

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
        import requests
        
        # Prepare the request
        url = f"{IMAGEKIT_URL_ENDPOINT}/api/v1/files/upload"
        auth_string = base64.b64encode(f"{IMAGEKIT_PRIVATE_KEY}:".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "multipart/form-data"
        }
        
        files = {
            "file": (filename, image_data),
            "fileName": (None, filename)
        }
        
        response = requests.post(url, files=files, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("url"), data.get("fileId"), None
        else:
            return None, None, f"Upload failed: {response.text}"
            
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
        "reviews": "Generated with Creatify AI"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        st.error(f"Error creating link: {str(e)}")
        return None

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
        "voiceover_volume": kwargs.get("volume", 0.5),
        "link": link_id,
        "no_background_music": kwargs.get("no_music", True),
        "caption_style": kwargs.get("caption_style", "normal-black"),
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        st.error(f"Error creating video: {str(e)}")
        return None

# Function to get video status
def get_video_status(video_id):
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/"
    
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        st.error(f"Error getting video status: {str(e)}")
        return None

# Function to render video
def render_video(video_id):
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/render/"
    
    try:
        response = requests.post(url, headers=headers)
        return response.json()
    except Exception as e:
        st.error(f"Error rendering video: {str(e)}")
        return None

# Display header
st.markdown('<div class="header"><h1>🎬 Creatify AI Video Generator</h1></div>', unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # Project details
    st.subheader("Project Details")
    project_name = st.text_input("Project Name", "My Awesome Video")
    
    # Script input
    st.subheader("Script")
    script = st.text_area("Enter your script", "You're not alone... Financial stress is affecting so many. Real help for real debt. Professional, confidential support awaits. Take the first step... Start your free debt review today.")
    
    # Video settings
    st.subheader("Video Settings")
    platform = st.selectbox("Target Platform", ["Facebook", "Instagram", "YouTube", "TikTok", "LinkedIn"])
    audience = st.text_input("Target Audience", "Debt Payers")
    language = st.selectbox("Language", ["en", "es", "fr", "de"])
    video_length = st.slider("Video Length (seconds)", 15, 60, 30)
    aspect_ratio = st.selectbox("Aspect Ratio", ["16x9", "1x1", "9x16"])
    
    # Image prompts
    st.subheader("Image Prompts")
    image_prompts = []
    
    num_scenes = st.number_input("Number of Scenes", 1, 5, 3, step=1)
    
    for i in range(num_scenes):
        prompt = st.text_area(f"Scene {i+1} Prompt", 
                              f"Professional financial advisor with sympathetic expression in a modern office, warm lighting, supportive environment, scene {i+1}", 
                              key=f"prompt_{i}")
        image_prompts.append(prompt)

# Main content
tab1, tab2, tab3 = st.tabs(["Generate Images", "Create Video", "Preview & Results"])

with tab1:
    st.header("Generate Scene Images")
    
    if st.button("Generate Images"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        image_urls = []
        image_file_ids = []
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]
        
        for i, prompt in enumerate(image_prompts):
            if i < len(columns):
                with columns[i]:
                    status_text.text(f"Generating image {i+1}/{len(image_prompts)}...")
                    
                    # Generate image with Gemini
                    image_data, error = generate_image(prompt)
                    
                    if error:
                        st.error(f"Error generating image: {error}")
                        continue
                    
                    # Create a filename
                    filename = f"scene-{i+1:02d}-gemini-image.png"
                    
                    # Display the image
                    image = Image.open(BytesIO(image_data))
                    st.image(image, caption=f"Scene {i+1}", use_column_width=True)
                    
                    # Upload to ImageKit
                    status_text.text(f"Uploading image {i+1} to ImageKit...")
                    
                    # Convert the PIL Image back to bytes for upload
                    buffered = BytesIO()
                    image.save(buffered, format="PNG")
                    img_bytes = buffered.getvalue()
                    
                    url, file_id, upload_error = upload_to_imagekit(img_bytes, filename)
                    
                    if upload_error:
                        st.error(f"Error uploading to ImageKit: {upload_error}")
                    else:
                        image_urls.append(url)
                        image_file_ids.append(file_id)
                        st.success(f"Image {i+1} uploaded successfully!")
                        
            progress_bar.progress((i + 1) / len(image_prompts))
            
        status_text.text("All images generated and uploaded!")
        
        # Store the image URLs in the session state
        st.session_state.image_urls = image_urls
        st.session_state.image_file_ids = image_file_ids
        
        # Create Creatify link
        if image_urls:
            status_text.text("Creating Creatify link...")
            link_data = create_creatify_link(
                image_urls, 
                f"{project_name} - Generated Images", 
                "Images generated with Google Gemini for video creation"
            )
            
            if link_data and 'id' in link_data:
                st.session_state.link_id = link_data['id']
                st.success(f"Creatify link created successfully! ID: {link_data['id']}")
                
                if 'url' in link_data:
                    st.markdown(f"[View Images Collection]({link_data['url']})")
            else:
                st.error("Failed to create Creatify link")
                
        status_text.empty()

with tab2:
    st.header("Create Video")
    
    # Get available personas
    personas = get_personas()
    
    if personas:
        st.subheader("Select Avatar")
        
        # Arrange personas in a grid
        cols = st.columns(3)
        persona_options = {}
        
        for i, persona in enumerate(personas[:6]):  # Limit to 6 personas for the demo
            with cols[i % 3]:
                preview_img = persona.get("preview_image_1_1")
                if preview_img:
                    st.image(preview_img, width=150)
                    
                persona_id = persona.get("id")
                gender = persona.get("gender", "unknown")
                age = persona.get("age_range", "adult")
                
                label = f"{gender.upper()} - {age}"
                st.markdown(f"<div class='bubble'>{label}</div>", unsafe_allow_html=True)
                
                select = st.checkbox("Select", key=f"persona_{i}")
                if select:
                    persona_options[persona_id] = True
                else:
                    persona_options[persona_id] = False
        
        # Get the selected persona ID
        selected_persona_id = None
        for persona_id, selected in persona_options.items():
            if selected:
                selected_persona_id = persona_id
                break
                
        if not selected_persona_id and personas:
            selected_persona_id = personas[0].get("id")  # Default to the first persona
        
        # Create video button
        if st.button("Create Video") and hasattr(st.session_state, 'link_id') and selected_persona_id:
            video_data = create_video(
                st.session_state.link_id,
                project_name,
                script,
                selected_persona_id,
                platform=platform,
                audience=audience,
                language=language,
                length=video_length,
                ratio=aspect_ratio
            )
            
            if video_data and 'id' in video_data:
                st.session_state.video_id = video_data['id']
                st.success(f"Video creation initiated! Video ID: {video_data['id']}")
                
                # Show the initial status
                video_status = get_video_status(video_data['id'])
                if video_status:
                    st.session_state.video_status = video_status
                    status = video_status.get('status', 'unknown')
                    progress = video_status.get('progress', 0)
                    
                    st.write(f"Status: {status}")
                    st.progress(progress)
            else:
                st.error("Failed to create video")
    else:
        st.warning("No personas available. Please check your API connection.")

with tab3:
    st.header("Preview & Results")
    
    if hasattr(st.session_state, 'video_id'):
        # Get current status
        if st.button("Check Status"):
            video_status = get_video_status(st.session_state.video_id)
            if video_status:
                st.session_state.video_status = video_status
        
        if hasattr(st.session_state, 'video_status'):
            status = st.session_state.video_status.get('status', 'unknown')
            progress = st.session_state.video_status.get('progress', 0)
            
            # Display status card
            st.markdown(f"""
                <div class="card">
                    <h3>Video Status</h3>
                    <p><strong>Project:</strong> {project_name}</p>
                    <p><strong>Status:</strong> {status}</p>
                    <p><strong>Progress:</strong> {progress * 100:.0f}%</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.progress(progress)
            
            # Preview if available
            preview_url = st.session_state.video_status.get('preview')
            if preview_url:
                st.markdown(f"""
                    <div class="card">
                        <h3>Video Preview</h3>
                        <p>Your video is being processed. You can preview it here:</p>
                        <a href="{preview_url}" target="_blank">Open Preview</a>
                    </div>
                """, unsafe_allow_html=True)
            
            # Final video if available
            video_url = st.session_state.video_status.get('video_output')
            if video_url:
                st.markdown(f"""
                    <div class="card">
                        <h3>Final Video</h3>
                        <div class="video-container">
                            <video width="100%" controls>
                                <source src="{video_url}" type="video/mp4">
                                Your browser does not support the video tag.
                            </video>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Download button
                st.download_button(
                    label="Download Video",
                    data=requests.get(video_url).content,
                    file_name=f"{project_name.replace(' ', '_')}.mp4",
                    mime="video/mp4"
                )
            
            # Render button (if not done yet)
            if status != "done" and status != "failed":
                if st.button("Render Final Video"):
                    render_result = render_video(st.session_state.video_id)
                    if render_result:
                        st.session_state.video_status = render_result
                        st.success("Rendering started!")
            
            # Video characteristics
            if status == "done":
                # Show characteristics in bubbles
                st.markdown("<h3>Video Characteristics</h3>", unsafe_allow_html=True)
                
                characteristics = [
                    f"Platform: {st.session_state.video_status.get('target_platform', 'unknown')}",
                    f"Audience: {st.session_state.video_status.get('target_audience', 'unknown')}",
                    f"Length: {st.session_state.video_status.get('video_length', 0)} seconds",
                    f"Aspect Ratio: {st.session_state.video_status.get('aspect_ratio', 'unknown')}",
                    f"Language: {st.session_state.video_status.get('language', 'unknown')}",
                    f"Style: {st.session_state.video_status.get('visual_style', 'unknown')}"
                ]
                
                bubble_html = "<div>"
                for char in characteristics:
                    bubble_html += f'<div class="bubble">{char}</div> '
                bubble_html += "</div>"
                
                st.markdown(bubble_html, unsafe_allow_html=True)
                
                # Script display
                script_text = st.session_state.video_status.get('override_script', '')
                if script_text:
                    st.markdown(f"""
                        <div class="card">
                            <h3>Script</h3>
                            <p>{script_text}</p>
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No video has been created yet. Go to the 'Create Video' tab to create one.")

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding: 1rem; background-color: #f8f9fa; border-radius: 10px;">
    <p>Created with Creatify AI API and Streamlit</p>
</div>
""", unsafe_allow_html=True)
