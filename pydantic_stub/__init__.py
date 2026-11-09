"""Minimal pydantic stub for offline use.
Provides BaseModel with model_dump, model_dump_json, and model_validate.
Supports subclassing and JSON serialization of nested BaseModel instances.
Also supplies simple Field and model_validator placeholders.
"""

import json
from typing import Any, Callable, Dict, List


class BaseModel:
    def __init__(self, **data: Any):
        for k, v in data.items():
            setattr(self, k, v)

    def model_dump(self) -> Dict[str, Any]:
        # Recursively serialize BaseModel instances
        def serialize(value):
            if isinstance(value, BaseModel):
                return value.model_dump()
            if isinstance(value, list):
                return [serialize(v) for v in value]
            if isinstance(value, dict):
                return {k: serialize(v) for k, v in value.items()}
            return value
        return {k: serialize(v) for k, v in self.__dict__.items()}

    def model_dump_json(self, indent: int = None) -> str:
        return json.dumps(self.model_dump(), indent=indent)

    @classmethod
    def model_validate(cls, data: Dict[str, Any]):
        if not isinstance(data, dict):
            raise TypeError("data must be a dict")
        return cls(**data)


def Field(*, default=None, default_factory=None, **kwargs):
    if default_factory is not None:
        return default_factory()
    return default


def model_validator(mode: str = "") -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        return func
    return decorator
