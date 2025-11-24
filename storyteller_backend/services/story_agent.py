"""
Story Agent Service

The main LangGraph agent for interactive storytelling.

This agent orchestrates the complete story generation pipeline:
1. get_last_story: Find parent story for continuity
2. generate_search_query: Convert user prompt to search query
3. retrieve_chunks: Get relevant text chunks from corpus
4. generate_story: Generate story chapter (with streaming)
5. update_graph_with_story: Add story node to graph
6. generate_choices: Generate follow-up prompts
7. update_graph_with_choices: Add choice nodes to graph

Migrated from src/agent/graph.py
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import networkx as nx
import asyncio
import json
from pathlib import Path

from config.settings import settings
from models.state import StorytellerState
from embed_retrieve import HybridRetriever
from services.image_generator import ImageGenerator
from services.journey_manager import get_journey_manager


# --- Pydantic Models for Structured Output ---

class SearchQuery(BaseModel):
    """Structured output for search query generation."""
    query: str = Field(description="A concise search query based on the user's prompt.")


class Story(BaseModel):
    """Structured output for story generation."""
    story: str = Field(description="The generated story text.")


class Choices(BaseModel):
    """Structured output for choice generation."""
    choices: List[str] = Field(description="A list of three follow-up prompts for the user.")


# --- Load Personas ---

_personas_file = Path(__file__).parent.parent / settings.personas_file
with open(_personas_file, "r") as f:
    PERSONAS_DATA = {p["name"]: p for p in json.load(f)}


# --- Node Functions ---

def get_last_story(state: StorytellerState) -> Dict[str, Any]:
    """
    If this is a continuation of a story, find the text of the parent story node
    and the prompt used for its image.
    
    Args:
        state: Current storyteller state
    
    Returns:
        Dict with last_story and parent_image_prompt
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


def generate_search_query(state: StorytellerState) -> Dict[str, Any]:
    """
    Takes the user's prompt and generates a targeted search query.
    
    Args:
        state: Current storyteller state
    
    Returns:
        Dict with search_query
    """
    print(f"--- Node: generate_search_query @ {datetime.now()} ---")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         """You are an expert at converting user prompts into effective search queries for a database of mythological and literary texts. 
         Based on the last user message, generate a concise search query that focuses on the key characters, events, or concepts. 
         Your query should be a sentence. Do not answer the user's question, just provide the query that will retrieve source-chunks
         that will help respond to the user's prompt."""),
        ("user", "{input}")
    ])
    
    llm_for_query = ChatOpenAI(
        temperature=0, 
        model_name=settings.chat_model
    ).with_structured_output(SearchQuery)

    query_generation_chain = prompt | llm_for_query
    
    # The user's prompt is the last message in the list
    last_message = state['messages'][-1].content
    search_query = query_generation_chain.invoke({"input": last_message}).query

    print(f"Generated Search Query: {search_query}")
    
    return {"search_query": search_query}


def retrieve_chunks(state: StorytellerState) -> Dict[str, Any]:
    """
    Retrieves text chunks from the database using the generated search query.
    
    Args:
        state: Current storyteller state
    
    Returns:
        Dict with retrieved_chunks
    """
    print(f"--- Node: retrieve_chunks @ {datetime.now()} ---")
    
    # Create a corpus-specific retriever instance
    corpus_name = state.get('corpus_name', 'mahabharata')
    retriever = HybridRetriever(corpus_name=corpus_name)
    
    results = retriever.search(
        query=state['search_query'], 
        top_k=settings.retrieval_top_k
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


async def generate_story(state: StorytellerState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Takes the retrieved chunks and generates a short story, streaming
    the text back to the client as it's generated. Concurrently,
    it kicks off an image generation task based on the initial text.
    
    Args:
        state: Current storyteller state
        config: Runnable config for streaming
    
    Returns:
        Dict with story, image_url, and image_prompt
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
        system_prompt = f"{persona_prompt}\n\n"
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
        # No persona selected, use base prompt
        if last_story:
            system_prompt = """You are continuing a narrative. The user has chosen a path, and you must now weave the next part of the story, building upon the provided previous chapter.
PREVIOUS CHAPTER:
{last_story}

Your task is to use the following text chunks as source material to write the next chapter of about {story_length} tokens. Your story MUST be as long as specified - deviation in n tokens shouldn't be more than 10%. 
You must explicitly reference how the current chapter connects to the previous chapter. Transition gracefully from the previous chapter to the current one. The story should be inspired by the user's prompt."""
        else:
            system_prompt = base_system_prompt

    # Add the source material context
    system_prompt += "\n\nSOURCE MATERIAL CHUNKS:\n{chunks}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}")
    ])

    story_llm = ChatOpenAI(
        temperature=0.9,
        model_name=settings.chat_model,
        streaming=True
    )

    story_generation_chain = prompt | story_llm

    # Prepare invoke parameters
    last_message = state['messages'][-1].content
    chunks_str = "\n\n---\n\n".join(state['retrieved_chunks'])
    
    invoke_params = {
        "input": last_message,
        "chunks": chunks_str,
        "story_length": story_length
    }

    if last_story:
        invoke_params["last_story"] = last_story

    # We stream the response and aggregate it, while also
    # yielding the chunks back to the client.
    full_story = ""
    image_gen_task = None
    min_chars_for_image = 1200

    async for chunk in story_generation_chain.astream(
        invoke_params, 
        config=config,
    ):
        full_story += chunk.content
        # Once we have enough text, start the image generation in the background
        if image_gen_task is None and len(full_story) > min_chars_for_image:
            image_generator = ImageGenerator()
            if image_generator.should_generate_image(full_story):
                image_gen_task = asyncio.create_task(
                    image_generator.generate_image(full_story, parent_image_prompt)
                )
    
    # Wait for the image generation to complete
    image_url, image_prompt = None, None
    if image_gen_task:
        result = await image_gen_task
        if result:
            image_url, image_prompt = result
    
    return {"story": full_story, "image_url": image_url, "image_prompt": image_prompt}


