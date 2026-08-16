# EconIB 🎓

A revision app for **IB Economics** (2027 syllabus, SL & HL). It keeps the three things every
exam answer needs — **definitions**, **diagrams** and **real-world examples** — in one place and
lets you link them together, instead of having them scattered across different apps and notebooks.

Built as my IB Computer Science Internal Assessment.

## What it does

- 📖 Store, search and filter **definitions, diagrams, real-world examples and answer structures**
  by section (Micro / Macro / Global), subtopic, level (SL/HL) and country
- 📦 Build **Study Kits** that link several definitions + one diagram + one example into a single view
- 🗂️ **Flashcards** with a Leitner spaced-repetition system (Again / Hard / Good / Easy)
- 🧮 A **grade calculator** that applies the 2027 IB weightings and estimates a 1–7 grade
- 📝 Personal **notes**, a saved **Library**, and private notes on each example
- Click any diagram to reveal its **IB-style explanation**

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + Flask |
| Frontend | HTML, CSS, JavaScript (no frameworks) |
| Storage | Local JSON files (no database server needed) |

## How to run it

You need **Python 3** installed. Then:

```bash
# 1. go into the project folder
cd EconIB

# 2. (optional but recommended) make a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate

# 3. install Flask
pip install -r requirements.txt

# 4. run the app
python3 app.py
```

Then open **http://127.0.0.1:5001** in your browser. To stop it, press `Ctrl + C` in the terminal.

> The diagrams are already included in `static/diagrams/`. If you ever want to redraw them from
> code, run `python3 gen_diagrams.py` (you don't need to for normal use).

## How it's organised

```
EconIB/
├── app.py                 # Flask: the routes + the small JSON API
├── models.py              # the OOP classes (Definition, Diagram, StudyKit, Flashcard, Note...)
├── datastore.py           # loads/saves everything to the JSON files
├── leitner.py             # the spaced-repetition algorithm
├── grade_calculator.py    # the weighted grade algorithm
├── gen_diagrams.py        # one-off script that draws the 15 SVG diagrams
├── requirements.txt
├── data/
│   ├── seed_data.json     # the built-in content (definitions, diagrams, examples...)
│   └── user_data.json     # everything you create (made automatically on first run)
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── diagrams/          # the 15 diagram images (.svg)
└── templates/             # the HTML pages (base.html + one per screen)
```

## About the data

There's no separate database program — the "database" is just the two JSON files in `data/`:
- `seed_data.json` is the built-in content (read-only).
- `user_data.json` is whatever you add or change; the app creates it on first run.

## Note on AI use

I built this myself while learning Python, and I used an AI assistant (Claude) to help with a few
of the harder parts. Those spots are marked with `AI help` comments in the code.
