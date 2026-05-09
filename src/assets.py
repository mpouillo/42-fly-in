import pyray as pr
from collections import defaultdict
from typing import Dict, Any


class Assets:
    """Utility class to handle loaded raylib assets."""

    def __init__(self) -> None:
        """Instantiate assets data structure."""
        self.assets: Dict[str, Any] = defaultdict(dict)

    def __str__(self) -> str:
        """Print saved assets."""
        return (
            "Assets:\n"
            + ",\n".join(
                [f"- {name} ({', '.join(part)})"
                 for name, part in self.assets.items()]
            )
        )

    def add(self, name: str, obj_type: str, obj: Any) -> None:
        """Add an asset to the library."""
        if self.assets[name] and obj_type in self.assets[name]:
            raise ValueError("Asset type already exists for name")

        self.assets[name][obj_type] = obj

    def get(self, name: str, obj_type: str) -> Any:
        """Get an asset from the library."""
        if name not in self.assets:
            raise ValueError("Asset does not exist")

        return self.assets[name].get(obj_type, None)

    def unload(self, name: str) -> None:
        """Unload an asset from the library."""
        asset: Any = self.assets.get(name)
        if not asset:
            return

        if "model" in asset:
            pr.unload_model(asset["model"])
        if "texture" in asset:
            pr.unload_texture(asset["texture"])
        if "image" in asset:
            pr.unload_image(asset["image"])
        if "font" in asset:
            pr.unload_font(asset["font"])
        if "mesh" in asset and "model" not in asset:
            pr.unload_mesh(asset["mesh"])

    def remove(self, name: str) -> None:
        """Remove an asset from the library."""
        if name in self.assets:
            self.assets.pop(name)

    def clear(self) -> None:
        """Clear all assets (unload + remove)."""
        for asset in self.assets.keys():
            self.unload(asset)
        self.assets.clear()
