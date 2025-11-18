# Storyteller Project: Manual Setup and Architecture Guide

This document provides a comprehensive guide to setting up and running the Storyteller project locally. It also offers a deep dive into the system's architecture for developers who wish to understand, modify, or contribute to the project.

## 1. Project Overview

Storyteller is a generative AI application that creates interactive, branching narratives. Users can guide the story by making choices, and the application will dynamically generate new story chapters, complete with unique, stylized images. The experience is further customizable through different storyteller "personas," each with a distinct voice, theme, and narrative style.

## 2. Core Features

- **Interactive Branching Narrative:** The story is presented as a graph that grows as the user makes choices, creating a unique journey every time.
- **Adaptable Source Material:** The project can be adapted to any text-based source material. The `embed_retrieve` system can process any raw text, create a vector database, and allow the AI to generate stories based on it.
- **Dynamic Image Generation:** Each story chapter is accompanied by a unique, AI-generated image that reflects the mood and content of the text.
- **Customizable Personas:** Users can select from various storyteller personas (e.g., Grandmother, Pirate, Freud), each with a unique system prompt, color theme, and AI temperature setting.
- **In-Place Editing:** Users can edit their choices directly within the graph before submitting them.
- **Real-time Streaming:** Story text is streamed from the backend to the frontend token-by-token, providing a responsive user experience.
- **Configurable Storytelling:** Key parameters, such as image generation and story length, can be easily toggled or adjusted in a configuration file.

## 3. System Architecture

The project is a full-stack application composed of a Python backend and a Next.js frontend.

### Backend (`src/agent/`)

The backend is built with Python, using **FastAPI** to serve the API and **LangGraph** to manage the AI agent's logic.

- **State Management (`state.py`):** Defines the `StorytellerState`, which is a graph-like structure that tracks the entire application state, including the story graph, user messages, and configuration settings.
- **Agent Graph (`graph.py`):** This is the core of the backend. It uses `LangGraph` to define a cyclical process where different nodes are responsible for specific tasks:
    1.  `generate_search_query`: Creates a targeted search query from the user's prompt.
    2.  `retrieve_chunks`: Fetches relevant text chunks from a vector database (not covered in this guide).
    3.  `generate_story`: Streams the story text to the frontend. Once enough text is available, it concurrently triggers image generation.
    4.  `generate_choices`: Creates three follow-up choices for the user.
    5.  `update_graph_*`: The `networkx` graph is updated with the new story and choice nodes.
- **Server (`server.py`):** Exposes the API endpoints. The primary endpoint is `/api/story`, which uses Server-Sent Events (SSE) to stream the story chunks and, finally, the full `networkx` graph data to the frontend.
- **Configuration (`config.py`):** A centralized file for managing all key parameters, such as AI model names, image generation settings, and retriever configurations.

### Vector Database (`src/embed_retrieve/`)

To provide relevant context to the storyteller AI, the application uses a vector database of source material. This component is responsible for creating and querying that database.

- **Database Builder (`build_database.py`):** This script processes raw text files, chunks them into smaller, semantically coherent pieces, generates embeddings for each chunk using an OpenAI model, and stores them in a FAISS vector database. It's a one-time setup process to prepare the source material.
- **Retriever (`retriever.py`):** This module provides the `HybridRetriever`, which is used by the agent graph. When the agent generates a search query, the retriever uses it to find the most relevant text chunks from the vector database, which are then used as context for generating the story.

### Frontend (`src/app/`)

The frontend is a **Next.js** and **React** application that provides the user interface.

- **UI Framework:** **React Flow** is used to render the interactive, branching graph of the story.
- **Styling:** **Tailwind CSS** is used for styling, with persona-specific themes dynamically applied to the UI.
- **State Management:** React hooks (`useState`, `useEffect`, `useCallback`) are used to manage the application's state, including the graph's nodes and edges, user input, and loading states.
- **Communication:** The frontend communicates with the backend via the `/api/story` endpoint. It listens for `story_chunk` events to display the streaming story in a modal and then receives the final graph data to render the new nodes.
- **Image Preloading:** To ensure a smooth user experience, the frontend preloads all images in the background before rendering the graph, preventing jarring layout shifts.

## 4. Manual Setup Guide

Follow these steps to set up and run the Storyteller project on your local machine.

### Prerequisites

-   Python 3.12 or later
-   Node.js v18.0 or later
-   An OpenAI API key

### Backend Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd storyteller
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    # On Windows, use: .venv\\Scripts\\activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:**
    Create a file named `.env` in the project's root directory and add your OpenAI API key:
    ```
    OPENAI_API_KEY="your-key-here"
    ```
5. **Database**
    Make sure you have the database in `data` directory at the root level of the project. Please contact the maintainer for the database or you can choose to build your own database using your preferred data.

6.  **Run the Backend Server:**
    From the project root, run the following command:
    ```bash
    python -m uvicorn src.agent.server:app --reload
    ```
    The backend server will be running at `http://localhost:8000`.

### Frontend Setup

1.  **Navigate to the Frontend Directory:**
    ```bash
    cd src/app
    ```

2.  **Install Node.js Dependencies:**
    ```bash
    npm install
    ```

3.  **Run the Frontend Development Server:**
    ```bash
    npm run dev
    ```
    The frontend application will be running at `http://localhost:3000`. You can now open this URL in your browser to use the application. 