"""Utility to list and read available Pydantic models.

Useful for:
- Visual node editor UI (show available models in dropdown for validation)
- Dynamic validation configuration
- Introspection and debugging

Usage:
    # List all available Pydantic models
    models = list_models()
    # Returns: ["Name", "Phone", "Vehicle", "Appointment", ...]

    # Get model details
    details = get_model_details("Name")
    # Returns: {"name": "Name", "fields": {...}, "validators": [...]}

    # Import model dynamically
    model_class = import_model("Name")
"""

import importlib
import inspect
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def list_models(base_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all available Pydantic models in the project.

    Scans models/ directory for all BaseModel classes.

    Args:
        base_path: Optional base path to scan (defaults to models/)

    Returns:
        List of model info dicts with name, module, fields, and validators

    Example:
        [
            {
                "name": "Name",
                "module": "models.customer",
                "description": "Validated customer name",
                "fields": {
                    "first_name": {"type": "str", "required": True},
                    "last_name": {"type": "str", "required": False},
                    "full_name": {"type": "str", "required": True}
                },
                "validators": ["validate_name_format", "validate_name_consistency"]
            },
            ...
        ]
    """
    if base_path is None:
        # Default to models directory
        base_path = Path(__file__).parent.parent / "models"

    models = []

    try:
        # Scan all Python files in models/
        for py_file in Path(base_path).rglob("*.py"):
            if py_file.name == "__init__.py" or py_file.name == "core.py":
                continue

            # Convert path to module name
            relative_path = py_file.relative_to(Path(base_path).parent)
            module_name = str(relative_path.with_suffix("")).replace("/", ".")

            try:
                # Import the module
                module = importlib.import_module(module_name)

                # Find all BaseModel classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a Pydantic BaseModel subclass
                    if (issubclass(obj, BaseModel) and
                        obj is not BaseModel and
                        not name.startswith("_")):

                        # Get model fields
                        fields = {}
                        if hasattr(obj, "model_fields"):
                            for field_name, field_info in obj.model_fields.items():
                                fields[field_name] = {
                                    "type": str(field_info.annotation),
                                    "required": field_info.is_required(),
                                    "description": field_info.description or "",
                                    "default": str(field_info.default) if field_info.default is not None else None
                                }

                        # Get validators
                        validators = []
                        for attr_name in dir(obj):
                            attr = getattr(obj, attr_name)
                            if callable(attr) and (
                                attr_name.startswith("validate_") or
                                hasattr(attr, "__validator_config__")
                            ):
                                validators.append(attr_name)

                        # Get docstring as description
                        description = obj.__doc__.strip() if obj.__doc__ else ""

                        models.append({
                            "name": name,
                            "module": module_name,
                            "description": description,
                            "fields": fields,
                            "validators": validators,
                            "file_path": str(py_file)
                        })

            except Exception as e:
                logger.debug(f"Error importing {module_name}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scanning models: {e}")

    return models


def get_model_details(model_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific Pydantic model.

    Args:
        model_name: Name of the model class

    Returns:
        Dict with model details or None if not found

    Example:
        details = get_model_details("Name")
        {
            "name": "Name",
            "module": "models.customer",
            "description": "Validated customer name with consistency checks.",
            "fields": {
                "first_name": {
                    "type": "str",
                    "required": True,
                    "description": "First name with middle names/initials",
                    "pattern": "^[A-Za-z]..."
                },
                ...
            },
            "validators": ["validate_name_format", "validate_name_consistency"]
        }
    """
    all_models = list_models()

    for model_info in all_models:
        if model_info["name"] == model_name:
            return model_info

    return None


def import_model(model_name: str) -> Optional[Type[BaseModel]]:
    """Dynamically import a Pydantic model class by name.

    Args:
        model_name: Name of the model class

    Returns:
        Model class or None if not found

    Example:
        Name = import_model("Name")
        validated = Name(
            first_name="Hrijul",
            last_name="Dey",
            full_name="Hrijul Dey",
            metadata=...
        )
    """
    model_info = get_model_details(model_name)

    if not model_info:
        logger.error(f"Model not found: {model_name}")
        return None

    try:
        module = importlib.import_module(model_info["module"])
        model_class = getattr(module, model_name)
        return model_class

    except Exception as e:
        logger.error(f"Error importing {model_name}: {e}")
        return None


def list_models_json() -> str:
    """List all models as JSON string.

    Useful for API endpoints that need to expose available models.

    Example:
        @app.get("/api/models")
        def get_models():
            return list_models_json()
    """
    import json
    models = list_models()
    return json.dumps(models, indent=2)


def get_model_schema(model_name: str) -> Optional[Dict[str, Any]]:
    """Get JSON schema for a Pydantic model.

    Useful for generating forms or validation in frontend.

    Args:
        model_name: Name of the model class

    Returns:
        JSON schema dict or None if not found

    Example:
        schema = get_model_schema("Name")
        # Use schema to generate a form in frontend
    """
    model_class = import_model(model_name)

    if not model_class:
        return None

    try:
        return model_class.model_json_schema()
    except Exception as e:
        logger.error(f"Error getting schema for {model_name}: {e}")
        return None
