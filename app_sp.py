import streamlit as st
import pandas as pd
import requests
import time
import os
import re
import json
import uuid
import base64
from io import BytesIO
from PIL import Image
from elevenlabs import ElevenLabs

# Optional imports for Google Gemini integration
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    
# Optional imports for CrewAI integration
try:
    from crewai import Agent, Task, Crew
    from langchain_serper import SerperDevTool
    CREW_AVAILABLE = True
except ImportError:
    CREW_AVAILABLE = False

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
if 'screenplay_data' not in st.session_state:
    st.session_state.screenplay_data = None
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = None
if 'creatify_link' not in st.session_state:
    st.session_state.creatify_link = None
if 'creatify_avatars' not in st.session_state:
    st.session_state.creatify_avatars = []

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

# Function to run the AI Crew for screenplay generation
def run_screenplay_crew(campaign_summary):
    st.info("Generating screenplay with AI Crew... (This may take a few minutes)")
    progress_bar = st.progress(0)
    
    # Check if CrewAI is available
    if not CREW_AVAILABLE:
        # Simulate the workflow execution with progress updates if CrewAI is not available
        for i in range(10):
            progress_bar.progress((i+1)/10)
            time.sleep(1)  # Simulate work being done
        
        # Return a sample result
        result = {
            "title": "Finding Financial Freedom",
            "style": "screenplay",
            "screenplay": "INT. LIVING ROOM - NIGHT\n\nA PERSON sits surrounded by bills, face illuminated by laptop screen, showing clear signs of stress.\n\nEXT. PARK - DAY\n\nSame person walks confidently, smiling as they talk on phone.\n\nINT. OFFICE - DAY\n\nFinancial advisor shows decreasing debt chart to person who reacts with relief.\n\nEXT. CAFE - DAY\n\nPerson enjoys coffee, carefree, checking phone with satisfaction.",
            "image_prompts": [
                "Person in dimly lit living room surrounded by bills, face showing stress and worry, illuminated by laptop screen with financial website visible",
                "Same person walking confidently through sunny park, smiling while talking on phone, with visible relief on their face",
                "Professional office setting with financial advisor showing declining debt chart on tablet to relieved client",
                "Person sitting at outdoor cafe, relaxed and smiling while checking positive bank balance on smartphone"
            ],
            "final_script": "You're not alone... Financial stress is affecting so many. Real help for real debt. Professional, confidential support awaits. Take the first step... Start your free debt review today."
        }
        
        return result
    
    # If CrewAI is available, use the actual implementation
    try:
        from pydantic import BaseModel
        from typing import List, Optional
        
        # Define the output model for the screenplay
        class ScriptOutput(BaseModel):
            title: str
            style: str
            hook: str = None
            body: str = None
            cta: str = None
            final_script: str = None
            screenplay: str = None
            image_prompts: List[str] = None  # List of prompts for the scenes
        
        # Define the Task planning Agent
        task_planning = Agent(
            role = "Workflow Architect for Ad Creation",
            goal = "transform a clean campaign summary into a detailed workflow and instructions for research and script writing agents.",
            backstory = """An experienced workflow architect specializing in streamlining creative processes for advertising campaigns. They excel at dissecting campaign objectives and translating them into clear, sequential tasks for specialized agents. With a deep understanding of the content creation lifecycle, they ensure that research and scripting are aligned and contribute effectively to the overall campaign goals. They focus on providing precise guidance to each agent, maximizing efficiency and creative output.""",
            memory = True,
            verbose = True,
            delegation = False,
            tools=[SerperDevTool()]  # Still useful for the architect to understand the landscape
        )
        
        # Update progress
        progress_bar.progress(0.2)
        
        # Define the researcher agent
        researcher = Agent(
            role = f"Researcher for Ad Script Generation",
            goal = f"Uncover the most effective trends, winning script elements, and impactful character characteristics relevant to creating a high-impact online ad as per user requirements and search by passing a string to the tool.",
            backstory = f"A seasoned researcher with an insatiable curiosity for understanding human behavior and the ever-shifting digital landscape, this agent brings years of experience in dissecting online trends and identifying the core elements that drive engagement. With a background in market research and digital anthropology, they possess a sharp eye for spotting emerging patterns and understanding the nuances of online communities. Their expertise lies in sifting through vast amounts of data – from social media analytics to competitor analysis – to extract the crucial insights that inform effective communication. They have a proven track record of identifying the 'why' behind successful online content, understanding what resonates with specific demographics and the psychological triggers that lead to action. Their ability to synthesize complex information into clear, actionable intelligence makes them an invaluable asset in laying the groundwork for impactful advertising. Furthermore, their understanding of the local context, provides an added layer of cultural sensitivity to their research.",
            memory = True,
            verbose = True,
            tools=[SerperDevTool()]
        )
        
        # Update progress
        progress_bar.progress(0.4)
        
        # Define the script writer agent
        new_writer = Agent(
            role="Script Writer for Online Ad Creatives",
            goal=(
                "Craft authentic, emotionally engaging ad scripts tailored for online platforms. "
                "Supports both UGC-style testimonial scripts and cinematic screenplay-style storytelling based on user instructions."
            ),
            backstory=(
                "A versatile storyteller with a background in social media marketing, digital filmmaking, and brand storytelling. "
                "Fluent in both casual UGC formats and cinematic screenwriting, this agent crafts scripts that align with digital trends while delivering emotional and visual impact. "
                "Whether writing in first-person influencer voice or formatting scenes for visual storytelling, this agent ensures brand alignment and audience resonance."
            ),
            memory=True,
            verbose=True,
            tools=[]
        )
        
        # Update progress
        progress_bar.progress(0.6)
        
        # Define the workflow generation task
        workflow_generation_task = Task(
            description = f"""The user has provided a clean and concise summary of the ad campaign requirements.
            {campaign_summary}

            The Workflow Architect will:
            1. Analyze the campaign summary to identify key information relevant to research and scripting.
            2. Define specific research objectives and questions that a research agent should address.
            3. Outline the core elements and guidelines for the script, including tone, style, target audience considerations, and the desired call-to-action.
            4. Create a structured brief for both the Research Agent and the Script Writing Agent, ensuring clarity and alignment.
            5. Consider any dependencies between the research and scripting phases.
            6. Searches should always be made in string only """,
            expected_output = """A structured workflow and set of briefs that includes:

            **For the Research Agent:**
            1. Specific research questions or areas of focus derived from the campaign summary.
            2. Key information the research should uncover to inform the script (e.g., audience insights, product details, competitive landscape).
            3. Suggested research methodologies or sources (if applicable).

            **For the Script Writing Agent:**
            1. A clear understanding of the target audience and their key characteristics.
            2. The desired tone and style of the script.
            3. Specific messaging points that must be included.
            4. Detailed instructions for the call-to-action.
            5. Any relevant background information or context from the campaign summary.
            6. (Optional) Examples or references for inspiration (if identified as helpful).

            **Overall Workflow Notes:**
            1. Any dependencies or the suggested order of tasks between research and scripting.
            2. Any overarching considerations for both agents to keep in mind.""",
            agent = task_planning
        )
        
        # Define the research task
        research_task = Task(
            description = f"""Conduct thorough research based on the provided instructions to uncover the most effective trends, winning script elements, and impactful character characteristics relevant to the target audience and product. Pay close attention to the specific research questions and objectives outlined in the instructions. Focus on online advertising only and ensure all findings are directly relevant to the campaign goals. Searches should always be made in string only""",
            expected_output = f"""A structured report containing the findings for each of the research questions and objectives provided in the input. This report should provide clear and actionable insights for the Writing Agent.""",
            agent = researcher,
            input_keys=["research_instructions", "campaign_context"] # Expecting these from task_planning
        )
        
        # Update progress
        progress_bar.progress(0.8)
        
        # Define the writing task
        new_writing_task = Task(
            description="""Using the research insights and script guidelines provided, craft a high-converting, emotionally engaging **screenplay-style ad creative**.

            The script must adhere to the specified tone, style, target audience profile, and call-to-action. Integrate the research findings on trends, winning script elements, and impactful visual storytelling techniques to create a compelling cinematic ad.
            
            Write the ad as a properly formatted screenplay with SCENE HEADINGS, action descriptions, and minimal dialogue. The narrative structure should still follow the Hook → Body → CTA format while maintaining a natural, cinematic tone suitable for the target audience and should adhere to creative timings as per screenplay.
            
            Additionally, create one AI image prompt per scene to help visualize the story. These prompts should capture the essence of each scene and align with the overall emotional journey of the ad.""",
            
            expected_output="""A JSON object containing the screenplay-style ad:

            {
                "title": "A descriptive ad title",
                "style": "screenplay",
                "screenplay": "Full formatted screenplay with scene headings, action descriptions, and dialogue",
                "image_prompts": ["One descriptive AI image prompt per scene"],
                "final_script": "Complete voiceover content/text"
            }
            
            The screenplay should:
            - Begin with a powerful HOOK scene that grabs attention
            - Develop through BODY scenes that showcase product benefits/experiences
            - End with a compelling CTA scene that drives action
            
            The final_script should contain the voiceover content or narration text that follows the Hook → Body → CTA structure and would be spoken during the ad
            
            Formatting guidelines:
            - Use proper screenplay format (SCENE HEADINGS, action paragraphs, character dialogue)
            - Use ellipses (...) for dramatic pauses
            - Use CAPITALIZATION for emphasis
            - Keep total word count under 200
            """,
            
            agent=new_writer,
            input_keys=["research_report", "script_guidelines", "campaign_context"],
            
            output_json=ScriptOutput
        )
        
        # Create the crew with all agents and tasks
        crew = Crew(
            agents=[task_planning, researcher, new_writer],
            tasks=[workflow_generation_task, research_task, new_writing_task],
            verbose=True
        )
        
        # Run the crew workflow
        result = crew.kickoff()
        
        # Update progress to completion
        progress_bar.progress(1.0)
        
        return result
    
    except Exception as e:
        st.error(f"Error in CrewAI workflow: {str(e)}")
        # Fall back to the sample result on error
        return {
            "title": "Finding Financial Freedom",
            "style": "screenplay",
            "screenplay": "INT. LIVING ROOM - NIGHT\n\nA PERSON sits surrounded by bills, face illuminated by laptop screen, showing clear signs of stress.\n\nEXT. PARK - DAY\n\nSame person walks confidently, smiling as they talk on phone.\n\nINT. OFFICE - DAY\n\nFinancial advisor shows decreasing debt chart to person who reacts with relief.\n\nEXT. CAFE - DAY\n\nPerson enjoys coffee, carefree, checking phone with satisfaction.",
            "image_prompts": [
                "Person in dimly lit living room surrounded by bills, face showing stress and worry, illuminated by laptop screen with financial website visible",
                "Same person walking confidently through sunny park, smiling while talking on phone, with visible relief on their face",
                "Professional office setting with financial advisor showing declining debt chart on tablet to relieved client",
                "Person sitting at outdoor cafe, relaxed and smiling while checking positive bank balance on smartphone"
            ],
            "final_script": "You're not alone... Financial stress is affecting so many. Real help for real debt. Professional, confidential support awaits. Take the first step... Start your free debt review today."
        }

