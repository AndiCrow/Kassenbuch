import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from difflib import get_close_matches

# Name der CSV-Datei, in der die Einträge gespeichert werden
FILE_NAME = "kassenbuch.csv"

# Funktion zum Hinzufügen eines Eintrags und Speichern in CSV
def add_entry(date_entry, desc_entry, category_entry, zahlung_entry, netto_entry, mwst_entry, mwst_satz_entry, brutto_entry, listbox, total_label):
    date_value = date_entry.get()
    desc_value = desc_entry.get()
    category_value = category_entry.get()
    zahlung_value = zahlung_entry.get()
    netto_value = netto_entry.get()
    mwst_value = mwst_entry.get()
    mwst_satz_value = mwst_satz_entry.get()
    brutto_value = brutto_entry.get()

    if date_value and desc_value and category_value and zahlung_value and netto_value and mwst_value and mwst_satz_value and brutto_value:
        try:
            brutto_value_float = float(brutto_value)
        except ValueError:
            print("Fehler: Brutto Betrag muss eine Zahl sein.")
            return

        # MwSt.-Betrag und MwSt.-Satz getrennt speichern
        entry = f"{date_value}, {desc_value}, {category_value}, {zahlung_value}, {netto_value}, {mwst_value}, {mwst_satz_value}, {brutto_value}"
        listbox.insert(tk.END, entry)

        # Speichere in CSV
        with open(FILE_NAME, 'a') as file:
            file.write(f"{date_value},{desc_value},{category_value},{zahlung_value},{netto_value},{mwst_value},{mwst_satz_value},{brutto_value}\n")

        # Leere die Eingabefelder
        desc_entry.delete(0, tk.END)
        category_entry.delete(0, tk.END)
        zahlung_entry.delete(0, tk.END)
        netto_entry.delete(0, tk.END)
        mwst_entry.delete(0, tk.END)
        mwst_satz_entry.delete(0, tk.END)
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

# Suchfunktion für Beschreibung, Kategorie oder Zahlung durch (mit 80% Übereinstimmung)
def search_entries(listbox, search_term, search_type):
    matching_entries = []
    threshold = 0.8  # Setze den Schwellenwert für die Übereinstimmung auf 80%

    for entry in listbox.get(0, tk.END):
        fields = entry.split(", ")
        
        # Stelle sicher, dass genügend Felder vorhanden sind
        if len(fields) >= 4:
            if search_type == "Beschreibung":
                match = get_close_matches(search_term.lower(), [fields[1].lower()], n=1, cutoff=threshold)
                if match:
                    matching_entries.append(entry)
                    
            elif search_type == "Kategorie":
                match = get_close_matches(search_term.lower(), [fields[2].lower()], n=1, cutoff=threshold)
                if match:
                    matching_entries.append(entry)
                    
            elif search_type == "Zahlung durch":
                match = get_close_matches(search_term.lower(), [fields[3].lower()], n=1, cutoff=threshold)
                if match:
                    matching_entries.append(entry)
        else:
            print(f"Ungültige Zeile: {entry}")  # Zum Debuggen

    return matching_entries

# Funktion zum Berechnen des End- und Anfangsbestands aus den Suchergebnissen
def calculate_balances(entries):
    start_balance = 0.0  # Anfangsbestand
    end_balance = 0.0    # Endbestand

    for entry in entries:
        brutto_value = entry.split(",")[-1].strip()
        try:
            end_balance += float(brutto_value)
        except ValueError:
            continue
    
    return start_balance, end_balance

# Funktion zum Erstellen einer PDF mit Suchergebnissen
def search_and_generate_pdf(listbox, search_term, search_type):
    matching_entries = search_entries(listbox, search_term, search_type)
    
    if matching_entries:
        # Berechne Anfangs- und Endbestand basierend auf den Suchergebnissen
        start_balance, end_balance = calculate_balances(matching_entries)
        create_pdf(matching_entries, start_balance, end_balance)
    else:
        print("Keine Übereinstimmungen gefunden.")

