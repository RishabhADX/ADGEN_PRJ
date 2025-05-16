import streamlit as st
import os
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import uuid
import threading
import queue

# Set page config
st.set_page_config(page_title="Ad Script Generator", layout="wide")

# LLM Configuration
config_list = [{
    "model": "llama3-8b-8192",
    "api_key": "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",
    "api_type": "groq",
}]

# Custom UserProxyAgent that stores messages rather than displaying in console
class StreamlitUserProxyAgent(UserProxyAgent):
    def __init__(self, name, message_queue, **kwargs):
        self.message_queue = message_queue
        super().__init__(name=name, **kwargs)
    
    def receive(self, message, sender, silent=False):
        # Store the message in queue for Streamlit to retrieve
        if sender.name != self.name:  # Don't add our own messages
            self.message_queue.put({
                "role": sender.name,
                "content": message["content"]
            })
        return super().receive(message, sender, silent)
    
    def get_human_input(self, prompt=""):
        # Instead of asking console, return stored input
        if hasattr(self, 'stored_input'):
            user_input = self.stored_input
            delattr(self, 'stored_input')  # Clear after use
            return user_input
        return ""

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'agents_initialized' not in st.session_state:
    st.session_state.agents_initialized = False

if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if 'termination_msg_received' not in st.session_state:
    st.session_state.termination_msg_received = False

if 'agent_message_queue' not in st.session_state:
    st.session_state.agent_message_queue = queue.Queue()

# UI Layout
st.title("Ad Script Generator")
st.subheader("Powered by AutoGen")

# Sidebar for user info
with st.sidebar:
    st.header("User Information")
    if 'user_name' not in st.session_state:
        user_name = st.text_input("Your Name:", key="name_input")
        if st.button("Start Chat"):
            if user_name:
                st.session_state.user_name = user_name
                st.rerun()
            else:
                st.error("Please enter your name to continue")
    else:
        st.success(f"Welcome, {st.session_state.user_name}!")
        if st.button("Start New Chat"):
            # Reset session
            for key in list(st.session_state.keys()):
                if key not in ['user_name']:
                    del st.session_state[key]
            st.session_state.messages = []
            st.session_state.agents_initialized = False
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.termination_msg_received = False
            st.session_state.agent_message_queue = queue.Queue()
            st.rerun()

# Function to check if a message contains the termination phrase
def check_termination(content):
    return "We've completed the ad script. Thank you!" in content

# Execute chat in a separate thread to avoid blocking Streamlit
def run_chat_in_thread(user_input):
    try:
        # Set input for the next round
        st.session_state.client.stored_input = user_input
        
        # Run this with a limited number of rounds
        st.session_state.group_chat_manager.groupchat.max_round = 3
        
        # Run a chat round
        st.session_state.group_chat_manager.run(
            new_message={"role": "user", "content": user_input},  
            sender=st.session_state.client
        )
    except Exception as e:
        st.session_state.agent_message_queue.put({
            "role": "ERROR",
            "content": f"Chat error: {str(e)}"
        })

