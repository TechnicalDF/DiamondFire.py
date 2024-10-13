from src.df import *

template = Template([
    CodeBlock(CodeBlockCategory.PLAYER_EVENT, "Join"),
    CodeBlock(CodeBlockCategory.PLAYER_ACTION, "SendMessage", [Text("<gray>$> connection<white>.<gray>accept<white>(<green>\"%default\"<white>)")], selection=Selection.ALL_PLAYERS),
    CodeBlock(CodeBlockCategory.PLAYER_ACTION, "GivePotion", [Potion("Saturation", amplifier=10), BlockTag("Show Icon", "False"), BlockTag("Overwrite Effect", "True"), BlockTag("Effect Particles", "None")])
])

template.send_to_recode()
