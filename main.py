from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Button, Label, DataTable, Select
from textual.containers import VerticalScroll, HorizontalScroll, Container, Horizontal
from textual import on

from textual_plotext import PlotextPlot
from plotext._figure import _figure_class

from StudyLogApp.extension import GameView
from StudyLogApp.calculate import compute_final_grade
from StudyLogApp.utils import running_in_web, parse_int, parse_float, MessageBox
from StudyLogApp.db import initialize_db, init_auth_db, DB_PATH
from StudyLogApp.login import LoginScreen

import json, sqlite3

from rich.text import Text
from rich.panel import Panel

from collections import defaultdict



# -----------------------------------------------------------------------------
# View: StudyDesignView (Modul Import, Anlegen, Löschen und Update)
# -----------------------------------------------------------------------------
class StudyDesignView(Screen):
    """Ermöglicht das Importieren, Hinzufügen, Updaten und Löschen von Modulen."""
    CSS = """
    Screen {
        align: center middle;
    }
    VerticalScroll, HorizontalScroll {
        height: 1fr;
        border: solid dodgerblue;
        align: center top;
    }
    Button {
        width: 100%;
    }
    Label {
        width: 100%;
        text-align: center;
    }
    #study_log {
        height: 20%;
    }
    """

    def __init__(self, name = None, id = None, classes = None):
        super().__init__(name, id, classes)
        self.ignore_dependencies=[]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll():
            with HorizontalScroll():
                with VerticalScroll():
                    yield Label("--- Import von Modulen über JSON-Datei ---")
                    yield Button("JSON Import", id="json_import")
                    yield Label("--- Manuelles Anlegen von Modulen ---")
                    yield Input(placeholder="Modulname", id="module_name_input")
                    yield Input(placeholder="Modulbezeichnung", id="module_desc_input")
                    yield Input(placeholder="ECTS", id="module_ects_input")
                    yield Input(placeholder="Semester (1-8)", id="module_semester_input")
                    yield Button("Modul hinzufügen", id="add_module")
                with VerticalScroll():
                    yield Label("--- Module löschen ---")
                    yield Input(placeholder="Modulname", id="delete_module_input")
                    yield Button("Modul löschen", id="delete_module")
                with VerticalScroll():
                    yield Label("--- Module zuweisen ---")
                    yield Select(((str(i) if not i == 9 else "Anrechnung", i) for i in range(0,10)), id="update_semester_input")
                    yield Input(placeholder="Modulname", id="update_module_input")
                    #yield Input(placeholder="Neues Semester (1-8)", id="update_semester_input")
                    yield Button("Update Semester", id="update_semester")
            yield DataTable(id="study_log")
        yield Footer()

    def on_mount(self) -> None:
        # Initialisiere leere Log-Tabelle
        table = self.query_one("#study_log", DataTable)
        table.add_columns("Name", "Bezeichnung", "ECTS", "Semester")
        table.clear()

    def on_screen_resume(self) -> None:
        self.show_modules()

    async def on_input_changed(self, event: Input.Changed) -> None:
        self.show_modules(event.value.lower())
        # Lösche die Liste zum Ignorieren der Modulabhängigkeiten, 
        # da beim betrachten von anderen Modulen die Abhängigkeiten wieder betrachtet werden müssen.
        self.ignore_dependencies.clear()

    @on(Button.Pressed)
    def handle_buttons(self, event: Button.Pressed) -> None:
        if event.button.id == "json_import":
            self.import_json()
            self.show_modules()
        elif event.button.id == "add_module":
            self.add_module()
            self.show_modules()
        elif event.button.id == "delete_module":
            self.delete_module()
            self.show_modules()
        elif event.button.id == "update_semester":
            self.update_semester()
            self.show_modules()

    def import_json(self):
        if running_in_web(self.parent):
            file_path = "Module v2.json"
        else:
            # Für den Dateidialog
            import tkinter
            from tkinter.filedialog import askopenfilename
            """öffnet einen Dateidialog, liest ein JSON ein und fügt neue Module (ohne Duplikate) ein."""
            root = tkinter.Tk()
            root.withdraw()

            file_path = askopenfilename(
                title="JSON Datei auswählen",
                filetypes=[("JSON Files", "*.json"), ("Alle Dateien", "*.*")]
            )
            root.destroy()

        if not file_path:
            return  # Abbruch, wenn keine Datei ausgewählt

        with open(file_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                return  # Ungültiges JSON

        with sqlite3.connect(self.app.db()) as conn:
            cursor = conn.cursor()
            if isinstance(data, list):
                for module in data:
                    mod_id = module.get("id") or 0
                    name = module.get("bezeichnung") or ""
                    description = module.get("name") or ""
                    beschreibung = module.get("description") or ""
                    msp = module.get("hasMsp") or ""
                    assessment = 1 if (module.get("assessment") or 0) else 0 
                    ects = module.get("ects") or 0
                    dependencies = module.get("dependingModulesIDs", {}) or []
                    if not name:
                        continue
                    if not id:
                        continue
                    cursor.execute("SELECT 1 FROM module WHERE name = ?", (name,))
                    if cursor.fetchone():
                        # Modul bereits vorhanden
                        cursor.execute(
                            "UPDATE module SET mod_id = ?, description = ?, beschreibung = ?, assessment = ?, msp = ?, ects = ?, dependencies = ? WHERE name == ?",
                            (mod_id, description, beschreibung, assessment, msp, ects, json.dumps(dependencies), name)
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO module (mod_id, name, description, beschreibung, assessment, msp, ects, dependencies, semester) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)",
                            (mod_id, name, description, beschreibung, assessment, msp, ects, json.dumps(dependencies))
                        )
            conn.commit()

    def add_module(self):
        """Fügt ein neues Modul in die Datenbank ein."""
        name = self.query_one("#module_name_input", Input).value.strip()
        description = self.query_one("#module_desc_input", Input).value.strip()
        ects = parse_int(self.query_one("#module_ects_input", Input).value)
        semester_str = self.query_one("#module_semester_input", Input).value
        semester_val = parse_int(semester_str)
        if not name:
            return
        if semester_val is None or semester_val < 1 or semester_val > 9:
            semester_val = 0

        with sqlite3.connect(self.app.db()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO module (name, description, ects, dependencies, semester) VALUES (?, ?, ?, ?, ?)",
                (name, description, ects, json.dumps([]), semester_val)
            )
            conn.commit()

    def delete_module(self):
        """Löscht ein Modul und assoziierte Grades aus der Datenbank."""
        delete_module_name = self.query_one("#delete_module_input", Input).value
        if not delete_module_name:
            return
        with sqlite3.connect(self.app.db()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM module WHERE name = ?", (delete_module_name,))
            result = cursor.fetchone()
            if result is None:
                return  # Modul nicht gefunden
            module_id = result[0]
            cursor.execute("DELETE FROM grades WHERE module_id = ?", (module_id,))
            cursor.execute("DELETE FROM module WHERE name = ?", (delete_module_name,))
            conn.commit()

    def update_semester(self):
        """Updated das Semester eines Moduls unter Prüfung von Abhängigkeiten."""
        module_name = self.query_one("#update_module_input", Input).value
        semester_val = self.query_one("#update_semester_input", Select).value
        if not module_name:
            return
        
        if semester_val == Select.BLANK:
            return
        
        if semester_val is None or semester_val < 1 or semester_val > 9:
            semester_val = 0
        
        with sqlite3.connect(self.app.db()) as conn:
            cursor = conn.cursor()
            # Abhängigkeiten aus Spalte dependencies lesen
            cursor.execute("SELECT dependencies FROM module WHERE name = ?", (module_name,))
            row = cursor.fetchone()
            if row is not None and row[0]:
                dependencies = json.loads(row[0])
            else:
                dependencies = []
            
        # Prüfe alle Abhängigkeiten
        for dependency in dependencies:
            cursor.execute("SELECT semester, name FROM module WHERE mod_id = ?", (dependency,))
            row_dep = cursor.fetchone()
            if row_dep is None or ((row_dep[0] > semester_val or row_dep[0] == 0) and semester_val != 0):
                if not dependency in self.ignore_dependencies:
                    # Definiere Call-Back Funktion für MsgBox, welche bei "Ignorieren" aufgerufen werden kann
                    def ignore_dependency():
                        self.ignore_dependencies.append(dependency)
                        # Führe diese funktion nochmals aus.
                        self.update_semester()
                    self.parent.push_screen(MessageBox(f"Modul erfuellt nicht alle Bedingungen! \nZuerst {row_dep[1]} erfüllen.", 
                                                        [
                                                            [Button("Abbrechen", id="close", variant="success"), False],
                                                            [Button("Ignorieren", id="acknowledge", variant="warning"), ignore_dependency]
                                                        ]
                                                        ))
                    return
        # Lösche die Liste zum Ignorieren der Modulabhängigkeiten, 
        # da beim betrachten von anderen Modulen die Abhängigkeiten wieder betrachtet werden müssen.
        self.ignore_dependencies.clear()

        with sqlite3.connect(self.app.db()) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE module SET semester = ? WHERE UPPER(name) = UPPER(?)", (semester_val, module_name))
            conn.commit()

        self.query_one("#update_module_input", Input).clear()
        self.query_one("#update_semester_input", Select).clear()

    def show_modules(self, filter_text=""):
        """Liest die Module aus der DB und zeigt sie in der Log-Tabelle an."""
        log_table = self.query_one("#study_log", DataTable)
        log_table.clear()
        with sqlite3.connect(self.app.db()) as conn:
            cursor = conn.cursor()
            if filter_text:
                cursor.execute(
                    "SELECT name, description, ects, dependencies, semester FROM module WHERE name LIKE ? ORDER BY name COLLATE NOCASE ASC",
                    (f"%{filter_text}%",)
                )
            else:
                cursor.execute("SELECT name, description, ects, dependencies, semester FROM module ORDER BY name COLLATE NOCASE ASC")
            rows = cursor.fetchall()
            for row in rows:
                name, description, ects, dependencies, semester = row
                sem_display = "---" if semester is None or semester == 0 else str(semester)
                log_table.add_row(name, description, str(ects), sem_display)

# -----------------------------------------------------------------------------
# View: GradeEntryView (Noten Eingabe)
# -----------------------------------------------------------------------------
class GradeEntryView(Screen):
    CSS = """
    Screen {
        align: center middle;
    }
    VerticalScroll, HorizontalScroll {
        height: 1fr;
        border: solid dodgerblue;
        align: center top;
    }
    Button {
        width: 100%;
    }
    Label {
        width: 100%;
        text-align: center;
    }
    Input {
        width: 40%;
        text-align: center;
    }
    .entry_label {
        margin: 1;
        width: 20;
        text-align: left;
    }
    .entry_box {

        align: left top;
    }
    """
    def compose(self) -> ComposeResult:
        calc_type = [
            "25 - 25 - 50 - (EN-Noten 1 zu 1, EN und MSP 1 zu 1)",
            "1/3 - 2/3 - 50 - (EN-Noten 1/3 zu 2/3, EN und MSP 1 zu 1)",
            "(25 - 25) - 50 - (EN-Noten 1 zu 1, EN und MSP 1 zu 1) wenn EN > als MSP sonnst MSP",
            "Spezifische Gewichtungen"
        ]
        yield Header(show_clock=True)
        with VerticalScroll():
            yield Label("Noten Eingabe")
            yield Select((), id="module_select")
            yield Select(((text, value) for value, text in enumerate(calc_type)), id="calc_type")
            with HorizontalScroll(classes="entry_box"):
                yield Label("Klausur 1", classes="entry_label")
                yield Input(placeholder="K1", id="input_k1")
                yield Input(placeholder="K1 Gewicht", id="input_k1_weight")
            with HorizontalScroll(classes="entry_box"):
                yield Label("Klausur 1", classes="entry_label")
                yield Input(placeholder="K2", id="input_k2")
                yield Input(placeholder="K2 Gewicht", id="input_k2_weight")
            with HorizontalScroll(classes="entry_box"):
                yield Label("Modulschluss Prüfung", classes="entry_label")
                yield Input(placeholder="MSP", id="input_msp")
                yield Input(placeholder="MSP Gewicht", id="input_msp_weight")
            yield Button("Speichern", id="save_grade")
        yield Footer()

    def on_screen_resume(self) -> None:
        fields = ["k1", "k2", "msp"]
        for i in fields:
            self.query_one("#input_"+ i, Input).visible = False
            self.query_one("#input_"+ i +"_weight", Input).visible = False
        self.query_one("#calc_type", Select).visible = False
            

        """Lädt alle Module (Semester 1-9) in das Select-Feld."""
        with sqlite3.connect(self.app.db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT name
                FROM module
                WHERE semester BETWEEN 1 AND 9
                ORDER BY semester, name
            ''')
            rows = cursor.fetchall()
        select_widget = self.query_one("#module_select", Select)
        select_widget.set_options((module[0], module[0]) for module in rows)

    @on(Button.Pressed)
    def save_grade(self, event: Button.Pressed) -> None:
        if event.button.id != "save_grade":
            return
        values = {
            "module_name": self.query_one("#module_select", Select).value,
            "k1": parse_float(self.query_one("#input_k1", Input).value),
            "k1_weight": parse_float(self.query_one("#input_k1_weight", Input).value),
            "k2": parse_float(self.query_one("#input_k2", Input).value),
            "k2_weight": parse_float(self.query_one("#input_k2_weight", Input).value),
            "msp": parse_float(self.query_one("#input_msp", Input).value),
            "msp_weight": parse_float(self.query_one("#input_msp_weight", Input).value),
            "calc_type": self.query_one("#calc_type", Select).value,
        }
        if self.query_one("#module_select", Select).value == Select.BLANK:
            self.parent.push_screen(MessageBox("Kein Modul ausgewahlt!", 
                                               [[Button("ok", id="close", variant="success"), False]]
                                               ))
            return
        
        with sqlite3.connect(self.app.db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id
                FROM module
                WHERE name == ?
            ''', (values["module_name"],))
            result = cursor.fetchone()
            if result is None:
                self.parent.push_screen(MessageBox("Modul nicht gefunden!", 
                                                   [[Button("ok", id="close", variant="success"), False]]
                                                   ))
                return
            module_id = result[0]
            cursor.execute(
                '''INSERT OR REPLACE INTO grades
                   (module_id, k1, k2, k1_weight, k2_weight, msp, msp_weight, calc_type)
                   VALUES (?, ?, ?, ?, ?, ?, ?,?)''',
                (
                    module_id,
                    values["k1"],
                    values["k2"],
                    values["k1_weight"],
                    values["k2_weight"],
                    values["msp"],
                    values["msp_weight"],
                    values["calc_type"]
                )
            )
            conn.commit()
        # Leere die Eingabefelder
        self.query_one("#input_k1", Input).clear()
        self.query_one("#input_k1_weight", Input).clear()
        self.query_one("#input_k2", Input).clear()
        self.query_one("#input_k2_weight", Input).clear()
        self.query_one("#input_msp", Input).clear()
        self.query_one("#input_msp_weight", Input).clear()
        self.query_one("#module_select", Select).clear()
        self.query_one("#calc_type", Select).clear()

    @on(Select.Changed)
    def on_module_change(self, event: Select.Changed):
        if event.control.id == "module_select":
            """Lädt zuletzt gespeicherte Noten für das ausgewählte Modul."""
            if self.query_one("#module_select", Select).value == Select.BLANK:
                return
            with sqlite3.connect(self.app.db()) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT
                        g.k1,
                        g.k2,
                        g.k1_weight,
                        g.k2_weight,
                        g.msp,
                        g.msp_weight,
                        g.calc_type
                    FROM module m
                    LEFT JOIN grades g ON m.id = g.module_id
                    AND g.id = (
                        SELECT MAX(id)
                        FROM grades
                        WHERE module_id = m.id
                    )
                    WHERE m.name == ?
                    ORDER BY m.semester, m.name
                ''', (event.value,))
                result = cursor.fetchone()
                if result:
                    k1, k2, k1_weight, k2_weight, msp, msp_weight,calc_type = result
                    fields = {"k1":k1, "k2":k2, "k1_weight":k1_weight, "k2_weight":k2_weight, "msp":msp, "msp_weight":msp_weight}
                    for key in fields:
                        self.query_one("#input_" + str(key), Input).value = str(fields.get(key)) if fields.get(key) != None else ""
                    self.query_one("#calc_type", Select).value = calc_type if calc_type != None else 0
                    fields = ["k1", "k2", "msp"]
                    for i in fields:
                        self.query_one("#input_"+ i, Input).visible = True
                        self.query_one("#input_"+ i +"_weight", Input).visible = (self.query_one("#calc_type", Select).value == 3)

                    self.query_one("#calc_type", Select).visible = True
        else:
            fields = ["k1", "k2", "msp"]
            for i in fields:
                self.query_one("#input_"+ i +"_weight", Input).visible = (self.query_one("#calc_type", Select).value == 3)

# -----------------------------------------------------------------------------
# View: DisplayView (Anzeige der Module pro Semester)
# -----------------------------------------------------------------------------
class DisplayView(Screen):
    """
    Zeigt Module getrennt nach Semester an.
    Für jedes Semester wird eine DataTable erstellt.
    """
    CSS = """
    .Header2 {
        align: center middle;
        height: 3;
    }
    .Grade_sum {
        align: right middle;
        height: 3;
        border: none;
        margin-right: 1;
    }
    .ECTS_sum {
        align: left middle;
        height: 3;
        border: none;
        margin-left: 1;
    }
    .Grade_sum Label {
        width: 100%;
        text-align: right;
    }
    """

    def __init__(self):
        super().__init__()
        # Container für dynamisch erzeugte Tabellen
        self.container = HorizontalScroll()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with HorizontalScroll(classes="Header2"):
            with VerticalScroll(classes="ECTS_sum"):
                yield Label ("Eingeplante ECTS-Punkte: xxx/180", id="ECTS_plan")
                yield Label ("Erreichte ECTS-Punkte:   xxx/180", id="ECTS_fix")
            with VerticalScroll(classes="Grade_sum"):
                yield Label("Notenschnitt: x.xx", id="grade_sum")
                yield Label("ToR:  x.x", id="tor")
        yield self.container
        yield Footer()

    def on_screen_resume(self) -> None:
        # Leere den Container, um Dopplungen zu vermeiden
        for child in list(self.container.children):
            child.remove()

        with sqlite3.connect(self.app.db()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    m.name,
                    m.semester,
                    m.assessment,
                    m.msp,
                    m.description,
                    g.k1,
                    g.k2,
                    g.k1_weight,
                    g.k2_weight,
                    g.msp,
                    g.msp_weight,
                    g.calc_type
                FROM module m
                LEFT JOIN grades g ON m.id = g.module_id
                  AND g.id = (
                    SELECT MAX(id)
                    FROM grades
                    WHERE module_id = m.id
                  )
                WHERE m.semester BETWEEN 1 AND 9
                ORDER BY m.semester, m.name
            ''')
            rows = cursor.fetchall()

        grade_table = VerticalScroll()
        self.container.mount(grade_table)

        # Gruppiere die Daten pro Semester
        data_per_semester = defaultdict(list)
        for (name, semester, assessment, msp, bezeichnung, k1, k2, k1_weight, k2_weight, mspn, msp_weight, calc_type) in rows:
            data_per_semester[semester].append((name, assessment, msp, bezeichnung, k1, k2, k1_weight, k2_weight, mspn, msp_weight, calc_type))

        for semester in range(1, 10):
            if not data_per_semester[semester]:
                continue

            grade_table.mount(Label(f"Semester {semester}" if not semester == 9 else f"Anrechnungen"))

            table = DataTable()
            table.add_columns("Modul", "AS", "MSP", "K1", "K2", "MSP", "EN", "Schnitt")

            for (name, assessment, msp, bezeichnung, k1, k2, k1_weight, k2_weight, mspn, msp_weight, calc_type) in data_per_semester[semester]:
                # Berechnung der Eingangsnote (EN) und Gesamtnote (final_average) je nach Berechnungstyp
                en, final_average = compute_final_grade(k1, k2, k1_weight, k2_weight, mspn, msp_weight, calc_type)

                # Formatierung der Werte zur Anzeige
                assessment_str = "x" if assessment == 1 else "-"
                msp_str = "x" if msp == 1 else "-"
                k1_str = f"{k1:.2f}" if k1 is not None else "-"
                k2_str = f"{k2:.2f}" if k2 is not None else "-"
                mspn_str = f"{mspn:.2f}" if mspn is not None else (f"? {3.75*2-en:.2f}" if (en is not None and msp==1) else "-")
                en_str = f"{en:.2f}" if en is not None else "-"
                average_str = f"{final_average:.2f}" if final_average is not None else "-"

                row = [name, assessment_str, msp_str, k1_str, k2_str, mspn_str, en_str, average_str]

                styled_row = []
                for idx, cell in enumerate(row):
                    if parse_float(cell) is None:
                        if cell == "x":
                            style = "#FF8C00"
                        elif idx == 0:
                            if (parse_float(row[-1]) is not None and parse_float(row[-1]) >= 3.75) or semester == 9:
                                style = "#03AC13"
                        else:
                            style = ""
                    elif parse_float(cell) >= 4.0:
                        style = "#03AC13"
                    elif cell[0] == "?":
                        style = "#AAAAAA"
                    else:
                        style = "#FF4500"
                    
                    styled_row.append(
                        Text(str(cell), style=style, justify="right") 
                    )
                table.add_row(*styled_row)

            grade_table.mount(table)
            grade_table.mount(Label(" "))
    
        self.render_visuals(data_per_semester)

    def render_visuals(self, data_per_semester):
        # ECTS und Durchschnittsverlauf vorbereiten
        semesters = []
        ects_values = []
        average_values = []
        heatmap_values = {}

        for semester in range(1, 10):
            semester_data = data_per_semester.get(semester, [])
            semesters.append(str(semester))

            ects = [0, 0, 0] # Norm-Modules, Projects, bestanden
            grades_in_sem = []
            for (name, assessment, msp, bezeichnung, k1, k2, k1_weight, k2_weight, mspn, msp_weight, calc_type) in semester_data:
                en, final_average = compute_final_grade(k1, k2, k1_weight, k2_weight, mspn, msp_weight, calc_type)
                with sqlite3.connect(self.app.db()) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT ects FROM module WHERE name = ?", (name,))
                    result = cursor.fetchone()
                    if result[0]:
                        if any(keyword in bezeichnung.lower() for keyword in ("projekt", "project")):
                            ects[1] += result[0]
                        else:
                            ects[0] += result[0]
                        if (final_average is not None and final_average >= 3.75) or semester == 9:
                            ects[2] += result[0]

                # final_average in Sammlung eintragen, falls definiert
                if final_average is not None:
                    grades_in_sem.append(final_average)

            avg = sum(grades_in_sem) / len(grades_in_sem) if grades_in_sem else 0
            ects_values.append(ects)
            average_values.append(avg)
            heatmap_values[semester]=(grades_in_sem if grades_in_sem else [0])
        
        all_avg = sum(average_values)/sum(1 for x in average_values if x != 0)
        all_ects = sum(sum(x[:2]) for x in ects_values)
        success_etcs = sum(x[2] for x in ects_values)
        self.query_one("#grade_sum", Label).update(f"Notenschnitt: {all_avg:.2f}")
        self.query_one("#tor", Label).update(f"ToR:  {all_avg:.1f}")
        self.query_one("#ECTS_plan", Label).update(f"Eingeplante ECTS-Punkte: {all_ects}/180")
        self.query_one("#ECTS_fix", Label).update(f"Erreichte ECTS-Punkte: {success_etcs}/180   -> {(success_etcs/1.8):.1f}%")

        # Visualisierung mit plotext vorbereiten
        visuals = VerticalScroll()
        self.container.mount(visuals)

        # Bar Chart ECTS
        plot1 = PlotextPlot()
        plot1.plt.title("ECTS pro Semester")
        values = [x[:2] for x in ects_values[:8]]
        plot1.plt.stacked_bar(semesters, [*zip(*values)], width = 0.3, color=[(3,172,19),32], labels=["Module", "Projekte"])
        plot1.plt.xlim(0, 9)
        plot1.plt.ylim(0, 5+max([sum(x) for x in values]))
        plot1.plt.yticks([i for i in range(0, 5+max([sum(x) for x in values]), 5)])
        [plot1.plt.text(value[0], y = value[0], x = parse_int(semesters[idx]), alignment = 'center', background=32 if value[1] != 0 else (3,172,19), color=255) for idx, value in enumerate([(sum(x), x[1]) for x in values])]
        
        visuals.mount(Label(""))
        visuals.mount(plot1)

        # Bar Chart Durchschnitt
        plot2 = PlotextPlot()
        plot2.plt.title("Notendurchschnitt pro Semester")
        plot2.plt.bar(semesters[:8], average_values[:8], orientation = "h", width = 0.001, color=32)
        plot2.plt.xlim(1, 6)
        # Werte der Balken anzeigen
        [plot2.plt.text(round(value,2), x = value, y = parse_int(semesters[idx]), alignment = 'right', background=32, color=255) for idx, value in enumerate(average_values[:8])]
        visuals.mount(Label(""))
        visuals.mount(plot2)

        visuals.mount(Label(""))
        visuals.mount(Label("Hinweise:"))
        # Infos
        # ECTS Warnungen
        for s, ects in zip(semesters, ects_values):
            ects_total = ects[0] + ects[1]
            if ects[0] + ects[1] < 15:
                visuals.mount(Label(f"Warnung: Semester {s} hat nur {ects_total} ECTS!", id=f"warn_{s}"))
        # Info Assessment
        ass_cnt = 0
        for s in semesters:
            for m in data_per_semester[int(s)]:
                if m[1] == 1: ass_cnt += 1
            if ass_cnt >= 9:
                visuals.mount(Label(f"Info: Ab dem Semester {s} ist das Assessment bestanden!", id=f"info_{s}"))
                break

