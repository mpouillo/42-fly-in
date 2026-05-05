import pyray as pr
from collections import defaultdict


class Assets:
    def __init__(self):
        self.assets = defaultdict(dict)

    def __str__(self):
        return (
            "Assets:\n"
            + ",\n".join(
                [f"- {name} ({", ".join(part)})"
                 for name, part in self.assets.items()]
            )
        )

    def add(self, name, obj_type, obj):
        if self.assets[name] and obj_type in self.assets[name]:
            raise ValueError("Asset type already exists for name")

        self.assets[name][obj_type] = obj

    def get(self, name, obj_type):
        if name not in self.assets:
            raise ValueError("Asset does not exist")

        return self.assets[name].get(obj_type, None)

    def unload(self, name):
        obj = self.assets.get(name)
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

    def remove(self, name):
        if name in self.assets:
            self.assets.pop(name)

    def clear(self):
        for asset in self.assets.keys():
            self.unload(asset)
        self.assets.clear()
