from .exceptions import MalformedItemJSONError
from .enums import VariableScope, Selection, DataType, get_from_value

class Item:
    """
    Base Item class. You shouldn't use this.
    """
    def __init__(self, id: str, slot: int = -1):
        self.id = id
        self.slot = slot

    def _getdata(self) -> dict:
        pass

    def to_json(self, index: int = 0) -> dict:
        """
        Serialize the Item into JSON.
        :return: The serialized JSON.
        """
        return {
            "item": {
                "id": self.id,
                "data": self._getdata()
            },
            "slot": index if self.slot == -1 else self.slot
        }

    @classmethod
    def from_json(cls, json: dict) -> 'Item':
        """
        Deserializes a JSON back into an Item.
        :param json: The JSON object.
        :return: The Item object.
        """
        if "slot" not in json:
            raise MalformedItemJSONError("No 'slot' key present.")
        if "item" not in json:
            raise MalformedItemJSONError("No 'item' key present.")

        if not isinstance(json["slot"], int):
            raise MalformedItemJSONError("Unexpected value for 'slot'.")
        if not isinstance(json["item"], dict):
            raise MalformedItemJSONError("Unexpected value for 'item'.")

        if "id" not in json["item"]:
            raise MalformedItemJSONError("No 'item.id' key present.")
        if "data" not in json["item"]:
            raise MalformedItemJSONError("No 'item.data' key present.")

        class_lookup = {
            "txt": String,
            "comp": Text,
            "num": Number,
            "var": Variable,
            "g_val": GameValue,
            "loc": Location,
            "vec": Vector,
            "snd": Sound,
            "part": Particle,
            "pot": Potion,
            "pn_el": Parameter, # AKA Pattern Element
            "bl_tag": BlockTag
        }
        if json["item"]["id"] in class_lookup:
            return class_lookup[json["item"]["id"]].from_json(json["item"]["data"], json["slot"])
        raise MalformedItemJSONError("Unexpected value for 'item.id'.")

class String(Item):
    """
    A String value.
    """
    def __init__(self, value: str, slot: int = -1):
        super().__init__("txt", slot)
        self.value = value

    def _getdata(self) -> dict:
        return {"name": self.value}

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'String':
        return cls(json["name"], slot)

class Text(Item):
    """
    A Styled Text value.
    """
    def __init__(self, value: str, slot: int = -1):
        super().__init__("comp", slot)
        self.value = value

    def _getdata(self) -> dict:
        return {"name": self.value}

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'Text':
        return cls(json["name"], slot)

class Number(Item):
    """
    A Number value.
    """
    def __init__(self, value: str | float | int, slot: int = -1):
        super().__init__("num", slot)
        self.value = value

    def _getdata(self) -> dict:
        return {"name": self.value}

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'Number':
        return cls(json["name"], slot)

class Location(Item):
    """
    A Location value.
    """
    def __init__(self, x: float, y: float, z: float, pitch: float = 0, yaw: float = 0, slot: int = -1):
        super().__init__("loc", slot)
        self.x = x
        self.y = y
        self.z = z
        self.pitch = pitch
        self.yaw = yaw

    def _getdata(self) -> dict:
        return {
            "isBlock": False,
            "loc": {
                "x": self.x,
                "y": self.y,
                "z": self.z,
                "pitch": self.pitch,
                "yaw": self.yaw
            }
        }

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'Location':
        return cls(json["loc"]["x"], json["loc"]["y"], json["loc"]["z"], json["loc"]["pitch"], json["loc"]["yaw"], slot)

