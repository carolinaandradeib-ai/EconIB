"""app.py it is the flash part that is responsable for two main jobs: first, they are the actual web pages (the html) and has a little "API" 
that my Java script calls to add/edit/delete things without reloading the whole page.
this is the flask part. 

AI help (Claude): flask was completely new to me, as I'm only used to Python so Claude helped me set up the routing and the
general API pattern (read the json the page sent -> check it's valid -> do it -> send something back with a status code like 200/400). 
Once i understood the pattern i wrote the rest of the routes myself as they're all basically the same shape.

run it with:  python3 app.py   then open http://127.0.0.1:5001"""

from flask import Flask, render_template, request, jsonify, abort

import grade_calculator
import leitner
from datastore import DataStore
from models import (Definition, Diagram, RealWorldExample, StudyKit,
                    Flashcard, Note)

app = Flask(__name__)
store = DataStore()

SECTIONS = {
    "micro": {
        "name": "Microeconomics",
        "icon": "🔬",
    },
    "macro": {
        "name": "Macroeconomics",
        "icon": "📍",
    },
    "global": {
        "name": "The Global Economy",
        "icon": "🌍",
    },
}
SUBTOPICS = {
    "micro": ["Demand & Supply", "Elasticities", "Government Intervention",
              "Market Failure", "Market Power (HL)",
              "Behavioural Economics (HL)"],
    "macro": ["Measuring Economic Activity", "AD & AS",
              "Macroeconomic Objectives", "Inequality & Poverty",
              "Demand-side Policies", "Supply-side Policies"],
    "global": ["Benefits of Trade", "Trade Protection", "Exchange Rates",
               "Balance of Payments", "Economic Integration",
               "Economic Development"],
}

def check_section(section):
    if section not in SECTIONS:
        abort(404)

@app.context_processor
def template_helpers():
    return {
        "SECTIONS": SECTIONS,
        "SUBTOPICS": SUBTOPICS,
        "in_library": store.in_library,
        "has_flashcard": store.has_flashcard,
        "due_count": len(leitner.due_cards(store.flashcards())),
    }


# Pages 

@app.route("/")
def home():
    return render_template("home.html", active="home")

@app.route("/section/<section>")
def section_home(section):
    check_section(section)
    counts = {
        "definitions": len(store.filtered("definitions", section=section)),
        "diagrams": len(store.filtered("diagrams", section=section)),
        "examples": len(store.filtered("examples", section=section)),
        "structures": len(store.dev.get("structures", [])),
    }
    return render_template("section.html", section=section, counts=counts,
                           active="home")

@app.route("/section/<section>/definitions")
def definitions_page(section):
    check_section(section)
    items = store.filtered("definitions", section=section)
    return render_template("definitions.html", section=section, items=items,
                           active="home")

@app.route("/section/<section>/diagrams")
def diagrams_page(section):
    check_section(section)
    items = store.filtered("diagrams", section=section)
    all_images = sorted({d.image for d in store.all("diagrams")})
    return render_template("diagrams.html", section=section, items=items,
                           all_images=all_images, active="home")

@app.route("/section/<section>/examples")
def examples_page(section):
    check_section(section)
    items = store.filtered("examples", section=section)
    countries = sorted({i.country for i in items})
    diagrams = store.filtered("diagrams", section=section)
    definitions = store.filtered("definitions", section=section)
    notes_by_rwe = {i.id: store.example_notes(i.id) for i in items}
    return render_template("examples.html", section=section, items=items,
                           countries=countries, diagrams=diagrams,
                           definitions=definitions,
                           notes_by_rwe=notes_by_rwe,
                           get_diagram=lambda i: store.get("diagrams", i),
                           get_definition=lambda i: store.get("definitions", i),
                           active="home")

@app.route("/section/<section>/structures")
def structures_page(section):
    check_section(section)
    items = store.dev.get("structures", [])
    return render_template("structures.html", section=section, items=items,
                           active="home")


@app.route("/library")
def library_page():
    groups = {"definition": [], "diagram": [], "rwe": [], "kit": []}
    collection_for = {"definition": "definitions", "diagram": "diagrams",
                      "rwe": "examples", "kit": "kits"}
    for saved in store.library_items():
        obj = store.get(collection_for.get(saved["type"], ""), saved["id"])
        if obj:
            groups.setdefault(saved["type"], []).append(obj)
    return render_template("library.html", groups=groups, active="library")

