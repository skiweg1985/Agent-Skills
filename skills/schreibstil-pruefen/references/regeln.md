# Der Regelkatalog

Dieser Katalog gilt, wenn das Repo keinen eigenen hat. Liegt im Repo eine `AGENTS.md` oder `CLAUDE.md`
mit einem Stilabschnitt, hat die Vorrang: sie ist die abgestimmte Fassung, dieser Katalog nur der
Rückfall.

Alles, was hier geregelt wird, ist technische Dokumentation für Kollegen, nicht für Kunden. Das gilt für
Markdown-Dateien genauso wie für Commit-Messages und für Beiträge in Linear oder Jira.

## Die zehn Regeln

1. **Direkt und knapp, aber in natürlichem Deutsch.** Kurze Sätze sind gut, solange der Zusammenhang
   erhalten bleibt. Nicht in Telegrammstil oder eine Folge isolierter Aussagen verfallen. Wenn Ursache,
   Beobachtung und Konsequenz zusammengehören, werden sie auch sprachlich miteinander verbunden.
2. **Lesbarkeit geht vor maximaler Kürze.** Der Leser soll die Argumentation beim normalen Lesen
   verstehen können und sie nicht selbst aus einzelnen Beobachtungen zusammensetzen müssen. Lieber zwei
   oder drei vollständige, zusammenhängende Sätze als mehrere verkürzte Aussagen.
3. **Absätze nach Gedanken strukturieren, nicht nach Satzlänge.** Ein Absatz darf mehrere Sätze
   enthalten, wenn sie denselben Zusammenhang erklären. Nicht für jede Zahl, Beobachtung oder
   Schlussfolgerung einen eigenen Absatz anfangen.
4. **Keine künstlichen Überschriften für einzelne Aussagen.** Zwischenüberschriften strukturieren echte
   Abschnitte. Formulierungen wie „Der Hit-Count zählt zu viel", „Der Log zeigt zu wenig" oder „Was
   daraus folgt" nicht als Ersatz für eine ausformulierte Argumentation verwenden.
5. **Keine Metaphern, die im Handbuch nichts verloren haben.** Kein „Rohbau steht", keine „sprachlosen
   Zonen", kein „der Gewinn liegt darin, dass". Schreib hin, was Sache ist.
6. **Kein Beratungs- oder Amtsdeutsch.** Also nicht „Zielbild", „Betrachtungszeitraum",
   „Handlungsbedarf", „Mehrwert", „ganzheitlich". Sondern „Ziel", „Zeitraum" oder „muss man nichts
   machen".
7. **Sparsam mit Gedankenstrichen.** Zwei pro Absatz sind meist einer zu viel. Im Deutschen tun es
   Doppelpunkt, Klammer oder ein neuer Satz.
8. **Englische Fachbegriffe sind in Ordnung, wo sie im Alltag üblich sind:** Repository, Commit,
   Deployment, Action, Workflow, Custom Object, Skill. Nicht übersetzen, was niemand übersetzt.
   Englische Fachbegriffe sind aber kein Grund, englischen Satzbau ins Deutsche zu übertragen.
9. **Zahlen statt Adjektive.** Nicht „deutlich mehr", sondern „85 von 94".
10. **Technische Zusammenhänge ausformulieren.** Bei Analysen nicht nur Beobachtung und Messwert nennen,
    sondern erklären, warum der Messwert relevant ist und was daraus folgt. Besonders bei
    Ursache-Wirkungs-Beziehungen Wörter wie „weil", „dadurch", „deshalb", „allerdings" oder „das
    bedeutet" verwenden, wenn sie den Zusammenhang klarer machen.

## Beispiele aus einer echten Überarbeitung

Die folgenden Paare stammen aus der Überarbeitung eines Dokuments über Zendesk-Tags. Sie zeigen, wie die
Regeln in der Praxis greifen.

### Metapher, Regel 5

Die linke Fassung klingt nach etwas, die rechte sagt etwas.

| Vorher | Nachher |
| --- | --- |
| `## Der Bestand, in den das hineinwächst` | `## Der vorhandene Tag-Bestand` |
| `## Zwei Regeln, ohne die es kippt` | `## Zwei Regeln für den Betrieb` |
| „weil jeder Lauf wieder ein Update schreibt, läuft das ohne Bremse" | „…, endet das nicht von allein" |
| „Tags sind der Filterkanal, nicht die zweite Buchhaltung" | „Tags sagen Zendesk nur, dass etwas passiert ist; sie führen den Status nicht" |

