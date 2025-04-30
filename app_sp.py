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
    client = genai.Client(api_key=GEMINI_API_KEY)
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
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=prompt        )
        
        # Get the response text from the response object
        response_text = response.candidates[0].content.parts[0].text
        
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

            # In Step 4 (Create Video), we need to add the voice selection UI
            # Add this code right after the aspect_ratio selection
            
            # Get available voices
            voices = get_voices()
            
            # Display voice selection
            st.subheader("Select Voice")
            voice_cols = st.columns(2)
            
            with voice_cols[0]:
                # Filter voices by selected language if needed
                filtered_voices = [v for v in voices if language in v.get("voice_id", "").lower()] if language else voices
                if not filtered_voices and voices:
                    # Fallback to all voices if no matches for language
                    filtered_voices = voices
                    st.warning(f"No voices found for {language} language. Showing all available voices.")
                
                voice_options = [(v.get("voice_id"), f"{v.get('name')} ({v.get('gender')}, {v.get('language')})") 
                                 for v in filtered_voices]
                
                # Add a "None" option
                voice_options = [("", "Default Voice")] + voice_options
                
                # Get voice IDs and display names
                voice_ids, voice_names = zip(*voice_options) if voice_options else ([""], ["No voices available"])
                
                # Create the selectbox
                selected_voice_index = st.selectbox("Voice", range(len(voice_ids)), 
                                                   format_func=lambda i: voice_names[i])
                selected_voice = voice_ids[selected_voice_index]
            
            with voice_cols[1]:
                voice_volume = st.slider("Voice Volume", 0.0, 1.0, 0.5, 0.1)
        
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
                voice_id=selected_voice,  # Add the selected voice
                volume=voice_volume  # Add the voice volume
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

# Step 5: View Results
elif st.session_state.step == 5:
    st.header("Video Results")
    
    if not st.session_state.video_data:
        st.error("No video data available. Please go back and create a video.")
        st.session_state.step = 4
        st.button("Go Back", on_click=lambda: st.rerun())
    else:
        # Get current status
        video_id = st.session_state.video_data.get("id")
        video_status, status_error = get_video_status(video_id)
        
        if status_error:
            st.error(status_error)
        else:
            # Update session state
            st.session_state.video_data = video_status
            
            # Display status card
            status = video_status.get("status", "unknown")
            progress = video_status.get("progress", 0)
            
            st.markdown(f"""
                <div class="card">
                    <h3>Video Status</h3>
                    <p><strong>Project:</strong> {st.session_state.project_name}</p>
                    <p><strong>Status:</strong> {status}</p>
                    <p><strong>Progress:</strong> {progress*100:.0f}%</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.progress(progress)
            
            # Show characteristics in bubbles
            st.subheader("Video Characteristics")
            
            characteristics = [
                f"Platform: {video_status.get('target_platform', 'unknown')}",
                f"Audience: {video_status.get('target_audience', 'unknown')}",
                f"Length: {video_status.get('video_length', 0)} seconds",
                f"Aspect Ratio: {video_status.get('aspect_ratio', 'unknown')}",
                f"Language: {video_status.get('language', 'unknown')}",
                f"Style: {video_status.get('visual_style', 'unknown')}"
            ]
            
            bubble_html = "<div>"
            for char in characteristics:
                bubble_html += f'<div class="bubble">{char}</div> '
            bubble_html += "</div>"
            
            st.markdown(bubble_html, unsafe_allow_html=True)
            
            # Check status and show appropriate content
            if status == "pending" or status == "running":
                st.info("Your video is being processed. This may take a few minutes.")
                
                # Show refresh button
                if st.button("Refresh Status"):
                    st.rerun()
                
                # Show preview if available
                preview_url = video_status.get("preview")
                if preview_url:
                    st.subheader("Preview")
                    st.markdown(f"""
                        <div class="card">
                            <p>View your video preview:</p>
                            <a href="{preview_url}" target="_blank" class="stButton">
                                <button>Open Preview</button>
                            </a>
                        </div>
                    """, unsafe_allow_html=True)
            
            elif status == "done":
                st.success("Your video is ready!")
                
                # Display the video
                video_url = video_status.get("video_output")
                if video_url:
                    st.subheader("Your Video")
                    st.markdown(f"""
                        <div class="video-container">
                            <video width="100%" controls>
                                <source src="{video_url}" type="video/mp4">
                                Your browser does not support video playback.
                            </video>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Download button
                    st.download_button(
                        label="Download Video",
                        data=requests.get(video_url).content,
                        file_name=f"{st.session_state.project_name.replace(' ', '_')}.mp4",
                        mime="video/mp4"
                    )
                    
                    # Show script for reference
                    st.subheader("Script")
                    st.markdown(f"""
                        <div class="card">
                            <p>{st.session_state.screenplay_data.get('final_script')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Video URL not available. There might be an issue with the video.")
            
            elif status == "failed":
                st.error("Video creation failed.")
                failed_reason = video_status.get("failed_reason", "Unknown reason")
                st.write(f"Reason: {failed_reason}")
                
                # Option to try again
                if st.button("Try Again"):
                    st.session_state.step = 4
                    st.rerun()
            
            # Render button (for pending/running status)
            if status != "done" and status != "failed":
                if st.button("Render Final Video"):
                    with st.spinner("Rendering video..."):
                        render_result, render_error = render_video(video_id)
                        
                        if render_error:
                            st.error(render_error)
                        else:
                            st.session_state.video_data = render_result
                            st.success("Rendering started!")
                            st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding: 1rem; background-color: #f8f9fa; border-radius: 10px;">
    <p>Complete AI Video Pipeline: Brief → Screenplay → Images → Video</p>
</div>
""", unsafe_allow_html=True)
