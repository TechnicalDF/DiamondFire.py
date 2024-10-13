from websockets.sync.client import connect
from . import Template
from .enums import Mode, PlotSize
from .exceptions import SendToMinecraftError
from enum import Flag, auto
from amulet_nbt import CompoundTag, from_snbt, ListTag

class CCOutOfScopeError(Exception): pass

class CCAuthScopes(Flag):
    DEFAULT = auto()
    INVENTORY = auto()
    MOVEMENT = auto()
    READ_PLOT = auto()
    WRITE_CODE = auto()
    CLEAR_PLOT = auto()

class CodeClient:
    """
    API to interact with CodeClient.
    """
    def __init__(self, timeout: int = 0.1):
        """
        Opens a connection to communicate with CodeClient.
        :param timeout: The timeout in seconds for waiting on responses.
        """
        self.socket = connect("ws://localhost:31375")
        self.timeout = timeout
        self._scopes = CCAuthScopes.DEFAULT
        self.__method._api = self

    def __del__(self):
        self.socket.close()

    def close(self):
        """
        Closes the internal socket.
        """
        self.socket.close()

    @staticmethod
    def _ts(data: str | bytes) -> str:
        return data if isinstance(data, str) else data.decode()

    def recv(self) -> str:
        return self._ts(self.socket.recv(self.timeout))

    class __method:
        _api: 'CodeClient' = None
        scope: CCAuthScopes = CCAuthScopes.DEFAULT

        def _require_scope(self):
            if CCAuthScopes.DEFAULT in self.scope:
                return
            if not self.scope in self._api._scopes:
                raise CCOutOfScopeError(f"The action require scope {self.scope.name}.")

    class give(__method):
        """
        Requires DEFAULT scope.
        """
        scope = CCAuthScopes.DEFAULT

        def __init__(self, item: str | CompoundTag):
            """
            Sends an item (SNBT) to Minecraft.
            :param item: The Item in SNBT or a Compound NBT Tag.
            :raises SendToMinecraftError: If the player is not in creative mode.
            """
            if isinstance(item, CompoundTag):
                item = item.to_snbt()
            self._api.socket.send("give " + item)
            try:
                message = self._api.recv()
                if message == "not creative mode":
                    raise SendToMinecraftError("The player is not in creative mode.")
            except TimeoutError:
                pass

    class scopes(__method):
        """
        Requires DEFAULT scope.
        """
        scope = CCAuthScopes.DEFAULT

        def __init__(self):
            """
            Gets the list of scopes the program is authorized with.
            """
            self._api.socket.send("scopes")
            message = self._api.recv()
            scopes = message.split()
            new_scopes = CCAuthScopes.DEFAULT
            if "inventory" in scopes:
                new_scopes |= CCAuthScopes.INVENTORY
            if "movement" in scopes:
                new_scopes |= CCAuthScopes.MOVEMENT
            if "read_plot" in scopes:
                new_scopes |= CCAuthScopes.READ_PLOT
            if "write_code" in scopes:
                new_scopes |= CCAuthScopes.WRITE_CODE
            if "clear_plot" in scopes:
                new_scopes |= CCAuthScopes.CLEAR_PLOT

        @classmethod
        def request(cls, requested_scopes: CCAuthScopes, timeout: int = None):
            """
            Requests new scopes for the program.
            :param requested_scopes: The new scopes.
            :param timeout: Timeout for player input in seconds.
            :raises TimeoutError: If the request times out.
            """
            scope_list = []
            if CCAuthScopes.INVENTORY in requested_scopes:
                scope_list.append("inventory")
            if CCAuthScopes.MOVEMENT in requested_scopes:
                scope_list.append("movement")
            if CCAuthScopes.READ_PLOT in requested_scopes:
                scope_list.append("read_plot")
            if CCAuthScopes.WRITE_CODE in requested_scopes:
                scope_list.append("write_code")
            if CCAuthScopes.CLEAR_PLOT in requested_scopes:
                scope_list.append("clear_plot")
            cls._api.socket.send("scopes " + " ".join(scope_list))
            if "auth" in cls._api._ts(cls._api.socket.recv(timeout)):
                cls._api._scopes = requested_scopes

    class inv(__method):
        """
        Requires INVENTORY scope.
        """
        scope = CCAuthScopes.INVENTORY

        @classmethod
        def get(cls) -> list[CompoundTag]:
            """
            Gets the player's inventory.
            :return: List of items in CompoundTag.
            :raises socket.timeout: If the request times out.
            """
            cls()._require_scope()
            cls._api.socket.send("inv")
            items = cls._api.recv()
            parsed: ListTag = from_snbt(items)
            decoded: list[CompoundTag] = []
            for item in parsed:
                decoded.append(item)
            
            return decoded
        
        @classmethod
        def set(cls, items: list[CompoundTag | str]):
            """
            Sets the player's inventory.
            :param items: List of item in SNBT or a Compound NBT Tag.
            :raises SendToMinecraftError: If the player is not in creative mode.
            """
            cls()._require_scope()

            parsed = []
            for item in parsed:
                if isinstance(item, CompoundTag):
                    item = item.to_snbt()
                parsed.append(item)

            cls._api.socket.send("setinv [" + ",".join(parsed) + "]")
            try:
                message = cls._api.recv()
                if message == "not creative mode":
                    raise SendToMinecraftError("The player is not in creative mode.")
            except TimeoutError:
                pass

    class spawn(__method):
        """
        Requires MOVEMENT scope.
        """
        scope = CCAuthScopes.MOVEMENT

        def __init__(self):
            """
            Moves the player to the codespace spawn.
            """
            self._require_scope()
            self._api.socket.send("spawn")

    class mode(__method):
        """
        Requires MOVEMENT scope.
        """
        scope = CCAuthScopes.MOVEMENT

        @classmethod
        def get(cls) -> Mode:
            """
            Gets the player's current mode.
            :return: The player's mode.
            :raises socket.timeout: If the request times out.
            """
            cls()._require_scope()
            cls()._api.socket.send("mode")
            mode = cls._api.recv()
            match mode:
                case "spawn": return Mode.SPAWN
                case "play": return Mode.PLAY
                case "dev": return Mode.DEV
                case "build": return Mode.BUILD

        @classmethod
        def set(cls, mode: Mode):
            """
            Sets the player's current mode. To confirm, use ``mode.get()`` again and compare.
            :param mode: The new mode to set to.
            """
            cls()._require_scope()
            cls()._api.socket.send("mode " + mode.value)

    class plot(__method):
        """
        Requires READ_PLOT scope.
        """
        scope = CCAuthScopes.READ_PLOT

        @classmethod
        def get_templates(cls) -> list[Template]:
            """
            Gets all templates of the plot. It's recommended to set a high timeout value for this.
            :return: The list of templates.
            :raises socket.timeout: If the request times out.
            """
            cls()._require_scope()
            cls()._api.socket.send("scan")
            data = cls._api.recv()
            templates = []
            for template in data.split("\n"):
                templates.append(Template.decompress(template))
            return templates

        @classmethod
        def get_size(cls) -> PlotSize:
            """
            Gets the current plot size.
            :return: The plot size.
            :raises socket.timeout: If the request times out.
            """
            cls()._require_scope()
            cls()._api.socket.send("size")
            size = cls._api.recv()
            return PlotSize(size)

    class place(__method):
        """
        Requires WRITE_CODE scope.
        """
        scope = CCAuthScopes.WRITE_CODE

        def __init__(self, compact: bool = False):
            """
            A builder. To actually place the code, call ``place.execute()``
            """
            self._require_scope()
            self.compact = compact

        def set_compact(self) -> 'place':
            """
            Makes the placer place templates one after another with no space.
            :return: The object for chaining.
            """
            self._require_scope()
            self.compact = True
            self._api.socket.send("place compact")
            return self

        def set_swap(self) -> 'place':
            """
            Makes the placer to swap any preexisting templates, and place any ones which don't exist.
            The most ideal use for this is a final "compilation", or you just don't have space (in which case you shouldn't be using swap).
            :return: The object for chaining.
            """
            self._require_scope()
            self.compact = False
            self._api.socket.send("place swap")
            return self

        def place(self, template: Template) -> 'place':
            """
            Queue a template placement.
            :param template: The template to place.
            :return: The object for chaining.
            """
            self._require_scope()
            self._api.socket.send("place " + template.compress())
            return self

        def execute(self):
            """
            Executes all the template placing.
            """
            self._require_scope()
            self._api.socket.send("place go")

    class clear_plot(__method):
        """
        Requires CLEAR_PLOT scope.
        """
        scope = CCAuthScopes.CLEAR_PLOT

        def __init__(self):
            """
            Clears the codespace. **USE WITH CAUTION** as this will remove all code.
            """
            self._require_scope()
            self._api.socket.send("clear")

    def __repr__(self):
        return f"CodeClient({self.timeout})"
