# OPD Triage Assistant 🏥

A beginner-friendly, end-to-end project that helps a busy government-hospital
**OPD (Out-Patient Department)** decide **who should see a doctor first**.

You type a patient's details and complaint (for example *"seene mein dard aur
pasina"* / *"chest pain and sweating"*), and the app instantly gives:

- a **triage priority from 1 to 5** (1 = life-threatening, 5 = routine),
- the **department** to send them to (Cardiology, Pediatrics, …), and
- any **red-flag warnings** it noticed.

The whole system is built around **safety**: it is designed so that it almost
never calls a real emergency "mild". That single idea is what makes this
project interesting.

> This README is written so that someone new to programming can run the whole
> thing from scratch. Take it step by step — you do **not** need to understand
> every line to run it.

---

## 📋 Table of contents

1. [What problem does this solve?](#1-what-problem-does-this-solve)
2. [What you need before you start](#2-what-you-need-before-you-start)
3. [Easiest way: run it online (no install)](#3-easiest-way-run-it-online-no-install)
4. [Run it on your own computer](#4-run-it-on-your-own-computer)
5. [What each command does (with sample output)](#5-what-each-command-does-with-sample-output)
6. [How to use the web app](#6-how-to-use-the-web-app)
7. [Understanding the results](#7-understanding-the-results)
8. [How it works inside (the safety pipeline)](#8-how-it-works-inside-the-safety-pipeline)
9. [Project structure (file by file)](#9-project-structure-file-by-file)
10. [Glossary (simple explanations)](#10-glossary-simple-explanations)
11. [Troubleshooting (common errors)](#11-troubleshooting-common-errors)
12. [How to present / explain this project](#12-how-to-present--explain-this-project)
13. [Notes, assumptions & credits](#13-notes-assumptions--credits)

---

## 1. What problem does this solve?

A real government hospital OPD can see **~800 walk-in patients a day with only 2
doctors**. Today patients are usually seen **first-come-first-served**, so a
person having a **heart attack can be stuck behind 40 people with a mild
fever**. A nurse has to make a quick "how urgent is this?" decision in about
**30 seconds** per patient.

This project is a software assistant for that 30-second decision. From a short
intake form + the patient's own words, it suggests how urgent the case is and
which department fits — **and it is deliberately careful never to downplay a
real emergency.**

**The key insight (and the whole point of the project):**
If you just build an ordinary machine-learning model that tries to be "accurate", it will look
great because ~95% of patients are not emergencies — but it will occasionally
call a true emergency "mild", which in a hospital can be fatal. So this project
is scored by a special rule: **missing an emergency is punished ~20× more
harshly than being over-cautious.** Everything in the code is designed around
that rule.

---

## 2. What you need before you start

If you use the **online option** (Section 3) you need **nothing** except a web
browser and a free GitHub account. 🎉

If you want to run it on your **own computer** (Section 4), you need **Python**
installed. That's the only thing you must install yourself — everything else
(pandas, scikit-learn, Streamlit, etc.) is downloaded automatically in one step
later. Follow the checks below; this assumes you have **nothing** installed yet.

### Step A — Do you already have Python?

Open a terminal and check:
- **Windows:** press `Start`, type **PowerShell**, press Enter. Then type:
  ```powershell
  python --version
  ```
- **Mac:** press `Cmd+Space`, type **Terminal**, press Enter. Then type:
  ```bash
  python3 --version
  ```

If it prints something like `Python 3.11.5` (any 3.9 or higher) ✅ you're done —
skip to Section 3 or 4. If it says *"not recognized"* / *"command not found"*,
do Step B.

### Step B — Install Python (if you don't have it)

**Windows**
1. Go to **https://www.python.org/downloads/** and click the big **Download
   Python** button.
2. Run the downloaded installer.
3. **VERY IMPORTANT:** on the first screen, tick the checkbox
   **"Add python.exe to PATH"** at the bottom ✅, *then* click **Install Now**.
   (This one checkbox is the #1 thing beginners forget — without it Windows
   can't find Python.)
4. When it finishes, **close and reopen PowerShell**, and run `python --version`
   again to confirm.

**Mac**
1. Go to **https://www.python.org/downloads/** and download the macOS installer.
2. Open it and click through **Continue → Install**.
3. Reopen Terminal and run `python3 --version` to confirm.
   (Alternatively, if you have Homebrew: `brew install python`.)

> **`pip` comes bundled with Python** — you do **not** install it separately.
> `pip` is the tool that will fetch this project's libraries for you in Section 4.

### Optional extras (nice but not required)

| Tool | Why you might want it | Where |
|------|-----------------------|-------|
| **Git** | to download the code with one command (otherwise just use the ZIP) | https://git-scm.com/downloads |
| **VS Code** | a friendly editor to read/edit the code | https://code.visualstudio.com/ |

### What gets installed automatically (you don't do this by hand)

In Section 4 the single command `pip install -r requirements.txt` downloads all
the libraries this project needs **from the internet** (so you need to be
online that one time). For reference, those libraries are:

- **pandas** & **numpy** – handling tables and numbers
- **scikit-learn** & **joblib** – the machine-learning model
- **streamlit** – turns the project into a web page

You do **not** need to know Python to run this — you just copy-paste commands.

---

## 3. Easiest way: run it online (no install)

This gives you a public website link that works on any phone or laptop — nothing
to install.

> 📝 **Before you start:** First upload this project to **your own** GitHub
> account (create a free account at https://github.com, make a new repository
> called `opd-triage-assistant`, and upload these files). Then, everywhere below
> you see `YOUR_GITHUB_USERNAME`, replace it with your own GitHub username.

1. Open this link and **sign in with a GitHub account**:
   👉 https://share.streamlit.io/deploy?repository=YOUR_GITHUB_USERNAME/opd-triage-assistant&branch=main&mainModule=app/streamlit_app.py
2. Click the **Deploy** button.
3. Wait ~1–2 minutes. You'll get a web address like
   `https://opd-triage-assistant-xxxx.streamlit.app`.
4. Open that address. The **first** time it loads it spends ~15 seconds building
   its model, then it's ready. Share the link with anyone.

> This works because the app **builds itself** on first run (it creates its own
> practice data and trains its model automatically). You don't have to do
> anything.

---

## 4. Run it on your own computer

You will copy-paste a few short commands. Pick your operating system below.

> 📁 **Already have the project folder?** If you were given the project as a ZIP
> (or downloaded it), just **unzip it**, then open your terminal **inside that
> folder** and **skip the `git clone` line** — start from the "Create a virtual
> environment" step. (On Windows you can open the terminal in the folder by
> `Shift + right-click` inside it → *"Open PowerShell window here"*.)

### 🪟 Windows (using PowerShell)

Open **PowerShell** (press `Start`, type *PowerShell*, hit Enter) and run these
one at a time:

```powershell
# 1. Download the code
git clone https://github.com/YOUR_GITHUB_USERNAME/opd-triage-assistant.git
cd opd-triage-assistant

# 2. Create an isolated "virtual environment" (keeps this project's packages separate)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install the required packages (one-time, ~1 minute)
pip install -r requirements.txt

# 4. Build everything: make data -> train model -> test it -> run simulation
python run_all.py

# 5. Start the web app (opens in your browser)
streamlit run app/streamlit_app.py
```

> If step 2 shows a **red "running scripts is disabled"** error, run this once,
> then repeat step 2:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```
> (Or, if you use the older **Command Prompt** instead of PowerShell, activate
> with `.venv\Scripts\activate.bat`.)

**No Git installed?** Instead of step 1, click the green **`< > Code`** button on
the [GitHub page](https://github.com/YOUR_GITHUB_USERNAME/opd-triage-assistant) → **Download
ZIP**, unzip it, then open PowerShell *inside* that folder and start from step 2.

### 🍎 macOS / 🐧 Linux (using Terminal)

```bash
# 1. Download the code
git clone https://github.com/YOUR_GITHUB_USERNAME/opd-triage-assistant.git
cd opd-triage-assistant

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install the required packages
pip install -r requirements.txt

# 4. Build everything
python run_all.py

# 5. Start the web app
streamlit run app/streamlit_app.py
```

When the app starts you'll see a line like `Local URL: http://localhost:8501`.
Open that link in your browser (it usually opens automatically). To stop the
app, press `Ctrl + C` in the terminal.

> **Do I have to run `run_all.py`?** The web app will build its model by itself
> the first time, so technically you can jump straight to step 5. But running
> `run_all.py` once is nice because it prints the project's scores so you can
> see everything working.

---

## 5. What each command does (with sample output)

`python run_all.py` runs four stages. Here is what they mean and roughly what
they print (your numbers will vary slightly each run):

**Stage 1 — Generate data.** Creates 30,000 fake-but-realistic patient records
to practice on (we can't use real patient data).
```
Generated 30000 records (24000 train / 6000 test)
True emergencies: 1557 (5.2%)
```

**Stage 2 — Train the model.** Teaches the model from 24,000 of those patients.
```
Trained on 24000 records.
Triage classes: [1, 2, 3, 4, 5]
```

**Stage 3 — Evaluate.** Tests the model on 6,000 *unseen* patients and prints the
real score. Example:
```
MEAN cost per patient     : 0.63        <- the real score (lower is better)
Under-triaged (danger)    : 0           <- never called an emergency "mild" ✅
Emergency sensitivity     : 98.1%       <- caught almost all true emergencies
Plain accuracy (MISLEADING): 61.1%      <- why "accuracy" is the wrong metric
```

**Stage 4 — Wait-time simulation (bonus).** Shows how much faster emergencies
would be seen if the hospital used this instead of first-come-first-served.
Example:
```
Avg wait EMERGENCIES  FCFS : 1158.8 min
Avg wait EMERGENCIES Triage:  168.7 min
Emergency wait reduction   :  -85%       <- emergencies seen ~85% sooner 🚑
```

You can also run any stage on its own:
```bash
python -m src.generate_data   # make the data
python -m src.train           # train the model
python -m src.evaluate        # print the score
python -m src.waittime        # the wait-time bonus
python -m src.predict         # quick test on 3 example patients
```

---

## 6. How to use the web app

Once `streamlit run app/streamlit_app.py` is running:

1. Fill in the patient's **age, sex, and vitals** (blood pressure, pulse,
   temperature, SpO₂). It's okay if some are wrong or missing — the app is built
   to handle messy data (e.g. a `0` blood pressure or a temperature typed in
   Fahrenheit).
2. Type the **chief complaint** in plain words. English, Hindi transliteration,
   or Hinglish all work (e.g. *"saans lene mein takleef"* = *"difficulty
   breathing"*).
3. Optionally add **known conditions** (like `diabetes`) and **medications**.
4. Click **Assess triage.**

The app shows a big colour-coded card with the **triage level** and target wait
time, the **recommended department**, the **red flags** it detected, which
**hard safety rules** fired, any **data-quality warnings**, and how **confident**
the model was.

Try these to see different behaviours:
- `runny nose and sore throat` → **Level 5** (routine), ENT
- `seene mein dard aur pasina` (chest pain + sweating) → **Level 1**, Emergency
- A patient with **SpO₂ 86** → the app **escalates to Level 1** no matter what
  the complaint says (that's a hard safety rule overriding the model).

---

## 7. Understanding the results

The project is **not** scored on normal "accuracy". Here's what the numbers mean
in plain terms:

| Term you'll see | What it means |
|-----------------|---------------|
| **Mean cost** | The real score. Lower is better. It punishes calling an emergency "mild" ~20× more than being over-cautious. |
| **Under-triaged** | Times the system called someone **less** urgent than they really were. This is the dangerous mistake — we want this at or near **0**. |
| **Over-triaged** | Times it was **too** cautious. This is "safe but wastes a little doctor time" — acceptable. |
| **Emergency sensitivity / recall** | Of all the true emergencies, what % did we catch? We want this very high (~98–100%). |
| **Abstentions** | Times the system said *"I'm not sure — send to a nurse now"* instead of guessing. Being honest here is rewarded. |
| **Plain accuracy** | Shown **only** to prove it's misleading: a lazy model can score high accuracy while still missing the few emergencies that matter. |

---

## 8. How it works inside (the safety pipeline)

For every patient the system does five things, in order:

1. **Clean the vitals.** Impossible values (0 blood pressure, SpO₂ of 0, a
   temperature of 96 "°C") are treated as *missing* instead of trusted. A
   Fahrenheit number typed into the Celsius box is auto-converted.
2. **Ask the model.** A machine-learning model reads the complaint text +
   vitals and estimates the chance of each triage level (1–5).
3. **Decide safely.** Instead of just picking the most likely level, it picks
   the level that is **safest given the 20× penalty** — so it leans urgent, and
   it **abstains** ("send to nurse") when it's genuinely unsure about a possible
   emergency.
4. **Apply hard safety rules.** A fixed rulebook (`src/escalation_rules.py`) can
   only ever make a case *more* urgent, never less — e.g. `SpO₂ < 85 → Level 1`,
   or chest-pain / stroke keywords → Level 1–2. Every rule that fires is shown.
5. **Output** the level, department, red flags, warnings and confidence.

The model itself is a **logistic regression** (a standard, explainable
technique) that reads the complaint text using **TF-IDF** (a way to turn words
into numbers) plus the cleaned vitals.

---

## 9. Project structure (file by file)

```
opd-triage-assistant/
├── README.md                 # this file
├── requirements.txt          # list of Python packages to install
├── run_all.py                # runs everything in one command
├── app/
│   └── streamlit_app.py      # the simple web app (the nurse's screen)
├── api/                      # optional: FastAPI backend (serves the ML + login)
│   ├── main.py               # HTTP endpoints (health, login, triage)
│   └── auth.py               # real staff authentication (hashed passwords + token)
├── web/                      # optional: React frontend (the "MediPriority" UI)
│   └── src/                  # see web/README.md to run it
├── docs/
│   ├── DOMAIN_PRIMER.md      # the medical background: triage scale + red flags
│   └── UI_IMPLEMENTATION_REPORT.md  # how the React login UI was built
└── src/                      # the brains of the project
    ├── triage_rubric.py      # defines the 5 triage levels & departments
    ├── conditions.py         # "recipes" used to generate realistic patients
    ├── generate_data.py      # creates the 30,000 practice patients
    ├── escalation_rules.py   # vitals cleaning + hard safety rules
    ├── features.py           # turns a patient into numbers the model understands
    ├── costs.py              # the 20× "missing an emergency is bad" rule
    ├── train.py              # trains the model
    ├── predict.py            # makes a decision for one patient
    ├── evaluate.py           # scores the model (the real grade)
    └── waittime.py           # the wait-time bonus simulation
```

> `data/` and `models/` folders are created automatically when you run the
> project; they are intentionally **not** stored in the repo so it stays small.

> **Two ways to use this project:**
> 1. **Simple (recommended for a quick demo):** the Streamlit app in `app/` —
>    one command, no extra tools. This is what Sections 3–6 above describe.
> 2. **Full UI (optional):** a React frontend (`web/`) with a login screen that
>    matches the "MediPriority" design, backed by a FastAPI server (`api/`) that
>    reuses the same model. It needs Node.js + a couple of extra steps —
>    see [`web/README.md`](web/README.md).

---

## 10. Glossary (simple explanations)

**Medical terms**
- **OPD** – Out-Patient Department (walk-in clinic; patients aren't admitted).
- **Triage** – sorting patients by how urgent they are.
- **ESI** – Emergency Severity Index, a real 5-level triage scale (Level 1 =
  most urgent).
- **Vitals** – body measurements: blood pressure (BP), pulse, temperature, and
  **SpO₂** (oxygen level in blood, where below ~90% is dangerous).
- **Red flag** – a warning sign that something could be serious (e.g. chest pain
  spreading to the arm).
- **Under-triage / Over-triage** – calling someone *less* urgent (dangerous) /
  *more* urgent (over-cautious) than they really are.

**Programming / machine-learning terms**
- **Python** – the programming language used here.
- **Virtual environment (`venv`)** – a private box for this project's packages so
  they don't clash with other projects.
- **Package / library** – reusable code written by others (installed via `pip`).
- **Model / training** – the program learns patterns from example patients
  ("training") so it can judge new ones.
- **Logistic regression** – a simple, well-understood prediction method.
- **TF-IDF** – a technique to turn sentences into numbers by looking at which
  words matter.
- **Streamlit** – the tool that turns the Python code into a web page.

---

## 11. Troubleshooting (common errors)

| Error message | Fix |
|---------------|-----|
| `'python' is not recognized` (Windows) | Python isn't on PATH. Reinstall Python and **tick "Add Python to PATH"**, or try typing `py` instead of `python`. |
| `running scripts is disabled on this system` (PowerShell) | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. Or use `.venv\Scripts\activate.bat`. |
| `pip is not recognized` | You forgot to activate the virtual environment (step 2), or Python wasn't added to PATH. |
| `ModuleNotFoundError: No module named 'pandas'` (or similar) | Packages aren't installed / env not active. Activate the env, then run `pip install -r requirements.txt`. |
| `Port 8501 is already in use` | Another app is using it. Run `streamlit run app/streamlit_app.py --server.port 8502`. |
| App says **"Model not found"** | Just run `python run_all.py` once, then restart the app. (Normally it self-builds.) |
| A yellow **scikit-learn version** warning appears | Harmless. To silence it, run `python run_all.py` to retrain on your machine. |
| Nothing opens in the browser | Copy the `Local URL` shown in the terminal (e.g. `http://localhost:8501`) and paste it into your browser. |

To exit the app: click the terminal and press **`Ctrl + C`**. To leave the
virtual environment: type `deactivate`.

---

## 12. How to present / explain this project

If you need to explain it in a viva or report, use this 4-sentence summary:

> "This project triages hospital OPD patients into 5 urgency levels from their
> vitals and their free-text complaint. The main challenge is **safety**:
> missing a real emergency is far worse than being over-cautious, so I score the
> system with an **asymmetric cost** that punishes under-triage ~20× more. On top
> of the machine-learning model I added a layer of **hard safety rules** (e.g.
> very low oxygen always becomes Level 1) and an **abstention** option where the
> system says *'send to a nurse'* instead of guessing. The result catches ~98%
> of emergencies with **zero dangerous under-triages** on the test set."

Good things to point to during a demo:
- Type a **mild complaint but set SpO₂ = 85** → show the hard rule forcing
  Level 1 (the model's opinion gets overruled for safety).
- Show the **evaluation output** where *under-triaged = 0* but *plain accuracy*
  is only ~61% → explains why accuracy is the wrong goal here.
- Show the **wait-time simulation** → emergencies seen ~85% sooner than
  first-come-first-served.

---

## 13. Notes, assumptions & credits

- The patient data is **synthetic** (computer-generated) — real medical records
  can't be shared publicly. The generator imitates the described setting:
  roughly ~5% true emergencies, complaint text written the way patients actually
  speak (across languages), and occasionally messy/missing vitals.
- The system uses **only the intake form** — no lab tests, X-rays, or ECG — just
  as the problem specifies.
- This is **decision support, not a diagnosis.** A human nurse always has the
  final say. The system is built to escalate or abstain rather than gamble on an
  emergency.
- To use real data later, match the column names defined in
  `src/generate_data.py` (`FEATURE_COLUMNS` / `LABEL_COLUMNS`).

---

*Built as a learning project. Questions? Open an issue on the
[GitHub repo](https://github.com/YOUR_GITHUB_USERNAME/opd-triage-assistant).*
