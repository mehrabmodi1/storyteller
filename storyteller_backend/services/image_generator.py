"""
Image Generator Service

Handles AI image generation for story chapters:
- Creates descriptive prompts with GPT-4o-mini
- Generates images with DALL-E 3
- Optionally uploads to Azure Blob Storage for persistence

Migrated from src/agent/graph.py (generate_image_for_story function)
"""

from typing import Optional, Tuple
from datetime import datetime
import io
import httpx

from config.settings import settings
from services.auth_service import get_async_openai_client


class ImageGenerator:
    """
    Generates images for story chapters using an image gen model.
    
    The service creates high-quality image prompts based on story text,
    then generates images that maintain visual continuity across a journey.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the image generator.
        
        Args:
            api_key: Optional API key for per-request authentication
        """
        self.client = get_async_openai_client(api_key)
        self.enable_generation = True  # Could be made configurable
        self.min_chars_for_generation = 1200
        
        # Azure storage setup (optional)
        self.use_azure_storage = (
            settings.azure_storage_connection_string is not None and
            settings.azure_container_name is not None
        )
        
        if self.use_azure_storage:
            try:
                from azure.storage.blob import BlobServiceClient
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    settings.azure_storage_connection_string
                )
                self.container_name = settings.azure_container_name
                self._ensure_container_exists()
            except ImportError:
                print("Warning: azure-storage-blob not installed. Disabling Azure storage.")
                self.use_azure_storage = False
            except Exception as e:
                print(f"Warning: Failed to initialize Azure storage: {e}")
                self.use_azure_storage = False
    
    def _ensure_container_exists(self):
        """Ensure the Azure container exists."""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            if not container_client.exists():
                container_client.create_container()
                print(f"Created Azure container: {self.container_name}")
        except Exception as e:
            print(f"Error ensuring container exists: {e}")
    
    async def _generate_image_prompt(
        self,
        story_text: str,
        parent_image_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a descriptive image prompt from story text using GPT-4o-mini.
        
        Args:
            story_text: The story chapter text
            parent_image_prompt: Optional previous image prompt for continuity
        
        Returns:
            Generated image prompt, or None if generation fails
        """
        system_content = """You are an expert at creating image prompts for DALL-E 3. Your goal is to translate story text into a prompt that generates a warm, coloured sketch.

Key stylistic requirements:
- **Artistic Style:** A coloured sketch, with minimal detail, and very rough strokes in the style of Impressionist painters like Monet, Van Gogh, and Degas. These should be sketches of characters and events.
- **Detail Level:** Minimal details on elements in the scene. There should be absolutely no text in the image.
- **Colour Palette:** The colours should reflect the mood of the provided story text.
- **Feeling:** The overall image should feel warm and evocative, not gritty or photorealistic.

Based on the story text, create a single, concise paragraph that describes a visually compelling scene, adhering to all the stylistic requirements above. Include the key stylistic requirements verbatim in your prompt.
Focus on key characters, the setting, the mood, and the action."""
        
        if parent_image_prompt:
            system_content += f"\n\nMaintain visual continuity with the previous image, which was described as: '{parent_image_prompt}'. Ensure characters and locations look consistent, while adhering to the specified artistic style."
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": story_text}
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.chat_model,
                messages=messages,
                max_tokens=250,
            )
            
            image_prompt = response.choices[0].message.content
            print(f"Generated Image Prompt: {image_prompt}")
            return image_prompt
            
        except Exception as e:
            print(f"Error generating image prompt: {e}")
            return None
    
    async def _generate_dalle_image(self, image_prompt: str) -> Optional[str]:
        """
        Generate an image using DALL-E.
        
        Args:
            image_prompt: The descriptive prompt for DALL-E
        
        Returns:
            Image URL, or None if generation fails
        """
        try:
            response = await self.client.images.generate(
                model=settings.image_model,
                prompt=image_prompt,
                n=1,
                size="1024x1024",  # DALL-E 3 supports 1024x1024, 1024x1792, 1792x1024
            )
            
            image_url = response.data[0].url
            print(f"Generated Image URL: {image_url}")
            return image_url
            
        except Exception as e:
            print(f"Error generating DALL-E image: {e}")
            return None
    
    async def _upload_to_azure(
        self,
        image_url: str,
        blob_name: str
    ) -> Optional[str]:
        """
        Download image from URL and upload to Azure Blob Storage.
        
        Args:
            image_url: URL of the image to download
            blob_name: Name for the blob in Azure storage
        
        Returns:
            Public URL of the uploaded blob, or None if upload fails
        """
        if not self.use_azure_storage:
            return image_url
        
        try:
            # Download image from DALL-E URL
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(image_url)
                response.raise_for_status()
                image_data = response.content
            
            # Upload to Azure
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(
                io.BytesIO(image_data),
                overwrite=True,
                content_settings={'content_type': 'image/png'}
            )
            
            # Return the public URL
            azure_url = blob_client.url
            print(f"Uploaded image to Azure: {azure_url}")
            return azure_url
            
        except Exception as e:
            print(f"Error uploading to Azure: {e}. Using original URL.")
            return image_url
    
    async def generate_image(
        self,
        story_text: str,
        parent_image_prompt: Optional[str] = None,
        story_node_id: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate an image for a story chapter.
        
        This is the main public method that orchestrates the full pipeline:
        1. Generate descriptive prompt with GPT-4o-mini
        2. Generate image with DALL-E 3
        3. Optionally upload to Azure Blob Storage
        
        Args:
            story_text: The story chapter text
            parent_image_prompt: Optional previous image prompt for continuity
            story_node_id: Optional node ID for blob naming
        
        Returns:
            Tuple of (image_url, image_prompt), or (None, None) if generation fails
        """
        print(f"--- Triggering Image Generation @ {datetime.now()} ---")
        
        if not self.enable_generation:
            return None, None
        
        if len(story_text) < self.min_chars_for_generation:
            print(f"Story too short for image generation ({len(story_text)} chars)")
            return None, None
        
        try:
            # Step 1: Generate image prompt
            image_prompt = await self._generate_image_prompt(story_text, parent_image_prompt)
            if not image_prompt:
                return None, None
            
            # Step 2: Generate image with DALL-E
            image_url = await self._generate_dalle_image(image_prompt)
            if not image_url:
                return None, image_prompt
            
            # Step 3: Optionally upload to Azure
            if self.use_azure_storage and story_node_id:
                blob_name = f"story_images/{story_node_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                image_url = await self._upload_to_azure(image_url, blob_name)
            
            return image_url, image_prompt
            
        except Exception as e:
            print(f"An error occurred during image generation: {e}")
            return None, None
    
    def should_generate_image(self, story_text: str) -> bool:
        """
        Check if an image should be generated for the given story text.
        
        Args:
            story_text: The story text to check
        
        Returns:
            True if image generation should proceed
        """
        return (
            self.enable_generation and
            len(story_text) >= self.min_chars_for_generation
        )


# Global instance for convenience
_image_generator: Optional[ImageGenerator] = None


def get_image_generator(api_key: Optional[str] = None) -> ImageGenerator:
    """
    Get the global image generator instance.
    
    Args:
        api_key: Optional API key for per-request authentication
    
    Returns:
        ImageGenerator instance
    """
    global _image_generator
    if _image_generator is None or api_key is not None:
        _image_generator = ImageGenerator(api_key)
    return _image_generator

