#!/usr/bin/env python3
"""Bricht Fliesstext-Absaetze auf eine feste Breite um.

    python3 umbrechen.py --breite 105 datei.md
    python3 umbrechen.py --check datei.md          # meldet nur, schreibt nicht
    python3 umbrechen.py --breite-messen docs/     # uebliche Breite des Bestands

Nach einer Textueberarbeitung stehen die Zeilenumbrueche schief: ersetzte
Saetze sind laenger oder kuerzer als das, was vorher dastand. Das Skript zieht
sie nach, ohne den Inhalt zu aendern.

Die Breite wird nicht geraten, sondern am Bestand gemessen (--breite-messen).
Ein Repo, dessen Dateien bei 100 Zeichen umbrechen, bekommt sonst eine Datei
mit 79, und der Diff zeigt Aenderungen, die keine sind.

Unangetastet bleiben Codebloecke, Tabellen, Ueberschriften, Zitate,
Listeneintraege und alles, was eingerueckt ist: dort traegt der Umbruch
Bedeutung. Absaetze, die mit **fett** beginnen, gehoeren dagegen zum
Fliesstext. Wer sie ueber das fuehrende Sternchen zusammen mit Listen
aussortiert, laesst genau die Absaetze unbehandelt, die eine Ueberarbeitung
am haeufigsten trifft, weil dort die Leitsaetze stehen.
"""
import io, re, sys, glob, os, textwrap

def ist_struktur(zeile):
    kopf = zeile.lstrip()
    if zeile.startswith((' ', '\t')):          # eingerueckt: Listenfortsetzung, Code
        return True
    if kopf.startswith(('|', '#', '>')):        # Tabelle, Ueberschrift, Zitat
        return True
    if re.match(r'^([-+*]|\d+\.)\s', kopf):     # Listeneintrag, aber nicht **fett**
        return True
    return False

def fliesstext(text):
    """Je Zeile: ist sie umbrechbarer Fliesstext? Der Codeblock-Zustand laesst
    sich nur beim Durchlaufen von oben feststellen, deshalb eine Liste statt
    einer Pruefung je Einzelzeile. Beide Pfade -- Umbrechen und Pruefen --
    muessen dieselbe Antwort bekommen, sonst meldet die Pruefung Zeilen, die
    das Umbrechen zu Recht in Ruhe laesst."""
    aus, incode = [], False
    for z in text.split('\n'):
        if z.strip().startswith('```'):
            incode = not incode; aus.append(False); continue
        aus.append(not (incode or not z.strip() or ist_struktur(z)))
    return aus

def umbrechen(text, breite):
    aus, buf, incode = [], [], False
    def leeren():
        if buf:
            zusammen = ' '.join(x.strip() for x in buf)
            aus.extend(textwrap.wrap(zusammen, width=breite,
                                     break_long_words=False, break_on_hyphens=False))
            buf.clear()
    for z in text.split('\n'):
        if z.strip().startswith('```'):
            leeren(); incode = not incode; aus.append(z); continue
        if incode or not z.strip() or ist_struktur(z):
            leeren(); aus.append(z); continue
        buf.append(z)
    leeren()
    return '\n'.join(aus)

def breite_messen(quelle):
    dateien = (sorted(glob.glob(os.path.join(quelle, '*.md')))
               if os.path.isdir(quelle) else sorted(glob.glob(quelle)))
    werte = []
    for p in dateien:
        laengen = sorted((len(z) for z in io.open(p, encoding='utf-8').read().split('\n')
                          if z.strip() and not ist_struktur(z)), reverse=True)
        if laengen:
            werte.append((p, laengen[len(laengen) // 10]))
    for p, w in werte:
        print(f"  {p:52} p90 {w}")
    if werte:
        haeufig = sorted(w for _, w in werte)
        print(f"\nUebliche Breite: {haeufig[len(haeufig)//2]} "
              f"(Spanne {haeufig[0]} bis {haeufig[-1]})")

def main(argv):
    breite, check, ziele = 105, False, []
    i = 0
    while i < len(argv):
        if argv[i] == '--breite': i += 1; breite = int(argv[i])
        elif argv[i] == '--check': check = True
        elif argv[i] == '--breite-messen':
            i += 1; breite_messen(argv[i]); return 0
        else: ziele.append(argv[i])
        i += 1
    if not ziele:
        print(__doc__); return 1
    for p in ziele:
        alt = io.open(p, encoding='utf-8').read()
        neu = umbrechen(alt, breite)
        if check:
            # Nicht auf Gleichheit pruefen: ein Umbruch, der anders faellt als der
            # eigene, ist kein Mangel. Gemeldet wird, was beim Lesen stoert -- zu
            # lange Zeilen und Zeilen, die mitten im Absatz abbrechen.
            zeilen = alt.split('\n')
            ist_text = fliesstext(alt)
            maengel = []
            for i, z in enumerate(zeilen, 1):
                if not ist_text[i - 1]:
                    continue
                folgt = i < len(zeilen) and ist_text[i]
                if len(z) > breite + 5:
                    maengel.append(f"Zeile {i}: {len(z)} Zeichen")
                elif folgt and len(z) < breite - 25:
                    # Eine kurze Zeile ist kein Mangel, wenn das naechste Wort ohnehin
                    # nicht mehr gepasst haette: lange URLs, Markdown-Links und
                    # Codebezeichner lassen sich nicht trennen.
                    naechstes = zeilen[i].strip().split(' ')[0] if zeilen[i].strip() else ''
                    if len(z) + 1 + len(naechstes) <= breite:
                        maengel.append(f"Zeile {i}: bricht nach {len(z)} Zeichen ab")
            print(f"{p}: " + ("in Ordnung" if not maengel else ", ".join(maengel)))
            continue
        if alt == neu:
            print(f"{p}: unveraendert")
        else:
            io.open(p, 'w', encoding='utf-8').write(neu)
            print(f"{p}: umgebrochen auf {breite}")
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
