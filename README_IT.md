# SENTRY.mark 🛡️
### Motore Automatizzato di Rilevamento Anomalie per Dati di Marketing Digitale

> 🇬🇧 [Read in English](README.md)

---

> SENTRY.mark è un motore automatizzato di rilevamento anomalie per dati di marketing digitale. Monitora i dati GA4 da BigQuery, rileva deviazioni statisticamente significative tramite baseline Z-Score rolling, classifica le anomalie per impatto di business e attiva alert Slack in tempo reale con un layer simulato di protezione del budget. L'obiettivo è spostare il marketing analytics dal reporting passivo al monitoraggio attivo dell'integrità dei dati.

---

## Il Problema

Nel marketing digitale, **la latenza nel rilevare anomalie costa migliaia di euro** in budget sprecato e decisioni basate su dati corrotti.

I report standard sono passivi: mostrano il problema quando è già troppo tardi.

Un bot attack svuota silenziosamente il budget CPC. Un tag di tracciamento rotto rende le campagne cieche. Una 404 su una landing page brucia la spesa pubblicitaria senza alcun ritorno. Quando arriva il report settimanale, il danno è già fatto.

**SENTRY.mark è stato costruito per cambiare questo.**

---

## La Soluzione

SENTRY.mark è un **Watchdog Engine** automatizzato per i dati di marketing digitale. Non è una semplice dashboard — è un sistema di rilevamento statistico che:

1. Interroga i dati raw GA4 da Google BigQuery
2. Identifica deviazioni statisticamente significative tramite modelli Z-Score
3. Classifica le anomalie per tipo e impatto di business
4. Attiva alert Slack in tempo reale e simula un layer di protezione del budget
5. Visualizza tutto in una dashboard esecutiva Power BI

> **Questo progetto trasforma l'analista da osservatore passivo del passato a custode attivo dell'integrità del business.**

---

## Tech Stack

| Strumento | Ruolo | Perché |
|---|---|---|
| Google BigQuery | Data Warehouse / Sorgente GA4 | Standard di settore per analytics su larga scala |
| SQL (Standard Dialect) | Data modeling con CTE | Query pulite, strutturate e production-grade |
| Python (Pandas, SciPy) | Motore statistico | Z-Score rolling e logica alert |
| Power BI (PL-300) | Dashboard esecutiva | Layer di reporting enterprise |
| Slack Webhooks | Alerting in tempo reale | Notifica operativa immediata |
| GitHub Actions | Automazione / CI-CD | Esecuzione schedulata del pipeline — nessun intervento umano |

---

## Architettura

```
┌─────────────────────────────────────┐
│            DATA LAYER               │
│  Dataset Pubblico GA4 BigQuery      │
│         ↓                           │
│  SQL — Trasformazione CTE           │
│  ga4_daily_metrics                  │
│         +                           │
│  synthetic_anomalies (chaos eng.)   │
│         ↓                           │
│  fact_daily_metrics_enriched        │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         DETECTION LAYER             │
│  Python — Motore Z-Score Rolling    │
│  Finestra 7 giorni per canale       │
│  Severity scoring: MEDIUM/HIGH/CRIT │
│         ↓                           │
│  anomalies_detected.csv             │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│        ACTIVATION LAYER             │
│  Alert Classifier → alerts.json     │
│  Kill-Switch Simulator              │
│  Notifiche Slack in Tempo Reale     │
│         ↓                           │
│  Dashboard Esecutiva Power BI       │
└─────────────────────────────────────┘
```

---

## Il Motore Statistico

### Come Funziona lo Z-Score

Lo Z-Score misura quanto un valore si discosta dal suo comportamento normale recente.

```
Z = (valore osservato - media mobile) / deviazione standard mobile
```

**Perché la media mobile e non la media globale?**
Il traffico digitale non è stazionario — novembre e gennaio si comportano in modo diverso. Usare una finestra mobile di 7 giorni significa confrontare ogni giorno con il suo contesto recente, non con una media che include stagionalità diverse. È lo stesso principio usato nei sistemi di monitoring industriale.

**La soglia 1.96**
Uno Z-Score superiore a 1.96 significa che il valore cade fuori dal 95% dei casi normali — c'è solo il 5% di probabilità che si tratti di fluttuazione casuale. È la soglia standard per un test di ipotesi a due code con α = 0.05.

### Bande di Severità

| Z-Score | Severità | Significato Statistico |
|---|---|---|
| 1.96 – 3.0 | MEDIUM | Fuori dal 95% della distribuzione normale |
| 3.0 – 4.0 | HIGH | Fuori dal 99.7% — evento raro |
| > 4.0 | CRITICAL | Statisticamente impossibile per caso |

