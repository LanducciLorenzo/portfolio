# Leggimi (per Lorenzo)

Questo progetto aggiunge i **numeri** alla tua tesi di Economia sull'accordo UE-Australia e il de-risking.

## Cosa fa, in breve
1. Prende da Eurostat le importazioni UE dal resto del mondo di litio, terre rare, cobalto, grafite e
   magneti permanenti, 2010-2025, per paese di provenienza.
2. Calcola quanto pesa ogni fornitore e l'**indice di Herfindahl-Hirschman (HHI)**: la somma delle quote al
   quadrato (in percentuale). 10.000 = un solo fornitore; più è basso, più i fornitori sono diversificati.
   "Fornitori equivalenti" = 10.000 / HHI: quanti fornitori uguali darebbero la stessa concentrazione.
3. **Scenario:** se il 10%, 25% o 50% di quello che arriva dalla Cina arrivasse dall'Australia, quanto
   scenderebbe la concentrazione? È un calcolo, non una previsione.

## Cosa esce (media 2023-2025)
- **Magneti permanenti:** l'89% arriva dalla Cina (75% nel 2010-12). È l'unico caso sopra il 65%, la soglia
  del Critical Raw Materials Act. La dipendenza più forte è sul prodotto lavorato, non sulla materia prima.
- **Litio:** il primo fornitore è il **Cile** (50%); la Cina è salita dal 7% al 23%.
- **Terre rare:** Cina 33% in valore, 43% in quantità.
- **Grafite:** Cina 43%. **Cobalto:** fornitori diversificati (Stati Uniti 20%, Cina 19%, Canada 18%).
- **Australia:** quasi zero in modo diretto, tranne l'idrossido di litio nel 2025 (9,7 milioni di euro).
  Però molte terre rare arrivano dalla **Malesia**, dove c'è l'impianto Lynas che raffina minerale australiano:
  i dati commerciali registrano l'ultimo paese di lavorazione, non la miniera. È un bel punto da dire a voce.

## Come si usa
```
pip install -r requirements.txt
python -m pytest          # 41 controlli
python run_analysis.py    # crea results/report.md, tabelle e grafici
```

## I controlli fatti
- Il file viene rifiutato se è tagliato (come quello incollato in chat), doppio o del tipo sbagliato.
- Per tutte le 320 combinazioni prodotto × indicatore × anno, la somma dei paesi coincide **esattamente**
  con i totali calcolati da Eurostat.
- Ogni HHI e quota della Cina è ricalcolato una seconda volta in modo indipendente.
- Ho anche "rotto" il codice di proposito in tre punti: i test se ne accorgono ogni volta.

## Domande che ti potrebbero fare
- *Perché solo extra-UE?* Perché la domanda è la dipendenza da fornitori esterni.
- *Perché l'HHI?* È la misura standard di concentrazione; la usa anche la Commissione nella metodologia
  sulle materie prime critiche (insieme alla qualità della governance dei paesi).
- *Limiti?* Importazioni ≠ consumo; il paese d'origine è l'ultimo che lavora il prodotto; i valori dipendono
  dai prezzi (per questo c'è il controllo con le quantità).
