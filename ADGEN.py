uv install elevenlabs
import streamlit as st
from elevenlabs import ElevenLabs

# Initialize the ElevenLabs client
client = ElevenLabs(api_key="sk_457392759b066ebb9b695f4f7f3b85d177d04350c85e494a")

def get_voices():
    response = client.voices.search(include_total_count=True, page_size=100)
    return response.voices

def show_selected_voice(voice_id):
    st.write(f"✅ Selected Voice ID: `{voice_id}`")

# Streamlit UI
st.title("🎤 ElevenLabs Voices Grid")

# Fetch voices
voices = get_voices()
cards_per_row = 3

# Store the selected voice_id
selected_voice = None

# Create grid of voice cards with preview and selection button
for i in range(0, len(voices), cards_per_row):
    col1, col2, col3 = st.columns(3)
    for j, col in enumerate([col1, col2, col3]):
        if i + j < len(voices):
            voice = voices[i + j]
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
                if st.button(f"Select {name}", key=voice_id):
                    selected_voice = voice_id
                    show_selected_voice(selected_voice)

if not selected_voice:
    st.write("Please select a voice.")
