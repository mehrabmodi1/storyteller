from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, AsyncGenerator
from dotenv import load_dotenv
import networkx as nx
from uuid import uuid4
from langchain_core.runnables import RunnableConfig
from langchain_core.output_parsers.string import StrOutputParser
import asyncio
from datetime import datetime
import json
from openai import AsyncOpenAI
from pathlib import Path
import os

# Load environment variables from .env file at the start
load_dotenv()

from . import config as agent_config
from .state import StorytellerState
from ..embed_retrieve.retriever import HybridRetriever

# --- LLM and Retriever Setup ---
# We will create specific LLM clients for each node to ensure the correct
# model is used for each specific task.
# Note: Retriever will be created per-request based on corpus_name in state

# Initialize the OpenAI client for image generation
# This uses the OPENAI_API_KEY from the .env file automatically
client = AsyncOpenAI()

_current_dir = Path(__file__).parent
_personas_path = _current_dir / "personas.json"

with open(_personas_path, "r") as f:
    PERSONAS_DATA = {p["name"]: p for p in json.load(f)}

# --- Pydantic Models for Structured Output ---
class SearchQuery(BaseModel):
    query: str = Field(description="A concise search query based on the user's prompt.")

class Story(BaseModel):
    story: str = Field(description="The generated story text, approximately 1-2 minutes in reading length.")

class Choices(BaseModel):
    choices: List[str] = Field(description="A list of three follow-up prompts for the user.")

# --- Image Generation ---
async def generate_image_for_story(story_text: str, parent_image_prompt: str = None):
    """
    Generates an image for a story by first creating a descriptive
    prompt with gpt-4o-mini, then calling DALL-E 3.
    If a parent image prompt is provided, it's used to maintain visual continuity.
    """
    print(f"--- Triggering Image Generation @ {datetime.now()} ---")
    try:
        # Step 1: Generate a high-quality image prompt with gpt-4o-mini
        system_content = """You are an expert at creating image prompts for DALL-E 3. Your goal is to translate story text into a prompt that generates a warm, coloured sketch.

Key stylistic requirements:
- **Artistic Style:** A coloured sketch, with minimal detail, and very rough strokes in the style of Impressionist paintings like Monet's. These should be sketches of characters and events.
- **Detail Level:** Minimal details on elements in the scene. There should be absolutely no text in the image. 
- **Colour Palette:** The colours should reflect the mood of the provided story text.
- **Feeling:** The overall image should feel warm and evocative, not gritty or photorealistic.

Based on the story text, create a single, concise paragraph that describes a visually compelling scene, adhering to all the stylistic requirements above. Focus on key characters, the setting, the mood, and the action."""
        if parent_image_prompt:
            system_content += f"\\n\\nMaintain visual continuity with the previous image, which was described as: '{parent_image_prompt}'. Ensure characters and locations look consistent, while adhering to the specified artistic style."

        prompt_generation_messages = [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": f"Here is the story text:\\n\\n{story_text}"
            }
        ]
        
        prompt_response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=prompt_generation_messages,
            max_tokens=250, # Increased max_tokens for potentially more detailed prompts
        )
        image_prompt = prompt_response.choices[0].message.content
        print(f"Generated Image Prompt: {image_prompt}")

        if not image_prompt:
            raise ValueError("Failed to generate an image prompt.")

        # Step 2: Generate the image with DALL-E 3
        image_response = await client.images.generate(
            model=agent_config.IMAGE_GENERATION_MODEL,
            prompt=image_prompt,
            n=1,
            size=agent_config.IMAGE_GENERATION_SIZE, 
        )
        
        image_url = image_response.data[0].url
        print(f"Generated Image URL: {image_url}")
        return image_url, image_prompt

    except Exception as e:
        print(f"An error occurred during image generation: {e}")
        return None, None

def ensure_user_dir(username):
    dir_path = os.path.join('saved_graphs', username)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def save_graph_to_file(graph, username, initial_prompt, last_prompt, persona=None, corpus_name=None):
    dir_path = ensure_user_dir(username)
    # Retrieve or generate graph_name
    meta = getattr(graph, 'graph', {})
    graph_name = meta.get('graph_name')
    if not graph_name:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        initial_snippet = (initial_prompt or '')[:25].replace(' ', '_').replace('/', '_')
        graph_name = f"{timestamp}_{initial_snippet}.json"
        # Store in graph metadata
        meta['graph_name'] = graph_name
        graph.graph['graph_name'] = graph_name
    file_path = os.path.join(dir_path, graph_name)
    # Find the latest story node timestamp
    story_timestamps = [d.get('timestamp') for _, d in graph.nodes(data=True) if d.get('type') == 'story' and d.get('timestamp')]
    last_story_timestamp = max(story_timestamps) if story_timestamps else None
    data = {
        'meta': {
            'username': username,
            'graph_name': graph_name,
            'initial_prompt': initial_prompt,
            'initial_snippet': (initial_prompt or '')[:25].replace(' ', '_').replace('/', '_'),
            'last_prompt': last_prompt,
            'last_snippet': (last_prompt or '')[:25].replace(' ', '_').replace('/', '_'),
            'persona': persona,
            'corpus_name': corpus_name,  # Add corpus information
            'num_story_nodes': sum(1 for _, d in graph.nodes(data=True) if d.get('type') == 'story'),
            'last_story_timestamp': last_story_timestamp,
        },
        'graph': nx.node_link_data(graph)
    }
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return graph_name

