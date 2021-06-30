from random import choice
from typing import List

from requests import post
from json import loads


def _toFloat(data: str):
    return float(data.replace(",", ".")) if data else None


class Teacher:
    def __init__(self, name, subject=None, isHeadTeacher=False):
        if name.startswith("Mme"):
            self.sex = 0
            self.name = name[4:-3]
        elif name.startswith("M."):
            self.sex = 1
            self.name = name[3:-3]

        self.surname = name[-2:]
        self.isHeadTeacher = isHeadTeacher
        self.subject = subject

    @property
    def fullname(self):
        return f"{'M.' if self.sex else 'Mme'} {self.name} {self.surname}"

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} {'[head teacher] ' if self.isHeadTeacher else ''}{self.fullname}>"


class Homework:
    def __init__(self, date, data):
        self.date = date
        self.subject = data["matiere"]
        self.done = data["effectue"]
        self.giveThe = data["donneLe"]

    def __repr__(self):
        return "Pour le " + self.date + ", matière : " + self.subject + (" (Finit)" if self.done else "")


class NoteList:
    def __init__(self, data: list):
        self.data: List[Note] = data

    def getBests(self):
        best = 0
        for n in self.data:
            if n.note is None:
                continue
            if n.note > best:
                best = n.note

        bests = []
        for n in self.data:
            if n.note is None:
                continue
            if n.note >= best:
                bests.append(n)

        return bests

    def getWorsts(self):
        worst = 21
        for n in self.data:
            if n.note is None:
                continue
            if n.note < worst:
                worst = n.note

        worsts = []
        for n in self.data:
            if n.note is None:
                continue
            if n.note <= worst:
                worsts.append(n)

        return worsts

    def random(self):
        return choice(self.data)

    def all(self):
        return self.data

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} {self.data!r}>"


class Note:
    def __init__(self, data, period):
        self.note = _toFloat(data["moyenne"])
        self.moyenneClass = _toFloat(data["moyenneClasse"])
        self.moyenneClassMin = _toFloat(data["moyenneMin"])
        self.moyenneClassMax = _toFloat(data["moyenneMax"])
        self.coef = data["coef"]
        self.subject = data["discipline"]
        self.period = period
        self.teachers = []
        for t in data["professeurs"]:
            t = t["nom"]
            if t == self.period.headTeacher.fullname:
                if not self.period.headTeacher.subject:
                    self.period.headTeacher.subject = self.subject
                self.teachers.append(Teacher(t, self.subject, True))
            else:
                self.teachers.append(Teacher(t, self.subject))

    def __repr__(self):
        return f"<Note: {self.note}; Moyenne de la classe: {self.moyenneClass}; coef: {self.coef}; matière: {self.subject}; profs: " + ", ".join(
            repr(t) for t in self.teachers)+">"


class Period:
    def __init__(self, data):
        self.name = data["periode"]
        self.start = data["dateDebut"]
        self.stop = data["dateFin"]
        self.moyenne = _toFloat(data["ensembleMatieres"]["moyenneGenerale"])
        self.moyenneClass = _toFloat(data["ensembleMatieres"]["moyenneClasse"])
        self.moyenneClassMin = _toFloat(data["ensembleMatieres"]["moyenneMin"])
        self.moyenneClassMax = _toFloat(data["ensembleMatieres"]["moyenneMax"])
        self.headTeacher = Teacher(data["ensembleMatieres"]["nomPP"], isHeadTeacher=True)
        self.appreciationHeadTeacher = data["ensembleMatieres"]["appreciationPP"]
        self.data = data["ensembleMatieres"]["disciplines"]
        self.dateCouncil = data.get("dateConseil")
        self.timeCouncil = data.get("heureConseil")

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} {self.name}>"


class Session:
    def __init__(self, username, password):
        r = post('https://api.ecoledirecte.com/v3/login.awp',
                 'data={"identifiant": "' + username + '","motdepasse": "' + password + '"}').text
        r = loads(r)

        self.token = r["token"]
        self.id = r["data"]["accounts"][0]["id"]

    def getHomeworks(self):
        r = post('https://api.ecoledirecte.com/v3/Eleves/' + str(self.id) + '/cahierdetexte.awp?verbe=get',
                 'data={"token": "' + self.token + '"}').text
        r = loads(r)

        result = []
        for date, hws in r["data"].items():
            for hw in hws:
                result.append(Homework(date, hw))

        return result

    def getHomeworksForDay(self, day):
        r = post('https://api.ecoledirecte.com/v3/Eleves/' + str(self.id) + '/cahierdetexte/' + day + '.awp?verbe=get',
                 'data={"token": "' + self.token + '"}').text

        return r

    def getNotes(self):
        r = post('https://api.ecoledirecte.com/v3/eleves/' + str(self.id) + '/notes.awp?verbe=get',
                 'data={"token": "' + self.token + '"}').text
        r = loads(r)

        result = []
        for p in r["data"]["periodes"]:
            p = Period(p)
            for n in p.data:
                result.append(Note(n, p))

        return NoteList(result)
