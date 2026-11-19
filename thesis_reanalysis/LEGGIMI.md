# Come usarlo (in italiano)

1. Prepara i dati della tesi in un file con **una riga per partecipante** e le colonne come in
   `data/data_template.csv` (va bene anche Excel o il file SPSS .sav).
   - Colonne: `id`, `paivio_visivo` (punteggio visivo del Paivio) oppure `gruppo` (`alto`/`basso`),
     e per ogni misura e condizione una proporzione da 0 a 1, ad esempio `recog_lure_immagini`.
2. Controlla in `config.py` il **numero di item** del test di riconoscimento (vecchi, lure critiche, nuovi):
   servono per d′ e c. Ora sono 15, 5 e 10.
3. Esegui `python run_analysis.py data/il_tuo_file.csv`.
4. Leggi `output/results.md` e confronta i risultati della parte 1 con quelli della tesi: devono coincidere
   con SPSS. Se non coincidono, guardiamo insieme dove sta la differenza.

I dati in `data/simulated_thesis_data.csv` sono **inventati**: servono solo a provare il programma.
I dati veri non vanno pubblicati su GitHub.