.placeholder.com/512x512" for _ in range(len(image_prompts))]
    
    # Initialize the gemini client
    try:
        client = genai.Client(api_key=gemini_api_key)
    except Exception as e:
        st.error(f"Error initializing Gemini client: {str(e)}")
        return ["https://via.placeholder.com/512x512" for _ in range(len(image_prompts))]
    
    # Lists to store generated image information
    image_urls = []
    
    # Process each prompt
    progress_bar = st.progress(0)
    
    for i, prompt in enumerate(image_prompts):
        progress_bar.progress((i+1)/len(image_prompts))
        
        try:
            # Use a descriptive col header
            st.write(f"**Scene {i+1}**: {prompt[:100]}...")
            
            # Generate image (simulate for now)
            time.sleep(2)  # Simulate API latency
            
            # Add placeholder URL (in real implementation, this would be the actual generated image URL)
            image_urls.append(f"https://via.placeholder.com/512x512?text=Scene+{i+1}")
            
            # Display placeholder image
            st.image(f"https://via.placeholder.com/512x512?text=Scene+{i+1}", caption=f"Generated image for Scene {i+1}")
            
        except Exception as e:
            st.error(f"Error generating image {i+1}: {str(e)}")
            image_urls.append("https://via.placeholder.com/512x512?text=Error")
    
    return image_urls

