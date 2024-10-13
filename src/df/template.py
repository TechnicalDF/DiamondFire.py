import json
import base64
import gzip

from .code import Block, CodeBlock, CodeBlockCategory
from .exceptions import MalformedTemplateJSONError, MalformedCodeBlockJSONError, SendToMinecraftError
from amulet_nbt import CompoundTag, ByteTag, StringTag

class Template:
    """
    Marks a DiamondFire Template.
    """
    def __init__(self, codeblocks: list[Block], name: str = None):
        """
        Creates a new Template object.
        :param codeblocks: The list of Blocks the Template contains.
        :param name: The name of the Template. This is used for item sending.
        """
        self.codeblocks = codeblocks
        self.name = name

    def __add__(self, code: Block | list[Block]) -> 'Template':
        """
        Returns a new Template with the code appended to it.
        :param code: The new block(s) to add.
        :return: The changed Template.
        """
        if isinstance(code, Block):
            code = [code]

        return Template(self.codeblocks + [*code])

    def __iadd__(self, code: Block | list[Block]):
        """
        Adds the code to the end of the blocks.
        :param code: The new block(s) to add.
        """
        if isinstance(code, Block):
            code = [code]

        self.codeblocks.extend(code)

    def to_json(self) -> dict:
        """
        Serializes the Template into a JSON object.
        :return: The serialized JSON.
        """
        blocks = []
        for block in self.codeblocks:
            blocks.append(block.to_json())

        return {"blocks": blocks}

    def compress(self) -> str:
        """
        Compresses the template into a single Base64 GZIP string.
        :return: The compressed string.
        :raises OverflowError: If the output is way too long.
        """
        compressed = base64.b64encode(gzip.compress(json.dumps(self.to_json()).encode())).decode()
        if len(compressed) > 65535:
            raise OverflowError(f"Compressed data too large: {len(compressed)} / 65535")

        return compressed

    @classmethod
    def from_json(cls, json: dict) -> 'Template':
        """
        Reconstructs the Template from the JSON.
        :param json: The JSON as a dictionary.
        :return: The Template object.
        :raises MalformedTemplateJSONError: If the template JSON is malformed or does not contain the expected data.
        """
        if "blocks" not in json:
            raise MalformedTemplateJSONError("No 'blocks' key present.")

        blocks = []
        for block in json["blocks"]:
            if not isinstance(block, dict):
                raise MalformedCodeBlockJSONError("CodeBlock is not a dict.")
            blocks.append(Block.from_json(block))

        return cls(blocks)

    @classmethod
    def decompress(cls, data: str | bytes) -> 'Template':
        """
        Decompresses the template data back into a template.
        :param data: The compressed data.
        :return: The decompressed template object.
        """
        if isinstance(data, str):
            data = data.encode()

        decompressed = json.loads(gzip.decompress(base64.b64decode(data)).decode())
        return cls.from_json(decompressed)

    def __get_name(self) -> str:
        if self.name: return self.name
        if len(self.codeblocks) == 0: return "§bEmpty Template"

        head = self.codeblocks[0]
        if isinstance(head, CodeBlock):
            prefix = "§bCode Template §3"
            action = "§b" + head.action
            if head.category == CodeBlockCategory.PLAYER_EVENT:
                prefix = "§e§lPlayer Event §6"
                action = "§e" + head.action
            elif head.category == CodeBlockCategory.ENTITY_EVENT:
                prefix = "§e§lEntity Event §6"
                action = "§e" + head.action
            elif head.category == CodeBlockCategory.FUNCTION:
                prefix = "§b§lFunction §5"
                action = "§b" + head.extras["data"]
            elif head.category == CodeBlockCategory.PROCESS:
                prefix = "§b§lProcess §5"
                action = "§b" + head.extras["data"]
            return prefix + "» " + action
        else:
            return "§bCode Template"

    @staticmethod
    def __make_safe(string: str) -> str:
        return string.translate(str.maketrans({
            '"': '\\"',
            "'": "\\'",
            "\\": "\\\\",
            "\n": "\\n",
            "\r": "\\r",
            "\t": "\\t",
            "\b": "\\b",
            "\f": "\\f"
        }))

    def __get_as_item(self, author: str) -> str:
        return CompoundTag({
            "Count": ByteTag(1),
            "id": StringTag("ender_chest"),
            "tag": CompoundTag({
                "display": CompoundTag({
                    "Name": StringTag(json.dumps({"italic": False, "text": self.__get_name()}))
                }),
                "PublicBukkitValues": CompoundTag({
                    "hypercube:codetemplatedata": StringTag(json.dumps({
                        "version": 1,
                        "author": author,
                        "name": self.__get_name(),
                        "code": self.compress()
                    }))
                })
            })
        }).to_snbt()

    def send_to_recode(self, source: str = "DiamondFire.py", author: str = "DiamondFire.py"):
        """
        Sends the Template to Minecraft via (Deprecated) Recode.
        :param source: The name of the program. This is displayed in the toast.
        :param author: The author of the Template.
        :raises SendToMinecraftError: If the sending failed for some reason.
        """
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(("localhost", 31372))

            data = json.dumps({
                "type": "nbt",
                "data": self.__get_as_item(author),
                "source": source
            })
            sock.send((data + "\n").encode())

            receive = sock.recv(1024)
            status = json.loads(receive.decode())
            if status["status"] == "error":
                raise SendToMinecraftError(status["error"])

        finally:
            sock.close()

    def send_to_codeclient(self, author: str = "DiamondFire.py", timeout: int = 0.1):
        """
        Sends the Template to Minecraft via CodeClient.
        :param author: The author of the Template.
        :param timeout: The timeout in seconds for waiting on responses.
        :raises SendToMinecraftError: If the player is not in creative mode.
        """
        from websockets.sync.client import connect
        socket = connect("ws://localhost:31375")

        # copied from codeclient.py due to circular import
        socket.send("give " + self.__get_as_item(author))
        try:
            message = socket.recv(timeout)
            message = message if isinstance(message, str) else message.decode()
            if message == "not creative mode":
                raise SendToMinecraftError("The player is not in creative mode.")
        except TimeoutError:
            pass
        finally:
            socket.close()
