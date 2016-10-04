from comfy import Conf
from comfy.fields import Field, ListField, DictField, ListUpdate
from yaml import load as yaml_load

class EntryConf(Conf):
    name = Field(str)
    value = Field(int)

class TestConf(Conf):
    entries = ListField(EntryConf, update=ListUpdate.append)
    banana = Field(str)

c1 = '''entries:
    - {name: banana, value: 5}
    - {name: orange, value: 4}
banana: orange
'''

c2 = '''banana: cherry
entries:
    - {name: poop, value: 8}'''

root = TestConf(yaml_load(c1))
root.sanitize()
print(root)

update = TestConf(yaml_load(c2))
print(update)

root.update(update)
print(root)
