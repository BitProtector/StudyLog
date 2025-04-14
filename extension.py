import random
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.reactive import reactive
from textual.timer import Timer
from textual import events


class DinoGameWidget(Static):
    """
    Einfaches Jump-and-Run-Spiel. Wir simulieren hier den "Dino" als '@' Symbol,
    das ueber Hindernisse in Form von "|" Symbolen springen kann.
    """

    # Spielparameter
    gravity = 1                # "Fallgeschwindigkeit"
    jump_velocity = 10        # Anfangsgeschwindigkeit beim Springen
    obstacle_speed = 1         # Geschwindigkeit mit der Hindernisse nach links wandern
    obstacle_frequency = 30    # Anzahl "Frames" bis neues Hindernis erscheint

    # Reaktive Variablen, die sich aendern und automatisch ein Neuzeichnen anstossen
    player_y = reactive(0)        # Position des Dinos
    player_velocity = reactive(0) # vertikale Geschwindigkeit
    score = reactive(0)           # Anzahl ueberstandener Frames
    is_game_over = reactive(False)

    def __init__(self):
        super().__init__()
        self.floor_y = 0   # "Boden" (einfache Version: wir liegen auf Zeile 0)
        self.obstacles = []  # Liste der Hindernisse
        self.frames_since_last_obstacle = 0
        self.ground_char = "_"  # Bodenanzeige

    def on_mount(self) -> None:
        """Diese Methode wird aufgerufen, sobald das Widget in die App eingebunden wird."""
        self.reset()
        # Regelmaessige Updates mit 60Hz (ca. alle 16ms)
        self.set_interval(1/60, self.game_loop)

    def reset(self):
        # Dino startet auf dem Boden
        self.player_y = self.floor_y
        self.player_velocity = 0
        self.score = 0
        self.is_game_over = False
        self.obstacles.clear()

    def game_loop(self) -> None:
        """Wird 60 mal pro Sekunde aufgerufen und aktualisiert den Spielzustand."""
        if self.is_game_over:
            return

        # Dino-Physik aktualisieren
        self.player_velocity -= self.gravity
        self.player_y += (self.player_velocity/10)

        # Absturz verhindern (Boden)
        if self.player_y <= self.floor_y:
            self.player_y = self.floor_y
            self.player_velocity = 0

        # Hindernisse erzeugen
        self.frames_since_last_obstacle += 1
        if self.frames_since_last_obstacle >= self.obstacle_frequency:
            self.obstacle_frequency = random.randint(10,50)
            self.frames_since_last_obstacle = 0
            # Wir platzieren das Hindernis rechts ausserhalb des Bildschirms
            # x-Position -> Start bei groesserem Wert
            new_obstacle_x = self.size.width - 2
            self.obstacles.append([new_obstacle_x])

        # Hindernisse bewegen
        for obstacle in self.obstacles:
            obstacle[0] -= self.obstacle_speed

        # Kollisionspruefung & Entfernen von Hindernissen ausserhalb des Bildschirms
        active_obstacles = []
        for obstacle in self.obstacles:
            x_pos = obstacle[0]
            # Falls Hindernis noch im Sichtbereich ist, behalten
            if x_pos >= 0:
                active_obstacles.append(obstacle)
            # Kollisionspruefung: Falls Dino und Hindernis gleiche X-Koordinate (gerundet)
            # und der Dino gerade am Boden ist, werten wir das als Kollision
            if round(x_pos) == 20 and self.player_y <= 0:
                self.game_over()

        self.obstacles = active_obstacles

        # Score erhoehen
        self.score += 1

        # Fuer das Textual-Widget wird ein Neuzeichnen angetriggert
        self.refresh()

    def game_over(self) -> None:
        """Setzt den Spielzustand auf 'Game Over'."""
        self.is_game_over = True

    def render(self) -> str:
        """
        Gibt den Bildschirm-Inhalt als Text zurueck.
        Die obere Zeile: Score
        Darunter: Darstellung des Spielgeschehens
        """
        if self.is_game_over:
            return (
                f"Score: {self.score}\n"
                f"\n"
                f"GAME OVER!\n"
                f"Druecke 'R' fuer Neustart.\n"
            )

        # Wir bauen den Bildschirm von oben nach unten.
        # 1) Score-Zeile
        output_lines = [f"Score: {self.score}"]

        # 2) Spielbereich (1 Zeile fuer Dino und Hindernisse)
        #    - Dino ist an x=2 positioniert
        #    - Hindernisse werden durch x-Position in self.obstacles bestimmt
        #    - Falls Dino in der Luft ist, zeichnen wir ihn in der oberen Zeile
        #      (vereinfachter 2-Zeilen-Spielbereich)
        game_area_height = 20
        # Erstelle leere Zeilen
        lines = [[" " for _ in range(self.size.width)] for _ in range(game_area_height)]

        # Bodenzeile = Index 0 (unterste Zeile), obere Zeile = Index 1
        dino_row = 0
        if self.player_y > 0:
            dino_row = int(self.player_y)

        # Dino zeichnen
        dino_x = 20
        if dino_x < self.size.width:
            lines[dino_row][dino_x] = "@"

        # Hindernisse platzieren
        for obstacle in self.obstacles:
            x_pos = round(obstacle[0])
            if 0 <= x_pos < self.size.width:
                # obstacle nur auf Bodenebene
                lines[0][x_pos] = "|"

        # Zeilen zusammenfassen
        for row in reversed(lines):
            output_lines.append("".join(row))

        # 3) Boden darstellen (untere Linie)
        #    (Optional, hier nur als einfache Darstellung)
        output_lines.append(self.ground_char * self.size.width)

        return "\n".join(output_lines)

class GameView(Screen):
    """
    Zeigt Module getrennt nach Semester an.
    Für jedes Semester wird eine DataTable erstellt.
    """

    def __init__(self):
        super().__init__()


    def compose(self) -> ComposeResult:
        self.dino_game = DinoGameWidget()
        yield self.dino_game

class DinoGameApp(App):
    """Die eigentliche App, in die das Spiel-Widget eingebaut wird."""

    CSS_PATH = None  # Keine CSS-Datei notwendig

    BINDINGS = [
        ("q", "quit", "Quit game"),
        ("space", "jump", "Jump"),
        ("up", "jump", "Jump"),
        ("r", "restart", "Restart"),
        ("enter", "restart", "Restart"),
    ]

    def compose(self) -> ComposeResult:
        self.dino_game = DinoGameWidget()
        yield self.dino_game

    def action_quit(self):
        self.exit()

    def action_jump(self):
        # analog zu on_key("space"/"up") ...
        if not self.dino_game.is_game_over and self.dino_game.player_y == self.dino_game.floor_y:
            self.dino_game.player_velocity = self.dino_game.jump_velocity

    def action_restart(self):
        # analog zu on_key("r"/"enter") ...
        if self.dino_game.is_game_over:
            self.dino_game.reset()


def run_dino_game():
    app = DinoGameApp()
    app.run()


if __name__ == "__main__":
    run_dino_game()