def update_graph_with_story(state: StorytellerState) -> Dict[str, Any]:
    """
    Adds the newly generated story as a node to the graph.
    If a choice from a previous step led to this story, it connects them.
    
    Args:
        state: Current storyteller state
    
    Returns:
        Dict with updated graph and latest_story_node_id
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
        image_prompt=image_prompt,
        type='story',
        timestamp=datetime.now().isoformat()
    )

    if parent_node_id:
        graph.add_edge(parent_node_id, story_node_id)
    
    # Automatic save after update
    journey_manager = get_journey_manager()
    username = state.get('username', 'default_user')
    initial_prompt = state.get('initial_prompt', last_message)
    last_prompt = last_message
    persona = state.get('persona_name', 'default')
    corpus_name = state.get('corpus_name', 'mahabharata')
    
    journey_manager.save_graph(
        graph, username, initial_prompt, last_prompt, persona, corpus_name
    )

    # This new story node is now the one to which choices will be attached
    return {"graph": graph, "latest_story_node_id": story_node_id}


def generate_choices(state: StorytellerState) -> Dict[str, Any]:
    """
    Generates three follow-up choices based on the new story.
    
    Args:
        state: Current storyteller state
    
    Returns:
        Dict with choices
    """
    print(f"--- Node: generate_choices @ {datetime.now()} ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an expert in narrative branching. Based on the following story, generate three distinct and interesting follow-up prompts that the user could choose to continue their exploration. "
         "Phrase them as commands or questions. For example: 'Tell me more about Arjuna's exile.' or 'What happened next at the dice game?'"
         "STORY:\n{story}"),
        ("user", "Please generate three follow-up choices.")
    ])

    choices_llm = ChatOpenAI(
        temperature=0.7,
        model_name=settings.chat_model
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


def update_graph_with_choices(state: StorytellerState) -> Dict[str, Any]:
    """
    Adds the generated choices as nodes to the graph, connected
    to the most recently created story node.
    
    Args:
        state: Current storyteller state
    
    Returns:
        Dict with updated graph and serializable_graph
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
            type='choice',
            timestamp=datetime.now().isoformat()
        )
        graph.add_edge(parent_story_id, choice_node_id)

    # Save the complete graph (including choice nodes) to file
    journey_manager = get_journey_manager()
    username = state.get('username', 'default_user')
    initial_prompt = state.get('initial_prompt', None)
    last_prompt = state['messages'][-1].content if state['messages'] else None
    persona = state.get('persona_name', 'default')
    corpus_name = state.get('corpus_name', 'mahabharata')
    
    journey_manager.save_graph(
        graph, username, initial_prompt, last_prompt, persona, corpus_name
    )

    # Serialize the graph for the frontend
    serializable_graph = nx.node_link_data(graph)

    return {"graph": graph, "serializable_graph": serializable_graph}


# --- Build LangGraph Workflow ---

def create_story_agent():
    """
    Create and compile the LangGraph workflow for story generation.
    
    Returns:
        Compiled LangGraph agent
    """
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
    return workflow.compile()


# Global instance
_story_agent = None


def get_story_agent():
    """
    Get the global story agent instance.
    
    Returns:
        Compiled LangGraph story agent
    """
    global _story_agent
    if _story_agent is None:
        _story_agent = create_story_agent()
    return _story_agent

