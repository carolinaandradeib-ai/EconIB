"""models.py, here I have all my öbjects, they are basically the different things the app stores:
definitions, diagrams, real world examples, study kits, flashcards and notes.
Each one is its own class. But the most important one is StudyKit because it links the others together.

Every class can turn itself into a dictionary (to_dict) so I can save it as json,
and build itself back from a dictionary (from_dict) when I load it again.
json only understands dicts/lists/text, not my python objects, so I need this to save stuff.
"""
import uuid
from datetime import date


def new_id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:6]}"


class Definition: 
    def __init__(self, term, definition, section, subtopic, level="Both",
                 source="user", id=None):
        self.id = id or new_id("def")
        self.term = term
        self.definition = definition
        self.section = section   
        self.subtopic = subtopic 
        self.level = level 
        self.source = source 

# Transform the whole definition into a dictionary so JSON can read and store
    def to_dict(self):
        return {
            "id": self.id, "term": self.term, "definition": self.definition,
            "section": self.section, "subtopic": self.subtopic,
            "level": self.level, "source": self.source,
        }

# Transform dictonary back as an argument 
    @classmethod
    def from_dict(cls, d):
        ''' AI help (Claude): I asked Claude to explain how to rebuild an object from a
        saved dictionary. It showed me the cls(**d) trick, which I then understood
        and reused on every class myself.
        what it does: **d takes every key in the dict and passes it in as an argument,
        so {"term": "Demand", ...} basically becomes Definition(term="Demand", ...)'''
        
        return cls(**d)

class Diagram:
    def __init__(self, title, section, subtopic, image, explanation,
                 level="Both", source="user", id=None):
        self.id = id or new_id("dia")
        self.title = title
        self.section = section
        self.subtopic = subtopic
        self.image = image              
        self.explanation = explanation  
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
        return cls(**d)


class RealWorldExample:
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
        self.data_context = data_context
        self.linked_diagram_id = linked_diagram_id
        self.linked_definition_ids = linked_definition_ids or []
        self.source = source
        
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
    def __init__(self, title, section, subtopic, definition_ids=None,
                 diagram_id=None, rwe_id=None, created=None, id=None):
        self.id = id or new_id("kit")
        self.title = title
        self.section = section
        self.subtopic = subtopic
        self.definition_ids = definition_ids or []
        self.diagram_id = diagram_id
        self.rwe_id = rwe_id
        self.created = created or date.today().isoformat()

    def validate(self):
        errors = []
        if not self.title or not self.title.strip():
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
    def __init__(self, source_type, source_id, box=1, next_review=None,
                 last_reviewed=None, id=None):
        self.id = id or new_id("fc")
        self.source_type = source_type  # definition/diagram/rwe
        self.source_id = source_id      # id of the thing it was made from
        self.box = box                  # leitner box, starts at 1 (shown most often)
        self.next_review = next_review or date.today().isoformat()
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
