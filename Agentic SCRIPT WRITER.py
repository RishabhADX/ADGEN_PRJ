import streamlit as st
st.set_page_config(page_title="Ad Scriptwriter Bot", layout="wide")

# Suppress console output
import sys
import os

from autogen import (
    AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager, register_function
)

# -- SETUP LLM CONFIG --
import os

config_list = [
    {
        # Let's choose the Llama 3 model
        "model": "llama3-8b-8192",
        # Put your Groq API key here or put it into the GROQ_API_KEY environment variable.
        "api_key": os.environ.get("GROQ_API_KEY"),
        # We specify the API Type as 'groq' so it uses the Groq client class
        "api_type": "groq",
    }
]
name = st.text_input("Enter your name")

# -- USER INTERFACE --

st.title("🎬 Ad Scriptwriter Multi-Agent Bot")

# -- SESSION STATE FOR CHAT --
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "manager" not in st.session_state:
    st.session_state.manager = None
if "user_agent" not in st.session_state:
    st.session_state.user_agent = None

# -- AGENT DEFINITIONS --

client = UserProxyAgent(
    name="User",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=1,
    code_execution_config=False,
    system_message="You are a human ad script writer collaborating with agents to write."
)

# Producer agent
ProducerAgent = AssistantAgent(
    name="ProducerAgent",
    llm_config={
        # Let's choose the Llama 3 model
        "model": "llama3-8b-8192",
        # Put your Groq API key here or put it into the GROQ_API_KEY environment variable.
        "api_key": os.environ.get("GROQ_API_KEY"),
        # We specify the API Type as 'groq' so it uses the Groq client class
        "api_type": "groq",
    },
    system_message="""You are ProducerAgent, an experienced advertising scriptwriter who channels the mindset of legendary ad creators like David Ogilvy, Gary Halbert, and Eugene Schwartz. You don’t just ask surface-level questions — you dig deep to uncover the emotional hooks, market awareness level, and psychological triggers necessary to write high-converting ad scripts.

When briefed by the CreativeDirector, your role is to speak directly to the client (User) and extract all essential information to prepare for script development. You combine the curiosity of a strategist with the instincts of a top-tier copywriter.

Use your persona to ask sharp, layered questions about:

The Product or Service:
  Examples:
  1. What exactly are we selling?
  2. What makes it unique, better, or different from anything else out there?
  3. What urgent problem does it solve for the customer?

The Target Audience:
  examples:
  1. Who is this for? (age, gender, lifestyle, values)
  2. What are they feeling before using the product — and how do we want them to feel after?
  3. What objections might they have?

Desired Outcomes & Brand Voice:
  examples:
  1. What’s the goal of this ad? (awareness, clicks, conversions, sign-ups?)
  2. Should the tone feel funny, premium, emotional, intense, rebellious, etc.?
  3. Is there a specific call to action or platform (e.g. YouTube, Instagram, TV) in mind?

Use deep follow-up questions to get beneath generic answers. If responses are vague, push for specifics — stories, customer pain points, product origin stories, or founder insight.
*Ask 1-2 questions at a time.
You can call the tool if needed.
Once you've collected enough information then only proceed to next step else keep on asking questions, before proceeding create a clear and persuasive summary brief to send to the Client for approval."""
)

# Researcher agent
ResearcherAgent = AssistantAgent(
    name="ResearcherAgent",
    llm_config={
        # Let's choose the Llama 3 model
        "model": "llama3-8b-8192",
        # Put your Groq API key here or put it into the GROQ_API_KEY environment variable.
        "api_key": os.environ.get("GROQ_API_KEY"),
        # We specify the API Type as 'groq' so it uses the Groq client class
        "api_type": "groq",
    },
    system_message="""You are ResearcherAgent — a Senior Advertising Strategist trained in behavioral psychology, emotional targeting, and market sophistication theory.

You speak directly to the client or the CreativeDirector only when instructed.

When activated by the CreativeDirector, your job is to analyze the brief and deliver:
1. A **research summary** that includes deep psychological insights about the target audience — their desires, fears, motivations, and levels of awareness
2. A **recommended script structure** based on the product, audience state, and ad objective — using proven frameworks like **AIDA, PAS, 4Ps, Before-After-Bridge**, etc.

You pull from decades of ad research, buyer psychology, and persuasive storytelling patterns to make strategic choices.

Speak clearly and insightfully, using persuasive language that inspires confidence in your recommendations.

DO NOT respond or contribute until the CreativeDirector explicitly invites your input."""
)