def list_saved_graphs(username):
    dir_path = ensure_user_dir(username)
    graphs = []
    for fname in os.listdir(dir_path):
        if fname.endswith('.json'):
            with open(os.path.join(dir_path, fname), 'r') as f:
                try:
                    data = json.load(f)
                    meta = data.get('meta', {})
                    meta['graph_id'] = fname
                    graphs.append(meta)
                except Exception:
                    continue
    # Sort by timestamp descending
    graphs.sort(key=lambda m: m.get('timestamp', ''), reverse=True)
    return graphs

def load_graph_from_file(username, graph_id):
    dir_path = ensure_user_dir(username)
    file_path = os.path.join(dir_path, graph_id)
    with open(file_path, 'r') as f:
        data = json.load(f)
    graph = nx.node_link_graph(data['graph'])
    meta = data.get('meta', {})
    return graph, meta

# --- Node Definitions ---
# Each node in the graph is a function that takes the current state
# and returns a dictionary with the updated state values.

def get_last_story(state: StorytellerState):
    """
    If this is a continuation of a story, find the text of the parent story node
    and the prompt used for its image.
    """
    print(f"--- Node: get_last_story @ {datetime.now()} ---")
    last_story = None
    parent_image_prompt = None
    choice_id = state.get('current_choice_id')
    
    if choice_id:
        graph = state['graph']
        # The parent of a choice node is the story node that led to it.
        # We find it by looking at the predecessors in the graph.
        predecessors = list(graph.predecessors(choice_id))
        if predecessors:
            parent_story_id = predecessors[0]
            parent_node_data = graph.nodes[parent_story_id]
            last_story = parent_node_data.get('story')
            parent_image_prompt = parent_node_data.get('image_prompt')
            print(f"Found parent story for choice {choice_id}: node {parent_story_id}")

    return {"last_story": last_story, "parent_image_prompt": parent_image_prompt}

def update_graph_with_story(state: StorytellerState):
    """
    Adds the newly generated story as a node to the graph.
    If a choice from a previous step led to this story, it connects them.
    """
    print(f"--- Node: update_graph_with_story @ {datetime.now()} ---")
    graph = state['graph'].copy()
    story = state['story']
    image_url = state.get('image_url')
    image_prompt = state.get('image_prompt')
    last_message = state['messages'][-1].content
    
    # The parent node is the choice that was clicked to trigger this story
    parent_node_id = state.get('current_choice_id')

    story_node_id = f"story_{uuid4()}"
    graph.add_node(
        story_node_id, 
        label=f"Chapter: \"{last_message[:30]}...\"", 
        story=story, 
        image_url=image_url,
        image_prompt=image_prompt, # Store the prompt
        type='story',
        timestamp=datetime.now().isoformat()
    )

    if parent_node_id:
        graph.add_edge(parent_node_id, story_node_id)
    
    # Automatic save after update
    username = state.get('username', 'default_user')
    initial_prompt = state.get('initial_prompt', None)
    last_prompt = last_message
    persona = state.get('persona_name', None)
    corpus_name = state.get('corpus_name', None)  # Get corpus_name from state
    graph_name = state.get('graph_name') # Get the graph_name from state
    save_graph_to_file(graph, username, initial_prompt, last_prompt, persona, corpus_name)

    # This new story node is now the one to which choices will be attached
    return {"graph": graph, "latest_story_node_id": story_node_id}


def update_graph_with_choices(state: StorytellerState):
    """
    Adds the generated choices as nodes to the graph, connected
    to the most recently created story node.
    """
    print(f"--- Node: update_graph_with_choices @ {datetime.now()} ---")
    graph = state['graph'].copy()
    choices = state['choices']
    parent_story_id = state['latest_story_node_id']

    for choice in choices:
        choice_node_id = f"choice_{uuid4()}"
        graph.add_node(
            choice_node_id, 
            label=choice, 
            isChoice=True,
            type='choice'
        )
        graph.add_edge(parent_story_id, choice_node_id)

    # Save the complete graph (including choice nodes) to file
    username = state.get('username', 'default_user')
    initial_prompt = state.get('initial_prompt', None)
    last_prompt = state['messages'][-1].content if state['messages'] else None
    persona = state.get('persona_name', None)
    corpus_name = state.get('corpus_name', None)
    save_graph_to_file(graph, username, initial_prompt, last_prompt, persona, corpus_name)

    # Serialize the graph for the frontend
    # networkx.node_link_data is a perfect format for this
    serializable_graph = nx.node_link_data(graph)

    return {"graph": graph, "serializable_graph": serializable_graph}


