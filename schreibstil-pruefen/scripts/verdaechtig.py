#!/usr/bin/env python3
"""Sucht Formulierungen, die den Regelkatalog meist verletzen.

    python3 verdaechtig.py datei.md [weitere.md ...]
    python3 verdaechtig.py --kategorie metapher datei.md

Die Treffer sind Hinweise, keine Urteile. Jeder einzelne kann im Kontext
richtig sein: „Fallstrick" ist in manchen Repos ein eingefuehrter Begriff,
„Rauschen" bei Messwerten fachlich korrekt. Deshalb wird jeder Treffer mit
seiner Zeile ausgegeben, damit er im Zusammenhang beurteilt werden kann,
statt ihn blind zu ersetzen.

Codebloecke und Inline-Code bleiben aussen vor. Ohne das schlaegt die Suche
auf Variablen- und Feldnamen an, die zufaellig ein Stichwort enthalten.
"""
import re, sys, io

MUSTER = {
    'metapher': (
        'Metapher statt Sachverhalt',
        [r'Rohbau', r'sprachlos\w*', r'der Gewinn liegt', r'\bkippt\b', r'ohne Bremse',
         r'zweite Buchhaltung', r'hineinwächst', r'bezahlt macht', r'ins Rollen',
         r'auf der Strecke', r'roter Faden', r'Hand in Hand', r'an einem Strang',
         r'das A und O', r'Herzstück', r'Dreh- und Angelpunkt', r'aus dem Ruder',
         r'gestrickt', r'auf dem Silbertablett', r'unter der Haube', r'Achillesferse',
         r'ins Blaue', r'aufs Gleis', r'Meilenstein', r'Leuchtturm']),
    'beratungsdeutsch': (
        'Beratungs- oder Amtsdeutsch',
        [r'Zielbild', r'Betrachtungszeitraum', r'Handlungsbedarf', r'Mehrwert',
         r'ganzheitlich', r'Synergie\w*', r'zeitnah', r'Optimierungspotenzial',
         r'adressier\w+', r'Thematik', r'Problematik', r'Herausforderung',
         r'im Rahmen von', r'seitens', r'diesbezüglich', r'dahingehend',
         r'Sollstand', r'Zielsetzung', r'Maßnahmenpaket', r'Stellschraube',
         r'Best Practice', r'Rahmenbedingung\w*', r'Zielerreichung']),
    'adjektiv': (
        'Adjektiv statt Zahl',
        [r'deutlich (mehr|weniger|besser|schlechter|höher|niedriger)', r'erheblich\w*',
         r'signifikant\w*', r'zahlreiche', r'diverse', r'etliche', r'massiv\w*',
         r'drastisch\w*', r'spürbar', r'merklich', r'\bviele Fälle', r'die meisten Fälle']),
    'vermenschlichung': (
        'Vermenschlichung von Software',
        [r'(Modell|Agent|Workflow|System|Skript) (traut sich|will|mag|denkt|glaubt|weiß nicht)',
         r'traut sich nicht', r'ist der Meinung', r'entscheidet sich dafür']),
    'fuellwort': (
        'Füllwort ohne Aussage',
        [r'\beigentlich\b', r'\bletztendlich\b', r'im Grunde', r'\bquasi\b',
         r'\bsozusagen\b', r'gewissermaßen', r'\bdurchaus\b', r'\bbekanntlich\b']),
}

def ohne_code(text):
    """Codebloecke leeren, Inline-Code maskieren, Zeilenzahl erhalten."""
    aus, incode = [], False
    for z in text.split('\n'):
        if z.strip().startswith('```'):
            incode = not incode; aus.append(''); continue
        if incode or z.lstrip().startswith('>'):
            # Zitiertes gehoert nicht dem Autor: in einem Regeldokument stehen die
            # verbotenen Formulierungen als Beispiel, und ein Vorher-Nachher-Paar
            # enthaelt den schlechten Stand absichtlich.
            aus.append(''); continue
        aus.append(re.sub(r'`[^`]*`', '``', z))
    return aus

def pruefen(pfad, nur=None):
    zeilen = ohne_code(io.open(pfad, encoding='utf-8').read())
    treffer = []
    for schluessel, (titel, muster) in MUSTER.items():
        if nur and schluessel != nur:
            continue
        for i, z in enumerate(zeilen, 1):
            for m in muster:
                for f in re.finditer(m, z, re.I):
                    treffer.append((i, titel, f.group(0), z.strip()))
    # strukturelle Pruefungen
    for i, z in enumerate(zeilen, 1):
        if z.count('—') >= 2:
            treffer.append((i, 'Zwei Gedankenstriche in einer Zeile', '—', z.strip()))
        e = re.match(r'^\*\*([^*]{1,60})\.\*\*(\s|$)', z)
        # Ein fetter Absatzanfang ist Hausstil, solange er ein Satz ist. Zum Etikett
        # wird er, wenn er aus einer blossen Nominalphrase besteht: „Der Schleifen-Guard."
        # Die Wortzahl trennt das zuverlaessiger als eine Verbliste, an der jedes
        # nicht aufgefuehrte Verb einen Fehlalarm ausloest.
        # „**3. Nachpruefen.**" ist eine Schrittmarke in einer Anleitung, kein
        # Absatz-Leitsatz. Ohne diese Ausnahme meldet jede nummerierte Anleitung
        # so viele Fehlalarme, dass die echten Treffer untergehen.
        if e and len(e.group(1).split()) <= 3 and not re.match(r'^\d+\.', e.group(1)):
            treffer.append((i, 'Etikett statt Satz (fetter Absatzanfang ohne Aussage)',
                            e.group(1), z.strip()))
    return sorted(treffer)

def main(argv):
    nur, ziele = None, []
    i = 0
    while i < len(argv):
        if argv[i] == '--kategorie':
            i += 1; nur = argv[i]
        else:
            ziele.append(argv[i])
        i += 1
    if not ziele:
        print(__doc__)
        print('Kategorien:', ', '.join(MUSTER)); return 1
    gesamt = 0
    for p in ziele:
        t = pruefen(p, nur)
        gesamt += len(t)
        print(f"\n=== {p}: {len(t)} Hinweise")
        for zeile, titel, fund, text in t:
            print(f"  {p}:{zeile}  [{titel}] „{fund}\"")
            print(f"      {text[:110]}")
    print(f"\n{gesamt} Hinweise insgesamt. Jeden im Zusammenhang beurteilen, nicht blind ersetzen.")
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
