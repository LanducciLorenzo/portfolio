# EU dependence on critical raw materials: a data extension of my BSc thesis

**Lorenzo Landucci** · BSc Economics, University of Pisa (2026) · supervisor Prof. Gianmoena

My BSc thesis (*La diplomazia delle materie prime critiche: l'accordo di libero scambio UE-Australia e la
strategia europea di de-risking*) analysed the EU-Australia free trade agreement as a tool to reduce the
EU's dependence on China for critical raw materials. The thesis was qualitative. This project adds the numbers:

1. **How concentrated** are the EU's imports of lithium, rare earths, cobalt, natural graphite and
   rare-earth permanent magnets from outside the EU, and how has **China's share** changed since 2010?
2. **How much** would concentration fall if part of China's supply came from **Australia** instead?

## Main results (Eurostat data, release of 13 Nov 2026; averages 2023-2025, by value)

| Material | China's share | Largest supplier | HHI | Like ... equal suppliers |
|---|---|---|---|---|
| Permanent magnets | 89% (75% in 2010-12) | China | 7,964 | 1.3 |
| Natural graphite | 43% | China | 2,357 | 4.2 |
| Rare earths | 33% (43% by quantity) | China | 1,817 | 5.5 |
| Lithium | 23% (7% in 2010-12) | Chile (50%) | 3,222 | 3.1 |
| Cobalt | 19% | United States (20%) | 1,345 | 7.4 |

- The strongest dependence is not on the raw materials but on the **processed product**: China supplies
  about nine in ten permanent magnets the EU imports. It is the only case where one country is above 65%,
  the single-country limit that the Critical Raw Materials Act (Regulation (EU) 2024/1252) sets for strategic
  raw materials (measured there on consumption, not imports).
- For lithium the main concentration is on **Chile**, and China's share grew from 7% to 23%.
- Australia's **direct** share is close to zero. The exception is lithium oxide and hydroxide (HS 282520) in 2025 (EUR 9.7 million,
  8% of lithium imports that year). Part of Australia's role is hidden: much of the rare earths imported from
  **Malaysia** (26% by quantity) likely comes from the Lynas plant, which refines ore mined in Western Australia.
  Trade data record the last processing country, not the mine.
- In the scenario, moving supply from China to Australia lowers concentration a lot for magnets and graphite,
  and very little for lithium, where the dominant supplier is Chile.

Full report with tables, figures and limitations: [`results/report.md`](results/report.md).

## Method
- **Data:** Eurostat Comext DS-045409, annual EU-27 imports by partner country and HS 6-digit product,
  2010-2025, in euros and in kilograms (`data/eurostat_raw.csv`, downloaded via the Eurostat API, link below).
- **Extra-EU only:** intra-EU trade is excluded. Confidential or unspecified partners are excluded from
  shares and reported separately.
- **Concentration:** Herfindahl-Hirschman index (HHI, 0-10,000) and its inverse, the number of equal-sized
  suppliers that would give the same concentration.
- **Scenario:** a fraction (10%, 25%, 50%) of China's supply is reassigned to Australia, total unchanged.
  The code also finds the smallest shift that brings China to 65% or the HHI below 1,800.
  This is arithmetic, not a forecast.

## Checks
`python -m pytest` runs 41 tests:
- the data file is refused if it is cut off, duplicated or of the wrong type (Namibia's code "NA" is kept,
  not read as a missing value);
- for all 320 product × indicator × year combinations, country rows add up exactly to Eurostat's own
  extra-EU and intra-EU totals;
- every HHI and China share is recomputed a second time with the Python standard library only, without
  pandas or the project code;
- HHI and scenario functions are checked against textbook values and a closed-form formula on 300 random markets.

## Use
```
pip install -r requirements.txt
python -m pytest          # checks
python run_analysis.py    # writes results/report.md, results/*.csv, results/figures/*.png
```
To update the data, download this link and save it as `data/eurostat_raw.csv`:
```
https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1/data/DS-045409/A.EU27_2020..283691+282520+280530+284610+284690+810520+282200+250410+250490+850511.1.VALUE_IN_EUROS+QUANTITY_IN_100KG?format=SDMX-CSV&startPeriod=2010
```
Products, country groups and thresholds are set in `config.py`.

## Limitations
Imports are not consumption; country of origin is the last processing country; values move with prices
(lithium 2022-23); quantities add different compounds by weight; some HS6 codes are broad. See the report.

## Sources
- Eurostat, *EU trade since 1988 by HS2-4-6 and CN8* (DS-045409), Comext.
- Regulation (EU) 2024/1252 (Critical Raw Materials Act), Art. 5: 65% single-country benchmark.
- US DOJ and FTC, *Merger Guidelines* (2023): HHI above 1,800 = highly concentrated (used only as a reference).