def generate_search_query(state: StorytellerState):
    """
    Takes the user's prompt and generates a targeted search query.
    """
    print(f"--- Node: generate_search_query @ {datetime.now()} ---")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         """You are an expert at converting user prompts into effective search queries for a database of ancient mythological texts like the Mahabharata. 
         Based on the last user message, generate a concise search query that focuses on the key characters, events, or concepts. 
         Your query should be a sentence. Do not answer the user's question, just provide the query that will retrieve source-chunks
         that will help respond to the user's prompt."""),
        ("user", "{input}")
    ])
    
    llm_for_query = ChatOpenAI(
        temperature=0, 
        model_name=agent_config.QUERY_GENERATION_MODEL
    ).with_structured_output(SearchQuery)

    query_generation_chain = prompt | llm_for_query
    
    # The user's prompt is the last message in the list
    last_message = state['messages'][-1].content
    search_query = query_generation_chain.invoke({"input": last_message}).query

    print(f"Generated Search Query: {search_query}")
    
    return {"search_query": search_query}

def retrieve_chunks(state: StorytellerState):
    """
    Retrieves text chunks from the database using the generated search query.
    """
    print(f"--- Node: retrieve_chunks @ {datetime.now()} ---")
    
    # Create a corpus-specific retriever instance
    corpus_name = state.get('corpus_name', 'mahabharata')  # Default to mahabharata for backward compatibility
    retriever = HybridRetriever(corpus_name=corpus_name)
    
    results = retriever.search(
        query=state['search_query'], 
        top_k=agent_config.TOP_K_CHUNKS
    )
    # If randomize_retrieval is set, shuffle the similarity scores among the results
    if state.get('randomize_retrieval'):
        import random
        scores = [item.get('similarity', 0) for item in results]
        random.shuffle(scores)
        for i, item in enumerate(results):
            item['similarity'] = scores[i]
    # Combine the context and base_text to form the document for the LLM
    retrieved_docs = [
        f"Context: {item.get('context', '')}\n\nText: {item.get('base_text', '')}" 
        for item in results
    ]
    print(f"Retrieved {len(retrieved_docs)} chunks from corpus '{corpus_name}'.")
    return {"retrieved_chunks": retrieved_docs}

