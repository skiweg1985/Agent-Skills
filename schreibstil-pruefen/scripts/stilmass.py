#!/usr/bin/env python3
"""Misst die Kennzahlen, die sich am Text objektiv feststellen lassen.

    python3 stilmass.py datei.md [weitere.md ...]
    python3 stilmass.py --bestand docs/ neue-datei.md

Der Sinn der Messung: eine Auffaelligkeit ist erst dann eine, wenn sie vom
uebrigen Bestand abweicht. Ein Text mit 0,5 Gedankenstrichen je Absatz ist in
einem Repo, das bei 0,2 liegt, ein Ausreisser und in einem, das bei 0,7 liegt,
schlicht Hausstil. Ohne Vergleichswert meldet man dem Nutzer Verstoesse, die
in Wahrheit die Norm sind.

Gezaehlt werden nur Fliesstext-Absaetze. Tabellen, Listen, Ueberschriften und
Codebloecke sind eigene Formen; ihre Gedankenstriche und Zeilenlaengen sagen
ueber den Schreibstil nichts aus.
"""
import re, sys, io, glob, os

def absaetze(text):
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    roh = re.split(r'\n\s*\n', text)
    return [a for a in roh if a.strip()
            and not a.strip().startswith(('|', '#', '-', '*', '>'))]

def fliesszeilen(text):
    """Zeilen, fuer die eine Breitenmessung sinnvoll ist."""
    aus, incode = [], False
    for z in text.split('\n'):
        if z.strip().startswith('```'):
            incode = not incode; continue
        if incode or not z.strip() or z.lstrip().startswith(('|', '#', '>')):
            continue
        aus.append(z)
    return aus

def messen(pfad):
    t = io.open(pfad, encoding='utf-8').read()
    a = absaetze(t)
    striche = [x.count('—') for x in a]
    semi = sum(x.count(';') for x in a)
    zeilen = fliesszeilen(t)
    laengen = sorted((len(z) for z in zeilen), reverse=True)
    return {
        'pfad': pfad,
        'absaetze': len(a),
        'striche': sum(striche),
        'dichte': round(sum(striche) / max(len(a), 1), 2),
        'ueber2': sum(1 for s in striche if s >= 2),
        'semikolon': semi,
        'breite_max': laengen[0] if laengen else 0,
        'breite_p90': laengen[len(laengen) // 10] if laengen else 0,
    }

def main(argv):
    ziele, bestand = [], []
    i = 0
    while i < len(argv):
        if argv[i] == '--bestand':
            i += 1
            quelle = argv[i]
            bestand = sorted(glob.glob(os.path.join(quelle, '*.md'))
                             if os.path.isdir(quelle) else glob.glob(quelle))
        else:
            ziele.append(argv[i])
        i += 1
    if not ziele and not bestand:
        print(__doc__); return 1

    kopf = f"{'Datei':44} {'Abs':>4} {'—':>4} {'—/Abs':>6} {'Abs>=2':>7} {'Semi':>5} {'Zeile max':>10}"
    print(kopf); print('-' * len(kopf))
    werte = []
    for p in ziele:
        d = messen(p); werte.append(d)
        print(f"{d['pfad'][:44]:44} {d['absaetze']:4} {d['striche']:4} "
              f"{d['dichte']:6} {d['ueber2']:7} {d['semikolon']:5} {d['breite_max']:10}")
    vergleich = [messen(p) for p in bestand if p not in ziele]
    if vergleich:
        print('-' * len(kopf))
        for d in sorted(vergleich, key=lambda x: x['dichte']):
            print(f"  {d['pfad'][:42]:42} {d['absaetze']:4} {d['striche']:4} "
                  f"{d['dichte']:6} {d['ueber2']:7} {d['semikolon']:5} {d['breite_max']:10}")
        dd = [d['dichte'] for d in vergleich]
        bb = [d['breite_p90'] for d in vergleich]
        print('-' * len(kopf))
        print(f"Bestand: Dichte {min(dd)} bis {max(dd)}, Mittel {round(sum(dd)/len(dd), 2)} "
              f"| uebliche Zeilenbreite (p90) {min(bb)} bis {max(bb)}")
        for d in werte:
            lage = ('ueber dem Bestand' if d['dichte'] > max(dd)
                    else 'unter dem Bestand' if d['dichte'] < min(dd) else 'im Rahmen des Bestands')
            print(f"  -> {d['pfad']}: Dichte {d['dichte']} liegt {lage}.")
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
