# NUMERIQ — Interactive Numerical Computing Lab
CS2008 Numerical Computing · FAST-NUCES Islamabad · M. Faizan Ansari (24I-6520), M. Saad Khan

Four pages: **Home**, **Method archive** (40 methods, lessons A–H), **Solver**, **Challenge arena**.
Every number comes from hand-written Python algorithms (`backend/methods/`), checked against NumPy/SciPy.

## Folder layout
```
NUMERIQ/
  backend/   Flask API + all algorithms (Python)
    methods/   one file per topic (root_finding.py, integration.py, ...)
    utils/     safe expression parser, plotting, input checks
    content/   lesson text + beginner Python examples
    tests/     test_numeriq.py
    app.py  registry.py  challenges.py  requirements.txt
  frontend/  React website (Vite)
    src/pages  Home, Learn, MethodDetail, Solver, Challenge
    src/data/team.js   <- edit names / roll numbers here
```

## Setup (one time)
Needs Python 3.10+ and Node.js 18+.
```
cd backend
pip install -r requirements.txt
cd ../frontend
npm install
```

## Before you proceed (run these first)
Run the front end and the back end in two separate terminals.

Front End:
```
cd frontend
npm run dev
```

Back End:
```
cd backend
python app.py
```

Then open: http://localhost:5173/

## Run — option 1: development (two terminals)
Terminal 1:  `cd backend` then `python app.py`   (API on http://127.0.0.1:5000)
Terminal 2:  `cd frontend` then `npm run dev`    (open the address it prints, usually http://localhost:5173)

## Run — option 2: single command
```
cd frontend
npm run build
cd ../backend
python app.py
```
Open http://127.0.0.1:5000

## Run the correctness tests
`cd backend` then `python tests/test_numeriq.py` — should print ALL TESTS PASSED.

## Demo tips
In the Solver, type your own function (e.g. `cos(x) - x`, `x^2*exp(-x)`) — the parser is safe (no eval).
Bad input shows a friendly message instead of crashing.
