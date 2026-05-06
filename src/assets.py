import pyray as pr
from collections import defaultdict
from typing import Dict, Any


class Assets:
    def __init__(self) -> None:
        self.assets: Dict[str, Any] = defaultdict(dict)

    def __str__(self) -> str:
        return (
            "Assets:\n"
            + ",\n".join(
                [f"- {name} ({', '.join(part)})"
                 for name, part in self.assets.items()]
            )
        )

    def add(self, name: str, obj_type: str, obj: Any) -> None:
        if self.assets[name] and obj_type in self.assets[name]:
            raise ValueError("Asset type already exists for name")

        self.assets[name][obj_type] = obj

    def get(self, name: str, obj_type: str) -> Any:
        if name not in self.assets:
            raise ValueError("Asset does not exist")

        return self.assets[name].get(obj_type, None)

    def unload(self, name: str) -> None:
        obj: Any = self.assets.get(name)
        if not obj:
            return

        for part in obj.values():
            match part:
                case "texture":
                    pr.unload_texture(self.assets[name]["texture"])
                case "model":
                    pr.unload_model(self.assets[name]["model"])
                case "font":
                    pr.unload_font(self.assets[name]["font"])
                case "image":
                    pr.unload_image(self.assets[name]["image"])
                case "mesh":
                    pr.unload_mesh(self.assets[name]["mesh"])
                case _:
                    pass

    def remove(self, name: str) -> None:
        if name in self.assets:
            self.assets.pop(name)

    def clear(self) -> None:
        for asset in self.assets.keys():
            self.unload(asset)
        self.assets.clear()
