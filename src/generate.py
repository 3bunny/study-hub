"""
Generate the course content with Gemini and write data/course.json.

Pipeline per subject:
  1. outline  -> 10-12 chapters, beginner -> advanced.
  2. chapter  -> structured content (blocks, key terms, exercises, links).

Resilient: a failed chapter becomes a small placeholder so the build still works.
Run in CI where GEMINI_API_KEY is set:  python src/generate.py
"""

import datetime as dt
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import gemini_client  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_cfg():
    with open(os.path.join(ROOT, "config", "subjects.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def gen_outline(subject, audience, n):
    prompt = (
        f"You are designing a progressive self-study course on '{subject['title']}' "
        f"for {audience}. Scope: {subject['description']}\n"
        f"Produce exactly {n} chapters that build from absolute beginner foundations "
        "to advanced, each relying on the previous ones. Cover the practical, "
        "job-relevant essentials.\n"
        'Return JSON: {"chapters": [{"title": str, "level": "Beginner"|"Intermediate"'
        '|"Advanced", "focus": str (one sentence on what it teaches)}]}'
    )
    r = gemini_client.generate_json(prompt, max_output_tokens=2048)
    if isinstance(r, dict) and isinstance(r.get("chapters"), list) and r["chapters"]:
        return r["chapters"][:n]
    # minimal fallback outline
    return [{"title": f"{subject['title']} — Part {i+1}", "level": "Beginner",
             "focus": "Core concepts."} for i in range(min(n, 4))]


def gen_chapter(subject, ch, all_titles, audience):
    prompt = (
        f"Write the full chapter '{ch['title']}' (level: {ch.get('level','Beginner')}) "
        f"of a self-study course on '{subject['title']}' for {audience}.\n"
        f"Chapter focus: {ch.get('focus','')}\n"
        f"It sits within this overall outline (assume earlier chapters are known): "
        f"{all_titles}\n\n"
        "Teach clearly and progressively with concrete examples. For Power BI, give "
        "exact step-by-step UI instructions (menus, buttons) and real DAX where useful. "
        "For modeling, explain the intuition first, then the method, then a worked "
        "example. Keep it practical and encouraging.\n\n"
        "Return JSON with this exact shape:\n"
        '{"summary": str (2-3 sentence intro),'
        ' "blocks": [ one of:'
        ' {"type":"h","text":str} (subheading),'
        ' {"type":"p","text":str} (paragraph),'
        ' {"type":"list","items":[str]} (bullets),'
        ' {"type":"steps","items":[str]} (numbered steps),'
        ' {"type":"code","text":str,"lang":str} (formula/snippet, e.g. DAX),'
        ' {"type":"tip","text":str} (callout) ],'
        ' "key_terms":[{"term":str,"def":str}],'
        ' "exercises":[str (a hands-on task or question)],'
        ' "links":[{"title":str,"url":str}] }\n'
        "For links, ONLY use real, well-known official URLs (e.g. learn.microsoft.com). "
        "If unsure of an exact URL, omit it. Aim for 8-16 blocks."
    )
    r = gemini_client.generate_json(prompt, max_output_tokens=8192)
    if isinstance(r, dict) and isinstance(r.get("blocks"), list) and r["blocks"]:
        r.setdefault("summary", "")
        r.setdefault("key_terms", [])
        r.setdefault("exercises", [])
        r.setdefault("links", [])
        return r
    return {"summary": "", "blocks": [
        {"type": "p", "text": "This chapter could not be generated on the last run. "
         "Re-run the build to populate it."}], "key_terms": [], "exercises": [], "links": []}


def main():
    cfg = load_cfg()
    audience = cfg.get("audience", "a beginner")
    n = int(cfg.get("chapters_per_subject", 11))
    print(f"[gen] LLM available: {gemini_client.available()}")

    course = {"built": dt.datetime.utcnow().strftime("%Y-%m-%d"), "subjects": []}
    for subject in cfg["subjects"]:
        print(f"[gen] {subject['title']}: outline...")
        outline = gen_outline(subject, audience, n)
        titles = [c["title"] for c in outline]
        chapters = []
        for i, ch in enumerate(outline):
            print(f"[gen]   ch {i+1}/{len(outline)}: {ch['title']}")
            content = gen_chapter(subject, ch, titles, audience)
            chapters.append({
                "title": ch["title"], "level": ch.get("level", "Beginner"),
                "focus": ch.get("focus", ""), **content})
        course["subjects"].append({
            "key": subject["key"], "title": subject["title"],
            "description": subject.get("description", ""), "chapters": chapters})

    d = os.path.join(ROOT, "data")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "course.json"), "w", encoding="utf-8") as f:
        json.dump(course, f, ensure_ascii=False, indent=2)
    print(f"[gen] wrote course.json ({sum(len(s['chapters']) for s in course['subjects'])} chapters); "
          f"gemini ok/fail={gemini_client.STATUS['ok']}/{gemini_client.STATUS['fail']}")


if __name__ == "__main__":
    main()