class Vector(Item):
    """
    A Vector value.
    """
    def __init__(self, x: float, y: float, z: float, slot: int = -1):
        super().__init__("vec", slot)
        self.x = x
        self.y = y
        self.z = z

    def _getdata(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'Vector':
        return cls(json["x"], json["y"], json["z"], slot)

class Sound(Item):
    """
    A Sound value. It may be a custom resourcepack sound.
    """
    def __init__(self, sound: str, pitch: float = 1, volume: float = 2, custom_sound: bool = False, slot: int = -1):
        super().__init__("snd", slot)
        self.sound = sound
        self.pitch = pitch
        self.volume = volume
        self.custom = custom_sound

    def _getdata(self) -> dict:
        if self.custom:
            return {
                "pitch": self.pitch,
                "vol": self.volume,
                "key": self.sound
            }
        else:
            return {
                "pitch": self.pitch,
                "vol": self.volume,
                "sound": self.sound
            }

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'Sound':
        if "key" in json:
            return cls(json["key"], json["pitch"], json["volume"], True, slot)
        else:
            return cls(json["sound"], json["pitch"], json["volume"], slot=slot)


class ParticleData:
    """
    Data relating to particles.
    """
    def __init__(self, *,
                 color: int = 0xFF0000, color_variation: float = 0, fade_color: int = 0x000000,
                 size: float = 1, size_variation: float = 0,
                 motion: tuple[float, float, float], motion_variation: float = 0,
                 material: str = "air", roll: float = 0
                 ):
        self.color = color
        self.color_variation = color_variation
        self.fade_color = fade_color
        self.size = size
        self.size_variation = size_variation
        self.motion = motion
        self.motion_variation = motion_variation
        self.material = material
        self.roll = roll

    def to_json(self) -> dict:
        return {
            "rgb": self.color,
            "colorVariation": self.color_variation,
            "rgb_fade": self.fade_color,
            "size": self.size,
            "sizeVariation": self.size_variation,
            "x": self.motion[0],
            "y": self.motion[1],
            "z": self.motion[2],
            "motionVariation": self.motion_variation,
            "material": self.material.upper(),
            "roll": self.roll
        }

    @classmethod
    def from_json(cls, json: dict) -> 'ParticleData':
        return cls(
            color=json["rgb"], color_variation=json["colorVariation"], fade_color=json["rgb_fade"],
            size=json["size"], size_variation=json["sizeVariation"],
            motion=(json["x"], json["y"], json["z"]), motion_variation=json["motionVariation"],
            material=json["material"].lower(), roll=json["roll"]
        )

class Particle(Item):
    """
    A Particle value. This is by far the most complex value type. Use ``ParticleData`` also for more complex particle creation.
    """
    def __init__(self, particle: str, spread: tuple[float, float], amount: int, data: ParticleData, slot: int = -1):
        super().__init__("part", slot)
        self.particle = particle
        self.amount = amount
        self.spread = spread
        self.data = data

    def _getdata(self) -> dict:
        return {
            "particle": self.particle,
            "cluster": {
                "amount": self.amount,
                "horizontal": self.spread[0],
                "vertical": self.spread[1]
            },
            "data": self.data.to_json()
        }

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'Particle':
        return Particle(json["particle"], (float(json["cluster"]["horizontal"]), float(json["cluster"]["vertical"])), json["cluster"]["amount"], ParticleData.from_json(json["data"]), slot)

class Potion(Item):
    """
    A Potion value.
    """
    def __init__(self, effect: str, duration: int = -1, amplifier: int = 1, slot: int = -1):
        super().__init__("pot", slot)
        self.effect = effect
        self.duration = duration
        self.amplifier = amplifier

    def _getdata(self) -> dict:
        return {"pot": self.effect, "dur": 1000000 if self.duration == -1 else self.duration, "amp": self.amplifier - 1}

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'Potion':
        return cls(json["pot"], -1 if json["dur"] == 1000000 else json["dur"], json["amp"] + 1, slot)

class Variable(Item):
    """
    A Variable value.
    """
    def __init__(self, name: str, scope: VariableScope = VariableScope.GAME, slot: int = -1):
        super().__init__("var", slot)
        self.name = name
        self.scope = scope

    def _getdata(self) -> dict:
        return {"name": self.name, "scope": self.scope.value}

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'Variable':
        return cls(json["name"], get_from_value(VariableScope, json["scope"]), slot)

class GameValue(Item):
    """
    A Game Value item.
    """
    def __init__(self, type: str, selection: Selection = Selection.DEFAULT, slot: int = -1):
        super().__init__("g_val", slot)
        self.type = type
        self.selection = selection

    def _getdata(self) -> dict:
        return {"type": self.type, "target": self.selection.value}

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'GameValue':
        return cls(json["type"], get_from_value(Selection, json["target"]), slot)

class Parameter(Item):
    """
    A Pattern Element (AKA Parameter) value. This is the 2nd most complex value.
    """
    def __init__(self, name: str, type: DataType, plural: bool = False, default: Item = None, description: str = None, note: str = None, slot: int = -1):
        super().__init__("pn_el", slot)
        self.name = name
        self.type = type
        self.plural = plural
        self.default = default
        self.description = description
        self.note = note

    def _getdata(self) -> dict:
        data = {
            "name": self.name,
            "type": self.type.value,
            "plural": self.plural,
            "optional": self.default is None
        }
        if self.default is not None:
            data["default_value"] = self.default.to_json(-1)["item"]
        if self.description:
            data["description"] = self.description
        if self.note:
            data["note"] = self.note

        return data

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'Parameter':
        return cls(json["name"], get_from_value(DataType, json["type"]), json["plural"], None if not json["optional"] else Item.from_json({"item": json["default_value"], "slot": -1}), json.get("description"), json.get("note"), slot)

class BlockTag(Item):
    def __init__(self, tag: str, option: str, slot: int = -1):
        super().__init__("bl_tag", slot)
        self.tag = tag
        self.option = option

    def _getdata(self) -> dict:
        return {"option": self.option, "tag": self.tag}

    @classmethod
    def from_json(cls, json: dict, slot: int = -1) -> 'BlockTag':
        return cls(json["tag"], json["option"], slot)
