# Ecoledirect-python-api

> Examples

```python
from ecoledirecte import Session            # Importation du module

session = Session("username", "password")   # Initialisation de la session
```

```python
for n in session.getNotes():      # Récupération et
    print(n)                      # affichage des notes
```

```python
notes = session.getNotes()        # Récupération des notes

print(notes.getBests())           # Affichage des meilleurs notes
print(notes.getWorsts())          # Affichage des pires notes
```

```python
notes = session.getNotes()        # Récupération des notes
n = notes.random()                # Récupération d'une note au hasard

print(n.teachers)                 # Affichage des professeurs ayant mis la note

p = n.period                      # Récupération de la periode de la note

print(p.dateCouncil)              # Affichage de la date du conseil de classe de la periode
print(p.timeCouncil)              # Affichage de l'heure du conseil de classe de la periode

print(p.headTeacher.subject)      # Affichage de la matière du professeur principal
```

```python
for hw in session.getHomeworks(): # Récupération et
    print(hw)                     # Affichage des devoirs
```

```python
cloud = session.getClouds()[0].get()                                              # Récupération du cloud de la classe

fichier = cloud.getFileByPath("Mathématiques/théorème de Pythagore/cours.pdf")    # Récupération du fichier dans le cloud de la classe

fichier.download("cours de maths/théorème de pythagore.pdf")                      # téléchargement du fichier
```

```python
cloud = session.getPersonalCloud()                                                           # Récupération du cloud personnel

fichier = cloud.getFileByPath("Mathématiques/mon devoir sur le théorème de Pythagore.pdf")   # Récupération du fichier dans le cloud de la classe

fichier.download("devoirs de maths/théorème de pythagore.pdf")                               # téléchargement du fichier
```

```python
notes = session.getDocuments()["notes"]  # récupération des documents dans le dossier 'note'

notes[0].download()                      # téléchargement du premier document
```

