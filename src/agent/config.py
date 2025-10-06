# --- Agent Model Configuration ---

# Model used to generate the targeted search query from the user's prompt.
QUERY_GENERATION_MODEL = "gpt-4o-mini"

# Model used to synthesize the story from the retrieved text chunks.
STORY_GENERATION_MODEL = "gpt-4o"

# Model used to generate follow-up choices for the user.
CHOICE_GENERATION_MODEL = "gpt-4o-mini"

# --- Image Generation Configuration ---
IMAGE_GENERATION_MODEL = "dall-e-2"
IMAGE_GENERATION_SIZE = "256x256"
ENABLE_IMAGE_GENERATION = True
MIN_CHARS_FOR_IMAGE = 1200

# --- Retriever Configuration ---
# The number of text chunks to retrieve for story generation.
TOP_K_CHUNKS = 8
