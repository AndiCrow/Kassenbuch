import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from datetime import datetime

# Name der CSV-Datei, in der die Einträge gespeichert werden
FILE_NAME = "kassenbuch.csv"

# Funktion zum Hinzufügen eines Eintrags und Speichern in CSV
def add_entry(date_entry, desc_entry, netto_entry, mwst_entry, brutto_entry, listbox, total_label):
    date_value = date_entry.get()
    desc_value = desc_entry.get()
    netto_value = netto_entry.get()
    mwst_value = mwst_entry.get()
    brutto_value = brutto_entry.get()

    if date_value and desc_value and netto_value and mwst_value and brutto_value:
        try:
            brutto_value_float = float(brutto_value)
        except ValueError:
            print("Fehler: Brutto Betrag muss eine Zahl sein.")
            return

        entry = f"{date_value}, {desc_value}, {netto_value}, {mwst_value}, {brutto_value}"
        listbox.insert(tk.END, entry)

        with open(FILE_NAME, 'a') as file:
            file.write(f"{date_value},{desc_value},{netto_value},{mwst_value},{brutto_value}\n")

        desc_entry.delete(0, tk.END)
        netto_entry.delete(0, tk.END)
        mwst_entry.delete(0, tk.END)
        brutto_entry.delete(0, tk.END)

        update_total(listbox, total_label)

# Funktion zum Laden der Einträge aus der CSV-Datei
def load_entries(listbox, total_label):
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, 'r') as file:
            for line in file:
                listbox.insert(tk.END, line.strip())

        update_total(listbox, total_label)

# Funktion zum Löschen eines Eintrags aus der Listbox und der CSV-Datei
def delete_entry(listbox, total_label):
    try:
        selected_index = listbox.curselection()[0]
        selected_entry = listbox.get(selected_index)
        listbox.delete(selected_index)

        with open(FILE_NAME, 'r') as file:
            lines = file.readlines()
        with open(FILE_NAME, 'w') as file:
            for line in lines:
                if line.strip() != selected_entry:
                    file.write(line)

        update_total(listbox, total_label)
    except IndexError:
        print("Kein Eintrag ausgewählt!")

# Funktion zum Berechnen und Aktualisieren des Kassenbestands
def update_total(listbox, total_label):
    total = 0.0
    for entry in listbox.get(0, tk.END):
        brutto_value = entry.split(",")[-1].strip()
        try:
            total += float(brutto_value)
        except ValueError:
            continue
    total_label.config(text=f"Kassenbestand: {total:.2f} €")

# Funktion zum Filtern von Einträgen nach Zeitraum und Drucken in PDF
def print_to_pdf(listbox, start_date, end_date):
    entries_in_range = []
    
    # Datumsformat "%d.%m.%Y" verwenden
    start_date_dt = datetime.strptime(start_date.get(), "%d.%m.%Y")
    end_date_dt = datetime.strptime(end_date.get(), "%d.%m.%Y")
    
    total_before_period = 0.0  # Anfangsbestand
    total_in_period = 0.0      # Summe im ausgewählten Zeitraum

    for entry in listbox.get(0, tk.END):
        date_str = entry.split(",")[0].strip()
        entry_date = datetime.strptime(date_str, "%d.%m.%Y")
        brutto_value = float(entry.split(",")[-1].strip())

        # Berechne Anfangsbestand (Einträge vor dem Startdatum)
        if entry_date < start_date_dt:
            total_before_period += brutto_value

        # Berechne Einträge im ausgewählten Zeitraum
        if start_date_dt <= entry_date <= end_date_dt:
            entries_in_range.append(entry)
            total_in_period += brutto_value

    # Endbestand berechnen
    total_end_balance = total_before_period + total_in_period

    if entries_in_range:
        create_pdf(entries_in_range, total_before_period, total_end_balance)
    else:
        print("Keine Einträge im angegebenen Zeitraum gefunden.")

# Funktion zum Erstellen einer PDF-Datei mit einer Tabelle
def get_next_number():
    num_file = "next_number.txt"
    
    if not os.path.exists(num_file):
        with open(num_file, 'w') as file:
            file.write('1')
        return 1
    
    with open(num_file, 'r') as file:
        num = int(file.read().strip())
    
    next_num = num + 1
    
    with open(num_file, 'w') as file:
        file.write(str(next_num))
    
    return num

def create_pdf(entries, start_balance, end_balance):
    pdf_number = get_next_number()
    pdf_file = f"Kassenbuch_{pdf_number}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
    
    styles = getSampleStyleSheet()

    # Tabellenüberschriften
    data = [["Datum", "Beschreibung", "Netto", "MwSt.", "Brutto"]]

    # Einträge in der Tabelle
    for entry in entries:
        data.append(entry.split(","))

    # Tabelle erstellen
    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)

    # Anfangsbestand und Endbestand hinzufügen
    summary = f"Anfangsbestand: {start_balance:.2f} €\nEndbestand: {end_balance:.2f} €"
    
    # Erstelle Paragraphen für die Zusammenfassung
    summary_paragraph = Paragraph(summary, styles['Normal'])

    elements = []
    elements.append(table)
    elements.append(summary_paragraph)  # Füge den Paragraphen hinzu

    # PDF speichern
    doc.build(elements)
    print("PDF erfolgreich erstellt!")

# Funktion zum Erstellen der GUI
def create_gui():
    root = tk.Tk()
    root.title("Kassenbuch")

    date_label = tk.Label(root, text="Datum:")
    date_label.pack()

    # DateEntry für die Datumsauswahl mit deutschem Datumsformat
    date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.MM.yyyy')
    date_entry.pack()

    desc_label = tk.Label(root, text="Beschreibung:")
    desc_label.pack()

    desc_entry = tk.Entry(root)
    desc_entry.pack()

    netto_label = tk.Label(root, text="Netto Betrag:")
    netto_label.pack()

    netto_entry = tk.Entry(root)
    netto_entry.pack()

    mwst_label = tk.Label(root, text="MwSt.:")
    mwst_label.pack()

    mwst_entry = tk.Entry(root)
    mwst_entry.pack()

    brutto_label = tk.Label(root, text="Brutto Betrag:")
    brutto_label.pack()

    brutto_entry = tk.Entry(root)
    brutto_entry.pack()

    add_button = tk.Button(root, text="Hinzufügen", command=lambda: add_entry(date_entry, desc_entry, netto_entry, mwst_entry, brutto_entry, listbox, total_label))
    add_button.pack()

    listbox = tk.Listbox(root, width=80)
    listbox.pack()

    delete_button = tk.Button(root, text="Löschen", command=lambda: delete_entry(listbox, total_label))
    delete_button.pack(pady=5)

    total_label = tk.Label(root, text="Kassenbestand: 0.00 €", font=('Arial', 14))
    total_label.pack(pady=10)

    # Zeitraum für PDF-Export
    start_date_label = tk.Label(root, text="Startdatum:")
    start_date_label.pack()

    start_date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.MM.yyyy')
    start_date_entry.pack()

    end_date_label = tk.Label(root, text="Enddatum:")
    end_date_label.pack()

    end_date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.MM.yyyy')
    end_date_entry.pack()

    # PDF-Drucken-Button
    print_button = tk.Button(root, text="Drucken als PDF", command=lambda: print_to_pdf(listbox, start_date_entry, end_date_entry))
    print_button.pack(pady=10)

    load_entries(listbox, total_label)

    root.mainloop()

# Aufruf der Funktion
create_gui()

