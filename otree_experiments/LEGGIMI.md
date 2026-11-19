# Esperimenti online in oTree – Lorenzo Landucci

Un unico progetto oTree con due esperimenti e gli script di analisi in Python.

| Cartella | Cosa contiene |
|---|---|
| `pgg_inequality/` | Esperimento 1: public goods game (disuguaglianza e cooperazione) |
| `drm_intro/`, `drm_study/`, `drm_distractor/`, `drm_test/`, `drm_questionnaire/` | Esperimento 2: falsi ricordi con il paradigma DRM, in 5 parti |
| `drm_common/` | Liste di parole, logica del DRM e questionario (file da modificare) |
| `analysis/` | Script di analisi in Python e dati finti per provarli |
| `tests/` | Test automatici della logica del DRM |
| `_static/drm_pictures/` | Le immagini per la condizione "pictures" (da aggiungere) |

---

## Esperimento 1 – Public goods game

**Domanda:** la disuguaglianza nelle dotazioni iniziali riduce la cooperazione?

**Disegno 2×2:**
- Dotazioni **uguali** (20, 20, 20, 20) o **disuguali** (10, 10, 30, 30). Il totale del gruppo è sempre 80.
- Gruppi **fissi** per tutti i round (partner) o **nuovi** a ogni round (stranger).

Gruppi da 4, 10 round, moltiplicatore 1,6, dotazioni degli altri visibili. Ogni giocatore mantiene la stessa dotazione per tutti i round, anche quando cambia gruppo.

**Ipotesi**
1. Con dotazioni disuguali la cooperazione media (quota della dotazione contribuita) è più bassa.
2. Chi ha la dotazione alta contribuisce una quota più bassa della propria dotazione.
3. Con gruppi fissi la cooperazione cala meno nel corso dei round.

**Novità rispetto alla prima versione**
- Domande di comprensione prima di iniziare: chi sbaglia deve riprovare.
- Tempo massimo di 120 secondi per decidere: chi non decide contribuisce 0 e viene segnalato (`timed_out`), così il gruppo non resta bloccato.
- Storico dei round precedenti nella pagina dei risultati.
- Questionario finale (età, genere, strategia) e pagina con il guadagno totale in euro.
- Variabile `is_high_endowment` per confrontare subito ricchi e poveri.

**Errori corretti**
- Con i punti interi oTree arrotondava la quota del progetto (es. 13 × 1,6 / 4 = 5,2 diventava 5). Ora i punti hanno 2 decimali.
- Il contributo ora è salvato come numero intero di punti, più semplice da controllare e da analizzare.

---

## Esperimento 2 – Falsi ricordi (DRM online)

**Domanda:** i falsi ricordi cambiano con la modalità di presentazione (parole scritte, parole ascoltate, immagini) e con lo stile cognitivo visivo-verbale?

**Procedura (circa 20 minuti)**
1. Consenso, dati demografici e, solo per la condizione uditiva, prova audio.
2. **Studio:** 6 liste da 12 elementi, uno ogni 2 secondi (1,5 s di presentazione + 0,5 s di pausa). Il partecipante preme Start, poi la lista scorre da sola.
3. **Rievocazione libera** dopo ogni lista (60 secondi), con punteggio automatico: parole corrette e intrusione della parola critica.
4. **Distrattore:** 2 minuti di calcoli, controllati sul server.
5. **Test di riconoscimento:** 48 parole, per ognuna "vecchia/nuova" (tasti F/J) e sicurezza da 1 a 4, con tempo di risposta.
6. Questionario visivo-verbale, controllo dell'attenzione, domande di consapevolezza e debriefing.

**Materiali e bilanciamento**
- 12 liste DRM classiche (Roediger e McDermott, 1995). **Da verificare** sulle norme pubblicate (Stadler et al., 1999) prima di uno studio vero.
- Ogni partecipante studia 6 liste (set A o B, alternati). Le altre 6 servono da controllo: la loro parola critica misura i "falsi allarmi di base".
- Ordine delle liste e degli item del test casuale per ogni partecipante.
- Modalità assegnata in modo bilanciato: ogni combinazione modalità × set di liste viene riempita in modo uguale.

**Misure principali (calcolate automaticamente)**
- `p_old_studied`: riconoscimenti corretti
- `p_old_critical_lure`: **falsi ricordi**
- `p_old_control_lure`: base di confronto
- `false_memory_corrected` = falsi ricordi − base
- `visual_minus_verbal`: indice di stile cognitivo dal questionario

**Robustezza**
- Ogni risposta del test viene salvata subito sul server: se la pagina si ricarica, il test riprende dalla parola giusta, senza perdere dati.
- Doppi clic e risposte arrivate in ritardo vengono ignorati.
- Viene registrato quante volte il partecipante cambia scheda durante le liste (`page_hidden_count`).
- Esportazione "lunga" (una riga per risposta) dalla pagina Data → Custom export di `drm_test`.

**Prima di usarlo davvero devi:**
1. Inserire gli item del tuo questionario in `drm_common/questionnaire_items.py` (ora ci sono segnaposto).
2. Per la condizione "pictures": mettere le immagini in `_static/drm_pictures/`, una per parola, con il nome della parola (es. `bed.png`). Se un'immagine manca, viene mostrata la parola scritta.
3. Sostituire i testi del consenso e del debriefing con quelli approvati per il tuo studio.
4. La condizione uditiva usa la voce del browser (funziona bene su Chrome, Edge e Safari da computer). Per uno studio vero è meglio registrare file audio.

---

## Come avviarlo

Serve un computer con **Python 3.10, 3.11 o 3.12**.
```
pip install otree
otree devserver
```
Poi apri **http://localhost:8000** nel browser e scegli una sessione demo.

**Test automatici con giocatori finti:**
```
otree test pgg_unequal_stranger
otree test drm_memory
python tests/test_logic.py
```

## Analisi in Python

Prova gli script sui dati finti:
```
pip install pandas scipy matplotlib
python analysis/simulate_data.py
python analysis/drm_analysis.py --demo
python analysis/pgg_analysis.py --demo
```
Con i dati veri, scarica le esportazioni dalla pagina Data di oTree:
```
python analysis/drm_analysis.py drm_test_custom_export.csv all_apps_wide.csv
python analysis/pgg_analysis.py pgg_inequality.csv
```
I grafici e le tabelle finiscono in `analysis/output/`. I dati in `analysis/demo_data/` sono **inventati**: servono solo a provare gli script.

## Cosa è stato verificato e cosa no
- Verificato: la logica di entrambi gli esperimenti (assegnazione delle condizioni, guadagni, punteggi, salvataggio e ripresa del test), il codice JavaScript delle pagine in un browser simulato, gli script di analisi.
- **Non** verificato: l'avvio dentro oTree vero e l'aspetto grafico delle pagine. Per questo serve `otree devserver` sul tuo computer.
