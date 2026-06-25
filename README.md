# Study Hub 📚

A self-paced, AI-authored textbook site. Two subjects to start:

- **Power BI** — connecting data, Power Query, data modeling, DAX, reports.
- **Predictive Modeling & What-If Planning** — forecasting, predictive models, and scenario planning.

Each subject runs **Beginner → Intermediate → Advanced**, with key terms, practice
exercises, official-doc links, a glossary, progress tracking, and a **Bionic Reading**
toggle. It's one clean static site served by GitHub Pages.

## How it works
`generate.py` (Gemini) writes the curriculum to `data/course.json`; `build_site.py`
renders it into `docs/index.html`. Content is generated on demand, not on a schedule.

## One-time setup
1. Add your free Gemini key as a repo secret named `GEMINI_API_KEY`
   (Settings → Secrets and variables → Actions).
2. Enable Pages: Settings → Pages → Deploy from a branch → `main` / `/docs`.
3. Actions tab → **Build Study Hub** → **Run workflow**. Wait a few minutes.
4. Open your Pages URL.

## Regenerate / expand
Edit `config/subjects.yaml` (add subjects, change `chapters_per_subject`), then run the
workflow again. It's AI-written study material — verify high-stakes specifics against the
linked official docs.

## Local preview (no key)
```bash
python src/build_site.py --course config/mock_course.json
# open docs/index.html
```
