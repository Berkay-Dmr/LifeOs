from __future__ import annotations

import pytest

from app.memory.memory_engine import MemoryEngine, MEMORY_TYPES
from app.memory.entities import extract_entities, Entity
from app.memory.relations import create_relation, get_relations_for_entity


class TestMemoryEngine:
    def test_create_memory(self, tmp_db):
        engine = MemoryEngine()
        memory = engine.create_memory("Test memory", memory_type="fact")
        assert memory.content == "Test memory"
        assert memory.type == "fact"
        assert memory.active is True

    def test_create_invalid_type_defaults_to_fact(self, tmp_db):
        engine = MemoryEngine()
        memory = engine.create_memory("Test", memory_type="invalid_type")
        assert memory.type == "fact"

    def test_recall(self, tmp_db):
        engine = MemoryEngine()
        engine.create_memory("Python programming language", memory_type="fact")
        engine.create_memory("JavaScript frameworks", memory_type="fact")

        results = engine.recall("Python")
        assert len(results) >= 1
        assert any("Python" in m.content for m in results)

    def test_forget(self, tmp_db):
        engine = MemoryEngine()
        memory = engine.create_memory("To be forgotten", memory_type="fact")
        assert engine.forget(memory.id) is True

        # Should not appear in active list
        active = engine.list_all(active_only=True)
        assert not any(m.id == memory.id for m in active)

    def test_forget_nonexistent(self, tmp_db):
        engine = MemoryEngine()
        assert engine.forget("nonexistent_id") is False

    def test_count(self, tmp_db):
        engine = MemoryEngine()
        initial = engine.count()
        engine.create_memory("Count me", memory_type="fact")
        assert engine.count() == initial + 1

    def test_list_all(self, tmp_db):
        engine = MemoryEngine()
        engine.create_memory("Item 1", memory_type="fact")
        engine.create_memory("Item 2", memory_type="preference")
        all_memories = engine.list_all()
        assert len(all_memories) >= 2


class TestEntities:
    def test_extract_technologies(self):
        text = "I use Python and Docker for my projects."
        entities = extract_entities(text)
        names = [e.name for e in entities]
        assert "Python" in names
        assert "Docker" in names

    def test_extract_errors(self):
        text = "Got a connection refused error."
        entities = extract_entities(text)
        names = [e.name for e in entities]
        assert "connection refused" in names

    def test_extract_concepts(self):
        text = "The API uses REST for authentication."
        entities = extract_entities(text)
        names = [e.name for e in entities]
        assert "API" in names
        assert "REST" in names

    def test_no_duplicates(self):
        text = "Python Python Python"
        entities = extract_entities(text)
        python_entities = [e for e in entities if e.name == "Python"]
        assert len(python_entities) == 1

    def test_entity_has_id(self):
        text = "Using PostgreSQL"
        entities = extract_entities(text)
        assert len(entities) >= 1
        assert entities[0].id is not None
        assert len(entities[0].id) > 0


class TestRelations:
    def test_create_relation(self, tmp_db):
        relation = create_relation("entity1", "entity2", "uses")
        assert relation.source_entity_id == "entity1"
        assert relation.target_entity_id == "entity2"
        assert relation.relation_type == "uses"

    def test_get_relations(self, tmp_db):
        create_relation("e1", "e2", "related_to")
        create_relation("e1", "e3", "uses")
        create_relation("e4", "e2", "contains")

        relations = get_relations_for_entity("e1")
        assert len(relations) >= 2

    def test_default_relation_type(self, tmp_db):
        relation = create_relation("a", "b")
        assert relation.relation_type == "related_to"
