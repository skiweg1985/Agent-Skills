---
name: schreibstil-pruefen
description: >-
  Deutschsprachige technische Dokumentation gegen einen festen Regelkatalog prüfen und überarbeiten -
  Metaphern, Beratungsdeutsch, Telegrammstil, Gedankenstrich-Häufung, Etiketten statt Sätze und
  verkürzte Folgerungen finden, am Bestand messen statt schätzen und gezielt korrigieren. Diesen Skill
  verwenden, sobald ein deutscher Text auf Formulierung hin angesehen oder verbessert werden soll:
  README, docs/, AGENTS.md, CLAUDE.md, Commit-Messages, Linear- und Jira-Beiträge. Auch dann verwenden,
  wenn das Wort Stil gar nicht fällt und nur „lies mal drüber", „klingt das gut so", „schreib das
  bitte um", „passt der Ton", „ist das zu geschwollen" oder „mach das lesbarer" gesagt wird. Ebenso
  verwenden, direkt nachdem selbst ein längeres deutsches Dokument geschrieben wurde, denn dann ist die
  Prüfung noch billig. Enthält den Regelkatalog, echte Vorher-Nachher-Beispiele und drei Skripte für
  Messung, Musterprüfung und Zeilenumbruch.
---

# Schreibstil prüfen

Der Zweck ist nicht, Texte zu glätten, sondern sie lesbar zu halten. Technische Dokumentation wird von
Kollegen gelesen, die eine Entscheidung treffen oder einen Fehler eingrenzen wollen. Sie brauchen die
Argumentation, nicht eine Sammlung von Stichpunkten, aus der sie den Zusammenhang selbst herstellen.

## Der wichtigste Punkt zuerst

**Erst messen, dann urteilen.** Eine Formulierung ist erst dann auffällig, wenn sie vom übrigen Bestand
abweicht. Ein Text mit 0,5 Gedankenstrichen je Absatz ist in einem Repo, das bei 0,2 liegt, ein
Ausreißer, und in einem, das bei 0,7 liegt, schlicht Hausstil. Wer ohne Vergleichswert prüft, meldet dem
Nutzer Verstöße, die in Wahrheit die Norm sind, und schlägt Änderungen vor, die den Text vom Rest des
Repos entfernen statt ihn anzugleichen.

Der zweite Punkt ist ebenso wichtig und wird häufiger falsch gemacht: **„direkt und knapp" ist keine
Aufforderung zum Kürzen.** Regel 2 des Katalogs verlangt ausdrücklich das Gegenteil, nämlich Lesbarkeit
vor Kürze. Wenn eine Korrektur einen Text kürzer, aber schwerer verständlich macht, war sie falsch.
Sätze zusammenzuziehen und Zusammenhänge mit „weil", „dadurch" oder „sonst" auszuschreiben ist oft die
richtige Korrektur, auch wenn der Text dabei länger wird.

## Welcher Maßstab gilt

Zuerst nachsehen, ob das Repo einen eigenen Katalog hat: ein Stilabschnitt in `AGENTS.md` oder
`CLAUDE.md`. Der hat Vorrang, weil er die abgestimmte Fassung ist. Nur wenn es keinen gibt, gilt
`references/regeln.md` aus diesem Skill. Dort stehen die zehn Regeln samt echter Vorher-Nachher-Paare
aus einer durchgeführten Überarbeitung; die Beispiele sind nützlicher als die Regeln allein, weil sie
zeigen, wo die Grenze zwischen Hausstil und Verstoß verläuft.

## Ablauf

**1. Messen.** Die Kennzahlen der Zieldatei gegen den Bestand des Repos:

```bash
python3 scripts/stilmass.py docs/neue-datei.md --bestand docs/
```

Das liefert Absatzzahl, Gedankenstriche je Absatz, Absätze mit zweien oder mehr, Semikolons und die
Zeilenbreite, dazu die Spanne des Bestands und die Einordnung der Zieldatei. Tabellen, Listen,
Überschriften und Codeblöcke bleiben außen vor, weil ihre Gedankenstriche keine Stilfrage sind.

**2. Muster suchen.**

```bash
python3 scripts/verdaechtig.py docs/neue-datei.md
```

Findet Metaphern, Beratungsdeutsch, Adjektive statt Zahlen, Vermenschlichung von Software, Füllwörter,
Zeilen mit zwei Gedankenstrichen und fette Absatzanfänge, die zum bloßen Etikett geschrumpft sind. Jeder
Treffer ist ein Hinweis, kein Urteil: „Fallstrick" kann ein eingeführter Begriff sein, „Rauschen" bei
Messwerten fachlich korrekt. Deshalb jeden Treffer im Zusammenhang lesen, statt ihn blind zu ersetzen.

