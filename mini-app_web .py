import asyncio
import tornado.web
import tornado.escape
import json
import pandas as pd

demo_entities = [
    {"id":0,"name": "Caritas", "contact": "info@caritas.it", "phone": "02-1234567",
     "address": "Via Roma 1, Milano", "sector": "Sociale", "site": "caritas.it","posti_rimasti":5,
     "capacity": 5, "tutor": "Mario Rossi", "tutor_phone": "333-1111111",
     "schedule": {
        "lun": [{"start": "08:00", "end": "12:00"}],
        "mar": [],
        "mer": [
            {"start": "08:00", "end": "12:00"},
            {"start": "14:00", "end": "18:00"}
        ],
        "gio": [],
        "ven": [{"start": "08:00", "end": "12:00"}],
        "sab": []
    }},
    {"id":1,"name": "Legambiente", "contact": "info@legambiente.it", "phone": "02-9876543",
     "address": "Via Verde 5, Milano", "sector": "Ambiente", "site": "legambiente.it",
     "capacity": 4,"posti_rimasti":4, "tutor": "Laura Bianchi", "tutor_phone": "333-2222222",
     "schedule": {"lun": [{"start": "09:00", "end": "13:00"}], "mar": [{"start": "09:00", "end": "13:00"}], "mer": [], "gio": [{"start": "09:00", "end": "13:00"}], "ven": [], "sab": []}},
    {"id":2,"name": "Croce Rossa", "contact": "info@cri.it", "phone": "02-5551234",
     "address": "Via Salute 10, Milano", "sector": "Sanitario", "site": "cri.it",
     "capacity": 6,"posti_rimasti":6, "tutor": "Giulia Verdi", "tutor_phone": "333-3333333",
     "schedule": {"lun": [], "mar": [{"start": "08:00", "end": "14:00"}], "mer": [{"start": "08:00", "end": "14:00"}], "gio": [], "ven": [{"start": "08:00", "end": "14:00"}], "sab": []}},
]
demo_students = [
    {
        "username": "ari",
        "password": "",
        "school":"Fermi",
        "choices": ["Cacca"],
        "entities": None,
        "assigned_entity":None
    },
    {
        "username": "w",
        "password": "",
        "school": "Corni",
        "choices": ["Legambiente", "Croce Rossa", "Caritas"],
        "entities": None,
        "assigned_entity":None
    }
]

demo_referent = [
    {
        "username": "ref",
        "password": "",
        "school":"Fermi",
    }
]
class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("login.html", error=None)

    def post(self):
        username = self.get_body_argument("username")
        password = self.get_body_argument("password")


        if username == "admin" and password == "":
            self.set_secure_cookie("user", username)
            self.redirect("/enti")
        elif username == "ari" and password == "":
            self.set_secure_cookie("user", username)
            self.redirect("/studente/scelta_enti")
        elif username == "ref" and password == "":
            self.set_secure_cookie("user", username)
            self.redirect("/referente")
        else:
            self.render("login.html", error="Sei scemo")



class AddEnteHandler(tornado.web.RequestHandler):
    def get(self):
#pubblico la pagina add_edit.html
        self.render("ADMIN/add_edit.html",name=None)

    def post(self):
#prendo il valore delle variabili del nuovo prodotto, creo il nuovo prodotto, e ritorno alla pagina iniziale(/products)
        name = self.get_body_argument("name")
        contact = self.get_body_argument("contact")
        phone = self.get_body_argument("phone")
        address = self.get_body_argument("address")
        sector = self.get_body_argument("sector")
        site = self.get_body_argument("site")
        capacity = self.get_body_argument("capacity")
        tutor = self.get_body_argument("tutor")
        tutor_phone = self.get_body_argument("tutor_phone")
        def parse_day(text):
            result = []

            if not text.strip():
                return result

            intervals = text.split(",")

            for interval in intervals:
                start, end = interval.strip().split("-")
                result.append({
                    "start": start.strip(),
                    "end": end.strip()
                })

            return result


        schedule = {
            "lun": parse_day(self.get_argument("lunedi")),
            "mar": parse_day(self.get_argument("martedi")),
            "mer": parse_day(self.get_argument("mercoledi")),
            "gio": parse_day(self.get_argument("giovedi")),
            "ven": parse_day(self.get_argument("venerdi")),
            "sab": parse_day(self.get_argument("sabato")),
            "dom": parse_day(self.get_argument("domenica")),
        }

        #valori base alle variabili
        id=1
        lista=[]
        #vado a creare una lista con gli id già utilizzati
        for ente in demo_entities:
            lista.append(ente["id"])
        #scorro la variabile fino a che trovo una non corrispondenza con un id già utilizzato
        while id < len(lista)+2:
            if id in lista:
                id = id+1
            else:
                break
        new_ente = {"id":id,"name":name,"contact":contact,"phone":phone,"address":address,"sector":sector,"site":site,"capacity":capacity,"tutor":tutor,"tutor_phone":tutor_phone,"schedule":schedule}
        demo_entities.append(new_ente)
        self.redirect("/enti")

