from json import loads, dumps
from os import mkdir
from os.path import exists
from random import choice
from typing import List, BinaryIO
from urllib.parse import urlencode

from requests import post, options


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


class NoteList(list):
    def getBests(self):
        best = 0
        for n in self:
            if n.note is None:
                continue
            if n.note > best:
                best = n.note

        bests = []
        for n in self:
            if n.note is None:
                continue
            if n.note >= best:
                bests.append(n)

        return bests

    def getWorsts(self):
        worst = 21
        for n in self:
            if n.note is None:
                continue
            if n.note < worst:
                worst = n.note

        worsts = []
        for n in self:
            if n.note is None:
                continue
            if n.note <= worst:
                worsts.append(n)

        return worsts

    def random(self):
        return choice(self)

    def all(self):
        return self

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} {list.__repr__(self)}>"


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
            repr(t) for t in self.teachers) + ">"


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


class Person:
    def __init__(self, name, surname, civility, id, role):
        self.id = id
        self.name = name
        self.surname = surname
        self.sex = civility == "M."
        self.role = role

    def asTeacher(self):
        if self.role != "P":
            return
        return Teacher(("M." if self.sex else "Mme") + " " + self.name + " " + self.surname)


class Message:
    def __init__(self, session, folder, data):
        self.session = session
        self.id = data["id"]
        self.read = data["read"]
        self.subject = data["subject"]
        self.date = data["date"]
        self.sent = data["mtype"] == "send"
        self.to = [Person(d["nom"], d["prenom"], d["civilite"], d["id"], d["role"]) for d in data["to"]]
        self.from_ = Person(data["from"]["nom"], data["from"]["prenom"], data["from"]["civilite"], data["from"]["id"],
                            data["from"]["role"])
        self.folder = folder

    def _action(self, name, **kwargs):
        r = post('https://api.ecoledirecte.com/v3/eleves/' + str(self.session.id) + '/messages.awp?verbe=put',
                 'data=' + dumps({"token": self.session.token, "ids": [self.id], "action": name, **kwargs})).text

        r = loads(r)

        return r

    def markAsUnread(self):
        self._action("marquerCommeNonLu")

    def markAsRead(self):
        self._action("marquerCommeLu")

    def archive(self):
        self._action("archiver")

    def unarchive(self):  ###################### Ne marche pas (jsp pk) ######################
        self._action("desarchiver")

    def moveTo(self, folderId):
        self._action("deplacer", idClasseur=folderId)

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} '{self.subject}'>"


def _fusion(data):
    r = []
    for x in data.values():
        for y in x:
            r.append(y)
    return r


class MessageList:
    def __init__(self, session, data):
        self.session = session
        self.folders = {}
        for folder, messages in data.items():
            self.folders[folder] = []
            for m in messages:
                self.folders[folder].append(Message(self.session, folder, m))

        self._messages: List[Message] = _fusion(self.folders)

    def getUnread(self):
        return [m for m in self._messages if not m.read]

    def getRead(self):
        return [m for m in self._messages if m.read]

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n < len(self._messages):
            self.n += 1
            return self._messages[self.n - 1]
        else:
            del self.n
            raise StopIteration

    def __getitem__(self, item):
        return self._messages[item]


def loadClassCloudElement(session, parent, data):
    if data["type"] == "folder":
        return ClassCloudFolder(session, parent, data)
    if data["type"] == "file":
        return ClassCloudFile(session, parent, data)


class ClassCloudFile:
    def __init__(self, session, parent, data):
        self.session = session
        self.name = data["libelle"]
        self.size = data["taille"]
        self.id = data["id"]
        self.parent = parent
        self.folder = False

    def download(self, filename: str = None):
        r = self.session.download("CLOUD", self.id)

        if not exists("downloads"):
            mkdir("downloads")

        with open(filename or ("downloads/" + self.name), "wb") as f:
            f.write(r)

        return filename or ("downloads/" + self.name)

    def getPath(self):
        return self.parent.getPath() + "\\" + self.name

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} '{self.getPath()}'>"


