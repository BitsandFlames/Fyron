"""Lightweight FHIR object wrapper for attribute-style access."""

import json
from types import SimpleNamespace
from typing import Any, Dict, List


class FHIRObj(SimpleNamespace):
    """Recursively wraps dicts/lists for attribute-style access."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the wrapper and recursively wrap dicts/lists."""
        super().__init__(**kwargs)
        for key, val in kwargs.items():
            if isinstance(val, Dict):
                setattr(self, key, FHIRObj(**val))
            elif isinstance(val, List):
                setattr(
                    self, key, [FHIRObj(**v) if isinstance(v, Dict) else v for v in val]
                )

    def __getattr__(self, item: str) -> None:
        """Return None for missing attributes instead of raising."""
        return None

    def __getstate__(self) -> Dict[str, Any]:
        """Support pickling by returning internal dict state."""
        return self.__dict__

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Restore state for unpickling."""
        self.__dict__.update(state)

    def to_json(self) -> str:
        """Serialize the object to JSON."""
        return json.dumps(self, default=lambda o: o.__dict__)

    def to_dict(self) -> Any:
        """Convert the object to a plain dict."""
        return json.loads(self.to_json())