class EditEnteHandler(tornado.web.RequestHandler):
    def get(self,id):
#contorllo se id del prodotto che voglio modificare c'è nella lista e prendo le variabili del prodotto da modificare
        id=int(id)
        print(id)
        for ente in demo_entities:
            if ente["id"] == id:
                name = ente["name"]
                contact = ente["contact"]
                phone = ente["phone"]
                address = ente["address"]
                sector = ente["sector"]
                site = ente["site"]
                capacity = ente["capacity"]
                tutor = ente["tutor"]
                tutor_phone = ente["tutor_phone"]
                schedule = ente["schedule"]

                giorni = {
                    "lun": "lunedi",
                    "mar": "martedi",
                    "mer": "mercoledi",
                    "gio": "giovedi",
                    "ven": "venerdi",
                    "sab": "sabato",
                    "dom": "domenica"
                }

                giorni_formattati = {}

                for key, nome in giorni.items():
                    if key not in schedule or len(schedule[key]) == 0:
                        giorni_formattati[nome] = ""
                    else:
                        giorni_formattati[nome] = ", ".join(
                            f"{orario['start']}-{orario['end']}"
                            for orario in schedule[key]
                        )
                lunedi = giorni_formattati["lunedi"]
                martedi = giorni_formattati["martedi"]
                mercoledi = giorni_formattati["mercoledi"]
                giovedi = giorni_formattati["giovedi"]
                venerdi = giorni_formattati["venerdi"]
                sabato = giorni_formattati["sabato"]
                domenica = giorni_formattati["domenica"]

    # pubblico la pagina add_edit.html, con le variabili modificate
        self.render("ADMIN/add_edit.html",lunedi=lunedi,martedi=martedi,mercoledi=mercoledi,giovedi=giovedi,venerdi=venerdi,sabato=sabato,domenica=domenica,id=id, name=name,contact=contact,phone=phone,address=address,sector=sector,site=site,capacity=capacity,tutor=tutor,tutor_phone=tutor_phone,schedule=schedule )

    def post(self,id):
#prendo i valori delle variabili modificate e cercando dall'id del prodotto, sostituisco i valori di ogni variabile e ritorno alla pagina iniziale(/products)
        name = self.get_body_argument("name")
        contact = self.get_body_argument("contact")
        phone = self.get_body_argument("phone")
        address = self.get_body_argument("address")
        sector = self.get_body_argument("sector")
        site = self.get_body_argument("site")
        capacity = self.get_body_argument("capacity")
        tutor = self.get_body_argument("tutor")
        tutor_phone = self.get_body_argument("tutor_phone")
        def parse_day(text):
            result = []

            if not text.strip():
                return result

            intervals = text.split(",")

            for interval in intervals:
                start, end = interval.strip().split("-")
                result.append({
                    "start": start.strip(),
                    "end": end.strip()
                })

            return result

        schedule = {
            "lun": parse_day(self.get_argument("lunedi")),
            "mar": parse_day(self.get_argument("martedi")),
            "mer": parse_day(self.get_argument("mercoledi")),
            "gio": parse_day(self.get_argument("giovedi")),
            "ven": parse_day(self.get_argument("venerdi")),
            "sab": parse_day(self.get_argument("sabato")),
            "dom": parse_day(self.get_argument("domenica")),
        }


        id=int(id)
        for ente in demo_entities:
            if ente["id"] == id:
                ente["name"] = name
                ente["contact"] = contact
                ente["phone"] = phone
                ente["address"] = address
                ente["sector"] = sector
                ente["site"] = site
                ente["capacity"] = capacity
                ente["tutor"] = tutor
                ente["tutor_phone"] = tutor_phone
                ente["schedule"] = schedule
        self.redirect("/enti")

