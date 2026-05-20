import asyncio
import tornado.web
import tornado.escape
import json
import pandas as pd
import time
import random
from collections import defaultdict

# ── BRUTE FORCE PROTECTION ──────────────────────────────────────────────────
# Tracciamento per username: { username -> [timestamp, ...] }
_failed_attempts: dict = defaultdict(list)

MAX_ATTEMPTS = 5      # tentativi falliti prima del blocco
WINDOW_SEC   = 300    # finestra in cui contare i tentativi (5 min)

# Durata blocco in secondi per ruolo
LOCKOUT_BY_ROLE = {
    "admin":    600,   # admin    → 10 minuti
    "ref":      300,   # referente →  5 minuti
}
LOCKOUT_DEFAULT = 120  # studenti  →  2 minuti

def _lockout_sec(username: str) -> int:
    return LOCKOUT_BY_ROLE.get(username, LOCKOUT_DEFAULT)

def _is_rate_limited(username: str) -> tuple[bool, int]:
    """Restituisce (bloccato, secondi_rimasti)."""
    now = time.time()
    lockout = _lockout_sec(username)
    attempts = _failed_attempts[username]
    # rimuovi tentativi più vecchi del periodo di blocco
    attempts[:] = [t for t in attempts if now - t < lockout]
    recent = [t for t in attempts if now - t < WINDOW_SEC]
    if len(recent) >= MAX_ATTEMPTS:
        wait = int(lockout - (now - recent[0]))
        return True, max(wait, 1)
    return False, 0

def _record_failure(username: str):
    _failed_attempts[username].append(time.time())

def _clear_failures(username: str):
    _failed_attempts.pop(username, None)

parole = ["Nebbia", "Fulmine", "Quaderno", "Astronave", "Cactus", "Lampione", "Cascata", "Vulcano", "Ombrello", "Biscotto", "Tornado", "Marmotta", "Pixel", "Satellitare", "Drago", "Cometa", "Tostapane", "Girasole", "Tempesta", "Bussola", "Pinguino", "Prisma", "Zaino", "Ciclone", "Diamante", "Meteora", "Lampadina", "Tastiera", "Ruggine", "Cannocchiale", "Foresta", "Corallo", "Aquila", "Origami", "Monolite", "Vortice", "Fenice", "Circuito", "Galassia", "Castoro", "Binocolo", "Radar", "Cratere", "Mandarino", "Pendolo", "Scogliera", "Marinaio", "Clessidra", "Fossile", "Zaffiro"]

simboli = ["!", "@", "#", "$", "%", "&", "*", "?"]

def genera_password():
    parola = random.choice(parole)
    numero = random.randint(0, 99)  # 2 cifre
    simbolo = random.choice(simboli)

    password = f"{parola}{numero}{simbolo}"
    return password

