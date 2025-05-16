import streamlit as st
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager, register_function
from pinecone import Pinecone
import uuid
import time

# --- Configuration ---
config_list = [{
    "model": "llama3-8b-8192",
    "api_key": "your-groq-key",  # Replace with your Groq API key
    "api_type": "groq",
}]

# Pinecone search function
def search_scriptwriting_concepts(query: str) -> str:
    try:
        pc = Pinecone(api_key="your-pinecone-key")  # Replace with your Pinecone API key
        index = pc.Index("script-writing-books")
        results = index.search(
            namespace="insights",
            query={"inputs": {"text": str(query)}, "top_k": 3},
            fields=["title", "chunk_text"]
        )
        output = "📘 Scriptwriting Insights:\n\n"
        for i, hit in enumerate(results["result"]["hits"]):
            fields = hit["fields"]
            output += f"{i+1}. {fields.get('title', 'Untitled')}: {fields.get('chunk_text', 'No content')}\n\n"
        return output
    except Exception as e:
        return f"Search error: {e}"

# --- Initialize Session State ---
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chat_initialized' not in st.session_state:
    st.session_state.chat_initialized = False
if 'group_chat_manager' not in st.session_state:
    st.session_state.group_chat_manager = None
if 'user_proxy' not in st.session_state:
    st.session_state.user_proxy = None
if 'creative_director' not in st.session_state:
    st.session_state.creative_director = None
if 'producer_agent' not in st.session_state:
    st.session_state.producer_agent = None
if 'researcher_agent' not in st.session_state:
    st.session_state.researcher_agent = None
if 'copywriter_agent' not in st.session_state:
    st.session_state.copywriter_agent = None

# --- Initialize Agents and Group Chat ---
def initialize_chat():
    if not st.session_state.chat_initialized:
        # Create agents
        user_proxy = UserProxyAgent(
            name="User",
            human_input_mode="ALWAYS",  # We'll manage input via Streamlit
            code_execution_config=False,
            system_message="You are a human ad script writer collaborating with agents to write."
        )
        producer_agent = AssistantAgent(
            name="ProducerAgent",
            llm_config={"config_list": config_list},
            system_message="""You are a seasoned ad producer.
Identify yourself as 'ProducerAgent:' in your messages.
Ask questions to understand product/service, audience, tone, and goals."""
        )
        researcher_agent = AssistantAgent(
            name="ResearcherAgent",
            llm_config={"config_list": config_list},
            system_message="""You are a senior advertising strategist.
Identify yourself as 'ResearcherAgent:' in your messages.
Provide strategic structure and audience insights."""
        )
        copywriter_agent = AssistantAgent(
            name="CopywriterAgent",
            llm_config={"config_list": config_list},
            system_message="""You are an award-winning copywriter.
Identify yourself as 'CopywriterAgent:' in your messages.
Write compelling HOOK-BODY-CTA ad scripts."""
        )
        creative_director = AssistantAgent(
            name="CreativeDirector",
            llm_config={"config_list": config_list},
            system_message="""You are the creative director coordinating this campaign.
Identify yourself as 'CreativeDirector:' in your messages.
Direct ONE agent at a time using their full name.
Start by greeting the client."""
        )

        # Register search function
        register_function(search_scriptwriting_concepts, caller=producer_agent, executor=producer_agent, description="Search advertising books")
        register_function(search_scriptwriting_concepts, caller=researcher_agent, executor=researcher_agent, description="Search advertising books")
        register_function(search_scriptwriting_concepts, caller=copywriter_agent, executor=copywriter_agent, description="Search advertising books")

        # Define allowed transitions
        allowed_transitions = {
            user_proxy: [creative_director, producer_agent, researcher_agent, copywriter_agent],
            producer_agent: [user_proxy, creative_director],
            researcher_agent: [user_proxy, creative_director],
            copywriter_agent: [user_proxy, creative_director],
            creative_director: [user_proxy, producer_agent, researcher_agent, copywriter_agent],
        }

        group_chat = GroupChat(
            agents=[user_proxy, creative_director, producer_agent, researcher_agent, copywriter_agent],
            allowed_or_disallowed_speaker_transitions=allowed_transitions,
            speaker_transitions_type="allowed",
            messages=[],
            max_round=50,
            send_introductions=True,
        )
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list}
        )

        st.session_state.user_proxy = user_proxy
        st.session_state.creative_director = creative_director
        st.session_state.producer_agent = producer_agent
        st.session_state.researcher_agent = researcher_agent
        st.session_state.copywriter_agent = copywriter_agent
        st.session_state.group_chat_manager = manager
        st.session_state.chat_initialized = True

        # Initial message from the Creative Director
        initial_message = {"role": "assistant", "name": "CreativeDirector", "content": "Hello! What can we help you create today?"}
        st.session_state.chat_history.append(initial_message)
        st.session_state.group_chat_manager.groupchat.messages.append({"role": "assistant", "name": "CreativeDirector", "content": "Hello! What can we help you create today?"})

# --- Main UI ---
st.title("Multi-Agent Ad Script Generator (Direct)")

if not st.session_state.chat_initialized:
    initialize_chat()

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"], name=message.get("name")):
        st.write(message["content"])

# User input
user_prompt = st.chat_input("Type your message here...")
if user_prompt:
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    # Send user message to the group chat manager
    st.session_state.user_proxy.initiate_chat(
        st.session_state.group_chat_manager,
        message=user_prompt,
        clear_history=False  # Keep the chat history
    )

    # Display new messages from agents
    for message in st.session_state.group_chat_manager.groupchat.messages[len(st.session_state.chat_history):]:
        st.session_state.chat_history.append({"role": "assistant", "name": message.get("name", "Agent"), "content": message["content"]})
        with st.chat_message("assistant", name=message.get("name")):
            st.write(message["content"])

    # Force a rerun to update the UI with new messages
    st.rerun()