class DeleteEnteHandler(tornado.web.RequestHandler):
#cerco prodotto in base al suo id e lo elimino dalla lista dei prodotti e ritorno alla pagina iniziale(/products)
    def post(self,id):
        id=int(id)
        for ente in demo_entities:
            if ente["id"] == id:
                demo_entities.remove(ente)
        self.redirect("/enti")


class EnteHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")

        if not user:
            self.redirect("/login")
            return

        enti=demo_entities
        # pubblico la pagina add_edit.html, con le variabili modificate
        self.render("ADMIN/visualizza_enti.html", enti=enti,user=user.decode())


class GraficiHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")
        if not user:
            self.redirect("/login")
            return

        # 🔥 LINK GOOGLE SHEETS
        url = "https://docs.google.com/spreadsheets/d/1GgYsNB5XGE-bEj_uKu1d9SiZram4gXO5l-AEtW5Wkl8/export?format=csv"

        df = pd.read_csv(url)

        data = df.to_dict(orient="records")

        # -------------------------
        # 1️⃣ TORTA
        # -------------------------
        scala = ["Moltissimo", "Molto", "Abbastanza", "Poco", "Per nulla"]
        conteggio_scala = {k: 0 for k in scala}

        for risposta in data:
            for key, value in risposta.items():
                if "In base alle domande selezionare la risposta" in key:
                    if value in conteggio_scala:
                        conteggio_scala[value] += 1

        for risposta in data:
            for key, value in risposta.items():
                if "Quanto reputi interessanti i seguenti aspetti dell’attività di volontariato?" in key:
                    if value in conteggio_scala:
                        conteggio_scala[value] += 1



        # -------------------------
        # 2️⃣ COMPETENZE
        # -------------------------
        competenze_lista = [
            "Problem solving","Empatia","Adattibilità","Autocontrollo",
            "Lavoro di squadra/networking","Sicurezza in sé stessi",
            "Spirito di collaborazione","Volontà di apprendere",
            "Creatività","Pensiero critico"
        ]

        conteggio_competenze = {k: 0 for k in competenze_lista}

        for risposta in data:
            val = risposta.get("Cosa pensi di aver imparato dall’esperienza di stage? ", "")
            for c in str(val).split(","):
                c = c.strip()
                if c in conteggio_competenze:
                    conteggio_competenze[c] += 1

        # -------------------------
        # 3️⃣ CONTESTI
        # -------------------------
        contesti_lista = [
            "Nel mondo della scuola","Nel mondo del lavoro",
            "Nell'attività di volontariato",
            "Nel mio contesto di amici","In famiglia"
        ]

        conteggio_contesti = {k: 0 for k in contesti_lista}

        for risposta in data:
            val = risposta.get("In quale contesto pensi che potresti spendere le competenze che hai sviluppato?", "")
            for c in str(val).split(","):
                c = c.strip()
                if c in conteggio_contesti:
                    conteggio_contesti[c] += 1

        self.render(
            "ADMIN/grafici.html",
            user=user.decode(),
            scala=json.dumps(conteggio_scala),
            competenze=json.dumps(conteggio_competenze),
            contesti=json.dumps(conteggio_contesti)
        )

class QuestionariAdminHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")

        if not user:
            self.redirect("/login")
            return
        self.render("ADMIN/questionari_admin.html", user=user.decode())


class ScheduleHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")
        if not user:
            self.redirect("/login")
            return

        for persona in demo_students:
            if persona["username"] == user.decode():
                if persona["assigned_entity"] is None:
                    self.redirect("/studente/scelta_enti")
                    return

                for ente in demo_entities:
                    if ente["id"] == persona["assigned_entity"]:
                        name = ente["name"]
                        contact = ente["contact"]
                        phone = ente["phone"]
                        address = ente["address"]
                        sector = ente["sector"]
                        site = ente["site"]
                        capacity = ente["capacity"]
                        tutor = ente["tutor"]
                        tutor_phone = ente["tutor_phone"]
                        schedule = ente["schedule"]

                        # converti in formato stringa per il JS
                        schedule_js = {}
                        for day, intervals in schedule.items():
                            if intervals:
                                schedule_js[day] = ", ".join(
                                    f"{i['start']}-{i['end']}" for i in intervals
                                )
                            else:
                                schedule_js[day] = ""

                        self.render("STUDENTE/schedule.html",
                                    user=user.decode(),
                                    name=name, contact=contact, phone=phone,
                                    address=address, sector=sector, site=site,
                                    capacity=capacity, tutor=tutor,
                                    tutor_phone=tutor_phone,
                                    schedule_json=json.dumps(schedule_js))
                        return
class SceltaHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")

        if not user:
            self.redirect("/login")
            return
        primo=""
        secondo=""
        terzo=""
        enti = demo_entities
        for persona in demo_students:
            if persona["username"] == user.decode():
                if len(persona["choices"]) == 1:
                    primo=persona["choices"][0]
                elif len(persona["choices"]) == 2:
                    primo=persona["choices"][0]
                    secondo=persona["choices"][1]
                elif len(persona["choices"]) == 3:
                    primo=persona["choices"][0]
                    secondo=persona["choices"][1]
                    terzo=persona["choices"][2]
                self.render("STUDENTE/scelta_enti.html", enti=enti,user=user.decode(),primo=primo,secondo=secondo,terzo=terzo)

    def post(self):
        enti = demo_entities
        user = self.get_secure_cookie("user")

        primo = self.get_body_argument("primo")
        secondo = self.get_body_argument("secondo")
        terzo = self.get_body_argument("terzo")

        for persona in demo_students:
            if persona["username"] == user.decode():
                persona["choices"] = [primo, secondo, terzo]

        self.redirect("/studente/scelta_enti")




class EditSceltaHandler(tornado.web.RequestHandler):
    def get(self):
        enti=demo_entities
        user = self.get_secure_cookie("user")
        primo=self.get_argument("primo","")
        secondo=self.get_argument("secondo","")
        terzo=self.get_argument("terzo","")
        for persona in demo_students:
            if persona["username"] == user.decode():
                persona["choices"] = [primo, secondo, terzo]
        self.render("STUDENTE/scelta_enti.html",user=user.decode(),primo=primo,terzo=terzo,secondo=secondo,enti=enti)

class QuestionarioStudenteHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")
        if not user:
            self.redirect("/login")
            return
        self.render("STUDENTE/questionario_studenti.html", user=user.decode())


class ReferenteHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")
        enti=demo_entities
        for referenti in demo_referent:
            if referenti["username"] == user.decode():
                referente=referenti
        if not user:
            self.redirect("/login")
            return
        enti=demo_entities
        studenti_fermi = []
        for persona in demo_students:
            if persona["school"] == referente["school"]:
                studenti_fermi.append(persona)
        id_to_name = {e["id"]: e["name"] for e in demo_entities} #crea un diz con solo id:nome
        self.render("REFERENTE/referente.html",id_to_name=id_to_name, user=user.decode(),studenti_fermi=studenti_fermi,enti=enti)


    def post(self, username):
        ente_id = self.get_body_argument("ente_id")

        # se non ha selezionato niente, togli l'assegnazione
        if ente_id == "":
            ente_id_val = None
        else:
            ente_id_val = int(ente_id)

        # cerca lo studente per username e aggiorna assigned_entity
        for studente in demo_students:
            if studente["username"] == username:
                studente["assigned_entity"] = ente_id_val
                break
        print(demo_students)
        self.redirect("/referente")





def make_app():
    return tornado.web.Application([
        (r"/login", LoginHandler),
        (r"/studente/scelta_enti", SceltaHandler),
        (r"/studente/visione_ente", ScheduleHandler),
        (r"/studente/questionario", QuestionarioStudenteHandler),
        (r"/referente", ReferenteHandler),
        (r"/referente/assegna/([^/]+)", ReferenteHandler),
        (r"/enti", EnteHandler),
        (r"/enti/add", AddEnteHandler),
        (r"/enti/edit/([0-9]+)", EditEnteHandler),
        (r"/enti/delete/([0-9]+)", DeleteEnteHandler),
        (r"/grafici", GraficiHandler),
        (r"/questionari", QuestionariAdminHandler)
    ], cookie_secret="SUPER_SECRET_KEY")

async def main(shutdown_event):
    app = make_app()
    app.listen(8888)
    print("Server attivo su http://localhost:8888/login")
    await shutdown_event.wait()
    print("Chiusura server...")


if __name__ == "__main__":
    shutdown_event = asyncio.Event()
    try:
        asyncio.run(main(shutdown_event))
    except KeyboardInterrupt:
        shutdown_event.set()