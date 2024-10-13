# DiamondFire.py
DiamondFire templating library in Python

## Installation
The package can be found on PYPI at [DiamondFire.py](https://pypi.org/project/DiamondFire.py/). To install, open terminal
and type in:
```shell
python3 -m pip --upgrade DiamondFire.py
```
This will install the package.

## Quick Start
The package can be used under the namespace `df`. Here's an example program that generate code that counts to 10:
```python
import df

index_variable = df.Variable(df.VariableScope.LINE, "index")

template = df.Template([
    df.CodeBlock(df.CodeBlockCategory.PLAYER_EVENT, "Join"),
    df.CodeBlock(df.CodeBlockCategory.REPEAT, "Multiple", [index_variable, 10]),
    df.Bracket(open=True, repeat=True),
        df.CodeBlock(df.CodeBlockCategory.PLAYER_ACTION, "SendMessage", [index_variable]),
    df.Bracket(open=False, repeat=True)
])

print(template.compress())
template.send_to_codeclient()
```

## Features
- Templates
- Code Blocks
- Brackets
- CodeClient API

## Documentation
I'm too lazy to figure out how to generate doc HTML so the docstring is shown by your IDE.