class ClassCloudFolder:
    def __init__(self, session, parent, data):
        self.session = session
        self.name = data["libelle"]
        self.size = data["taille"]
        self.id = data["id"]
        self.isLoaded = data["isLoaded"]
        self.children = [loadClassCloudElement(self.session, self, c) for c in data["children"]]
        self.parent = parent
        self.folder = True

    def load(self):
        r = post('https://api.ecoledirecte.com/v3/cloud/W/' + str(self.getId()) + '.awp?' + urlencode(
            dict(verbe="get", idFolder=self.getPath())),
                 'data={"token": "' + self.session.token + '"}').content.decode("utf8")

        data = loads(r)["data"][0]

        self.children = [loadClassCloudElement(self.session, self, c) for c in data["children"]]
        self.isLoaded = data["isLoaded"]

        return self

    def loadAll(self):
        self.load()
        for c in self.children:
            if c.folder:
                c.loadAll()

    def getChildByName(self, name: str):
        self.load()
        for c in self.children:
            if c.name.lower().strip() == name.lower().strip():
                return c

        return None

    def getFileByPath(self, path: str):
        self.load()

        f, *p = path.split("/")

        p = "/".join(p)

        f = self.getChildByName(f)

        if not f:
            return

        if not p:
            return f

        return f.getFileByPath(p)

    def tree(self):
        self.loadAll()
        r = {}
        for c in self.children:
            if c.folder:
                r[c.name] = c.tree()
            else:
                r[c.name] = c
        return r

    def getPath(self):
        return self.parent.getPath() + "\\" + self.name

    def getId(self):
        return self.parent.getId()

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} '{self.getPath()}'>"


class ClassCloud(ClassCloudFolder):
    def __init__(self, session, id, data):
        super().__init__(session, None, data[0])
        self.cloudId = id

    def getPath(self):
        return ""

    def getId(self):
        return self.cloudId


class MetaClassCloud:
    def __init__(self, session, data):
        self.session = session
        self.id = int(data["id"])
        self.name = data["titre"]

    def get(self) -> ClassCloud:
        return self.session.getCloud(self.id)

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} '{self.id}'>"


def loadPersonalCloudElement(session, parent, data):
    if data["type"] == "folder":
        return PersonalCloudFolder(session, parent, data)
    if data["type"] == "file":
        return PersonalCloudFile(session, parent, data)


class PersonalCloudFile:
    def __init__(self, session, parent, data):
        self.session = session
        self.name = data["libelle"]
        self.size = data["taille"]
        self.id = data["id"]
        self.parent = parent
        self.folder = False

    def download(self, filename: str = None):
        r = self.session.download("CLOUD", self.id)

        if not exists("downloads"):
            mkdir("downloads")

        with open(filename or ("downloads/" + self.name), "wb") as f:
            f.write(r)

        return filename or ("downloads/" + self.name)

    def getPath(self):
        return self.parent.getPath() + "\\" + self.name

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} '{self.getPath()}'>"


class PersonalCloudFolder:
    def __init__(self, session, parent, data):
        self.session = session
        self.name = data["libelle"]
        self.size = data["taille"]
        self.id = data["id"]
        self.isLoaded = data["isLoaded"]
        self.children = [loadPersonalCloudElement(self.session, self, c) for c in data["children"]]
        self.parent = parent
        self.folder = True

    def load(self):
        if self.isLoaded:
            return
        r = post('https://api.ecoledirecte.com/v3/cloud/E/' + str(self.session.id) + '.awp?' + urlencode(
            dict(verbe="get", idFolder=self.getPath())),
                 'data={"token": "' + self.session.token + '"}').content.decode("utf8")

        data = loads(r)["data"][0]

        self.children = [loadPersonalCloudElement(self.session, self, c) for c in data["children"]]
        self.isLoaded = data["isLoaded"]

        return self

    def loadAll(self):
        self.load()
        for c in self.children:
            if c.folder:
                c.loadAll()

    def getChildByName(self, name: str):
        self.load()
        for c in self.children:
            if c.name.lower().strip() == name.lower().strip():
                return c

        return None

    def getFileByPath(self, path: str):
        self.load()

        f, *p = path.split("/")

        p = "/".join(p)

        f = self.getChildByName(f)

        if not f:
            return

        if not p:
            return f

        return f.getFileByPath(p)

    def tree(self):
        self.loadAll()
        r = {}
        for c in self.children:
            if c.folder:
                r[c.name] = c.tree()
            else:
                r[c.name] = c
        return r

    def getPath(self):
        return self.parent.getPath() + "\\" + self.name

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} '{self.getPath()}'>"