**3. Selbst lesen.** Die schwerwiegendsten Verstöße findet kein Skript, weil sie in der Argumentation
liegen und nicht in Wörtern: unverbundene Aussagen, Folgerungen ohne Begründung, künstliche
Zwischenüberschriften, Absätze, die für jede einzelne Beobachtung neu anfangen. Dafür den Text einmal
ganz lesen und an jeder Stelle prüfen, ob der nächste Satz aus dem vorigen folgt oder ob der Leser die
Verbindung selbst herstellen muss.

**4. Befunde vorlegen, bevor korrigiert wird.** Je Fundstelle: wo, welche Regel, wohin die Korrektur
geht. Dazu die Messwerte und die ehrliche Einordnung, was davon Ausreißer ist und was Hausstil. Der
Nutzer entscheidet dann über den Umfang, etwa nur die neue Datei oder auch den Bestand. Das ist keine
Förmlichkeit: an einem gewachsenen Dokument hängen oft Absprachen, von denen im Text nichts steht.

**5. Korrigieren.** Ersetzungen so schreiben, dass sie fehlschlagen statt danebenzugreifen: Suchtext
gegen Zeilenumbrüche unempfindlich machen und darauf bestehen, dass es genau einen Treffer gibt.

```python
def rep(alt, neu):
    global s
    pat = r'\s+'.join(re.escape(w) for w in alt.split())   # Umbrüche egal
    s2, cnt = re.subn(pat, lambda m: neu, s)
    assert cnt == 1, f'{cnt} Treffer für: {alt[:60]!r}'    # 0 oder 2 sind Fehler
    s = s2
```

Ein Suchtext, der zweimal passt, ändert eine Stelle, die niemand angesehen hat. Ein Suchtext, der nicht
passt, lässt den Befund stillschweigend offen. Beides fällt ohne die Prüfung nicht auf.

**6. Zeilenumbrüche nachziehen.** Nach der Überarbeitung stehen sie schief, weil ersetzte Sätze länger
oder kürzer sind als das, was vorher dastand. Die Breite wird am Bestand gemessen, nicht geraten:

```bash
python3 scripts/umbrechen.py --breite-messen docs/
python3 scripts/umbrechen.py --breite 105 docs/neue-datei.md
python3 scripts/umbrechen.py --check --breite 105 docs/*.md
```

**7. Nachprüfen.** Musterprüfung und Messung erneut laufen lassen, danach den Text noch einmal ganz
lesen. Die Zahlen belegen, dass die gemeldeten Stellen weg sind; ob die Argumentation trägt, zeigen sie
nicht.

## Fallstricke

**Fette Leitsätze sind in vielen Repos Hausstil.** Ein Absatz, der mit einem fetten Satz beginnt und
dann die Begründung liefert, ist keine künstliche Überschrift, sondern eine übliche und gut lesbare
Form. Zum Verstoß wird sie erst, wenn der fette Teil zur Nominalphrase schrumpft: „**Der
Schleifen-Guard.**" ersetzt eine Überschrift, „**Der auslösende Trigger muss die eigenen Tags
ausschließen**" sagt etwas. Vor einer Änderung an dieser Stelle nachsehen, wie es die Nachbardateien
halten.

**Wer Überschriften ändert, ändert das Inhaltsverzeichnis.** Manche Repos erzeugen es mit einem eigenen
Werkzeug (hier `node tools/toc.mjs`, geprüft mit `--check`). Nach jeder Änderung an einer Überschrift
laufen lassen, sonst zeigt das Verzeichnis auf Anker, die es nicht mehr gibt.

**Beim Umbrechen sind `**fett**`-Zeilen Fließtext.** Wer sie über das führende Sternchen zusammen mit
Listen aussortiert, lässt genau die Absätze unbehandelt, die eine Überarbeitung am häufigsten trifft,
weil dort die Leitsätze stehen. `scripts/umbrechen.py` behandelt das richtig; bei einer eigenen Lösung
ist es der erste Fehler, der passiert.

**Eine kurze Zeile ist nicht immer ein Mangel.** Steht als Nächstes eine lange URL, ein Markdown-Link
oder ein Codebezeichner, dann ist der frühe Umbruch unvermeidbar und korrekt.

**Commit-Messages und Linear-Beiträge fallen unter dieselben Regeln.** Sie werden nur seltener geprüft,
weil sie niemandem als Datei begegnen.

## Abgrenzung

Dieser Skill regelt die Formulierung. Was überhaupt dokumentiert wird, wie ein Repo seine Doku
gliedert und welche Dokumente es geben muss, steht in `documentation-standards`. Die beiden greifen
ineinander, widersprechen sich aber nicht: der eine sagt, welche Datei entsteht, der andere, wie darin
geschrieben wird.
