# models.py
# these are all my "objects" - basically the different things the app stores
# (definitions, diagrams, real world examples, study kits, flashcards and notes).
# each one is its own class. the important one is StudyKit because it links the others together.
#
# every class can turn itself into a dictionary (to_dict) so i can save it as json,
# and build itself back from a dictionary (from_dict) when i load it again.
# json only understands dicts/lists/text, not my python objects, so i need this to save stuff.

import uuid
from datetime import date


def new_id(prefix):
    # makes a short random id like "def-3f9a2c"
    # every object needs its own id so i can link things and find them later.
    # uuid4 is a random unique string, i just grab the first 6 chars so it stays short.
    return f"{prefix}-{uuid.uuid4().hex[:6]}"


class Definition:
    # a key term + its IB definition, with tags for section / subtopic / level

    def __init__(self, term, definition, section, subtopic, level="Both",
                 source="user", id=None):
        # if it already has an id (means i'm loading it from a save) keep that one,
        # otherwise make a new one so i never get two things with the same id
        self.id = id or new_id("def")
        self.term = term
        self.definition = definition
        self.section = section          # micro / macro / global
        self.subtopic = subtopic        # like "Market Failure"
        self.level = level              # SL / HL / Both
        self.source = source            # "developer" = built in by me, "user" = added by the user

    def to_dict(self):
        # turn this object into a plain dictionary so it can be saved into the json file
        return {
            "id": self.id, "term": self.term, "definition": self.definition,
            "section": self.section, "subtopic": self.subtopic,
            "level": self.level, "source": self.source,
        }

    @classmethod
    def from_dict(cls, d):
        # AI help (Claude): I asked Claude to explain how to rebuild an object from a
        # saved dictionary. It showed me the cls(**d) trick, which I then understood
        # and reused on every class myself.
        # what it does: **d takes every key in the dict and passes it in as an argument,
        # so {"term": "Demand", ...} basically becomes Definition(term="Demand", ...)
        return cls(**d)


class Diagram:
    # an economics diagram (an svg image) + the IB style explanation of what it shows

    def __init__(self, title, section, subtopic, image, explanation,
                 level="Both", source="user", id=None):
        self.id = id or new_id("dia")
        self.title = title
        self.section = section
        self.subtopic = subtopic
        self.image = image              # just the file name inside static/diagrams/
        self.explanation = explanation  # the paragraph that shows when you click the diagram
        self.level = level
        self.source = source

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "section": self.section,
            "subtopic": self.subtopic, "image": self.image,
            "explanation": self.explanation, "level": self.level,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**d)     # same cls(**d) trick as in Definition (see the note up there)


class RealWorldExample:
    # a real world example. the cool part is it doesn't copy the diagram/definitions,
    # it just stores their IDS, so the same diagram can be used by loads of examples
    # without me having 50 copies of it.

    def __init__(self, title, description, section, subtopic, country,
                 data_context="", linked_diagram_id=None,
                 linked_definition_ids=None, source="user",
                 created=None, updated=None, id=None):
        self.id = id or new_id("rwe")
        self.title = title
        self.description = description
        self.section = section
        self.subtopic = subtopic
        self.country = country
        self.data_context = data_context          # the little stats line (dates, %, figures)
        self.linked_diagram_id = linked_diagram_id        # id of ONE diagram
        self.linked_definition_ids = linked_definition_ids or []   # ids of the linked definitions
        self.source = source
        # if no date is given just use today. isoformat() gives "2026-08-15" as text.
        self.created = created or date.today().isoformat()
        self.updated = updated or self.created

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "description": self.description,
            "section": self.section, "subtopic": self.subtopic,
            "country": self.country, "data_context": self.data_context,
            "linked_diagram_id": self.linked_diagram_id,
            "linked_definition_ids": self.linked_definition_ids,
            "source": self.source, "created": self.created,
            "updated": self.updated,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class StudyKit:
    # THE main object. a study kit is basically a container that links
    # many definitions + one diagram + one example, again just by storing their ids.
    # this is what lets me revise everything about one topic in a single view.

    def __init__(self, title, section, subtopic, definition_ids=None,
                 diagram_id=None, rwe_id=None, created=None, id=None):
        self.id = id or new_id("kit")
        self.title = title
        self.section = section
        self.subtopic = subtopic
        self.definition_ids = definition_ids or []   # can link lots of definitions
        self.diagram_id = diagram_id                 # only one diagram
        self.rwe_id = rwe_id                         # only one example
        self.created = created or date.today().isoformat()

    def validate(self):
        # SC-10: don't let a kit be saved if it's missing important stuff.
        # i collect all the problems in a list and return it. empty list = it's fine to save.
        # doing this here (in python, on the server) means it can't be skipped even if
        # someone messes with the page.
        errors = []
        if not self.title or not self.title.strip():
            # .strip() removes spaces, so a title of only spaces "   " still counts as empty
            errors.append("A Study Kit needs a title.")
        if not self.section:
            errors.append("A Study Kit needs a section (Micro/Macro/Global).")
        if not self.subtopic:
            errors.append("A Study Kit needs a subtopic tag.")
        if not self.definition_ids:
            errors.append("Link at least one definition.")
        return errors

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "section": self.section,
            "subtopic": self.subtopic, "definition_ids": self.definition_ids,
            "diagram_id": self.diagram_id, "rwe_id": self.rwe_id,
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class Flashcard:
    # a flashcard made from a definition, diagram or example.
    # it remembers WHERE it came from (source_type + source_id) and its leitner state:
    # which box it's in (1-5) and when it should next show up.

    def __init__(self, source_type, source_id, box=1, next_review=None,
                 last_reviewed=None, id=None):
        self.id = id or new_id("fc")
        self.source_type = source_type  # "definition" / "diagram" / "rwe"
        self.source_id = source_id      # id of the thing it was made from
        self.box = box                  # leitner box, starts at 1 (shown most often)
        self.next_review = next_review or date.today().isoformat()   # new cards are due today
        self.last_reviewed = last_reviewed

    def to_dict(self):
        return {
            "id": self.id, "source_type": self.source_type,
            "source_id": self.source_id, "box": self.box,
            "next_review": self.next_review,
            "last_reviewed": self.last_reviewed,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class Note:
    # just a free text note for the notes page (SC-08)

    def __init__(self, title, content="", updated=None, id=None):
        self.id = id or new_id("note")
        self.title = title
        self.content = content
        self.updated = updated or date.today().isoformat()

    def to_dict(self):
        return {"id": self.id, "title": self.title,
                "content": self.content, "updated": self.updated}

    @classmethod
    def from_dict(cls, d):
        return cls(**d)
