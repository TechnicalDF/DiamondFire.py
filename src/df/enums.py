from enum import Enum, EnumType

def get_from_value(enum: EnumType, value):
    for member in enum:
        if member.value == value:
            return member

class CodeBlockCategory(Enum):
    PLAYER_ACTION = "player_action"
    IF_PLAYER = "if_player"
    START_PROCESS = "start_process"
    CALL_FUNCTION = "call_func"
    CONTROL = "control"
    SET_VARIABLE = "set_var"
    ENTITY_EVENT = "entity_event"
    PLAYER_EVENT = "event"
    FUNCTION = "func"
    IF_ENTITY = "if_entity"
    ENTITY_ACTION = "entity_action"
    IF_VARIABLE = "if_var"
    SELECT_OBJECT = "select_obj"
    GAME_ACTION = "game_action"
    ELSE = "else"
    PROCESS = "process"
    REPEAT = "repeat"
    IF_GAME = "if_game"

class Selection(Enum):
    SELECTION = "Selection"
    DEFAULT = "Default"
    KILLER = "Killer"
    DAMAGER = "Damager"
    VICTIM = "Victim"
    SHOOTER = "Shooter"
    PROJECTILE = "Projectile"
    LAST_ENTITY = "LastEntity"
    ALL_PLAYERS = "AllPlayers"
    ALL_ENTITIES = "AllEntities"
    ALL_MOBS = "AllMobs"
    AUTO = ""

class VariableScope(Enum):
    GAME = "unsaved"
    SAVED = "saved"
    LOCAL = "local"
    LINE = "line"

class DataType(Enum):
    STRING = "txt"
    TEXT = "comp"
    NUMBER = "num"
    LOCATION = "loc"
    VECTOR = "vec"
    SOUND = "snd"
    PARTICLE = "part"
    POTION = "pot"
    ITEM = "item"

    ANY = "any"
    VARIABLE = "var"
    LIST = "list"
    DICTIONARY = "dict"

class Mode(Enum):
    SPAWN = "spawn"
    PLAY = "play"
    DEV = "dev"
    BUILD = "build"

class PlotSize(Enum):
    BASIC = "basic"
    LARGE = "large"
    MASSIVE = "massive"
    MEGA = "mega"
