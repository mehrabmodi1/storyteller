from typing import List, TypedDict, Optional
from langchain_core.messages import BaseMessage
import networkx as nx

class StorytellerState(TypedDict):
    """
    Represents the state of our storyteller agent. This is the "memory"
    that gets passed between each step of the agent's process.
    """
    # The history of messages in the conversation.
    messages: List[BaseMessage]
    
    # The graph that stores the entire story structure
    graph: nx.DiGraph
    
    # The ID of the choice node that triggered the current story generation
    current_choice_id: Optional[str]
    
    # The ID of the most recently created story node
    latest_story_node_id: Optional[str]
    
    # The search query generated from the user's prompt.
    search_query: str

    # The chunks retrieved from the database based on the search query.
    retrieved_chunks: List[str]
    
    # The most recently generated story text.
    story: str

    # The list of generated follow-up prompts for the user.
    choices: List[str]
    
    # The desired length of the story in tokens
    story_length: int

    # The story from the previous turn, to be used as context.
    last_story: Optional[str]

    # The final, serialized graph to be sent to the frontend
    serializable_graph: Optional[dict]
    
    # The name of the selected storyteller persona.
    persona_name: Optional[str]

    # The URL of the image generated for the latest story chapter.
    image_url: Optional[str]

    # The username for saving user-specific graphs.
    username: Optional[str]

    # The initial prompt for saving graph metadata.
    initial_prompt: Optional[str]
    
    # The name of the corpus being used for this story generation.
    corpus_name: Optional[str] 