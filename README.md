# Ecoledirect-python-api

> Examples

```python
from ecoledirecte import Session # Importation du module

session = Session("username", "password") # Initialisation de la session
```

```python
for n in session.getNotes(): # Récupération et
    print(n)                 # affichage des notes
```

```python
for hw in session.getHomeworks(): # Récupération et
    print(hw)                     # Affichage des devoirs
```
