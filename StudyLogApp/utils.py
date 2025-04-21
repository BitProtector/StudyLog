from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.containers import Container, Horizontal
from textual import on

def running_in_web(app) -> bool:
    """True, falls Textual als Web‑Server laeuft (textual run ... --port)."""
    # Ab 0.45 besitzt App.web ein Driver‑Objekt; auf dem Desktop ist es None
    return app.is_web


# -----------------------------------------------------------------------------
# Parser-Funktionen für float und int
# -----------------------------------------------------------------------------
def parse_float(value: str):
    """Gibt None zurück, wenn value leer ist, sonst wird versucht, in float umzuwandeln."""
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None

def parse_int(value: str):
    """Gibt None zurück, wenn value leer ist oder kein int darstellt."""
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None

# -----------------------------------------------------------------------------
# Modal Screen für Nachrichten (MessageBox)
# -----------------------------------------------------------------------------
class MessageBox(ModalScreen):
    """Ein modaler Dialog zur Anzeige von Nachrichten."""
    DEFAULT_CSS = """
    MessageBox {
        align: center middle;
    }
    MessageBox > Container {
        width: auto;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }
    MessageBox > Container > Label {
        width: 100%;
        content-align-horizontal: center;
        margin-top: 1;
    }
    MessageBox > Container > Horizontal {
        width: auto;
        height: auto;
    }
    MessageBox > Container > Horizontal > Button {
        margin: 2 4;
    }
    """
    
    def __init__(self, message, button_list=[], name=None, id=None, classes=None):
        super().__init__(name, id, classes)
        self.message = message
        # Buttons werden in folgendem Format erwartet:
        # [[Button_object, callback_func], [Button_object, callback_func], usw...]
        self.button_list = button_list

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self.message)
            with Horizontal():
                for button, callback in self.button_list:
                    yield button                    
    
    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
        for button, callback in self.button_list:
            if button.id == event.button.id and callback:
                callback()
                break