---

## Catalogo delle Anomalie

### 🤖 Bot Attack
**Cosa succede:** Le sessioni esplodono, il tasso di conversione scende a 0%, il bounce rate raggiunge il 100%.
**Impatto di business:** Stai pagando CPC/CPM per traffico non umano che non convertirà mai. Con un budget di €10k/mese, anche il 20% di traffico bot significa €2.000 sprecati.
**Protocollo:** AZIONE IMMEDIATA — revisione della spesa pubblicitaria.

### 📡 Tracking Break
**Cosa succede:** Le sessioni su un canale attivo crollano a quasi zero. Il segnale sparisce completamente.
**Impatto di business:** Ogni decisione di ottimizzazione presa mentre il tracciamento è rotto si basa su dati falsi. Sposti budget su canali che sembrano performare ma non performano.
**Protocollo:** AZIONE IMMEDIATA — verifica il firing del tag GTM e il data stream GA4.

### 👻 Ghost 404
**Cosa succede:** Il volume di traffico è normale, ma la revenue è zero e il bounce rate è al 100%.
**Impatto di business:** Ogni click a pagamento atterra su una pagina rotta. Il budget della campagna continua a girare; le conversioni sono zero.
**Protocollo:** AZIONE IMMEDIATA — controlla l'URL della landing page e le regole di redirect.

### 📈 PPC Spike
**Cosa succede:** Le sessioni aumentano del 300%+ senza un aumento proporzionale di revenue o conversioni.
**Impatto di business:** Un errore nella strategia di bidding o un bug della piattaforma sta bruciando il budget giornaliero in poche ore invece di 24h. Lo scopri a fine giornata — troppo tardi.
**Protocollo:** REPORT SETTIMANALE — revisione della strategia di bidding e impatto sul ROAS.

### 💱 Currency / Tax Glitch
**Cosa succede:** Il numero di acquisti è normale, ma la revenue è 10 volte il valore atteso.
**Impatto di business:** Il management prende decisioni strategiche su numeri gonfiati — allocazione budget, forecast, obiettivi — tutti basati su dati corrotti.
**Protocollo:** AZIONE IMMEDIATA — audit del layer di validazione dati nel checkout.

---

## Kill-Switch Simulator

Il Kill-Switch si attiva solo quando **entrambe** le condizioni sono soddisfatte:

1. Il tipo di anomalia è classificato come errore tecnico (bot attack, ghost 404, tracking break)
2. Z-Score ≥ 3.0 — l'evento è fuori dal 99.7% dei casi normali

La doppia condizione previene i falsi positivi. Non fermi la spesa per una fluttuazione statistica — solo per un evento tecnicamente grave e statisticamente estremo.

> **Nota:** In questa versione portfolio, il kill-switch non modifica campagne pubblicitarie reali. Genera un log decisionale e un alert Slack con raccomandazione di sospensione. In produzione, questo layer sarebbe integrato con le Ads API dietro un workflow di approvazione human-in-the-loop.

---

## Dashboard

### Pagina 1 — Command Center
Overview in tempo reale: KPI card, gauge Z-Score con soglia di allerta 1.96, trend delle anomalie nel tempo per canale, distribuzione per canale e tipo.

![Command Center](docs/images/page1.png)

### Pagina 2 — Deep Dive
Drill-down operativo: log dettagliato delle anomalie con slicer interattivo per tipo, frequenza delle anomalie per tipo, e raccomandazioni A/B test basate sulle anomalie rilevate.

![Deep Dive](docs/images/page2.png)

---

## Struttura del Progetto

```
sentry_mark/
├── data/
│   ├── raw/                    # Dati estratti da BigQuery (CSV)
│   ├── processed/              # Output Z-Score con flag anomalie
│   └── anomalies/              # Alert JSON e log kill-switch
├── src/
│   ├── ingestion/
│   │   └── extract_bigquery.py # Connessione a BigQuery ed export dati
│   ├── detection/
│   │   └── zscore_engine.py    # Motore di calcolo Z-Score rolling
│   └── alerting/
│       ├── alert_classifier.py # Classifica anomalie per tipo e protocollo
│       ├── kill_switch.py      # Valuta le condizioni di blocco spesa
│       └── slack_notifier.py   # Invia alert Slack in tempo reale
├── dashboard/
│   └── SENTRY.mark.pbix        # File dashboard Power BI
├── docs/
│   └── images/                 # Screenshot della dashboard
├── .github/
│   └── workflows/
│       └── sentry_pipeline.yml # Automazione GitHub Actions
├── .env                        # Variabili d'ambiente (non committato)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Come Eseguire il Progetto

### Prerequisiti

- Python 3.10+
- Account Google Cloud con BigQuery API abilitata
- Dataset BigQuery con dati GA4 (o usa il dataset pubblico `bigquery-public-data.ga4_obfuscated_sample_ecommerce`)
- Workspace Slack con Incoming Webhook configurato
- Power BI Desktop

### 1. Clona il repository

```bash
git clone https://github.com/your-username/sentry-mark.git
cd sentry-mark
```

### 2. Crea e attiva il virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 4. Configura le variabili d'ambiente

Crea un file `.env` nella root del progetto:

```
GOOGLE_APPLICATION_CREDENTIALS=./your-service-account-key.json
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
```

### 5. Esegui il pipeline

```bash
# Step 1 — Estrai i dati da BigQuery
python src/ingestion/extract_bigquery.py

