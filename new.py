import streamlit as st
import sys
import os
import re
import requests
import pandas as pd
import datetime
import base64
import json
import time
from google.colab import drive
from IPython.display import Audio, display
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool
from pydantic import BaseModel
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from elevenlabs import ElevenLabs
import uuid
from imagekitio import ImageKit

# Environment setup
os.environ["SERPER_API_KEY"] = "14b865cf1dae8d1149dea6a7d2c93f8ac0105970"
os.environ["OPENAI_API_KEY"] = "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"
os.environ["GROQ_API_KEY"] = "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"

# Initialize APIs
llm = ChatGroq(model="gemma2-9b-it", temperature=0.7, max_tokens=2048)
client = ElevenLabs(api_key="sk_dc93814b406fe1cdce288749514157a6ffbcd35b34158339")
gemini_client = genai.Client(api_key="AIzaSyBLzfjImenFp60acvXgKygaEDKGqKfHyKI")
imagekit = ImageKit(
    private_key='private_OGgux+C54n9PIYDlLdOrYysEWrw=',
    public_key='public_Qq9s197rBPKyx5eWhq+aN6TQ3Iw=',
    url_endpoint='https://ik.imagekit.io/b6pq3mgo7'
)

# Creatify API headers
creatify_headers = {
    "X-API-ID": "5f8b3a5c-6e33-4e9f-b85c-71941d675270",
    "X-API-KEY": "c019dd017d22e2e40627f87bc86168b631b9a345"
}

# Heygen API headers
heygen_headers = {
    "accept": "application/json",
    "x-api-key": "MzhiYTJmZWU5OWM0NGFlYWI5ZjdmNWRkMWVkNjQ4MTctMTc0NTA1NDU2OQ=="
}

# Your original functions
class Script(BaseModel):
    hook: str
    body: str
    cta: str
    final_script: str