@app.route("/calculator")
def calculator_page():
    return render_template("calculator.html",
                           components=grade_calculator.components,
                           active="calculator")

@app.route("/notes")
def notes_page():
    return render_template("notes.html", notes=store.all("notes"),
                           active="notes")

@app.route("/kits")
def kits_page():
    kits = store.all("kits")
    return render_template("kits.html", kits=kits,
                           definitions=store.all("definitions"),
                           diagrams=store.all("diagrams"),
                           examples=store.all("examples"),
                           active="kits")

@app.route("/kits/<kit_id>")
def kit_detail(kit_id):
    kit = store.get("kits", kit_id)
    if not kit:
        abort(404)
    definitions = [store.get("definitions", d) for d in kit.definition_ids]
    definitions = [d for d in definitions if d]
    diagram = store.get("diagrams", kit.diagram_id) if kit.diagram_id else None
    rwe = store.get("examples", kit.rwe_id) if kit.rwe_id else None
    return render_template("kit_detail.html", kit=kit,
                           definitions=definitions, diagram=diagram,
                           rwe=rwe, active="kits")

@app.route("/flashcards")
def flashcards_page():
    cards = store.flashcards()
    due = leitner.due_cards(cards)
    return render_template("flashcards.html", total=len(cards),
                           due_total=len(due), active="flashcards")


#  API: definitions 
#  Claude helped me with this part of the code, so I reproduced in the other sections.
@app.route("/api/definitions", methods=["POST"])
def api_add_definition():
    data = request.get_json()
    required = ["term", "definition", "section", "subtopic", "level"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        # 400 = error message
        return jsonify({"errors": [f"Missing field: {f}" for f in missing]}), 400
    obj = Definition(data["term"].strip(), data["definition"].strip(),
                     data["section"], data["subtopic"], data["level"])
    store.add("definitions", obj)
    return jsonify(obj.to_dict()), 201     # 201 = New Item


@app.route("/api/definitions/<obj_id>", methods=["PUT", "DELETE"])
def api_edit_definition(obj_id):
    if not store.is_user_item("definitions", obj_id):
        return jsonify({"errors": ["Only items you created can be edited or deleted."]}), 403
    if request.method == "DELETE":
        store.delete("definitions", obj_id)
        return jsonify({"ok": True})
    store.update("definitions", obj_id, request.get_json())
    return jsonify({"ok": True})


# API: diagrams

@app.route("/api/diagrams", methods=["POST"])
def api_add_diagram():
    data = request.get_json()
    required = ["title", "section", "subtopic", "level", "image", "explanation"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        return jsonify({"errors": [f"Missing field: {f}" for f in missing]}), 400
    obj = Diagram(data["title"].strip(), data["section"], data["subtopic"],
                  data["image"], data["explanation"].strip(), data["level"])
    store.add("diagrams", obj)
    return jsonify(obj.to_dict()), 201

@app.route("/api/diagrams/<obj_id>", methods=["PUT", "DELETE"])
def api_edit_diagram(obj_id):
    if not store.is_user_item("diagrams", obj_id):
        return jsonify({"errors": ["Only items you created can be edited or deleted."]}), 403
    if request.method == "DELETE":
        store.delete("diagrams", obj_id)
        return jsonify({"ok": True})
    store.update("diagrams", obj_id, request.get_json())
    return jsonify({"ok": True})

# API: real-world examples 

@app.route("/api/examples", methods=["POST"])
def api_add_example():
    data = request.get_json()
    required = ["title", "description", "section", "subtopic", "country"]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        return jsonify({"errors": [f"Missing field: {f}" for f in missing]}), 400
    obj = RealWorldExample(
        data["title"].strip(), data["description"].strip(), data["section"],
        data["subtopic"], data["country"].strip(),
        data.get("data_context", "").strip(),
        data.get("linked_diagram_id") or None,
        data.get("linked_definition_ids", []))
    store.add("examples", obj)
    return jsonify(obj.to_dict()), 201


@app.route("/api/examples/<obj_id>", methods=["PUT", "DELETE"])
def api_edit_example(obj_id):
    if not store.is_user_item("examples", obj_id):
        return jsonify({"errors": ["Only items you created can be edited or deleted."]}), 403
    if request.method == "DELETE":
        store.delete("examples", obj_id)
        return jsonify({"ok": True})
    store.update("examples", obj_id, request.get_json())
    return jsonify({"ok": True})


@app.route("/api/examples/<obj_id>/notes", methods=["POST"])
def api_add_example_note(obj_id):
    text = (request.get_json().get("text") or "").strip()
    if not text:
        return jsonify({"errors": ["Note text cannot be empty."]}), 400
    note = store.add_example_note(obj_id, text)
    return jsonify(note), 201


# API: study kits

@app.route("/api/kits", methods=["POST"])
def api_add_kit():
    data = request.get_json()
    kit = StudyKit(
        title=(data.get("title") or "").strip(),
        section=data.get("section") or "",
        subtopic=data.get("subtopic") or "",
        definition_ids=data.get("definition_ids", []),
        diagram_id=data.get("diagram_id") or None,
        rwe_id=data.get("rwe_id") or None)
    errors = kit.validate()
    if errors:
        return jsonify({"errors": errors}), 400
    store.add("kits", kit)
    return jsonify(kit.to_dict()), 201


@app.route("/api/kits/<obj_id>", methods=["DELETE"])
def api_delete_kit(obj_id):
    if not store.delete("kits", obj_id):
        return jsonify({"errors": ["Kit not found."]}), 404
    return jsonify({"ok": True})


# API: notes

@app.route("/api/notes", methods=["POST"])
def api_add_note():
    data = request.get_json()
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"errors": ["A note needs a title."]}), 400
    note = Note(title, data.get("content", ""))
    store.add("notes", note)
    return jsonify(note.to_dict()), 201


