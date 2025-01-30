from websockets.sync.client import connect
from . import Template
from .enums import Mode, PlotSize
from .exceptions import SendToMinecraftError
from enum import Flag, auto
from amulet_nbt import CompoundTag, from_snbt, ListTag

class CCOutOfScopeError(Exception): pass
class CCInvalidToken(Exception): pass

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

    Each method have a ``.scope`` attribute. You can use this to check for the scope the method requires.
    Example::

        codeclient = CodeClient()
        can_get_inv = codeclient.inv.scope
        if codeclient.have_scope(can_get_inv):
            codeclient.inv.set([])

        codeclient.close()

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

        self.scopes = self.__scopes()
        self.give = self.__give()
        self.token = self.__token()
        self.inv = self.__inv()
        self.spawn = self.__spawn()
        self.mode = self.__mode()
        self.plot = self.__plot()
        self.place = self.__place()
        self.clear_plot = self.__clear_plot()

    def have_scope(self, scope: CCAuthScopes) -> bool:
        """
        Checks if the current session have the scope.
        :param scope: The scope to check for.
        :return: Whether the scope is authorized or not.
        """
        return scope in self._scopes

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

    def _recv(self) -> str:
        return self._ts(self.socket.recv(self.timeout))

    class __method:
        _api: 'CodeClient' = None
        scope: CCAuthScopes = CCAuthScopes.DEFAULT

        def _require_scope(self):
            if CCAuthScopes.DEFAULT in self.scope:
                return
            if not self.scope in self._api._scopes:
                raise CCOutOfScopeError(f"The action require scope {self.scope.name}.")

    class __give(__method):
        """
        Requires DEFAULT scope.
        """
        scope = CCAuthScopes.DEFAULT

        def __call__(self, item: str | CompoundTag):
            """
            Sends an item (SNBT) to Minecraft.
            :param item: The ItemValue in SNBT or a Compound NBT Tag.
            :raises SendToMinecraftError: If the player is not in creative mode.
            """
            if isinstance(item, CompoundTag):
                item = item.to_snbt()
            self._api.socket.send("give " + item)
            try:
                message = self._api._recv()
                if message == "not creative mode":
                    raise SendToMinecraftError("The player is not in creative mode.")
            except TimeoutError:
                pass

    class __token(__method):
        """
        Requires DEFAULT scope.
        """
        scope = CCAuthScopes.DEFAULT

        def get(self) -> str:
            """
            Gets a token that is authenticated with the currently approved scopes.
            :return: The token that can be used to authenticate with.
            """
            self._api.socket.send("token")
            token = self._api._recv()
            return token

        def authenticate(self, token: str):
            """
            Authenticates using the token.
            :param token: The token attached to the scopes.
            :raises CCInvalidToken: If the token is invalid.
            """
            self._api.socket.send("token " + token)
            message = self._api._recv()
            if message == "invalid token":
                raise CCInvalidToken()
            elif message == "auth":
                self._api.scopes()

    class __scopes(__method):
        """
        Requires DEFAULT scope.
        """
        scope = CCAuthScopes.DEFAULT

        def __call__(self) -> CCAuthScopes:
            """
            Gets the list of scopes the program is authorized with.
            :return: The list of scopes
            """
            self._api.socket.send("scopes")
            message = self._api._recv()
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

            self._api._scopes = new_scopes
            return new_scopes

        def request(self, requested_scopes: CCAuthScopes, timeout: int = None):
            """
            Requests new scopes for the program and continues when the player runs /auth.
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
            self._api.socket.send("scopes " + " ".join(scope_list))
            if "auth" in self._api._ts(self._api.socket.recv(timeout)):
                self._api._scopes = requested_scopes

    class __inv(__method):
        """
        Requires INVENTORY scope.
        """
        scope = CCAuthScopes.INVENTORY

        def get(self) -> list[CompoundTag]:
            """
            Gets the player's inventory.
            :return: List of items in CompoundTag.
            :raises socket.timeout: If the request times out.
            """
            self._require_scope()
            self._api.socket.send("inv")
            items = self._api._recv()
            parsed: ListTag = from_snbt(items)
            decoded: list[CompoundTag] = []
            for item in parsed:
                decoded.append(item)
            
            return decoded
        
        def set(self, items: list[CompoundTag | str]):
            """
            Sets the player's inventory.
            :param items: List of item in SNBT or a Compound NBT Tag.
            :raises SendToMinecraftError: If the player is not in creative mode.
            """
            self._require_scope()

            parsed = []
            for item in items:
                if isinstance(item, CompoundTag):
                    item = item.to_snbt()
                parsed.append(item)

            self._api.socket.send("setinv [" + ",".join(parsed) + "]")
            try:
                message = self._api._recv()
                if message == "not creative mode":
                    raise SendToMinecraftError("The player is not in creative mode.")
            except TimeoutError:
                pass

    class __spawn(__method):
        """
        Requires MOVEMENT scope.
        """
        scope = CCAuthScopes.MOVEMENT

        def __call__(self):
            """
            Moves the player to the codespace spawn.
            """
            self._require_scope()
            self._api.socket.send("spawn")

    class __mode(__method):
        """
        Requires MOVEMENT scope.
        """
        scope = CCAuthScopes.MOVEMENT

        def get(self) -> Mode:
            """
            Gets the player's current mode.
            :return: The player's mode.
            :raises socket.timeout: If the request times out.
            """
            self._require_scope()
            self._api.socket.send("mode")
            mode = self._api._recv()
            match mode:
                case "spawn": return Mode.SPAWN
                case "play": return Mode.PLAY
                case "dev": return Mode.DEV
                case "build": return Mode.BUILD


        def set(self, mode: Mode):
            """
            Sets the player's current mode. To confirm, use ``mode.get()`` again and compare.
            :param mode: The new mode to set to.
            """
            self._require_scope()
            self._api.socket.send("mode " + mode.value)

    class __plot(__method):
        """
        Requires READ_PLOT scope.
        """
        scope = CCAuthScopes.READ_PLOT


        def get_templates(self) -> list[Template]:
            """
            Gets all templates of the plot. It's recommended to set a high timeout value for this.
            :return: The list of templates.
            :raises socket.timeout: If the request times out.
            """
            self._require_scope()
            self._api.socket.send("scan")
            data = self._api._recv()
            templates = []
            for template in data.split("\n"):
                templates.append(Template.decompress(template))
            return templates


        def get_size(self) -> PlotSize:
            """
            Gets the current plot size.
            :return: The plot size.
            :raises socket.timeout: If the request times out.
            """
            self._require_scope()
            self._api.socket.send("size")
            size = self._api._recv()
            return PlotSize(size)

    class __place(__method):
        """
        Requires WRITE_CODE scope.
        """
        scope = CCAuthScopes.WRITE_CODE

        def __init__(self):
            self.compact = False

        def __call__(self, compact: bool = False):
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

    class __clear_plot(__method):
        """
        Requires CLEAR_PLOT scope.
        """
        scope = CCAuthScopes.CLEAR_PLOT

        def __call__(self):
            """
            Clears the codespace. **USE WITH CAUTION** as this will remove all code.
            """
            self._require_scope()
            self._api.socket.send("clear")

    def __repr__(self):
        return f"CodeClient({self.timeout})"