def script_crew(cleaned_summary):
    # Define the Task planning Agent
    task_planning = Agent(
        role="Workflow Architect for Ad Creation",
        goal="transform a clean campaign summary into a detailed workflow and instructions for research and script writing agents.",
        backstory="""An experienced workflow architect specializing in streamlining creative processes for advertising campaigns. They excel at dissecting campaign objectives and translating them into clear, sequential tasks for specialized agents. With a deep understanding of the content creation lifecycle, they ensure that research and scripting are aligned and contribute effectively to the overall campaign goals. They focus on providing precise guidance to each agent, maximizing efficiency and creative output.""",
        memory=True,
        verbose=True,
        delegation=True,
        tools=[SerperDevTool()]
    )

    # Define the workflow generation task
    workflow_generation_task = Task(
        description=f"""The user has provided a clean and concise summary of the ad campaign requirements.
        {cleaned_summary}

        The Workflow Architect will:
        1. Analyze the campaign summary to identify key information relevant to research and scripting.
        2. Define specific research objectives and questions that a research agent should address.
        3. Outline the core elements and guidelines for the script, including tone, style, target audience considerations, and the desired call-to-action.
        4. Create a structured brief for both the Research Agent and the Script Writing Agent, ensuring clarity and alignment.
        5. Consider any dependencies between the research and scripting phases.
        6. Searches should be made in string only """,
        expected_output="""A structured workflow and set of briefs that includes:

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
        agent=task_planning
    )

    researcher = Agent(
        role=f"Researcher for Ad Script Generation",
        goal=f"Uncover the most effective trends, winning script elements, and impactful character characteristics relevant to creating a high-impact online ad as per user requirements and search by passing a string to the tool.",
        backstory=f"A seasoned researcher with an insatiable curiosity for understanding human behavior and the ever-shifting digital landscape, this agent brings years of experience in dissecting online trends and identifying the core elements that drive engagement. With a background in market research and digital anthropology, they possess a sharp eye for spotting emerging patterns and understanding the nuances of online communities. Their expertise lies in sifting through vast amounts of data – from social media analytics to competitor analysis – to extract the crucial insights that inform effective communication. They have a proven track record of identifying the 'why' behind successful online content, understanding what resonates with specific demographics and the psychological triggers that lead to action. Their ability to synthesize complex information into clear, actionable intelligence makes them an invaluable asset in laying the groundwork for impactful advertising. Furthermore, their understanding of the local context, provides an added layer of cultural sensitivity to their research.",
        memory=True,
        verbose=True,
        tools=[SerperDevTool()]
    )

    writer = Agent(
        role=f"Script Writer for Online Ad Creatives",
        goal=f"Craft authentic, emotionally engaging, high-converting ad scripts structured into Hook, Body, and CTA sections tailored for as per user requirements. The scripts should reflect research insights on trends, character dynamics, and emotional triggers, while maintaining a natural, relatable, first-person or testimonial tone designed to resonate with audiences",
        backstory=f"A passionate storyteller and digital creator, this agent specializes in writing ad scripts that feel authentic, personal, and culturally relevant. With years of experience in social media marketing and influencer partnerships, they have an intuitive understanding of how real people speak, share opinions, and build trust online. Their portfolio includes hundreds of successful ad creatives styled for Instagram, YouTube Shorts, and TikTok, each designed to spark genuine engagement and drive conversions.This agent excels at capturing emotional hooks, structuring casual product narratives, and closing with compelling CTAs — all while maintaining the voice of a real consumer. Fluent in multi-character conversations and diverse digital trends, they transform strategic insights into natural, relatable scripts optimized for the Indian online market. Their ability to balance brand messaging with authentic storytelling makes them an invaluable asset for creating high-impact ad creatives.",
        memory=True,
        verbose=True,
        tools=[]
    )

    research_task = Task(
        description=f"""Conduct thorough research based on the provided instructions to uncover the most effective trends, winning script elements, and impactful character characteristics relevant to the target audience and product. Pay close attention to the specific research questions and objectives outlined in the instructions. Focus on online advertising only and ensure all findings are directly relevant to the campaign goals.""",
        expected_output=f"""A structured report containing the findings for each of the research questions and objectives provided in the input. This report should provide clear and actionable insights for the Writing Agent.""",
        agent=researcher,
        input_keys=["research_instructions", "campaign_context"]
    )

    writing_task = Task(
        description=f"""Using the research insights and the script guidelines provided, craft a high-converting, emotionally engaging **UGC-style ad script**.

        The script must adhere to the specified tone, style, target audience profile, and call-to-action. Integrate the research findings on trends, winning script elements, and impactful character characteristics to create a compelling and authentic ad.

        The script should be structured into three clear sections: Hook, Body, and Call-to-Action (CTA), maintaining a natural, conversational, first-person or testimonial tone suitable for the target audience. Follow all additional formatting instructions provided in the guidelines.""",
        expected_output=f"""A JSON object containing the UGC ad script:

        **Hook:**
        - 1-2 authentic, relatable opening lines tailored to the target audience.

        **Body:**
        - 3-5 natural-sounding lines presenting the product's benefits or personal experiences.

        **Call-to-Action (CTA):**
        - 1-2 casual, persuasive closing lines urging immediate action.

        **Final Script:**
        - The complete UGC ad script in 'Hook + Body + CTA' format.

        The final output will be a JSON object with the following fields:
        - **title**: A descriptive title for the script.
        - **content**: The full content of the ad script.

        **Additional Formatting Instructions**:
        1. **Pauses**: Indicate pauses using ellipses (`...`).
        2. **Capitalization**: Use CAPITALIZATION for emphasis.
        3. **Length**: Keep the script under 200 words.""",
        agent=writer,
        input_keys=["research_report", "script_guidelines", "campaign_context"],
        output_json=Script
    )

    crew = Crew(
        agents=[task_planning, researcher, writer],
        tasks=[workflow_generation_task, research_task, writing_task],
        verbose=True
    )

    # Run the crew workflow
    result = crew.kickoff()
    return result

def breifer():
    with open("/content/drive/MyDrive/ADGEN MAIN/REQUIREMENT PROMPTS/PROMPT1.txt", "r") as file:
        prompt = file.read()
    
    system_prompt = SystemMessage(content=prompt)
    memory = ConversationBufferMemory(return_messages=True)
    memory.chat_memory.add_message(system_prompt)
    
    conversation_chain = ConversationChain(
        llm=llm,
        memory=memory,
        verbose=False
    )
    
    initial_fact_finder = Agent(
        role="Initial Fact Finder",
        goal="Understand the key elements of the campaign before it moves to briefing or scripting",
        backstory="You're the first point of contact for campaign planning. You ask smart, progressive questions to understand the user's intent and goals.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    crew = Crew(
        agents=[initial_fact_finder],
        verbose=True
    )
    
    return conversation_chain

# Creatify API functions
def get_creatify_personas():
    url = "https://api.creatify.ai/api/personas/"
    personas = requests.request("GET", url, headers=creatify_headers)
    return personas

def get_creatify_voices():
    url = "https://api.creatify.ai/api/voices/"
    creatify_voices = requests.request("GET", url, headers=creatify_headers)
    return creatify_voices

def get_creatify_music():
    url = "https://api.creatify.ai/api/musics/"
    creatify_music = requests.request("GET", url, headers=creatify_headers)
    return creatify_music

def create_creatify_link_params(image_urls):
    url = "https://api.creatify.ai/api/links/link_with_params/"
    payload = {
        "title": "Generated Images Collection",
        "description": "Images generated with Google Gemini",
        "image_urls": image_urls,
        "video_urls": [],
        "reviews": "Finding Your Way to Financial Freedom"
    }
    headers = creatify_headers.copy()
    headers["Content-Type"] = "application/json"
    creatify_link_param = requests.request("POST", url, json=payload, headers=headers)
    return creatify_link_param

def create_creatify_video(script_text, link_id, avatar_id, voice_id):
    url = "https://api.creatify.ai/api/link_to_videos/"
    payload = {
        "name": "Generated Ad Video",
        "target_platform": "social_media",
        "target_audience": "general",
        "language": "en",
        "video_length": 30,
        "aspect_ratio": "9x16",
        "script_style": "BenefitsV2",
        "visual_style": "AvatarBubbleTemplate",
        "override_avatar": avatar_id,
        "override_voice": voice_id,
        "override_script": script_text,
        "background_music_url": "",
        "background_music_volume": 0.5,
        "voiceover_volume": 0.5,
        "webhook_url": "",
        "link": link_id,
        "no_background_music": False,
        "no_caption": False,
        "no_emotion": False,
        "no_cta": False,
        "no_stock_broll": False,
        "caption_style": "normal-black"
    }
    headers = creatify_headers.copy()
    headers["Content-Type"] = "application/json"
    creatify_video = requests.request("POST", url, json=payload, headers=headers)
    return creatify_video

def get_creatify_status(video_id):
    url = f"https://api.creatify.ai/api/link_to_videos/{video_id}/"
    creatify_status = requests.request("GET", url, headers=creatify_headers)
    return creatify_status

# Heygen API functions
def list_all_avatars():
    url = "https://api.heygen.com/v2/avatars"
    avatars = requests.get(url, headers=heygen_headers)
    return avatars

def list_heygen_voices():
    url = "https://api.heygen.com/v2/voices"
    heygen_voices = requests.get(url, headers=heygen_headers)
    return heygen_voices

def generate_heygen_video(script_text, avatar_id, voice_id):
    url = "https://api.heygen.com/v2/video/generate"
    payload = {
        "caption": True,
        "dimension": {"width": 1280, "height": 720},
        "title": "Generated Ad Video",
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "scale": 1,
                    "avatar_style": "normal",
                    "avatar_id": avatar_id
                },
                "voice": {
                    "type": "text",
                    "voice_id": voice_id,
                    "input_text": script_text,
                    "speed": 1,
                    "pitch": 0,
                    "emotion": "Friendly",
                    "locale": "en-US"
                },
                "background": {
                    "type": "color",
                    "value": "#ffffff"
                }
            }
        ]
    }
    generated_video = requests.post(url, json=payload, headers=heygen_headers)
    return generated_video

def check_heygen_status(video_id):
    url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    heygen_status = requests.get(url, headers=heygen_headers)
    return heygen_status

# ElevenLabs functions
def list_elevenlabs_voices():
    voices = client.voices.search(include_total_count=True)
    return voices

def text_speech(voice_id, text, voice_settings):
    generated_audio = client.text_to_speech.convert(
        voice_id=voice_id,
        output_format="mp3_44100_128",
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=voice_settings
    )
    return generated_audio

# Image generation function
def generate_images(data):
    image_urls = []
    prompt_size = len(data["image_prompts"])
    
    for i in range(prompt_size):
        current_prompt = data["image_prompts"][i]
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=current_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE']
                )
            )
            
            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None):
                    image = Image.open(BytesIO(part.inline_data.data))
                    filename = f"scene-{i+1:02d}-gemini-image.png"
                    image.save(filename)
                    
                    upload = imagekit.upload(
                        file=open(filename, "rb"),
                        file_name=filename
                    )
                    
                    image_urls.append(upload.url)
        except Exception as e:
            st.error(f"Error generating image: {str(e)}")
    
    return image_urls

# Page config
st.set_page_config(
    page_title="Ad Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Same as before
st.markdown("""
    <style>
    .main { background-color: #f0f8ff; }
    .stApp { background-color: #f0f8ff; }
    
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
    }
    
    .bubble {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        background-color: #87CEEB;
        color: white;
        margin-right: 5px;
        margin-bottom: 5px;
        font-size: 0.9em;
    }
    
    .stButton > button {
        background-color: #87CEEB;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        transition: background-color 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #4682B4;
    }
    
    h1, h2, h3 {
        color: #4682B4;
    }
    
    .status-pending {
        color: #FFA500;
        font-weight: bold;
    }
    .status-complete {
        color: #32CD32;
        font-weight: bold;
    }
    .status-failed {
        color: #FF4500;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'workflow_step' not in st.session_state:
    st.session_state.workflow_step = 'start'
if 'script' not in st.session_state:
    st.session_state.script = None
if 'requirements' not in st.session_state:
    st.session_state.requirements = {}
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = {
        'audio': None,
        'video': None,
        'images': [],
        'script': None
    }
if 'saved_scripts' not in st.session_state:
    st.session_state.saved_scripts = {}
if 'selected_voice' not in st.session_state:
    st.session_state.selected_voice = None
if 'selected_avatar' not in st.session_state:
    st.session_state.selected_avatar = None
if 'conversation_chain' not in st.session_state:
    st.session_state.conversation_chain = None

# Sidebar
with st.sidebar:
    st.header("🎯 Ad Generator")
    st.markdown("---")
    
    # Progress tracker
    steps = ["Start", "Requirements", "Script", "Voice", "Avatar", "Generate", "Complete"]
    current_step_idx = steps.index(st.session_state.workflow_step.capitalize()) if st.session_state.workflow_step.capitalize() in steps else 0
    
    for i, step in enumerate(steps):
        if i <= current_step_idx:
            st.markdown(f"✅ **{step}**")
        else:
            st.markdown(f"⭕ {step}")
    
    st.markdown("---")
    
    # Saved Scripts
    if st.session_state.saved_scripts:
        st.subheader("📚 Saved Scripts")
        for name, script in st.session_state.saved_scripts.items():
            if st.button(f"Load: {name}", key=f"load_{name}"):
                st.session_state.script = script
                st.session_state.workflow_step = 'script'
                st.rerun()

# Main content area
st.title("🎬 Ad Generator Studio")

# Start page
if st.session_state.workflow_step == 'start':
    st.markdown("""
    <div class="card">
        <h2>Welcome to Ad Generator Studio</h2>
        <p>Create professional ad content with AI-powered tools.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 I have a script", use_container_width=True):
            st.session_state.workflow_step = 'script'
            st.rerun()
    
    with col2:
        if st.button("✨ Create new campaign", use_container_width=True):
            st.session_state.workflow_step = 'requirements'
            st.rerun()

# Requirements gathering page
elif st.session_state.workflow_step == 'requirements':
    st.header("📋 Campaign Requirements")
    
    # Option to use automated briefer
    use_automated = st.checkbox("Use AI Assistant for Requirements Gathering", value=False)
    
    if use_automated:
        st.markdown("""
        <div class="card">
            <h3>AI Requirements Assistant</h3>
            <p>Chat with our AI to gather your campaign requirements</p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'conversation_chain' not in st.session_state or st.session_state.conversation_chain is None:
            st.session_state.conversation_chain = breifer()
        
        # Chat interface
        user_input = st.text_input("Your response:", key="requirements_chat")
        
        if user_input:
            with st.spinner("Thinking..."):
                response = st.session_state.conversation_chain.predict(input=user_input)
                st.markdown(f"**AI:** {response}")
                
                # Check if we have reached final brief
                if "========== Final Brief ==========" in response:
                    summary = response.split("========== Final Brief ==========", 1)[1].strip()
                    
                    # Generate script with the summary
                    with st.spinner("Generating your campaign script..."):
                        result = script_crew(summary)
                        st.session_state.script = result
                        st.session_state.workflow_step = 'script'
                        st.rerun()
    
    else:
        # Manual form
        with st.form("requirements_form"):
            st.markdown("""
            <div class="card">
                <h3>Tell us about your campaign</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                campaign_name = st.text_input("Campaign Name", placeholder="Enter campaign name")
                target_audience = st.text_area("Target Audience", placeholder="Describe your target audience")
                product_name = st.text_input("Product/Service Name")
                
            with col2:
                campaign_goal = st.selectbox("Campaign Goal", 
                    ["Brand Awareness", "Product Launch", "Lead Generation", "Sales Conversion", "Customer Retention"])
                platform = st.multiselect("Target Platforms",
                    ["Instagram", "YouTube", "TikTok", "Facebook", "LinkedIn"],
                    default=["Instagram"])
                budget = st.selectbox("Budget Range",
                    ["Small ($100-500)", "Medium ($500-2000)", "Large ($2000+)"])
            
            st.markdown("""
            <div class="card">
                <h3>Additional Details</h3>
            </div>
            """, unsafe_allow_html=True)
            
            key_message = st.text_area("Key Message", placeholder="What's the main message you want to convey?")
            tone = st.selectbox("Tone", 
                ["Professional", "Casual", "Humorous", "Emotional", "Educational"])
            additional_notes = st.text_area("Additional Notes (Optional)")
            
            submitted = st.form_submit_button("Generate Campaign Brief", use_container_width=True)
            
            if submitted:
                # Create summary from form data
                campaign_summary = f"""
                Campaign Name: {campaign_name}
                Product/Service: {product_name}
                Target Audience: {target_audience}
                Campaign Goal: {campaign_goal}
                Target Platforms: {', '.join(platform)}
                Budget: {budget}
                Key Message: {key_message}
                Tone: {tone}
                Additional Notes: {additional_notes}
                """
                
                st.session_state.requirements = {
                    'campaign_name': campaign_name,
                    'target_audience': target_audience,
                    'product_name': product_name,
                    'campaign_goal': campaign_goal,
                    'platform': platform,
                    'budget': budget,
                    'key_message': key_message,
                    'tone': tone,
                    'additional_notes': additional_notes
                }
                
                # Call script_crew() to generate script
                with st.spinner("Generating your campaign script..."):
                    result = script_crew(campaign_summary)
                    st.session_state.script = result
                    st.session_state.workflow_step = 'script'
                    st.rerun()

# Script page - With rest of the pages as before...

# Complete page
elif st.session_state.workflow_step == 'complete':
    st.header("🎉 Content Generation Complete!")
    
    st.markdown("""
    <div class="card">
        <h3>Your Generated Content</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Audio preview
    if st.session_state.generated_content['audio']:
        st.markdown("### 🎙️ Audio")
        st.audio(st.session_state.generated_content['audio'], format='audio/mp3')
        
        with open(st.session_state.generated_content['audio'], 'rb') as audio_file:
            st.download_button(
                label="Download Audio",
                data=audio_file,
                file_name="generated_audio.mp3",
                mime="audio/mp3"
            )
    
    # Images preview
    if st.session_state.generated_content['images']:
        st.markdown("### 🖼️ Images")
        cols = st.columns(3)
        for i, img_url in enumerate(st.session_state.generated_content['images']):
            with cols[i % 3]:
                st.image(img_url, caption=f"Generated Image {i+1}")
    
    # Video preview
    if st.session_state.generated_content['video']:
        st.markdown("### 🎥 Video")
        st.markdown(f"Video ID: `{st.session_state.generated_content['video']}`")
        st.info("Video preview will be available once the video is fully processed.")
    
    # Export options
    st.markdown("### 📤 Export Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Campaign", use_container_width=True):
            campaign_data = {
                'script': st.session_state.script,
                'requirements': st.session_state.requirements,
                'generated_content': st.session_state.generated_content,
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # Save to local storage or database
            st.success("Campaign saved successfully!")
    
    with col2:
        if st.button("📋 Copy Script", use_container_width=True):
            st.text_area("Script to Copy", value=st.session_state.script.get('final_script', ''), height=100)
            st.info("Copy the script from the text area above")
    
    with col3:
        if st.button("🔄 Start New Campaign", use_container_width=True):
            # Reset session state
            st.session_state.workflow_step = 'start'
            st.session_state.script = None
            st.session_state.requirements = {}
            st.session_state.generated_content = {
                'audio': None,
                'video': None,
                'images': [],
                'script': None
            }
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #4682B4;'>
    Ad Generator Studio © 2024 | Powered by AI
</div>
""", unsafe_allow_html=True)
