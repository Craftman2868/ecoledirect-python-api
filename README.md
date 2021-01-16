# Ecoledirect-python-api

> Examples

```python
from ecoledirecte import Session

session = Session("username", "password")

for n in session.getNotes():
    print(n)
```

```python
from ecoledirecte import Session

session = Session("username", "password")

for hw in session.getHomeworks():
    print(hw)
```
