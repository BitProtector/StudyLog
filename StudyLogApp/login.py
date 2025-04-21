# login.py
from textual.screen import Screen
from textual.widgets import Input, Button, Label
from textual.containers import Container, Horizontal
from textual.validation import Function
from textual import on
import sqlite3, re
from StudyLogApp.db import check_user, add_user, initialize_db
from StudyLogApp.utils import MessageBox

class LoginScreen(Screen):
    CSS = """
            Screen {
                align: center middle;
                background: $surface;
            }
            #login_box {
                width: 40%;
                padding: 2 4;
                layout: vertical;
                align: center middle;
                background: $background;
                border: none;
            }
            #login_frame {
                border: round $accent;
                padding: 1 2;
                layout: vertical;
                align: center middle;
                width: 100%;
            }
            #login_title {
                content-align: center middle;
                margin-bottom: 1;
            }
            #login_buttons {
                layout: horizontal;
                content-align: center middle;

            }
            Input {
                width: 100%;
                margin: 1 0;
            }

            #login_buttons Button {
                width: 48%;
                margin: 1 1 0 0;
                margin: 0 1;
            }
    """

    def compose(self):
        # Äussere Box, zentriert im Screen
        with Container(id="login_box"):
            # Eingabefelder
           
            # Rahmen um Titel und Buttons
            with Container(id="login_frame"):
                yield Label("Anmeldung", id="login_title")
                yield Input(placeholder="Benutzer", id="user", validators=[Function(self.validate_username, "Bitte nur Buchstaben [a-z] [A-Z] verwenden.")])
                yield Input(placeholder="Passwort", password=True, id="pw")
                with Horizontal(id="login_buttons"):
                    yield Button("Einloggen", id="login")
                    yield Button("Registrieren", id="register")

    def validate_username(self, string):
        try:
            return not re.search(r"[^A-Za-z0-9]", string)
        except ValueError:
            return False


    @on(Button.Pressed, "#login")
    def do_login(self):
        u = self.query_one("#user", Input).value.strip()
        p = self.query_one("#pw", Input).value
        db_path = check_user(u, p)
        if db_path:
            # Session‑Daten merken
            self.app.session["username"] = u
            self.app.session["db_path"] = db_path
            initialize_db(db_path)        # legt User‑DB an falls noetig
            self.app.push_screen("study_design")
        else:
            self.app.bell()               # PW falsch

    @on(Button.Pressed, "#register")
    def do_register(self):
        u = self.query_one("#user", Input).value.strip()
        p = self.query_one("#pw", Input).value
        if u == "" or p == "":
            self.parent.push_screen(MessageBox("Bitte beide Felder ausfüllen.", 
                                               [[Button("ok", id="close", variant="success"), False]]
                                               ))
            return
        if not self.validate_username(u):
            self.parent.push_screen(MessageBox("Bitte nur Buchstaben und Zahlen [a-z] [A-Z] [0-9] verwenden.", 
                                               [[Button("ok", id="close", variant="success"), False]]
                                               ))
            return
    
        try:
            add_user(u, p)
            self.app.push_screen("login") # zurück zum Login
        except sqlite3.IntegrityError:
            self.parent.push_screen(MessageBox("Benutzer bereits vorhanden.", 
                                               [[Button("ok", id="close", variant="success"), False]]
                                               ))
