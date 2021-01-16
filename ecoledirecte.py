from requests import post, get
from json import loads

class Homework:
    def __init__(self, date, data):
        self.date = date
        self.subject = data["matiere"]
        self.done = data["effectue"]
        self.giveThe = data["donneLe"]
    def __repr__(self):
        return "Pour le "+self.date+", matière : "+self.subject+(" (Finit)" if self.done else "")

class Note:
    def __init__(self, data):
        self.note = data["moyenne"]
        self.moyenneClass = data["moyenneClasse"]
        self.moyenneClassMin = data["moyenneMin"]
        self.moyenneClassMax = data["moyenneMax"]
        self.coef = data["coef"]
        self.subject = data["discipline"]
        self.profs = [prof["nom"] for prof in data["professeurs"]]
    def __repr__(self):
        return f"Note: {self.note}; Moyenne de la classe: {self.moyenneClass}; coef: {self.coef}; matière: {self.subject}; profs: "+", ".join(self.profs)

class Session:
    def __init__(self, username, password):
        r = post('https://api.ecoledirecte.com/v3/login.awp', 'data={"identifiant": "'+username+'","motdepasse": "'+password+'"}').text
        r = loads(r)

        self.token = r["token"]
        self.id = r["data"]["accounts"][0]["id"]

    def getHomeworks(self):
        r = post('https://api.ecoledirecte.com/v3/Eleves/'+str(self.id)+'/cahierdetexte.awp?verbe=get', 'data={"token": "'+self.token+'"}').text
        r = loads(r)

        result = []
        for date, hws in r["data"].items():
            for hw in hws:
                result.append(Homework(date, hw))

        return result
    
    def getNotes(self):
        r = post('https://api.ecoledirecte.com/v3/eleves/'+str(self.id)+'/notes.awp?verbe=get', 'data={"token": "'+self.token+'"}').text
        r = loads(r)

        result = []
        for p in r["data"]["periodes"]:
            for n in p["ensembleMatieres"]["disciplines"]:
                result.append(Note(n))
        
        return result