class PersonalCloud(PersonalCloudFolder):
    def __init__(self, session, data):
        super().__init__(session, None, data[0])

    def getPath(self):
        return ""


class Document:
    def __init__(self, session, data):
        self.type = data["type"]
        self.id = int(data["id"])
        self.name = data["libelle"]
        self.date = data["date"]
        self.session = session

    def download(self, filename: str = None):
        r = self.session.download(self.type, self.id)

        if not exists("downloads"):
            mkdir("downloads")

        with open(filename or ("downloads/" + self.name + ".pdf"), "wb") as f:
            f.write(r)

        return filename or ("downloads/" + self.name + ".pdf")

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} '{self.name}'>"


class Session:
    def __init__(self, username, password):
        r = post('https://api.ecoledirecte.com/v3/login.awp',
                 'data={"identifiant": "' + username + '","motdepasse": "' + password + '"}').text
        r = loads(r)

        self.token = r["token"]
        self.id = r["data"]["accounts"][0]["id"]

    def download(self, type, id):
        return post('https://api.ecoledirecte.com/v3/telechargement.awp?verbe=get',
                    'token=' + self.token + '&leTypeDeFichier='+type+'&' + 'fichierId=' + str(id)).content

    def getHomeworks(self):
        r = post('https://api.ecoledirecte.com/v3/Eleves/' + str(self.id) + '/cahierdetexte.awp?verbe=get',
                 'data={"token": "' + self.token + '"}').content.decode("utf8")
        r = loads(r)

        result = []
        for date, hws in r["data"].items():
            for hw in hws:
                result.append(Homework(date, hw))

        return result

    def getHomeworksForDay(self, day):
        r = post('https://api.ecoledirecte.com/v3/Eleves/' + str(self.id) + '/cahierdetexte/' + day + '.awp?verbe=get',
                 'data={"token": "' + self.token + '"}').content.decode("utf8")

        return r

    def getNotes(self):
        r = post('https://api.ecoledirecte.com/v3/eleves/' + str(self.id) + '/notes.awp?verbe=get',
                 'data={"token": "' + self.token + '"}').content.decode("utf8")
        r = loads(r)

        result = []
        for p in r["data"]["periodes"]:
            p = Period(p)
            for n in p.data:
                result.append(Note(n, p))

        return NoteList(result)

    def getMessages(self):
        r = post('https://api.ecoledirecte.com/v3/eleves/' + str(
            self.id) + '/messages.awp?verbe=getall&orderBy=date&order=desc',
                 'data={"token": "' + self.token + '"}').content.decode("utf8")
        r = loads(r)

        data = r["data"]["messages"]

        return MessageList(self, data)

    def getPersonalCloud(self):
        r = post('https://api.ecoledirecte.com/v3/cloud/E/' + str(self.id) + '.awp?verbe=get',
                 'data={"token": "' + self.token + '"}').content.decode("utf8")
        r = loads(r)

        data = r["data"]

        return PersonalCloud(self, data)

    def getClouds(self):
        r = post('https://api.ecoledirecte.com/v3/E/' + str(self.id) + '/espacestravail.awp?verbe=get',
                 'data={"token": "' + self.token + '"}').content.decode("utf8")
        r = loads(r)

        data = r["data"]

        return [MetaClassCloud(self, c) for c in data if c["cloud"]]

    def getCloud(self, id: int):
        r = post('https://api.ecoledirecte.com/v3/cloud/W/' + str(id) + '.awp?verbe=get',
                 'data={"token": "' + self.token + '"}').content.decode("utf8")

        r = loads(r)

        data = r["data"]

        return ClassCloud(self, id, data)

    def getDocuments(self):
        r = post('https://api.ecoledirecte.com/v3/elevesDocuments.awp?verbe=get',
                 'data={"token": "' + self.token + '"}').content.decode("utf8")

        r = loads(r)

        data = r["data"]

        return {
            "administrative": [Document(self, d) for d in data["administratifs"]],
            "schoolLife": [Document(self, d) for d in data["viescolaire"]],
            "notes": [Document(self, d) for d in data["notes"]]
        }