# Main chat area
if 'user_name' in st.session_state:
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]
            
            if role == "User":
                with st.chat_message("user"):
                    st.write(content)
            elif role == "ERROR":
                with st.chat_message("error"):
                    st.error(content)
            else:
                with st.chat_message("assistant"):
                    st.write(f"**{role}**: {content}")
    
    # Initialize agents if not already done
    if not st.session_state.agents_initialized:
        # Create client agent with the queue
        client = StreamlitUserProxyAgent(
            name="User",
            message_queue=st.session_state.agent_message_queue,
            human_input_mode="ALWAYS",  # We override get_human_input, so this is fine
            code_execution_config=False,
            system_message="You are a human ad script writer collaborating with agents to write."
        )
        
        producer_agent = AssistantAgent(
            name="ProducerAgent",
            llm_config={"config_list": config_list},
            system_message="""You are ProducerAgent, an experienced advertising scriptwriter who channels the mindset of legendary ad creators like David Ogilvy, Gary Halbert, and Eugene Schwartz.

When briefed by the CreativeDirector, your role is to speak directly to the client (User) and extract all essential information to prepare for script development.

IMPORTANT:
- Always begin your messages with 'ProducerAgent:' 
- Ask sharp, layered questions about the product/service, target audience, and desired outcomes
- Ask 1-2 questions at a time
- Once you've collected enough information, create a clear summary brief for client approval
- After the client approves your brief, wait for the CreativeDirector to direct the next agent"""
        )
        
        researcher_agent = AssistantAgent(
            name="ResearcherAgent",
            llm_config={"config_list": config_list},
            system_message="""You are ResearcherAgent, a Senior Advertising Strategist.

When instructed by the CreativeDirector, analyze the brief and create:
1. A research summary with psychological insights on the target audience
2. A proposed script structure (e.g., AIDA, PAS)

IMPORTANT:
- Always begin your messages with 'ResearcherAgent:' 
- Present your findings directly to the User (client) for approval
- Wait for explicit direction from the CreativeDirector before contributing"""
        )
        
        copywriter_agent = AssistantAgent(
            name="CopywriterAgent",
            llm_config={"config_list": config_list},
            system_message="""You are CopywriterAgent, an award-winning copywriter.

When instructed by the CreativeDirector, use the approved structure and research insights to create an ad script with:
1. Attention-grabbing hook
2. Emotionally resonant body
3. Clear call to action

IMPORTANT:
- Always begin your messages with 'CopywriterAgent:' 
- Don't write a screenplay, just write the script
- Break the script into HOOK, BODY, CTA
- Present the script directly to the User (client) for approval
- Wait for explicit direction from the CreativeDirector before contributing"""
        )
        
        creative_director = AssistantAgent(
            name="CreativeDirector",
            llm_config={"config_list": config_list},
            system_message=f"""You are the Creative Director coordinating this ad campaign.

Your role is to manage the workflow by explicitly directing ONE agent at a time:
1. First, welcome the client (User) by name: {st.session_state.user_name}
2. Then ask the user what they want to do and delegate agents based on that
3. If script generation is needed, direct the ProducerAgent to gather information
4. After ProducerAgent has gathered sufficient information, direct the ResearcherAgent to analyze it
5. After the client approves the research, direct the CopywriterAgent to create the script
6. After the client reviews the script, help with any requested revisions

IMPORTANT: 
- Always begin your messages with 'CreativeDirector:' 
- Direct ONE specific agent at a time using their full name (e.g., "ProducerAgent, please...")
- Wait for that agent to complete their task before directing another agent
- End the conversation only when the client approves the final script by saying "We've completed the ad script. Thank you!"
"""
        )
        
        # Define allowed transitions
        allowed_transitions = {
            client: [creative_director, producer_agent, researcher_agent, copywriter_agent],
            producer_agent: [client, creative_director],
            researcher_agent: [client, creative_director],
            creative_director: [client, producer_agent, researcher_agent, copywriter_agent],
            copywriter_agent: [client, creative_director],
        }
        
        # Set up group chat
        group_chat = GroupChat(
            agents=[client, creative_director, producer_agent, researcher_agent, copywriter_agent],
            allowed_or_disallowed_speaker_transitions=allowed_transitions,
            speaker_transitions_type="allowed",
            messages=[],
            max_round=3,
            send_introductions=False,
        )
        
        # Custom termination check
        def is_termination_msg(message):
            if isinstance(message, dict):
                content = message.get("content", "")
                if check_termination(content):
                    st.session_state.termination_msg_received = True
                    return True
            return False
        
        # Set up group chat manager
        group_chat_manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": config_list},
            is_termination_msg=is_termination_msg
        )
        
        # Store in session state
        st.session_state.client = client
        st.session_state.group_chat_manager = group_chat_manager
        st.session_state.agents_initialized = True
        
        # Add initial welcome message
        welcome_msg = {
            "role": "CreativeDirector",
            "content": f"Hello, {st.session_state.user_name}! Welcome to our ad campaign creation session. What type of ad would you like to create today?"
        }
        st.session_state.messages.append(welcome_msg)
        
        # Force a rerun to update the UI
        st.rerun()
    
    # Check for new messages in the queue and add them to the display
    while not st.session_state.agent_message_queue.empty():
        try:
            new_message = st.session_state.agent_message_queue.get_nowait()
            st.session_state.messages.append(new_message)
            
            # Check for termination
            if check_termination(new_message.get("content", "")):
                st.session_state.termination_msg_received = True
        except queue.Empty:
            break
    
    # User input area (disabled if termination message received)
    if st.session_state.termination_msg_received:
        st.info("This conversation has ended. Click 'Start New Chat' to begin a new session.")
        user_input = st.chat_input("Type your message here...", disabled=True)
    else:
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Add user message to conversation
            user_message = {"role": "User", "content": user_input}
            st.session_state.messages.append(user_message)
            
            # Start a thread to run the chat (prevents blocking Streamlit)
            threading.Thread(
                target=run_chat_in_thread, 
                args=(user_input,)
            ).start()
            
            # Force a rerun to update the UI
            time.sleep(0.1)  # Small delay to let the thread start
            st.rerun()
else:
    # User needs to enter name first
    st.info("Please enter your name in the sidebar to begin.")