# Function to create a Creatify Link from generated images
def create_creatify_link(image_urls, title="Generated Images Collection", description="Images generated with Google Gemini"):
    st.info("Creating Creatify link for generated images...")
    
    # Filter out any None values
    valid_image_urls = [url for url in image_urls if url is not None]
    
    if not valid_image_urls:
        return "No valid image URLs to create a link with.", None
    
    # Prepare payload for Creatify API
    url = "https://api.creatify.ai/api/links/link_with_params/"
    
    payload = {
        "title": title,
        "description": description,
        "image_urls": valid_image_urls,
        "video_urls": [],
        "reviews": "Finding Your Way to Financial Freedom"
    }
    
    headers = {
        "X-API-ID": creatify_api_id,
        "X-API-KEY": creatify_api_key,
        "Content-Type": "application/json"
    }
    
    try:
        # Make the API request
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            return f"Error creating Creatify link: {response.status_code} - {response.text}", None
        
        response_data = response.json()
        
        # Return the link URL and full response data
        if 'url' in response_data:
            return f"✅ Successfully created Creatify link: {response_data['url']}", response_data
        else:
            return "Link created but no URL found in response", response_data
        
    except Exception as e:
        return f"Exception during Creatify link creation: {str(e)}", None

# Function to get available Creatify avatars
def get_creatify_avatars():
    url = "https://api.creatify.ai/api/personas/paginated/"
    
    headers = {
        "X-API-ID": creatify_api_id,
        "X-API-KEY": creatify_api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            st.error(f"Error fetching Creatify avatars: {response.status_code} - {response.text}")
            return []
        
        data = response.json()
        
        # Extract relevant avatar information
        avatars = []
        for avatar in data.get('results', []):
            avatars.append({
                'id': avatar.get('id'),
                'gender': avatar.get('gender'),
                'age_range': avatar.get('age_range'),
                'style': avatar.get('style'),
                'preview_image': avatar.get('preview_image_1_1') or avatar.get('preview_image_16_9'),
                'is_active': avatar.get('is_active')
            })
        
        return avatars
    
    except Exception as e:
        st.error(f"Exception while fetching Creatify avatars: {e}")
        return []

# Function for Creatify API video generation
def generate_screenplay_video(screenplay_script, name="AI TEST", target_platform="Facebook", 
                             target_audience="Debt Payers", language="en", video_length=30,
                             aspect_ratio="16x9", visual_style="GreenScreenEffectTemplate", 
                             avatar_id="a7a240e8-efbf-4ab5-a02d-0f367a810875", link_id=None):
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
        "link": link_id or "9a98f404-f3d9-4f74-b452-f73013be938f",
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
        video_id = response_data.get("id")
        
        if not video_id:
            return "❌ No video ID returned by Creatify.", None
        
        # Check if we need to poll for completion
        if response_data.get("status") != "done":
            # Initialize progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Poll for completion
            for i in range(30):  # Up to ~5 minutes
                progress_percentage = min(response_data.get("progress", 0), 1.0)
                progress_bar.progress(progress_percentage)
                status_text.text(f"Video processing: {int(progress_percentage * 100)}% complete...")
                
                if response_data.get("status") == "done":
                    break
                    
                time.sleep(10)  # Check every 10 seconds
                status_response = requests.get(f"https://api.creatify.ai/api/link_to_videos/{video_id}/", headers=headers)
                response_data = status_response.json()
            
            # Final status check
            if response_data.get("status") != "done":
                # Try to render the video if it's not done yet
                try:
                    render_response = requests.post(f"https://api.creatify.ai/api/link_to_videos/{video_id}/render/", headers=headers)
                    if render_response.status_code == 200:
                        render_data = render_response.json()
                        if render_data.get("video_output"):
                            return f"✅ Screenplay video is ready after render!", render_data
                    return "⏳ Screenplay video is still processing. Please check back later.", response_data
                except Exception as e:
                    return f"❌ Error rendering video: {str(e)}", response_data
        
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
    
    # If there are no session state variables for screenplay generation, initialize them
    if 'screenplay_data' not in st.session_state:
        st.session_state.screenplay_data = None
    if 'generated_images' not in st.session_state:
        st.session_state.generated_images = None
    if 'creatify_link' not in st.session_state:
        st.session_state.creatify_link = None
    
    # Create tabs for different steps of screenplay generation
    tabs = st.tabs(["Step 1: Generate Screenplay", "Step 2: Generate Images", "Step 3: Create Video"])
    
    # Tab 1: Generate Screenplay
    with tabs[0]:
        st.subheader("Generate Screenplay with AI Crew")
        
        # Form for campaign details to generate screenplay
        with st.form("screenplay_generation_form"):
            st.write("Provide campaign details to generate a compelling screenplay:")
            
            campaign_goal = st.text_area("What is the goal of your campaign?", 
                                         "Help people struggling with debt find financial freedom")
            target_audience = st.text_area("Who is your target audience?", 
                                          "Adults 30-55 years old, stressed about debt, looking for solutions")
            key_message = st.text_area("What is the key message you want to convey?", 
                                      "Professional debt relief services can help overcome financial stress")
            preferred_style = st.selectbox("What emotional tone should the ad have?",
                                         ["Inspirational", "Empathetic", "Informative", "Urgent", "Hopeful"])
            
            generate_button = st.form_submit_button("Generate Screenplay")
            
            if generate_button:
                # Construct a summary from the form inputs
                campaign_summary = f"""
                Campaign Goal: {campaign_goal}
                Target Audience: {target_audience}
                Key Message: {key_message}
                Preferred Style: {preferred_style}
                """
                
                # Run the Crew AI to generate screenplay
                with st.spinner("Generating screenplay with CrewAI..."):
                    screenplay_data = run_screenplay_crew(campaign_summary)
                    st.session_state.screenplay_data = screenplay_data
                    st.session_state.screenplay_script = screenplay_data["final_script"]
                
                st.success("✅ Screenplay generated successfully!")
                
        # Display screenplay data if available
        if st.session_state.screenplay_data:
            data = st.session_state.screenplay_data
            
            st.subheader("Generated Screenplay")
            
            # Display title
            st.write(f"### {data['title']}")
            
            # Display screenplay in an expander
            with st.expander("View Screenplay", expanded=True):
                st.code(data["screenplay"], language=None)
            
            # Display script in an expander
            with st.expander("View Final Script", expanded=True):
                st.write(data["final_script"])
                
                # Add edit button for the script
                if st.button("Edit Script"):
                    st.session_state.screenplay_script = st.text_area("Edit Script", 
                                                                    value=data["final_script"], 
                                                                    height=150)
                    if st.button("Save Edited Script"):
                        st.session_state.screenplay_data["final_script"] = st.session_state.screenplay_script
                        st.success("Script updated!")
            
            # Display image prompts
            st.subheader("Generated Image Prompts")
            for i, prompt in enumerate(data["image_prompts"]):
                st.write(f"**Scene {i+1}**: {prompt}")
            
            # Button to proceed to image generation
            if st.button("Proceed to Image Generation", use_container_width=True):
                st.success("Navigate to the 'Generate Images' tab to create visuals for your screenplay!")
    
    # Tab 2: Generate Images
    with tabs[1]:
        st.subheader("Generate Images for Screenplay")
        
        # Check if screenplay data is available
        if not st.session_state.screenplay_data:
            st.warning("Please generate a screenplay first in Step 1!")
        else:
            data = st.session_state.screenplay_data
            
            # Display the image prompts
            st.write("### Image Prompts")
            for i, prompt in enumerate(data["image_prompts"]):
                st.write(f"**Scene {i+1}**: {prompt}")
            
            # Button to generate images
            if st.button("Generate Images with Google Gemini"):
                with st.spinner("Generating images... This may take a few minutes."):
                    # Generate images using Gemini API
                    image_urls = generate_gemini_images(data["image_prompts"])
                    st.session_state.generated_images = image_urls
                
                st.success("✅ Images generated successfully!")
            
            # Display generated images if available
            if st.session_state.generated_images:
                st.subheader("Generated Images")
                
                # Display images in a grid
                cols = st.columns(2)
                for i, url in enumerate(st.session_state.generated_images):
                    with cols[i % 2]:
                        st.image(url, caption=f"Scene {i+1}", use_column_width=True)
                
                # Button to create Creatify link
                if st.button("Create Creatify Link for Images", use_container_width=True):
                    with st.spinner("Creating Creatify link..."):
                        status_msg, link_data = create_creatify_link(
                            st.session_state.generated_images,
                            title=data["title"],
                            description=f"Visual scenes for {data['title']}"
                        )
                        
                        st.session_state.creatify_link = link_data
                        st.success(status_msg)
                        
                        if link_data and 'url' in link_data:
                            st.write(f"**Creatify Link:** {link_data['url']}")
                
                # Button to proceed to video generation
                if st.button("Proceed to Video Generation", use_container_width=True):
                    st.success("Navigate to the 'Create Video' tab to generate your final video!")
    
    # Tab 3: Create Video
    with tabs[2]:
        st.subheader("Generate Video with Creatify.ai")
        
        # Check if screenplay is available
        if not st.session_state.screenplay_data:
            st.warning("Please generate a screenplay first in Step 1!")
        else:
            # If there's no screenplay script yet, initialize with the one from the data
            if not hasattr(st.session_state, 'screenplay_script'):
                st.session_state.screenplay_script = st.session_state.screenplay_data["final_script"]
            
            # Script editing section
            st.subheader("Edit Your Screenplay Script")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                new_screenplay_script = st.text_area("Screenplay Script", st.session_state.screenplay_script, height=150)
                
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
            
            # Get available avatars (in a real implementation, this would fetch from the API)
            if 'creatify_avatars' not in st.session_state:
                with st.spinner("Loading avatars..."):
                    st.session_state.creatify_avatars = get_creatify_avatars()
            
            # Display avatars if available
            if st.session_state.creatify_avatars:
                st.write("### Available Avatars")
                
                # Display avatars in a grid
                avatar_cols = st.columns(4)
                selected_avatar_id = "a7a240e8-efbf-4ab5-a02d-0f367a810875"  # Default
                
                for i, avatar in enumerate(st.session_state.creatify_avatars[:8]):  # Limit to 8 avatars for display
                    with avatar_cols[i % 4]:
                        if avatar.get('preview_image'):
                            st.image(avatar.get('preview_image'), width=100)
                        else:
                            st.image("https://via.placeholder.com/100?text=Avatar", width=100)
                        
                        avatar_info = f"{avatar.get('gender', 'unknown')} {avatar.get('age_range', 'adult')}"
                        st.write(avatar_info)
                        
                        if st.button(f"Select Avatar {i+1}", key=f"avatar_{avatar.get('id')}"):
                            selected_avatar_id = avatar.get('id')
                            st.success(f"Selected avatar: {avatar_info}")
            
            # Video generation form
            with st.form("video_generation_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    video_name = st.text_input("Video Name", st.session_state.screenplay_data["title"] if st.session_state.screenplay_data and "title" in st.session_state.screenplay_data else "AI Debt Relief Campaign")
                    target_platform = st.selectbox("Target Platform", ["Facebook", "Instagram", "YouTube", "TikTok", "LinkedIn"])
                    target_audience = st.text_input("Target Audience", "Debt Payers")
                    language = st.selectbox("Language", ["en", "es", "fr", "de", "it"])
                
                with col2:
                    video_length = st.slider("Video Length (seconds)", min_value=15, max_value=60, value=30, step=5)
                    aspect_ratio = st.selectbox("Aspect Ratio", ["16x9", "9x16", "1x1", "4x5"])
                    visual_style = st.selectbox("Visual Style", ["GreenScreenEffectTemplate", "ModernCorporate", "Casual", "Professional", "Energetic"])
                
                # Additional options
                st.markdown("### Additional Options")
                
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
                
                # Use Creatify link if available
                link_id = None
                if st.session_state.creatify_link and 'link' in st.session_state.creatify_link and 'id' in st.session_state.creatify_link['link']:
                    link_id = st.session_state.creatify_link['link']['id']
                    st.info(f"Using generated images from Creatify link: {st.session_state.creatify_link.get('url', 'Unknown URL')}")
                
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
                        avatar_id=selected_avatar_id,
                        link_id=link_id
                    )
                    
                    # Store the response in session state
                    st.session_state.creatify_response = response_data
                    
                    # Display status message
                    st.markdown(status_msg)
                    
                    # Show preview if available
                    if response_data and "preview" in response_data and response_data["preview"]:
                        st.markdown(f"**Preview URL:** [View Preview]({response_data['preview']})")
                    
                    # Show render button if status is not "done"
                    if response_data and response_data.get("status") != "done" and "id" in response_data:
                        video_id = response_data["id"]
                        if st.button("Render Final Video"):
                            with st.spinner("Rendering final video..."):
                                render_url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/render/"
                                headers = {
                                    "X-API-ID": creatify_api_id,
                                    "X-API-KEY": creatify_api_key,
                                    "Content-Type": "application/json"
                                }
                                
                                try:
                                    render_response = requests.post(render_url, headers=headers)
                                    if render_response.status_code == 200:
                                        render_data = render_response.json()
                                        st.session_state.creatify_response = render_data
                                        
                                        st.success("✅ Video rendering started successfully!")
                                        
                                        if "video_output" in render_data and render_data["video_output"]:
                                            st.video(render_data["video_output"])
                                    else:
                                        st.error(f"Error rendering video: {render_response.status_code} - {render_response.text}")
                                except Exception as e:
                                    st.error(f"Exception during video rendering: {str(e)}")
            
            # Display generated video if available
            if "creatify_response" in st.session_state and st.session_state.creatify_response:
                st.subheader("Generated Video")
                
                # Extract video details
                video_data = st.session_state.creatify_response
                
                # Display preview URL if available
                if "preview" in video_data and video_data["preview"]:
                    st.markdown(f"**Preview URL:** [View Preview]({video_data['preview']})")
                
                # Display the video if available
                if "video_output" in video_data and video_data["video_output"]:
                    st.video(video_data["video_output"])
                    
                    # Add download button for the video
                    st.markdown(f"[Download Video]({video_data['video_output']})")
                    
                    # Display thumbnail if available
                    if "video_thumbnail" in video_data and video_data["video_thumbnail"]:
                        st.image(video_data["video_thumbnail"], caption="Video Thumbnail")
                
                # Display video details in an expander
                with st.expander("Video Details"):
                    # Format the JSON for readability
                    formatted_json = json.dumps(video_data, indent=2)
                    st.code(formatted_json, language="json")
            
            # Navigation buttons
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Back to Script Editor", use_container_width=True):
                    st.session_state.step = "edit_script"
                    st.rerun()
            
            with col2:
                if st.button("Generate Audio", use_container_width=True):
                    st.session_state.step = "audio_generation"
                    st.rerun()
            
            with col3:
                if st.button("Generate Regular Video", use_container_width=True):
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

# Add information about the AI agents used in screenplay generation
with st.sidebar:
    st.markdown("### AI Crew for Screenplay Generation")
    
    with st.expander("About the AI Crew"):
        st.markdown("""
        **Workflow Architect Agent**: Analyzes campaign requirements and creates a structured workflow.
        
        **Research Agent**: Uncovers trends, winning script elements, and audience insights.
        
        **Script Writer Agent**: Crafts authentic, emotionally engaging ad scripts with both UGC-style testimonials and cinematic screenplay formats.
        
        The crew works together to create high-converting video content based on your campaign brief.
        """)
    
    with st.expander("About Creatify.ai Integration"):
        st.markdown("""
        The AdGen AI Platform integrates with Creatify.ai to generate professional videos based on AI-generated screenplays.
        
        **Features**:
        - Automatic script-to-video conversion
        - Professional AI avatars
        - Multiple aspect ratios and visual styles
        - Customizable captions and formatting
        - Image collection for rich visuals
        
        Learn more at [Creatify.ai](https://creatify.ai)
        """)
    
    with st.expander("About Google Gemini Integration"):
        st.markdown("""
        We use Google's Gemini AI to generate high-quality images for each scene in your screenplay.
        
        These images can be:
        - Used in your video productions
        - Combined into Creatify collections
        - Downloaded for other marketing materials
        - Customized with detailed prompts
        """)
    
    # Add example button
    if st.button("Load Example Campaign", use_container_width=True):
        # Set example data in session state
        st.session_state.screenplay_data = {
            "title": "Finding Financial Freedom",
            "style": "screenplay",
            "screenplay": "INT. LIVING ROOM - NIGHT\n\nA PERSON sits surrounded by bills, face illuminated by laptop screen, showing clear signs of stress.\n\nEXT. PARK - DAY\n\nSame person walks confidently, smiling as they talk on phone.\n\nINT. OFFICE - DAY\n\nFinancial advisor shows decreasing debt chart to person who reacts with relief.\n\nEXT. CAFE - DAY\n\nPerson enjoys coffee, carefree, checking phone with satisfaction.",
            "image_prompts": [
                "Person in dimly lit living room surrounded by bills, face showing stress and worry, illuminated by laptop screen with financial website visible",
                "Same person walking confidently through sunny park, smiling while talking on phone, with visible relief on their face",
                "Professional office setting with financial advisor showing declining debt chart on tablet to relieved client",
                "Person sitting at outdoor cafe, relaxed and smiling while checking positive bank balance on smartphone"
            ],
            "final_script": "You're not alone... Financial stress is affecting so many. Real help for real debt. Professional, confidential support awaits. Take the first step... Start your free debt review today."
        }
        st.session_state.screenplay_script = st.session_state.screenplay_data["final_script"]
        st.session_state.step = "screenplay_generation"
        st.success("Example campaign loaded! Go to the Screenplay Generation page.")
        st.rerun()