# -----------------------------------------------------------------------------
# Haupt-App: StudyApp
# -----------------------------------------------------------------------------
class StudyApp(App):
    TITLE = "Studium App"
    CSS_PATH = None
    BINDINGS = [
        ("1", "switch_to_view('study_design')", "Studium Design"),
        ("2", "switch_to_view('grade_entry')", "Noten Eingabe"),
        ("3", "switch_to_view('display')", "Anzeige"),
        ("q", "quit", "Quit")
    ]

    def db(self) -> str:
        if running_in_web(self):
            return self.session.get("db_path", None)   # pro User
        return DB_PATH  

    def on_mount(self):
        self.session = {}
        if running_in_web(self):
            init_auth_db()                                 # erzeugt users.db
            self.install_screen(LoginScreen(),  name="login")
            # DB für App wird im Loginscreen angelegt, falls diese fehlt.
        else:
            initialize_db(DB_PATH)                        
        
        self.install_screen(StudyDesignView(), name="study_design")
        self.install_screen(GradeEntryView(), name="grade_entry")
        self.install_screen(DisplayView(), name="display")
        self.install_screen(GameView(), name="game")

        if running_in_web(self):
            self.push_screen("login")
        else:
            self.push_screen("study_design")

        self.easteregg_keys = "game"

    def action_switch_to_view(self, view_name: str) -> None:
        self.switch_screen(view_name)

    def on_key(self, event):
        if len(event.key) == 1:
            self.easteregg_keys = self.easteregg_keys[1:4] + event.key
            if self.easteregg_keys == "game":
                self.switch_screen("game")
        
        gamescreen = self.get_screen("game")
        if event.key == "space":
            if not gamescreen.dino_game.is_game_over and gamescreen.dino_game.player_y == gamescreen.dino_game.floor_y:
                gamescreen.dino_game.player_velocity = gamescreen.dino_game.jump_velocity
        if event.key == "r":
            if gamescreen.dino_game.is_game_over:
                        gamescreen.dino_game.reset()

if __name__ == "__main__":
    StudyApp().run()