# Funktion zum Erstellen einer PDF-Datei mit einer Tabelle
def create_pdf(entries, start_balance, end_balance):
    pdf_number = get_next_number()  # Hol die nächste PDF-Nummer
    pdf_file = f"Kassenbuch_Suche_{pdf_number}.pdf"
    
    doc = SimpleDocTemplate(pdf_file, pagesize=landscape(A4))
    
    styles = getSampleStyleSheet()

    # Tabellenüberschriften
    data = [["Datum", "Beschreibung", "Kategorie", "Zahlung durch", "Netto", "MwSt.", "MwSt.-Satz", "Brutto"]]

    # Einträge in der Tabelle (MwSt.-Satz ist eine eigene Spalte)
    for entry in entries:
        data.append(entry.split(", "))

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
    print(f"PDF erfolgreich erstellt: {pdf_file}")

# Funktion zum Erstellen der fortlaufenden Nummer für PDFs
def get_next_number():
    num_file = "next_number.txt"
    
    # Erstelle die Datei, falls sie nicht existiert
    if not os.path.exists(num_file):
        with open(num_file, 'w') as file:
            file.write('1')  # Starte bei Nummer 1
        return 1
    
    # Lese die Datei und prüfe auf leere oder ungültige Inhalte
    with open(num_file, 'r') as file:
        content = file.read().strip()
        if content == '' or not content.isdigit():
            next_num = 1  # Wenn die Datei leer ist oder ungültige Daten enthält, auf 1 setzen
        else:
            next_num = int(content) + 1  # Nummer inkrementieren
    
    # Schreibe die nächste Nummer zurück in die Datei
    with open(num_file, 'w') as file:
        file.write(str(next_num))
    
    return next_num

# Funktion zum Erstellen der GUI
def create_gui():
    root = tk.Tk()
    root.title("Kassenbuch")

    # Eingabefelder
    date_label = tk.Label(root, text="Datum:")
    date_label.pack()
    date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.MM.yyyy')
    date_entry.pack()

    desc_label = tk.Label(root, text="Beschreibung:")
    desc_label.pack()
    desc_entry = tk.Entry(root)
    desc_entry.pack()

    category_label = tk.Label(root, text="Kategorie:")
    category_label.pack()
    category_entry = tk.Entry(root)
    category_entry.pack()

    zahlung_label = tk.Label(root, text="Zahlung durch:")
    zahlung_label.pack()
    zahlung_entry = tk.Entry(root)
    zahlung_entry.pack()

    netto_label = tk.Label(root, text="Netto Betrag:")
    netto_label.pack()
    netto_entry = tk.Entry(root)
    netto_entry.pack()

    mwst_label = tk.Label(root, text="MwSt.:")
    mwst_label.pack()
    mwst_entry = tk.Entry(root)
    mwst_entry.pack()

    mwst_satz_label = tk.Label(root, text="MwSt.-Satz (%):")
    mwst_satz_label.pack()
    mwst_satz_entry = tk.Entry(root)
    mwst_satz_entry.pack()

    brutto_label = tk.Label(root, text="Brutto Betrag:")
    brutto_label.pack()
    brutto_entry = tk.Entry(root)
    brutto_entry.pack()

    add_button = tk.Button(root, text="Hinzufügen", command=lambda: add_entry(date_entry, desc_entry, category_entry, zahlung_entry, netto_entry, mwst_entry, mwst_satz_entry, brutto_entry, listbox, total_label))
    add_button.pack()

    # Listbox für Einträge
    listbox = tk.Listbox(root, width=100)
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

    # Suchfunktion
    search_label = tk.Label(root, text="Suche nach:")
    search_label.pack()

    search_entry = tk.Entry(root)
    search_entry.pack()

    search_type_label = tk.Label(root, text="Suchfeld auswählen:")
    search_type_label.pack()

    search_type = ttk.Combobox(root, values=["Beschreibung", "Kategorie", "Zahlung durch"])
    search_type.pack()

    search_button = tk.Button(root, text="Suche und PDF", command=lambda: search_and_generate_pdf(listbox, search_entry.get(), search_type.get()))
    search_button.pack(pady=10)

    # Lade die vorhandenen Einträge
    load_entries(listbox, total_label)

    root.mainloop()

# Aufruf der Funktion
create_gui()
