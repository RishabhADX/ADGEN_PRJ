import streamlit as st
import requests
import json
import base64
from PIL import Image
from io import BytesIO
import uuid
import time
import io
import re
from google import genai
from google.genai import types

# Page configuration
st.set_page_config(
    page_title="AI Video Generator Pipeline",
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
        background-color: #2196F3;
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
        background-color: #2196F3;
        color: white;
        font-weight: bold;
    }
    .screenplay {
        font-family: 'Courier New', monospace;
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 5px;
        white-space: pre-wrap;
    }
    .scene-heading {
        font-weight: bold;
        text-transform: uppercase;
    }
    .voice-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: white;
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

# Headers for API requests
headers = {
    "X-API-ID": API_ID,
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

# Initialize Gemini client
try:
    genai.configure(api_key=GEMINI_API_KEY)
    client = genai.GenerativeModel("gemini-1.5-pro")
except Exception as e:
    st.error(f"Failed to initialize Gemini: {str(e)}")

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

# Function to get available voices
@st.cache_data(ttl=3600)
def get_voices():
    url = "https://api.creatify.ai/api/voices/"
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        st.error(f"Error fetching voices: {str(e)}")
        # Return a fallback list of voices in case the API call fails
        return [
            {"voice_id": "en-US-Wavenet-A", "name": "US Male", "gender": "Male", "language": "English (US)"},
            {"voice_id": "en-US-Wavenet-C", "name": "US Female", "gender": "Female", "language": "English (US)"},
            {"voice_id": "en-GB-Wavenet-B", "name": "UK Male", "gender": "Male", "language": "English (UK)"},
            {"voice_id": "en-GB-Wavenet-C", "name": "UK Female", "gender": "Female", "language": "English (UK)"},
            {"voice_id": "es-ES-Wavenet-B", "name": "Spanish Male", "gender": "Male", "language": "Spanish"},
            {"voice_id": "fr-FR-Wavenet-C", "name": "French Female", "gender": "Female", "language": "French"}
        ]

# Function to generate screenplay using Gemini
def generate_screenplay(campaign_brief, tone, target_audience, product_details, num_scenes):
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

        # Use the generate_content method instead of generate_text
        response = client.generate_content(prompt)
        
        # Get the response text from the response object
        response_text = response.text
        
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

# Function to generate a voice preview
def generate_voice_preview(voice_id, text="This is a sample of how this voice sounds."):
    url = "https://api.creatify.ai/api/tts/"
    
    payload = {
        "text": text,
        "voice_id": voice_id
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        return data.get("audio_url"), None
    except Exception as e:
        return None, f"Error generating voice preview: {str(e)}"
        
# Function to generate image with Gemini
def generate_image(prompt):
    try:
        # Configure the generative model for image generation
        image_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate the image
        response = image_model.generate_content(prompt)
        
        # Check if there's content in the response
        if not hasattr(response, 'parts') or not response.parts:
            return None, "No content generated"
            
        for part in response.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                return part.inline_data.data, None
        
        return None, "No image found in response"
    except Exception as e:
        return None, str(e)

# Function to upload image to ImageKit
def upload_to_imagekit(image_data, filename):
    try:
        # Convert image to bytes if it's not already
        if isinstance(image_data, Image.Image):
            buffer = io.BytesIO()
            image_data.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
        else:
            image_bytes = image_data
            
        # Create a file-like object
        file_like = io.BytesIO(image_bytes)
        
        # Prepare the upload
        url = f"https://upload.imagekit.io/api/v1/files/upload"
        
        # Create authentication header
        auth_str = base64.b64encode(f"{IMAGEKIT_PRIVATE_KEY}:".encode()).decode()
        
        headers_upload = {
            "Authorization": f"Basic {auth_str}"
        }
        
        files = {
            'file': (filename, file_like, 'image/png'),
            'fileName': (None, filename),
            'publicKey': (None, IMAGEKIT_PUBLIC_KEY),
        }
        
        response = requests.post(url, files=files, headers=headers_upload)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("url"), result.get("fileId"), None
        else:
            return None, None, f"Upload failed with status {response.status_code}: {response.text}"
            
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
        "reviews": "Generated with AI Video Pipeline"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json(), None
    except Exception as e:
        return None, f"Error creating link: {str(e)}"

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

# Function to get video status
def get_video_status(video_id):
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/"
    
    try:
        response = requests.get(url, headers=headers)
        return response.json(), None
    except Exception as e:
        return None, f"Error getting video status: {str(e)}"

# Function to render video
def render_video(video_id):
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/render/"
    
    try:
        response = requests.post(url, headers=headers)
        return response.json(), None
    except Exception as e:
        return None, f"Error rendering video: {str(e)}"

# Function to format screenplay for display
def format_screenplay_display(screenplay_text):
    # Replace scene headings with styled versions
    formatted = re.sub(r'(INT\.|EXT\.)(.*?)(?=\n)', r'<div class="scene-heading">\1\2</div>', screenplay_text)
    # Replace double line breaks with paragraph breaks
    formatted = formatted.replace('\n\n', '</p><p>')
    return f'<p>{formatted}</p>'

# Display header
st.markdown('<div class="header"><h1>🎬 AI Video Pipeline: From Brief to Video</h1></div>', unsafe_allow_html=True)

# Initialize session state for storing data between steps
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'screenplay_data' not in st.session_state:
    st.session_state.screenplay_data = None
if 'image_urls' not in st.session_state:
    st.session_state.image_urls = []
if 'link_data' not in st.session_state:
    st.session_state.link_data = None
if 'video_data' not in st.session_state:
    st.session_state.video_data = None

# Sidebar for navigation and status
with st.sidebar:
    st.header("Workflow")
    
    # Show workflow steps
    steps = [
        "1. Enter Campaign Details",
        "2. Generate Screenplay",
        "3. Generate & Upload Images",
        "4. Create Video",
        "5. View Results"
    ]
    
    for i, step in enumerate(steps):
        if i + 1 < st.session_state.step:
            st.success(step)
        elif i + 1 == st.session_state.step:
            st.info(step + " (Current)")
        else:
            st.write(step)
    
    # Reset button
    if st.button("Start Over"):
        st.session_state.step = 1
        st.session_state.screenplay_data = None
        st.session_state.image_urls = []
        st.session_state.link_data = None
        st.session_state.video_data = None
        st.rerun()

# Step 1: Enter Campaign Details
if st.session_state.step == 1:
    st.header("Enter Campaign Details")
    
    with st.form("campaign_form"):
        project_name = st.text_input("Project Name", "My AI Video")
        
        col1, col2 = st.columns(2)
        with col1:
            campaign_brief = st.text_area("Campaign Brief", "A financial service helping people manage and reduce their debt through personalized plans and expert guidance.")
            tone = st.selectbox("Tone", ["Professional", "Emotional", "Humorous", "Serious", "Inspirational", "Conversational"])
        
        with col2:
            target_audience = st.text_area("Target Audience", "Adults 30-55 who are struggling with debt and seeking reliable solutions to regain financial stability.")
            product_details = st.text_area("Product/Service Details", "Debt resolution services with personalized plans, expert financial advisors, and a track record of helping clients reduce debt by an average of 30%.")
        
        num_scenes = st.slider("Number of Scenes", 2, 5, 3)
        
        submitted = st.form_submit_button("Generate Screenplay")
        
        if submitted:
            with st.spinner("Generating screenplay..."):
                screenplay_data, error = generate_screenplay(
                    campaign_brief, tone, target_audience, product_details, num_scenes
                )
                if error:
                    st.error(f"Error generating screenplay: {error}")
                else:
                    st.session_state.screenplay_data = screenplay_data
                    st.session_state.project_name = project_name
                    st.session_state.step = 2
                    st.rerun()

# Step 2: Display Screenplay and Confirm
elif st.session_state.step == 2:
    st.header("Review Generated Screenplay")
    
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
    
    # Edit screenplay if needed
    if st.button("Edit Screenplay"):
        st.session_state.step = 1
        st.rerun()
    
    # Proceed to image generation
    if st.button("Generate Images from Prompts"):
        st.session_state.step = 3
        st.rerun()

# Step 3: Generate and Upload Images
elif st.session_state.step == 3:
    st.header("Generate & Upload Images")
    
    screenplay_data = st.session_state.screenplay_data
    image_prompts = screenplay_data["image_prompts"]
    
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
                filename = f"scene-{i+1:02d}-{st.session_state.project_name.replace(' ', '-')}.png"
                
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
                st.session_state.project_name,
                f"Images for {st.session_state.project_name}"
            )
            
            if link_error:
                st.error(link_error)
            else:
                st.session_state.image_urls = image_urls
                st.session_state.link_data = link_data
                st.session_state.step = 4
                status_text.empty()
                st.success("All images generated and uploaded! Link created successfully.")
                st.button("Continue to Video Creation", on_click=lambda: st.rerun())
        else:
            st.error("No images were successfully generated and uploaded. Please try again.")

# Step 4: Create Video
elif st.session_state.step == 4:
    st.header("Create Video")
    
    # Display images that will be used
    st.subheader("Images for Your Video")
    cols = st.columns(min(len(st.session_state.image_urls), 3))
    for i, url in enumerate(st.session_state.image_urls):
        with cols[i % len(cols)]:
            st.image(url, caption=f"Scene {i+1}", use_column_width=True)
    
    # Get available personas
    personas = get_personas()
    
    if personas:
        st.subheader("Select Avatar")
        
        # Display personas in a grid
        persona_cols = st.columns(3)
        selected_persona = None
        
        for i, persona in enumerate(personas[:6]):  # Limit to first 6 personas
            with persona_cols[i % 3]:
                persona_id = persona.get("id")
                preview_img = persona.get("preview_image_1_1")
                
                if preview_img:
                    st.image(preview_img, width=150)
                
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
                
                # Selection radio button
                if st.radio("Select", ["No", "Yes"], key=f"persona_{i}") == "Yes":
                    selected_persona = persona_id
        
        # Video settings
        st.subheader("Video Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            platform = st.selectbox("Target Platform", ["Facebook", "Instagram", "YouTube", "TikTok", "LinkedIn"])
            language = st.selectbox("Language", ["en", "es", "fr", "de"])
        
        with col2:
            video_length = st.slider("Video Length (seconds)", 15, 60, 30)
            aspect_ratio = st.selectbox("Aspect Ratio", ["16x9", "1x1", "9x16"])

        # Voice Selection Section
        st.subheader("Select Voice")
        
        # Initialize session state variables for voice selection if not present
        if 'selected_voice' not in st.session_state:
            st.session_state.selected_voice = ""
            st.session_state.selected_voice_name = ""
        
        # Initialize pagination state
        if 'voice_page' not in st.session_state:
            st.session_state.voice_page = 0
        
        # Get voices with their preview URLs
        voices = get_voices()
        
        # Create voice selection section with pagination
        if not voices:
            st.warning("No voices available")
        else:
            # Define page size and calculate total pages
            page_size = 10
            total_pages = (len(voices) + page_size - 1) // page_size
            
            # Display pagination controls
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if st.button("Previous", key="prev_voice_page", disabled=st.session_state.voice_page <= 0):
                    st.session_state.voice_page -= 1
                    st.rerun()
                    
            with col2:
                st.write(f"Page {st.session_state.voice_page + 1} of {max(1, total_pages)}")
                
            with col3:
                if st.button("Next", key="next_voice_page", disabled=st.session_state.voice_page >= total_pages - 1):
                    st.session_state.voice_page += 1
                    st.rerun()
            
            # Calculate slice of voices to display on current page
            start_idx = st.session_state.voice_page * page_size
            end_idx = min(start_idx + page_size, len(voices))
            page_voices = voices[start_idx:end_idx]
            
            # Display filter options
            st.write("#### Filter Options")
            col1, col2 = st.columns(2)
            
            with col1:
                filter_gender = st.selectbox("Gender", ["All", "Male", "Female"], key="voice_filter_gender")
            
            with col2:
                # Extract all unique languages from voices
                all_languages = sorted(set(voice.get("language", "Unknown") for voice in voices))
                filter_language = st.selectbox("Language", ["All"] + all_languages, key="voice_filter_language")
            
            # Filter voices based on selected criteria
            filtered_voices = page_voices
            if filter_gender != "All":
                filtered_voices = [v for v in filtered_voices if v.get("gender", "") == filter_gender]
            
            if filter_language != "All":
                filtered_voices = [v for v in filtered_voices if v.get("language", "") == filter_language]
            
            # Show message if no voices match filters
            if not filtered_voices:
                st.warning("No voices match your filters. Try different filter options.")
            
            # Display each voice with its audio player
            for voice in filtered_voices:
                voice_id = voice.get("voice_id", "")
                voice_name = voice.get("name", "Unnamed")
                voice_gender = voice.get("gender", "Unspecified")
                voice_language = voice.get("language", "Unknown")
                
                # Get preview URL if available
                preview_url = ""
                accent_name = ""
                accents = voice.get("accents", [])
                if accents and len(accents) > 0:
                    preview_url = accents[0].get("preview_url", "")
                    accent_name = accents[0].get("accent_name", "")
                
                # Check if this is the selected voice
                is_selected = st.session_state.selected_voice == voice_id
                
                # Create a card for each voice
                with st.container():
                    # Create a card div with conditional selected badge
                    st.markdown("""
                    <style>
                    .selected-badge {
                        position: absolute;
                        top: 10px;
                        right: 10px;
                        background-color: #28a745;
                        color: white;
                        padding: 5px 10px;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    selected_badge = '<div class="selected-badge">✓ Selected</div>' if is_selected else ''
                    st.markdown(f'<div class="voice-card">{selected_badge}', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Voice name and properties
                        st.markdown(f"### {voice_name}")
                        
                        # Show voice characteristics as bubbles
                        bubbles = [
                            f"Gender: {voice_gender}",
                            f"Language: {voice_language}"
                        ]
                        
                        if accent_name:
                            bubbles.append(f"Accent: {accent_name}")
                            
                        bubble_html = "<div>"
                        for bubble in bubbles:
                            bubble_html += f'<span class="bubble">{bubble}</span> '
                        bubble_html += "</div>"
                        
                        st.markdown(bubble_html, unsafe_allow_html=True)
                    
                    with col2:
                        # Select button
                        if st.button("Select", key=f"select_voice_{voice_id}", 
                                   disabled=is_selected,
                                   help="Click to select this voice"):
                            st.session_state.selected_voice = voice_id
                            st.session_state.selected_voice_name = voice_name
                            st.rerun()
                    
                    # Display audio player if we have a preview URL
                    if preview_url:
                        st.audio(preview_url, format="audio/mp3")
                    else:
                        with st.expander("Generate voice preview"):
                            preview_text = st.text_input("Enter text for preview", 
                                                      "Hello, this is a sample of how this voice sounds.", 
                                                      key=f"preview_text_{voice_id}")
                            
                            if st.button("Generate Preview", key=f"gen_preview_{voice_id}"):
                                with st.spinner("Generating voice preview..."):
                                    preview_url, preview_error = generate_voice_preview(voice_id, preview_text)
                                    
                                    if preview_error:
                                        st.error(preview_error)
                                    elif preview_url:
                                        st.audio(preview_url, format="audio/mp3")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Display currently selected voice with clear feedback
            if st.session_state.selected_voice:
                st.success(f"Selected voice: {st.session_state.selected_voice_name}")
                st.info(f"Voice ID: {st.session_state.selected_voice}")
                
                # Voice volume slider
                st.session_state.voice_volume = st.slider("Voice Volume", 0.0, 1.0, 0.5, 0.1)
            else:
                st.warning("No voice selected yet. Please select a voice before creating your video.")
                st.session_state.voice_volume = 0.5
        
        # Create video button
        if st.button("Create Video") and selected_persona and st.session_state.link_data:
            with st.spinner("Creating video..."):
                link_id = st.session_state.link_data.get("id")
                script = st.session_state.screenplay_data.get("final_script")
                
                video_data, video_error = create_video(
                    link_id,
                    st.session_state.project_name,
                    script,
                    selected_persona,
                    platform=platform,
                    language=language,
                    length=video_length,
                    ratio=aspect_ratio,
                    voice_id=st.session_state.selected_voice,
                    volume=st.session_state.voice_volume
                )
                
                if video_error:
                    st.error(video_error)
                else:
                    st.session_state.video_data = video_data
                    st.session_state.step = 5
                    st.success("Video creation initiated!")
                    st.button("View Results", on_click=lambda: st.rerun())
    else:
        st.error("No personas available. Please check your API connection.")
