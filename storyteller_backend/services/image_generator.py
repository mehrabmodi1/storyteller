"""
Image Generator Service

Handles AI image generation for story chapters:
- Creates descriptive prompts with GPT-4o-mini
- Generates images with DALL-E

Migrated from src/agent/graph.py (generate_image_for_story function)
"""

from typing import Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import base64

from config.settings import settings
from services.auth_service import get_async_openai_client


STYLE_PREFIX = (
    "impressionist watercolour sketch, soft pastel colour palette, "
    "loose gestural brushstrokes, minimal detail, no text, warm dreamlike atmosphere — "
)


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
        system_content = """Describe a single visual scene from the story text in one concise sentence or short paragraph.

You MUST include at least one main character from the passage — name them and briefly describe their appearance or posture as it appears in the text.
Focus on: that character in their setting, the dominant mood, and one central action or moment.
Do NOT include any style, artistic, or colour instructions — those are handled separately.
Do NOT include any text, labels, or captions in your description."""
        
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
    
    async def _generate_dalle_image(self, image_prompt: str) -> Union[Optional[str], Optional[bytes]]:
        """
        Generate an image using DALL-E.

        When local_image_storage is enabled, returns raw PNG bytes (via b64_json).
        Otherwise returns the temporary blob URL.
        """
        try:
            use_b64 = settings.local_image_storage
            response = await self.client.images.generate(
                model=settings.image_model,
                prompt=STYLE_PREFIX + image_prompt,
                n=1,
                size=settings.image_generation_size,
                response_format="b64_json" if use_b64 else "url",
            )

            if use_b64:
                image_bytes = base64.b64decode(response.data[0].b64_json)
                print(f"Generated image ({len(image_bytes)} bytes)")
                return image_bytes
            else:
                image_url = response.data[0].url
                print(f"Generated Image URL: {image_url}")
                return image_url

        except Exception as e:
            print(f"Error generating DALL-E image: {e}")
            return None
    
    def _save_image_locally(self, image_bytes: bytes) -> Optional[str]:
        """
        Save raw image bytes to saved_graphs/images/{uuid}.png.
        Returns the image UUID, or None on failure.
        """
        image_dir = settings.image_storage_path
        image_dir.mkdir(parents=True, exist_ok=True)

        self._enforce_storage_limit(image_dir)

        image_id = str(uuid4())
        file_path = image_dir / f"{image_id}.png"

        try:
            file_path.write_bytes(image_bytes)
            print(f"Saved image locally: {file_path}")
            return image_id
        except Exception as e:
            print(f"Error saving image locally: {e}")
            return None

    @staticmethod
    def _enforce_storage_limit(image_dir: Path) -> None:
        """
        If the images folder exceeds the configured size limit,
        delete oldest files (by creation time) until under the cap.
        """
        limit_bytes = settings.image_storage_limit_mb * 1024 * 1024
        files = sorted(image_dir.glob("*.png"), key=lambda f: f.stat().st_ctime)

        total = sum(f.stat().st_size for f in files)
        while total > limit_bytes and files:
            oldest = files.pop(0)
            total -= oldest.stat().st_size
            oldest.unlink()
            print(f"Evicted stale image: {oldest.name}")

    async def generate_image(
        self,
        story_text: str,
        parent_image_prompt: Optional[str] = None,
        story_node_id: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate an image for a story chapter.

        Returns:
            Tuple of (image_ref, image_prompt).
            image_ref is a UUID (local storage) or a URL (cloud), or None.
        """
        print(f"--- Triggering Image Generation @ {datetime.now()} ---")

        if not self.enable_generation:
            return None, None

        try:
            image_prompt = await self._generate_image_prompt(story_text, parent_image_prompt)
            if not image_prompt:
                return None, None

            result = await self._generate_dalle_image(image_prompt)
            if not result:
                return None, image_prompt

            if settings.local_image_storage:
                image_id = self._save_image_locally(result)  # result is bytes
                return image_id, image_prompt

            return result, image_prompt  # result is URL string

        except Exception as e:
            print(f"An error occurred during image generation: {e}")
            return None, None
    

def resolve_image_urls(serializable_graph: dict) -> dict:
    """
    Walk the serialized node-link graph and convert any local image UUID
    in 'image_url' to its serving URL (/images/{uuid}.png).
    Leaves full URLs (http/https) untouched.
    """
    if not settings.local_image_storage:
        return serializable_graph

    base_url = f"http://localhost:{settings.api_port}"
    for node in serializable_graph.get("nodes", []):
        image_ref = node.get("image_url")
        if image_ref and not image_ref.startswith("http"):
            node["image_url"] = f"{base_url}/images/{image_ref}.png"

    return serializable_graph


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