async def generate_story(state: StorytellerState, config: RunnableConfig):
    """
    Takes the retrieved chunks and generates a short story, streaming
    the text back to the client as it's generated. Concurrently,
    it kicks off an image generation task based on the initial text.
    """
    print(f"--- Node: generate_story @ {datetime.now()} ---")
    story_length = state['story_length']
    last_story = state.get('last_story')
    parent_image_prompt = state.get('parent_image_prompt')
    persona_name = state.get('persona_name')

    # Default system prompt if no persona is selected
    base_system_prompt = """You are a master storyteller. Your task is to weave a cohesive and engaging story from the provided source material, inspired by the user's prompt. 
        The story's length and level of detail should be appropriate for approximately {story_length} tokens.
        Do not just summarize the chunks; create a rich narrative, staying true to the events described in the source material."""

    # Fetch persona prompt if a persona is selected
    if persona_name and persona_name in PERSONAS_DATA:
        persona_prompt = PERSONAS_DATA[persona_name]["system_prompt"]
        # The persona prompt will give the core instruction
        system_prompt = f"{persona_prompt}\\n\\n"
        if last_story:
             # Add context about continuing the story
            system_prompt += """You are continuing a narrative. The user has chosen a path, and you must now weave the next part of the story, building upon the provided previous chapter.
PREVIOUS CHAPTER:
{last_story}

Your task is to use the following text chunks as source material to write the next chapter of about {story_length} tokens. Your story MUST be as long as specified - deviation in n tokens shouldn't be more than 10%. 
You must explicitly reference how the current chapter connects to the previous chapter. Transition gracefully from the previous chapter to the current one. The story should be inspired by the user's prompt."""
        else:
            # Add context for starting a new story
            system_prompt += """Use the provided source material to write a story inspired by the user's prompt. 
The story's length and level of detail should be appropriate for approximately {story_length} tokens.
Do not just summarize the chunks; create a rich narrative, staying true to the events described in the source material."""
    else:
        # Fallback to the original logic if no persona or an invalid persona is provided
        if last_story:
            system_prompt = """You are a master storyteller continuing a narrative. 
        The user has chosen a path, and you must now weave the next part of the story, building upon the provided previous chapter.
        
        PREVIOUS CHAPTER:
        {last_story}
        
        Your task is to use the following text chunks as source material to write the next chapter of about {story_length} tokens. Your story MUST be as long as specified - deviation in n tokens shouldn't be more than 10%. 
        You must explicitly reference how 
        the current chapter connects to the previous chapter. Transition gracefully from the previous chapter to the current one. The story should be inspired by
        the user's prompt. Do not just summarize the chunks, create a rich narrative that logically follows the previous chapter."""
        else:
            system_prompt = base_system_prompt

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt + "\\n\\nUSER PROMPT: {prompt}\\n\\nREFERENCE CHUNKS:\\n{chunks}"),
        ("user", "Please generate the story.")
    ])
    
    # Default temperature
    temperature = 0.7
    if persona_name and persona_name in PERSONAS_DATA:
        temperature = PERSONAS_DATA[persona_name]["temperature"]

    story_llm = ChatOpenAI(
        temperature=temperature, 
        model_name=agent_config.STORY_GENERATION_MODEL,
        max_tokens=story_length,
        streaming=True,
    )

    story_generation_chain = prompt | story_llm | StrOutputParser()
    
    last_message = state['messages'][-1].content
    chunks_str = "\\n---\\n".join(state['retrieved_chunks'])
    
    invoke_params = {
        "prompt": last_message,
        "chunks": chunks_str,
        "story_length": story_length,
    }
    if last_story:
        invoke_params["last_story"] = last_story

    # We stream the response and aggregate it, while also
    # yielding the chunks back to the client.
    full_story = ""
    image_gen_task = None
    MIN_CHARS_FOR_IMAGE = agent_config.MIN_CHARS_FOR_IMAGE

    async for chunk in story_generation_chain.astream(
        invoke_params, 
        config=config, # Pass config to get stream events
    ):
        full_story += chunk
        # Once we have enough text, start the image generation in the background
        if agent_config.ENABLE_IMAGE_GENERATION and image_gen_task is None and len(full_story) > MIN_CHARS_FOR_IMAGE:
            image_gen_task = asyncio.create_task(
                generate_image_for_story(full_story, parent_image_prompt)
            )
    
    # Wait for the image generation to complete
    image_url, image_prompt = None, None
    if image_gen_task:
        result = await image_gen_task
        if result:
            image_url, image_prompt = result
    
    return {"story": full_story, "image_url": image_url, "image_prompt": image_prompt}

def generate_choices(state: StorytellerState):
    """
    Generates three follow-up choices based on the new story.
    """
    print(f"--- Node: generate_choices @ {datetime.now()} ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an expert in narrative branching. Based on the following story, generate three distinct and interesting follow-up prompts that the user could choose to continue their exploration. "
         "Phrase them as commands or questions. For example: 'Tell me more about Arjuna's exile.' or 'What happened next at the dice game?'"
         "STORY:\\n{story}"),
        ("user", "Please generate three follow-up choices.")
    ])

    choices_llm = ChatOpenAI(
        temperature=0.7,
        model_name=agent_config.CHOICE_GENERATION_MODEL
    ).with_structured_output(Choices)
    
    choice_generation_chain = prompt | choices_llm
    
    story_for_choices = state['story']
    # Truncate the story if it's too long, to avoid context window errors.
    # The end of the story is most relevant for generating the next steps.
    max_chars = 4000
    if len(story_for_choices) > max_chars:
        story_for_choices = story_for_choices[-max_chars:]

    generated_choices = choice_generation_chain.invoke({
        "story": story_for_choices
    }).choices

    return {"choices": generated_choices}

# --- Graph Definition ---

# Initialize the state graph with our StorytellerState
workflow = StateGraph(StorytellerState)

# Add nodes to the graph
workflow.add_node("get_last_story", get_last_story)
workflow.add_node("generate_search_query", generate_search_query)
workflow.add_node("retrieve_chunks", retrieve_chunks)
workflow.add_node("generate_story", generate_story)
workflow.add_node("update_graph_with_story", update_graph_with_story)
workflow.add_node("generate_choices", generate_choices)
workflow.add_node("update_graph_with_choices", update_graph_with_choices)

# Define the edges that connect the nodes
workflow.set_entry_point("get_last_story")
workflow.add_edge("get_last_story", "generate_search_query")
workflow.add_edge("generate_search_query", "retrieve_chunks")
workflow.add_edge("retrieve_chunks", "generate_story")
workflow.add_edge("generate_story", "update_graph_with_story")
workflow.add_edge("update_graph_with_story", "generate_choices")
workflow.add_edge("generate_choices", "update_graph_with_choices")
workflow.add_edge("update_graph_with_choices", END)

# Compile the graph into a runnable app
story_agent = workflow.compile()

print("Storyteller agent graph compiled with new NetworkX logic.") 