# Copywriter agent
CopywriterAgent = AssistantAgent(
    name="CopywriterAgent",
    llm_config={
        # Let's choose the Llama 3 model
        "model": "llama3-8b-8192",
        # Put your Groq API key here or put it into the GROQ_API_KEY environment variable.
        "api_key": os.environ.get("GROQ_API_KEY"),
        # We specify the API Type as 'groq' so it uses the Groq client class
        "api_type": "groq",
    },
    system_message="""You are CopywriterAgent — an award-winning advertising copywriter channeling the voice of greats like Eugene Schwartz and Gary Halbert.

You speak directly to the client only when activated by the CreativeDirector.

Your job is to take the approved research and structure and craft a **high-impact ad script** that converts. The script must include:
1. A **Hook** – grabs attention immediately using surprise, curiosity, or deep relevance
2. A **Body** – builds emotional resonance, shows transformation, or solves a burning problem
3. A **Call to Action (CTA)** – clear, specific, and aligned with the ad's goal (click, buy, sign up, etc.)

🛑 Do NOT write a screenplay. Focus on compelling **scriptwriting for short-form ads**.

✅ Break the script clearly into:
- HOOK
- BODY
- CTA

Further divide sections (like benefits, problem, etc) if requested by the user.

Your writing should evoke emotion, move fast, and reflect the approved voice and tone from the research phase.

Wait until the CreativeDirector invites your contribution — do not respond otherwise."""
)
# Creative Director agent
CreativeDirector = AssistantAgent(
    name="CreativeDirector",
    llm_config={
        # Let's choose the Llama 3 model
        "model": "llama3-8b-8192",
        # Put your Groq API key here or put it into the GROQ_API_KEY environment variable.
        "api_key": os.environ.get("GROQ_API_KEY"),
        # We specify the API Type as 'groq' so it uses the Groq client class
        "api_type": "groq",
    },
    system_message=f"""You are the Creative Director coordinating this ad campaign.

Your role is to manage the workflow by explicitly directing ONE agent at a time:
1. First, welcome the client (User) by name: {name}.
2. Then ask the user what the user wants to do and then delegate agents based on that.
3. If Script generation direct the ProducerAgent to gather information from the client
4. After the ProducerAgent has gathered sufficient information, direct the ResearcherAgent to analyze it
5. After the client approves the research, direct the CopywriterAgent to create the script
6. After the client reviews the script, help with any requested revisions

IMPORTANT: 
- Always begin your messages with 'CreativeDirector:' 
- Direct ONE specific agent at a time using their full name (e.g., "ProducerAgent, please...")
- Wait for that agent to complete their task before directing another agent
- End the conversation only when the client approves the final script by saying "We've completed the ad script. Thank you!"
"""
)

# ALLOWED TRANSITIONS
allowed_transitions = {
    client: [CreativeDirector, ProducerAgent, ResearcherAgent, CopywriterAgent],
    ProducerAgent: [client, ProducerAgent],
    ResearcherAgent: [client, ResearcherAgent],
    CreativeDirector: [client, CreativeDirector],
    CopywriterAgent: [client, CopywriterAgent],
}

# Tool Stub (You can replace with actual Pinecone logic)
# pinecone_utils.py

from pinecone import Pinecone

