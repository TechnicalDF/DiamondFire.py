from src.df import *

client = codeclient.CodeClient()
client.give("{Count:1b,id:\"minecraft:netherite_sword\"}")
print(client.scopes())
client.scopes.request(codeclient.CCAuthScopes.MOVEMENT)
client.mode.set(Mode.BUILD)
client.scopes.request(codeclient.CCAuthScopes.INVENTORY)
print(client.inv.get())
client.close()