@app.route("/api/notes/<obj_id>", methods=["PUT", "DELETE"])
def api_edit_note(obj_id):
    if request.method == "DELETE":
        store.delete("notes", obj_id)
        return jsonify({"ok": True})
    store.update("notes", obj_id, request.get_json())
    return jsonify({"ok": True})


#  API: flashcards(leitner) 

@app.route("/api/flashcards", methods=["POST"])
def api_add_flashcard():
    data = request.get_json()
    source_type, source_id = data.get("source_type"), data.get("source_id")
    if source_type not in ("definition", "diagram", "rwe"):
        return jsonify({"errors": ["Invalid flashcard source."]}), 400
    if store.has_flashcard(source_id):
        # 409 = conflict
        return jsonify({"errors": ["A flashcard for this item already exists."]}), 409
    card = Flashcard(source_type, source_id)
    if not store.card_faces(card):
        return jsonify({"errors": ["Source item not found."]}), 404
    store.save_flashcard(card)
    return jsonify(card.to_dict()), 201


@app.route("/api/flashcards/due")
def api_due_flashcards():
    due = leitner.due_cards(store.flashcards())
    payload = []
    for card in due:
        faces = store.card_faces(card)
        if faces:
            payload.append({**card.to_dict(), **faces})
    return jsonify(payload)


@app.route("/api/flashcards/<card_id>/review", methods=["POST"])
def api_review_flashcard(card_id):
    rating = request.get_json().get("rating")
    card = next((c for c in store.flashcards() if c.id == card_id), None)
    if not card:
        return jsonify({"errors": ["Card not found."]}), 404
    try:
        leitner.review(card, rating)
    except ValueError as e:
        return jsonify({"errors": [str(e)]}), 400
    store.save_flashcard(card)
    return jsonify(card.to_dict())


#  API: library + grade calculator

@app.route("/api/library/toggle", methods=["POST"])
def api_toggle_library():
    data = request.get_json()
    saved = store.toggle_library(data.get("type"), data.get("id"))
    return jsonify({"saved": saved})


@app.route("/api/grade", methods=["POST"])
def api_grade():
    data = request.get_json()
    try:
        result = grade_calculator.calculate(data.get("level"),
                                            data.get("marks", {}))
    except ValueError as e:
        return jsonify({"errors": [str(e)]}), 400
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5001)