import asyncio
import tornado.web
import tornado.escape

demo_entities = [
    {"id":0,"name": "Caritas", "contact": "info@caritas.it", "phone": "02-1234567",
     "address": "Via Roma 1, Milano", "sector": "Sociale", "site": "caritas.it",
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
     "capacity": 4, "tutor": "Laura Bianchi", "tutor_phone": "333-2222222",
     "schedule": {"lun": [{"start": "09:00", "end": "13:00"}], "mar": [{"start": "09:00", "end": "13:00"}], "mer": [], "gio": [{"start": "09:00", "end": "13:00"}], "ven": [], "sab": []}},
    {"id":2,"name": "Croce Rossa", "contact": "info@cri.it", "phone": "02-5551234",
     "address": "Via Salute 10, Milano", "sector": "Sanitario", "site": "cri.it",
     "capacity": 6, "tutor": "Giulia Verdi", "tutor_phone": "333-3333333",
     "schedule": {"lun": [], "mar": [{"start": "08:00", "end": "14:00"}], "mer": [{"start": "08:00", "end": "14:00"}], "gio": [], "ven": [{"start": "08:00", "end": "14:00"}], "sab": []}},
]
demo_students = [
    {
        "email": "giacomo.bruni@fermi.mo.it",
        "password": "psw",
        "choices": ["Caritas", "Legambiente", "Croce Rossa"],
        "assigned_entity":None
    },
    {
        "email": "arianna.tagliavini@fermi.mo.it",
        "password": "psw",
        "choices": ["Legambiente", "Croce Rossa", "Caritas"],
        "assigned_entity":None
    }
]
products = [
            {"id": 1, "nome": "Telefono", "categoria": "Elettronica", "prezzo": 299.99, "disponibile": True},
            {"id": 2, "nome": "Maglietta", "categoria": "Abbigliamento", "prezzo": 19.99, "disponibile": False},
        ]
class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("login.html", error=None)

    def post(self):
        username = self.get_body_argument("username")
        password = self.get_body_argument("password")

        # login semplice (hardcoded)
        if username == "admin" and password == "":
            self.set_secure_cookie("user", "admin")
            self.redirect("/home")
        elif username == "ari" and password == "":
            self.set_secure_cookie("user", "studente")
            self.redirect("/products")
        elif username == "ref" and password == "":
            self.set_secure_cookie("user", "referente")
            self.redirect("/products")
        else:
            self.render("login.html", error="Sei scemo")

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")

        if not user:
            self.redirect("/login")
            return

        self.render("home.html", user=user.decode())

class MainHandler(tornado.web.RequestHandler):
    def get(self):

#prendo la categoria e la disponibilità del prodotto dalla query string, trasformo disponibile da on o off a True o False
#nei controlli sotto trovo il prodotto in base alla categoria e la disponibilità
#finiti i controlli riordino e tolgo i doppioni dalla lista di prodotti

        categoria = self.get_query_argument("categoria", None)
        disponibile = self.get_query_argument("disponibile", None)

        if disponibile== "on":
            disponibile = True
        elif disponibile == "off":
            disponibile = False

        if categoria and disponibile:
            filtered_tasks = [t for t in products if t["categoria"] == categoria and t["disponibile"] == disponibile]

        elif categoria:
            filtered_tasks = [t for t in products if t["categoria"] == categoria]

        elif disponibile == True :
            filtered_tasks = [t for t in products if t["disponibile"] == disponibile]

        else:
            filtered_tasks = products


        categories = sorted(set(t["categoria"] for t in products)) if products else []  # set elimina i doppioni da qualsiasi tipo di variabile
        print(categories)
        print(categoria)
        print(filtered_tasks)
        self.render("index.html", products=filtered_tasks, categories=categories, selected=categoria,solo_disponibile=disponibile)

class AddEnteHandler(tornado.web.RequestHandler):
    def get(self):
#pubblico la pagina add_edit.html
        self.render("add_edit.html",nome=None)

    def post(self):
#prendo il valore delle variabili del nuovo prodotto, creo il nuovo prodotto, e ritorno alla pagina iniziale(/products)
        nome = self.get_body_argument("nome")
        prezzo = self.get_body_argument("prezzo")
        if self.get_body_argument("disponibile", None):
            disponibile = True
        else:
            disponibile = False
        categoria = self.get_body_argument("categoria")

        #valori base alle variabili
        id=1
        lista=[]
        #vado a creare una lista con gli id già utilizzati
        for product in products:
            lista.append(product["id"])
        #scorro la variabile fino a che trovo una non corrispondenza con un id già utilizzato
        while id < len(lista)+2:
            if id in lista:
                id = id+1
            else:
                break
        new_product = {"id":id,"nome":nome,"categoria":categoria,"prezzo":prezzo,"disponibile":disponibile}
        products.append(new_product)
        self.redirect("/products")

class EditEnteHandler(tornado.web.RequestHandler):
    def get(self,id):
#contorllo se id del prodotto che voglio modificare c'è nella lista e prendo le variabili del prodotto da modificare
        id=int(id)
        print(id)
        for ente in demo_entities:
            if ente["id"] == id:
                nome = ente["name"]
                contact = ente["contact"]
                phone = ente["phone"]
                address = ente["address"]
                sector = ente["sector"]
                site = ente["site"]
                capacity = ente["capacity"]
                tutor = ente["tutor"]
                tutor_phone = ente["tutor_phone"]
                schedule = ente["schedule"]

    # pubblico la pagina add_edit.html, con le variabili modificate
        self.render("add_edit.html", nome=nome,categoria=categoria,prezzo=prezzo,disponibile=disponibile,id=id)

    def post(self,id):
#prendo i valori delle variabili modificate e cercando dall'id del prodotto, sostituisco i valori di ogni variabile e ritorno alla pagina iniziale(/products)
        nome = self.get_body_argument("nome")
        prezzo = self.get_body_argument("prezzo")
        if self.get_body_argument("disponibile", None):
            disponibile = True
        else:
            disponibile = False
        categoria = self.get_body_argument("categoria")
        id=int(id)
        for product in products:
            if product["id"] == id:
                product["nome"] = nome
                product["prezzo"] = prezzo
                product["disponibile"] = disponibile
                product["categoria"] = categoria
        self.redirect("/products")

class DeleteEnteHandler(tornado.web.RequestHandler):
#cerco prodotto in base al suo id e lo elimino dalla lista dei prodotti e ritorno alla pagina iniziale(/products)
    def post(self,id):
        id=int(id)
        for product in products:
            if product["id"] == id:
                products.remove(product)
        self.redirect("/products")


class EnteHandler(tornado.web.RequestHandler):
    def get(self):
        enti=demo_entities
        # pubblico la pagina add_edit.html, con le variabili modificate
        self.render("visualizza_enti.html", enti=enti)


def make_app():
    return tornado.web.Application([
        (r"/login", LoginHandler),
        (r"/home", HomeHandler),
        (r"/studente/scelta", HomeHandler),
        (r"/studente/scelta/enti", HomeHandler),
        (r"/studente/scelta/enti/([0-9]+)", HomeHandler),
        (r"/studente/scelta/ente", HomeHandler),
        (r"/studente/questionario", HomeHandler),
        (r"/products", MainHandler),
        (r"/ente", EnteHandler),
        (r"/enti/add", AddEnteHandler),
        (r"/enti/edit/([0-9]+)", EditEnteHandler),
        (r"/enti/delete/([0-9]+)", DeleteEnteHandler)
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