# Step 2 — Esegui il rilevamento anomalie Z-Score
python src/detection/zscore_engine.py

# Step 3 — Classifica le anomalie
python src/alerting/alert_classifier.py

# Step 4 — Valuta le condizioni del kill-switch
python src/alerting/kill_switch.py

# Step 5 — Invia le notifiche Slack
python src/alerting/slack_notifier.py
```

### 6. Apri la dashboard

Apri `dashboard/SENTRY.mark.pbix` in Power BI Desktop e aggiorna la connessione dati.

---

## Chaos Engineering — Anomalie Sintetiche

Per validare il motore di rilevamento, cinque anomalie sintetiche sono state iniettate nei dati GA4 reali tramite insert SQL controllati:

| Anomalia | Data | Canale | Metrica Attivata |
|---|---|---|---|
| Tracking Break | 2020-11-08 | Organic / Google | Sessioni → 0 |
| Bot Attack | 2020-11-15 | CPC / Google | Spike sessioni, CVR = 0% |
| PPC Spike | 2020-11-22 | CPC / Google | Sessioni +300%, revenue invariata |
| Ghost 404 | 2020-11-29 | Email / Newsletter | Revenue = 0, bounce = 100% |
| Currency/Tax Glitch | 2021-01-10 | Organic / Google | Revenue x10 |

Tutte e 5 le anomalie sono state rilevate con successo con `is_synthetic_anomaly = TRUE`.

---

## Limitazioni

Questo progetto utilizza un dataset GA4 pubblico offuscato e anomalie sintetiche. È progettato come prototipo portfolio, non come sistema di monitoring production deployato.

Limitazioni note:
- Lo Z-Score rolling assume distribuzioni metriche relativamente stabili. In produzione, baseline adattive o correzione della stagionalità day-of-week migliorerebbero la precisione.
- I canali a basso volume possono produrre alert rumorosi per i pochi punti dati nella finestra rolling.
- I valori di bounce rate sono prossimi allo zero per l'offuscamento del dataset — completamente popolati in un ambiente GA4 reale.
- Il kill-switch è simulato e non modifica campagne pubblicitarie reali.
- In produzione, sarebbero richiesti approvazione umana e governance delle Ads API prima di qualsiasi azione automatica sul budget.

---

## Production Roadmap

- Sostituire le soglie Z-Score fisse con baseline adattive
- Aggiungere correzione stagionalità day-of-week (confrontare i lunedì con i lunedì)
- Aggiungere rilevamento anomalie robusto MAD / IQR per distribuzioni non gaussiane
- Aggiungere integrazione Google Ads API in modalità read-only
- Aggiungere workflow di approvazione umana prima della sospensione campagne
- Archiviare la storia delle anomalie in BigQuery invece che in JSON locale
- Aggiungere modelli dbt per il layer di trasformazione SQL
- Aggiungere unit test e validazione CI
- Aggiungere deployment Docker
- Aggiungere versione Looker Studio della dashboard

---

## Target Role

Questo progetto dimostra competenze end-to-end per:

- **Marketing Data Analyst**
- **Digital Analytics Specialist**
- **Junior Analytics Engineer**
- **Marketing Operations Analyst**
- **Growth Data Analyst**

Competenze dimostrate: estrazione e modellazione dati su larga scala (BigQuery + SQL), analisi statistica e rilevamento anomalie (Python + SciPy), implementazione logica di business (classificazione alert, kill-switch simulator), comunicazione esecutiva (dashboard Power BI), automazione production-ready (GitHub Actions).

---

## Autrice

**Francesca**
Marketing Data Analyst | Digital Analytics | BigQuery | Power BI | Python

[LinkedIn](https://www.linkedin.com/in/francesca-monte/) · [GitHub](https://github.com/francescaetnom-wq)