demo_entities = [
    {"id": 0, "name": "Caritas", "contact": "info@caritas.it", "phone": "02-1234567",
     "address": "Via Roma 1, Milano", "sector": "Sociale", "site": "caritas.it", "posti_rimasti": 2,
     "capacity": 2, "tutor": "Mario Rossi", "tutor_phone": "333-1111111",
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
    {"id": 1, "name": "Legambiente", "contact": "info@legambiente.it", "phone": "02-9876543",
     "address": "Via Verde 5, Milano", "sector": "Ambiente", "site": "legambiente.it",
     "capacity": 4, "posti_rimasti": 4, "tutor": "Laura Bianchi", "tutor_phone": "333-2222222",
     "schedule": {"lun": [{"start": "09:00", "end": "13:00"}], "mar": [{"start": "09:00", "end": "13:00"}], "mer": [],
                  "gio": [{"start": "09:00", "end": "13:00"}], "ven": [], "sab": []}},
    {"id": 2, "name": "Croce Rossa", "contact": "info@cri.it", "phone": "02-5551234",
     "address": "Via Salute 10, Milano", "sector": "Sanitario", "site": "cri.it",
     "capacity": 6, "posti_rimasti": 6, "tutor": "Giulia Verdi", "tutor_phone": "333-3333333",
     "schedule": {"lun": [], "mar": [{"start": "08:00", "end": "14:00"}], "mer": [{"start": "08:00", "end": "14:00"}],
                  "gio": [], "ven": [{"start": "08:00", "end": "14:00"}], "sab": []}},
]

id_to_name = {e["id"]: e["name"] for e in demo_entities}  # crea un diz con solo id:nome
demo_students = [
    {
        "username": "studente",
        "password": "",
        "school": "Fermi",
        "choices": ["Croce Rossa"],
        "entities": None,
        "assigned_entity": None
    },
    {
        "username": "ari",
        "password": "",
        "school": "Fermi",
        "choices": ["Caritas"],
        "entities": None,
        "assigned_entity": None
    },
    {
        "username": "giacomo",
        "password": "",
        "school": "Fermi",
        "choices": ["Legambiente"],
        "entities": None,
        "assigned_entity": None
    },
]

demo_referent = [
    {
        "username": "ref",
        "password": "",
        "school": "Fermi",
    }
]


class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("login.html", error=None)

    def post(self):
        username = self.get_body_argument("username").strip()
        password = self.get_body_argument("password")

        # Controlla blocco sull'username prima ancora di verificare la password
        blocked, wait = _is_rate_limited(username)
        if blocked:
            minuti = wait // 60
            secondi = wait % 60
            msg = f"Account bloccato. Riprova tra {minuti}m {secondi:02d}s."
            self.render("login.html", error=msg)
            return

        if username == "admin" and password == "":
            _clear_failures(username)
            self.set_secure_cookie("user", username)
            self.redirect("/enti")
        elif username == "ari" and password == "":
            _clear_failures(username)
            self.set_secure_cookie("user", username)
            self.redirect("/studente/scelta_enti")
        elif username == "studente" and password == "":
            _clear_failures(username)
            self.set_secure_cookie("user", username)
            self.redirect("/studente/scelta_enti")
        elif username == "ref" and password == "":
            _clear_failures(username)
            self.set_secure_cookie("user", username)
            self.redirect("/referente")
        else:
            _record_failure(username)
            blocked, wait = _is_rate_limited(username)
            if blocked:
                lockout_min = _lockout_sec(username) // 60
                msg = f"Troppi tentativi. Account bloccato per {lockout_min} minuti."
            else:
                recent = [t for t in _failed_attempts[username]
                          if time.time() - t < WINDOW_SEC]
                rimasti = MAX_ATTEMPTS - len(recent)
                msg = f"Credenziali errate. Tentativi rimasti: {rimasti}."
            self.render("login.html", error=msg)


class AddEnteHandler(tornado.web.RequestHandler):
    def get(self):
        #pubblico la pagina add_edit.html
        self.render("ADMIN/add_edit.html", name=None)

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
        id = 1
        lista = []
        #vado a creare una lista con gli id già utilizzati
        for ente in demo_entities:
            lista.append(ente["id"])
        #scorro la variabile fino a che trovo una non corrispondenza con un id già utilizzato
        while id < len(lista) + 2:
            if id in lista:
                id = id + 1
            else:
                break
        new_ente = {"id": id, "name": name, "contact": contact, "phone": phone, "address": address, "sector": sector,
                    "site": site, "capacity": capacity, "tutor": tutor, "tutor_phone": tutor_phone,
                    "schedule": schedule}
        demo_entities.append(new_ente)
        self.redirect("/enti")


class EditEnteHandler(tornado.web.RequestHandler):
    def get(self, id):
        #contorllo se id del prodotto che voglio modificare c'è nella lista e prendo le variabili del prodotto da modificare
        id = int(id)
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
        self.render("ADMIN/add_edit.html", lunedi=lunedi, martedi=martedi, mercoledi=mercoledi, giovedi=giovedi,
                    venerdi=venerdi, sabato=sabato, domenica=domenica, id=id, name=name, contact=contact, phone=phone,
                    address=address, sector=sector, site=site, capacity=capacity, tutor=tutor, tutor_phone=tutor_phone,
                    schedule=schedule)

    def post(self, id):
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

        id = int(id)
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
    def post(self, id):
        id = int(id)

        for ente in demo_entities:
            if ente["id"] == id:
                for student in demo_students:
                    if student["assigned_entity"] == id:
                        student["assigned_entity"] = None
                    for scelta in student["choices"]:
                        if scelta == id_to_name[id]:
                            student["choices"].remove(scelta)

                demo_entities.remove(ente)
        self.redirect("/enti")


class EnteHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")

        if not user:
            self.redirect("/login")
            return

        enti = demo_entities
        # pubblico la pagina add_edit.html, con le variabili modificate
        self.render("ADMIN/visualizza_enti.html", enti=enti, user=user.decode())


class GraficiHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")
        if not user:
            self.redirect("/login")
            return

        # LINK GOOGLE SHEETS
        url = "https://docs.google.com/spreadsheets/d/1GgYsNB5XGE-bEj_uKu1d9SiZram4gXO5l-AEtW5Wkl8/export?format=csv"
        df = pd.read_csv(url)
        data = df.to_dict(orient="records")

        # -------------------------
        # 1. LETTURA DEL FILTRO
        # -------------------------
        # Uso get_argument perché il form è method="GET"
        id_filtro = self.get_argument("id_filtro", "")
        enti = demo_entities
        anno_filtro = self.get_argument("anno_filtro", "")
        anni = []
        for risposta in data:
            crono = risposta.get("Informazioni cronologiche", "")
            anno = crono[6:10]
            if anno not in anni:
                anni.append(anno)
        # Creo mappe di utilità
        id_to_name = {e["id"]: e["name"] for e in demo_entities}
        name_to_id = {e["name"]: str(e["id"]) for e in demo_entities}

        # =========================
        # FILTRAGGIO DATI
        # =========================
        dati_filtrati = []
        for risposta in data:
            # ---- filtro ente ----
            ente_ok = True
            if id_filtro and id_filtro in name_to_id:
                target_id = name_to_id[id_filtro]
                ente_id_risposta = str(
                    risposta.get(
                        "Inserisci il numero in riferimento all'ente in cui sei stato (guardare legenda)",
                        ""
                    )
                ).strip()
                ente_ok = ente_id_risposta == target_id

            # ---- filtro anno ----
            anno_ok = True
            if anno_filtro:
                crono = str(risposta.get("Informazioni cronologiche", ""))
                if len(crono) >= 10:
                    anno_risposta = crono[6:10]
                else:
                    anno_risposta = ""
                anno_ok = anno_risposta == anno_filtro
            # ---- aggiunta finale ----
            if ente_ok and anno_ok:
                dati_filtrati.append(risposta)

        # sostituisco i dati originali
        data = dati_filtrati

        # -------------------------
        # TORTA (Ora usa 'data' che è eventualmente filtrato)
        # -------------------------
        scala = ["Moltissimo", "Molto", "Abbastanza", "Poco", "Per nulla"]
        conteggio_scala = {k: 0 for k in scala}

        for risposta in data:
            for key, value in risposta.items():
                if "In base alle domande selezionare la risposta" in key or "Quanto reputi interessanti i seguenti aspetti dell’attività di volontariato?" in key:
                    if value in conteggio_scala:
                        conteggio_scala[value] += 1

        # -------------------------
        # COMPETENZE
        # -------------------------
        competenze_lista = [
            "Problem solving", "Empatia", "Adattibilità", "Autocontrollo",
            "Lavoro di squadra/networking", "Sicurezza in sé stessi",
            "Spirito di collaborazione", "Volontà di apprendere",
            "Creatività", "Pensiero critico"
        ]

        conteggio_competenze = {k: 0 for k in competenze_lista}

        for risposta in data:
            val = risposta.get("Cosa pensi di aver imparato dall’esperienza di stage? ", "")
            for c in str(val).split(","):
                c = c.strip()
                if c in conteggio_competenze:
                    conteggio_competenze[c] += 1

        # -------------------------
        # CONTESTI
        # -------------------------
        contesti_lista = [
            "Nel mondo della scuola", "Nel mondo del lavoro",
            "Nell'attività di volontariato",
            "Nel mio contesto di amici", "In famiglia"
        ]

        conteggio_contesti = {k: 0 for k in contesti_lista}

        for risposta in data:
            val = risposta.get("In quale contesto pensi che potresti spendere le competenze che hai sviluppato?", "")
            for c in str(val).split(","):
                c = c.strip()
                if c in conteggio_contesti:
                    conteggio_contesti[c] += 1

        # Renderizzo la pagina passando l'id_filtro corretto
        self.render(
            "ADMIN/grafici.html",
            user=user.decode(),
            scala=json.dumps(conteggio_scala),
            competenze=json.dumps(conteggio_competenze),
            contesti=json.dumps(conteggio_contesti),
            id_to_name=id_to_name,
            enti=enti,
            id_filtro=id_filtro,
            anni=anni,
            anno_filtro=anno_filtro,
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
        primo = ""
        secondo = ""
        terzo = ""
        enti = demo_entities
        for persona in demo_students:
            if persona["username"] == user.decode():
                if len(persona["choices"]) == 1:
                    primo = persona["choices"][0]
                elif len(persona["choices"]) == 2:
                    primo = persona["choices"][0]
                    secondo = persona["choices"][1]
                elif len(persona["choices"]) == 3:
                    primo = persona["choices"][0]
                    secondo = persona["choices"][1]
                    terzo = persona["choices"][2]
                self.render("STUDENTE/scelta_enti.html", enti=enti, user=user.decode(), primo=primo, secondo=secondo,
                            terzo=terzo)

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
        enti = demo_entities
        user = self.get_secure_cookie("user")
        primo = self.get_argument("primo", "")
        secondo = self.get_argument("secondo", "")
        terzo = self.get_argument("terzo", "")
        for persona in demo_students:
            if persona["username"] == user.decode():
                persona["choices"] = [primo, secondo, terzo]
        self.render("STUDENTE/scelta_enti.html", user=user.decode(), primo=primo, terzo=terzo, secondo=secondo,
                    enti=enti)


class QuestionarioStudenteHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")
        if not user:
            self.redirect("/login")
            return
        id_to_name = {e["id"]: e["name"] for e in demo_entities}  #crea un diz con solo id:nome
        self.render("STUDENTE/questionario_studenti.html", user=user.decode(), id_to_name=id_to_name)


class ReferenteHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")
        enti = demo_entities
        for referenti in demo_referent:
            if referenti["username"] == user.decode():
                referente = referenti
        if not user:
            self.redirect("/login")
            return
        enti = demo_entities
        studenti_fermi = []
        for persona in demo_students:
            if persona["school"] == referente["school"]:
                studenti_fermi.append(persona)
        id_to_name = {e["id"]: e["name"] for e in demo_entities}  #crea un diz con solo id:nome
        error = self.get_argument("error", None)
        self.render("REFERENTE/referente.html", id_to_name=id_to_name, user=user.decode(),
                    studenti_fermi=studenti_fermi, enti=enti,error=error)


    def post(self, username):
        ente_id = self.get_body_argument("ente_id")

        # Trova lo studente
        studente = None
        for s in demo_students:
            if s["username"] == username:
                studente = s
                break

        if not studente:
            self.redirect("/referente")
            return

        # RIMUOVI ASSEGNAZIONE VECCHIA (ripristina posti)
        if studente["assigned_entity"] is not None:
            for ente in demo_entities:
                if ente["id"] == studente["assigned_entity"]:
                    ente["posti_rimasti"] += 1  # Ripristina il posto
                    break

        # NUOVA ASSEGNAZIONE
        if ente_id == "":
            studente["assigned_entity"] = None
        else:
            ente_id_val = int(ente_id)
            for ente in demo_entities:
                if ente["id"] == ente_id_val:
                    if ente["posti_rimasti"] > 0:
                        ente["posti_rimasti"] -= 1
                        studente["assigned_entity"] = ente_id_val
                    else:
                        # ERRORE: posti esauriti - ripristina vecchia assegnazione se esisteva
                        self.render("REFERENTE/referente.html",
                                    error=f"Impossibile assegnare: {ente['name']} ha posti esauriti",
                                    user=self.get_secure_cookie("user").decode(),
                                    id_to_name={e["id"]: e["name"] for e in demo_entities},
                                    studenti_fermi=[s for s in demo_students if s["school"] == "Fermi"],
                                    enti=demo_entities)
                        return

        self.redirect("/referente")

class CreaStudenteHandler(tornado.web.RequestHandler):
    def post(self):
        user = self.get_secure_cookie("user")
        for referenti in demo_referent:
            if referenti["username"] == user.decode():
                scuola=referenti["school"]
        nome_cognome=self.get_body_argument("nome_cognome")
        parte_finale=self.get_body_argument("parte_finale")
        mail=nome_cognome+"@"+parte_finale
        demo_students.append({"username": mail, "password": genera_password(), "school": scuola,"choices":[],"entities":None,"assigned_entity":None})
        self.redirect("/referente")
def make_app():
    return tornado.web.Application([
        (r"/login", LoginHandler),
        (r"/studente/scelta_enti", SceltaHandler),
        (r"/studente/visione_ente", ScheduleHandler),
        (r"/studente/questionario", QuestionarioStudenteHandler),
        (r"/referente", ReferenteHandler),
        (r"/referente/assegna/([^/]+)", ReferenteHandler),
        (r"/referente/crea", CreaStudenteHandler),
        (r"/enti", EnteHandler),
        (r"/enti/add", AddEnteHandler),
        (r"/enti/edit/([0-9]+)", EditEnteHandler),
        (r"/enti/delete/([0-9]+)", DeleteEnteHandler),
        (r"/grafici", GraficiHandler),
        (r"/questionari", QuestionariAdminHandler)
    ], cookie_secret="SUPER_SECRET_KEY", static_path=".")


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
