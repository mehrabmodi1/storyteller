"""
Personas API Routes

Endpoints for managing storyteller personas:
- GET /api/personas - List all personas
- POST /api/personas - Create new persona
- PUT /api/personas/{name} - Update persona
- DELETE /api/personas/{name} - Delete persona
"""

from fastapi import APIRouter, HTTPException, status
from typing import List
import json
from pathlib import Path
from datetime import datetime

from models.api_models import PersonaInfo
from config.settings import settings

router = APIRouter()


def _get_personas_file_path() -> Path:
    """Get the path to the personas.json file."""
    return Path(__file__).parent.parent.parent / settings.personas_file


def _load_personas() -> List[dict]:
    """Load personas from JSON file."""
    personas_file = _get_personas_file_path()
    if not personas_file.exists():
        return []
    
    with open(personas_file, 'r') as f:
        return json.load(f)


def _save_personas(personas: List[dict]) -> None:
    """Save personas to JSON file."""
    personas_file = _get_personas_file_path()
    personas_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(personas_file, 'w') as f:
        json.dump(personas, f, indent=2)


@router.get("/personas", response_model=List[PersonaInfo])
async def list_personas():
    """
    List all available storyteller personas.
    
    Returns:
        List of persona information with name, description, and color theme
    """
    personas = _load_personas()
    
    # Convert to PersonaInfo model
    return [
        PersonaInfo(
            name=p["name"],
            short_description=p["short_description"],
            color_theme=p["color_theme"]
        )
        for p in personas
    ]


@router.post("/personas", status_code=status.HTTP_201_CREATED)
async def create_persona(persona_data: dict):
    """
    Create a new storyteller persona.
    
    Args:
        persona_data: Full persona configuration including:
            - name (required)
            - short_description (required)
            - system_prompt (required)
            - color_theme (required)
            - temperature (optional, defaults to 0.7)
    
    Returns:
        Created persona data
    """
    # Validate required fields
    required_fields = ["name", "short_description", "system_prompt", "color_theme"]
    for field in required_fields:
        if field not in persona_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    personas = _load_personas()
    
    # Check if persona already exists
    if any(p["name"] == persona_data["name"] for p in personas):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Persona '{persona_data['name']}' already exists"
        )
    
    # Add metadata
    persona_data["type"] = "system"
    persona_data["created_at"] = datetime.now().isoformat()
    if "temperature" not in persona_data:
        persona_data["temperature"] = 0.7
    
    personas.append(persona_data)
    _save_personas(personas)
    
    return {
        "success": True,
        "message": f"Persona '{persona_data['name']}' created successfully",
        "persona": persona_data
    }


@router.put("/personas/{name}")
async def update_persona(name: str, persona_data: dict):
    """
    Update an existing persona.
    
    Args:
        name: Name of the persona to update
        persona_data: Updated persona fields
    
    Returns:
        Updated persona data
    """
    personas = _load_personas()
    
    # Find persona
    persona_index = next(
        (i for i, p in enumerate(personas) if p["name"] == name),
        None
    )
    
    if persona_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{name}' not found"
        )
    
    # Update fields (preserve name and created_at)
    updated_persona = personas[persona_index].copy()
    for key, value in persona_data.items():
        if key not in ["name", "created_at"]:  # Prevent changing name/created_at
            updated_persona[key] = value
    
    updated_persona["updated_at"] = datetime.now().isoformat()
    
    personas[persona_index] = updated_persona
    _save_personas(personas)
    
    return {
        "success": True,
        "message": f"Persona '{name}' updated successfully",
        "persona": updated_persona
    }


@router.delete("/personas/{name}")
async def delete_persona(name: str):
    """
    Delete a persona.
    
    Args:
        name: Name of the persona to delete
    
    Returns:
        Success confirmation
    """
    personas = _load_personas()
    
    # Find and remove persona
    original_count = len(personas)
    personas = [p for p in personas if p["name"] != name]
    
    if len(personas) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{name}' not found"
        )
    
    _save_personas(personas)
    
    return {
        "success": True,
        "message": f"Persona '{name}' deleted successfully"
    }