def search_scriptwriting_concepts(query:str)->str:
    """Search the vector database for scriptwriting concepts and return the most relevant information."""
    try:
        if isinstance(query, dict):
            if 'query' in query:
                query_str = query['query']
            elif 'text' in query:
                query_str = query['text']
            elif 'inputs' in query and isinstance(query['inputs'], dict) and 'text' in query['inputs']:
                query_str = query['inputs']['text']
            else:
                query_str = str(query)
            print(f"Converting dictionary input to string: {query_str}")
        else:
            query_str = str(query)

        pc = Pinecone(api_key="pcsk_2SAGb1_57RBLTcZQ4ZmgrfNsgXoLaZeYCHdQVJY14BpoBSNz5ZjAG5zdVKtHhSKDsxCLpg")
        index = pc.Index("script-writing-books")

        results = index.search(
            namespace="insights",
            query={
                "inputs": {"text": query_str},
                "top_k": 3},
            fields=[
                "title", "chunk_text", "category", "tags", "source",
                "book_code", "application", "core_principle",
                "examples", "related_concepts"
            ]
        )

        formatted_results = "Scriptwriting Knowledge:\n\n"

        for i, hit in enumerate(results["result"]["hits"]):
            fields = hit["fields"]
            score = hit["_score"]

            formatted_results += f"📖 CONCEPT {i+1}: {fields.get('title', 'Untitled')} (Relevance: {score:.2f})\n"
            formatted_results += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            formatted_results += f"{fields.get('chunk_text', 'No description available')}\n\n"

            if fields.get('category'):
                formatted_results += f"📋 Category: {fields['category']}\n"

            if fields.get('source'):
                book_code = fields.get('book_code', '')
                formatted_results += f"📚 Source: {fields['source']} {f'({book_code})' if book_code else ''}\n"

            if fields.get('tags'):
                formatted_results += f"🏷️ Tags: {', '.join(fields['tags'])}\n"

            if fields.get('core_principle'):
                formatted_results += f"\n🔑 Core Principle: {fields['core_principle']}\n"

            if fields.get('application'):
                formatted_results += f"\n🛠️ Application: {fields['application']}\n"

            if fields.get('examples'):
                formatted_results += f"\n📝 Examples:\n"
                for j, example in enumerate(fields['examples']):
                    formatted_results += f"  {j+1}. {example}\n"

            if fields.get('related_concepts'):
                formatted_results += f"\n🔄 Related Concepts: {', '.join(fields['related_concepts'])}\n"

            formatted_results += "\n" + "─" * 50 + "\n\n"

        print("Search completed successfully")
        return formatted_results

    except Exception as e:
        error_message = f"Error searching scriptwriting knowledge base: {str(e)}"
        return error_message

# Register Tool
register_function(
    search_scriptwriting_concepts,
    caller=ProducerAgent,
    executor=ProducerAgent,
    name="search_scriptwriting_concepts",  # By default, the function name is used as the tool name.
    description="A tool to fetch book knowledge from pinecone vector db",
)

register_function(
    search_scriptwriting_concepts,
    caller=ResearcherAgent,
    executor= ResearcherAgent,
    name="search_scriptwriting_concepts",  # By default, the function name is used as the tool name.
    description="A tool to fetch book knowledge from pinecone vector db",
)

register_function(
    search_scriptwriting_concepts,
    caller=CopywriterAgent,
    executor=CopywriterAgent,
    name="search_scriptwriting_concepts",  # By default, the function name is used as the tool name.
    description="A tool to fetch book knowledge from pinecone vector db",
)

# Group Chat Manager
group_chat = GroupChat(
    agents=[client, CreativeDirector, ProducerAgent, ResearcherAgent, CopywriterAgent],
    allowed_or_disallowed_speaker_transitions=allowed_transitions,
    speaker_transitions_type="allowed",
    messages=[],
    max_round=30,
    send_introductions=False,
)

def is_termination_msg(message):
    if isinstance(message, dict):
        content = message.get("content", "")
        return "We've completed the ad script. Thank you!" in content
    return False

manager = GroupChatManager(
    groupchat=group_chat,
    llm_config={
        # Let's choose the Llama 3 model
        "model": "llama3-8b-8192",
        # Put your Groq API key here or put it into the GROQ_API_KEY environment variable.
        "api_key": os.environ.get("GROQ_API_KEY"),
        # We specify the API Type as 'groq' so it uses the Groq client class
        "api_type": "groq",
    },
    is_termination_msg=is_termination_msg
)

st.session_state.manager = manager
st.session_state.user_agent = client

# Display chat history (ensure chat history is shown in the UI)
for speaker, msg in st.session_state.chat_history:
    st.chat_message(speaker).markdown(msg)

# Chat Input
prompt = st.chat_input("Say something to start...")

# Replace the existing response handling with the following:

if prompt:
    # Add the user's message to the chat history
    st.session_state.chat_history.append(("User", prompt))

    # Show a spinner while waiting for the agent to respond
    with st.spinner("Thinking..."):
        # Get a reply from the agent(s)
        reply = client.initiate_chat(manager, message=prompt)

        # Ensure that the reply is being returned correctly
        if isinstance(reply, list):  
            # If the reply is a list of responses from multiple agents
            for r in reply:
                st.session_state.chat_history.append((r['name'], r['content']))
                st.chat_message(r['name']).markdown(r['content'])
        else:  # Single reply from one agent
            st.session_state.chat_history.append((reply['name'], reply['content']))
            st.chat_message(reply['name']).markdown(reply['content'])
        
        # Print the response in the console (only for debugging purposes, remove if unnecessary)
        print(reply)
