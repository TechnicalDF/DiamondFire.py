from .enums import CodeBlockCategory, Selection, get_from_value
from .exceptions import MalformedCodeBlockJSONError
from .values import ItemValue, BlockTag, Number, String

class Block:
    """
    Represents a Block in a Template. You should not use this.
    """
    def to_json(self) -> dict:
        pass

    @classmethod
    def from_json(cls, json: dict) -> 'Block':
        if json.get("id") == "block":
            return CodeBlock.from_json(json)
        elif json.get("id") == "bracket":
            return Bracket.from_json(json)
        else:
            if "id" in json:
                raise MalformedCodeBlockJSONError("Unexpected value for 'id'.")
            else:
                raise MalformedCodeBlockJSONError("No 'id' key present.")

class Bracket(Block):
    """
    A bracket Block.
    """
    def __init__(self, open: bool, repeat: bool = False):
        self.open = open
        self.repeat = repeat

    def to_json(self) -> dict:
        """
        Serializes the Bracket into JSON.
        :return: The serialized JSON.
        """
        return {
            "id": "bracket",
            "direct": "open" if self.open else "close",
            "type": "repeat" if self.repeat else "norm"
        }

    @classmethod
    def from_json(cls, json: dict) -> 'Bracket':
        """
        Deserializes a Block from JSON.
        :param json: The serialized JSON.
        :return: The Bracket object.
        """
        if "direct" not in json:
            raise MalformedCodeBlockJSONError("No 'direct' key present.")
        if "type" not in json:
            raise MalformedCodeBlockJSONError("No 'type' key present.")

        if json["direct"] not in ("open", "close"):
            raise MalformedCodeBlockJSONError("Unexpected value for 'direct'.")
        if json["type"] not in ("norm", "repeat"):
            raise MalformedCodeBlockJSONError("Unexpected value for 'type'.")

        return Bracket(json["direct"] == "open", json["type"] == "repeat")

    def __repr__(self):
        return f"Bracket({self.open}, {self.repeat})"

class CodeBlock(Block):
    """
    Represents a Code Block.
    """
    def __init__(self, category: CodeBlockCategory, action: str = "", args: list[ItemValue] = None, selection: Selection = Selection.AUTO, **kwargs):
        """
        Initialize and creates a Code Block.

        Extra kwargs:

        ``attribute`` - Only for If's. Can only be set to `"NOT"`.

        ``subAction`` - Only for While and Select by Condition. Prefixed with the IfVar type then the IfVar action.

        ``data`` - Only for Function, Process, Call Function, and Start Process. The Func/Proc name lives here.

        :param category: The category the block is in.
        :param action: The action of the block.
        :param args: List of arguments in the chest.
        :param selection: The targets the code block targets.
        :param kwargs: Extra data. See `Extra kwargs`.
        """
        self.category = category
        self.action = action
        self.selection = selection
        self.args = args if args else []
        self.extras = kwargs

    def __parse_values(self):
        for index, value in enumerate(self.args.copy()):
            if isinstance(value, (int, float)):
                self.args[index] = Number(value)
            elif isinstance(value, str):
                self.args[index] = String(value)

    def to_json(self) -> dict:
        """
        Serializes the Code Block into JSON.
        :return: The serialized JSON.
        """
        self.__parse_values()
        args_list = []
        tags = 0
        for index, item in enumerate(self.args):
            convert = item.to_json(index)
            if isinstance(item, BlockTag):
                index = 26 - tags
                convert = item.to_json(index)
                tags += 1
                convert["item"]["data"]["action"] = self.action if self.action else "dynamic"
                convert["item"]["data"]["block"] = self.category.value

            args_list.append(convert)

        data = {
            "id": "block",
            "block": self.category.value,
            "action": self.action,
            "args": {"items": args_list}
        }

        if self.selection != Selection.AUTO:
            data["target"] = self.selection.value

        for k, v in self.extras.items():
            data[k] = v

        return data

    @classmethod
    def from_json(cls, json: dict) -> 'CodeBlock':
        """
        Deserializes a Code Block from JSON.
        :param json: The serialized JSON.
        :return: The deserialized Code Block.
        :raises MalformedCodeBlockJSONError:
        """
        if "block" not in json:
            raise MalformedCodeBlockJSONError("No 'block' key present.")
        if json["block"] in ("func", "start_process", "process", "func"):
            if "data" not in json:
                raise MalformedCodeBlockJSONError("No 'data' key present.")
        else:
            if json["block"] != "else" and "action" not in json:
                raise MalformedCodeBlockJSONError("No 'action' key present.")

        block = get_from_value(CodeBlockCategory, json["block"])
        action = json.get("action", "")
        target = get_from_value(Selection, json.get("target", ""))
        args = [ItemValue.from_json(item) for item in json.get("args", {"items": []})["items"]]
        code = cls(block, action, args, target)
        for k, v in json:
            if k not in ("block", "action", "target", "args"):
                code.extras[k] = v

        return code

    def __repr__(self):
        return f"CodeBlock({self.category.name}, \"{self.action}\", {self.args!r})"
