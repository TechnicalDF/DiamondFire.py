from src.df import *

index_var = Variable("index", VariableScope.LINE)

template = Template([
    CodeBlock(CodeBlockCategory.PLAYER_EVENT, "SwapHands"),
    CodeBlock(CodeBlockCategory.REPEAT, "Multiple", [index_var, 10]),
    Bracket(True, True),
        CodeBlock(CodeBlockCategory.SET_VARIABLE, "Exponent", [Variable("square", VariableScope.LINE), index_var, 2]),
        CodeBlock(CodeBlockCategory.PLAYER_ACTION, "SendMessage", [Text("The square of <red>%var(index)</red> is <red>%var(square)</red>.")]),
    Bracket(False, True)
])

template.send_to_codeclient("Author")