### Floskel, Regel 5

„Der Punkt, an dem sich der Aufwand bezahlt macht" ist die Familie „der Gewinn
liegt darin, dass". Sie kündigt eine Begründung an, statt sie zu geben:

> Vorher: Die Trennung von `failed` und `empty` ist der Punkt, an dem sich der Aufwand bezahlt macht:
> `failed` ist ein Retry-Kandidat, `empty` ausdrücklich nicht.
>
> Nachher: `failed` und `empty` sind getrennt, weil nur `failed` ein Retry-Kandidat ist. Ein
> Wiederholungslauf lohnt sich, wenn ein Timeout den Lauf abgebrochen hat; bei einem Ticket, zu dem das
> Modell nichts zu sagen hat, kostet er dagegen nur Geld.

### Etikett statt Satz, Regel 4

Ein fetter Absatzanfang ist in vielen Repos Hausstil und völlig in
Ordnung, solange er ein vollständiger Satz ist und die Begründung folgt. Zum Verstoß wird er, wenn er zur
bloßen Nominalphrase schrumpft und damit die Überschrift ersetzt, die man nicht setzen wollte:

> Vorher: **Der Schleifen-Guard.** Der auslösende Trigger muss `running`, `done` und `failed`
> ausschließen.
>
> Nachher: **Der auslösende Trigger muss die eigenen Tags ausschließen**, also `running`, `done` und
> `failed`.

Unverändert bleiben durften im selben Dokument „**Trigger können nicht auf Tag-Präfixe matchen.**" und
„**Es fehlt eine Action.**" — beides Sätze mit Aussage.

### Verkürzte Folgerung, Regeln 2 und 10

Der Leser soll die Kette nicht selbst schließen müssen:

> Vorher: Jedes Tag landet in jeder Zählung. Deshalb bleibt die Familie klein und die Kardinalität
> endlich.
>
> Nachher: Jedes Tag landet in jeder Zählung, also in Explore, in `analyze_tickets` und in jeder Suche.
> Je mehr verschiedene Werte es gibt, desto unbrauchbarer wird eine Auswertung über Tags. Deshalb bleibt
> die Familie der Prozess-Tags klein und ihre Wertemenge abgeschlossen.

Dasselbe bei einem Semikolon, das zwei Aussagen nebeneinanderstellt, ohne ihr Verhältnis zu benennen:
„Zwei Quellen für dieselbe Aussage driften; die Übernahme-Statistik ist dann wertlos" wurde zu „Stünde
dieselbe Aussage an zwei Stellen, liefen beide früher oder später auseinander, und dadurch wäre die
Übernahme-Statistik wertlos."

### Beratungsdeutsch, Regel 6

„Sollstand", „Datenwahrheit" und „Auslöser- und Filterkanal" sind
Wörter, die niemand sagt. „Es beschreibt einen **Sollstand**" wurde zu „Es beschreibt, was gelten soll,
nicht was schon läuft".

### Gedankenstriche, Regel 7

In der Ausgangsfassung standen 11 Gedankenstriche auf 20 Absätze, nach der
Überarbeitung 2 auf 23. Fast alle ließen sich durch einen Punkt oder einen Doppelpunkt ersetzen, ohne
dass ein Wort geändert werden musste:

> Vorher: …wenn man ihm `tags` mitgibt — dieselbe Falle wie beim Langdock-`PUT`, nur dass hier die
> fachlichen Tags eines echten Kundentickets verschwinden.
>
> Nachher: …wenn man ihm `tags` mitgibt. Das ist derselbe Fehler wie beim Langdock-`PUT`, nur dass hier
> die fachlichen Tags eines echten Kundentickets verschwinden.

### Vermenschlichung

„das Modell traut sich nicht" wurde zu „das Modell ist unsicher". Software hat
keine Absichten, und die Zuschreibung verdeckt, was tatsächlich gemessen wurde.

## Was der Katalog nicht verlangt

Er verlangt keine kurzen Sätze um jeden Preis. Der häufigste Fehler bei einer Stilüberarbeitung ist,
dass „direkt und knapp" als Aufforderung zum Kürzen gelesen wird und am Ende eine Reihe abgehackter
Aussagen dasteht, deren Zusammenhang der Leser selbst herstellen muss. Regel 2 sagt ausdrücklich das
Gegenteil. Wenn eine Korrektur einen Text kürzer, aber schwerer verständlich macht, war sie falsch.
