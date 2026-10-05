from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .db import Base, SessionLocal


# =========================================================
# KNOWLEDGE GRAPH NODE
# =========================================================

class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    name = Column(
        String(200),
        nullable=False,
        index=True
    )

    node_type = Column(
        String(50),
        nullable=False,
        default="concept"
    )

    description = Column(
        Text,
        nullable=True
    )


# =========================================================
# KNOWLEDGE GRAPH EDGE
# =========================================================

class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    source_id = Column(
        Integer,
        ForeignKey("knowledge_nodes.id"),
        nullable=False
    )

    target_id = Column(
        Integer,
        ForeignKey("knowledge_nodes.id"),
        nullable=False
    )

    relation = Column(
        String(100),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "source_id",
            "target_id",
            "relation",
            name="unique_knowledge_edge"
        ),
    )


# =========================================================
# GET OR CREATE NODE
# =========================================================

def get_or_create_node(
    db,
    user_id: int,
    name: str,
    node_type: str = "concept",
    description: str = None
):

    name = name.strip()

    node = (
        db.query(KnowledgeNode)
        .filter(
            KnowledgeNode.user_id == user_id,
            KnowledgeNode.name == name
        )
        .first()
    )

    if node:
        return node

    node = KnowledgeNode(
        user_id=user_id,
        name=name,
        node_type=node_type,
        description=description
    )

    db.add(node)
    db.commit()
    db.refresh(node)

    return node


# =========================================================
# CREATE RELATIONSHIP
# =========================================================

def create_relationship(
    db,
    user_id: int,
    source_name: str,
    target_name: str,
    relation: str,
    source_type: str = "concept",
    target_type: str = "concept"
):

    source = get_or_create_node(
        db,
        user_id,
        source_name,
        source_type
    )

    target = get_or_create_node(
        db,
        user_id,
        target_name,
        target_type
    )

    existing = (
        db.query(KnowledgeEdge)
        .filter(
            KnowledgeEdge.user_id == user_id,
            KnowledgeEdge.source_id == source.id,
            KnowledgeEdge.target_id == target.id,
            KnowledgeEdge.relation == relation
        )
        .first()
    )

    if existing:
        return existing

    edge = KnowledgeEdge(
        user_id=user_id,
        source_id=source.id,
        target_id=target.id,
        relation=relation
    )

    db.add(edge)
    db.commit()
    db.refresh(edge)

    return edge


# =========================================================
# GET USER GRAPH
# =========================================================

def get_graph(db, user_id: int):

    nodes = (
        db.query(KnowledgeNode)
        .filter(
            KnowledgeNode.user_id == user_id
        )
        .all()
    )

    edges = (
        db.query(KnowledgeEdge)
        .filter(
            KnowledgeEdge.user_id == user_id
        )
        .all()
    )

    node_data = [
        {
            "id": node.id,
            "name": node.name,
            "type": node.node_type,
            "description": node.description
        }
        for node in nodes
    ]

    edge_data = [
        {
            "id": edge.id,
            "source": edge.source_id,
            "target": edge.target_id,
            "relation": edge.relation
        }
        for edge in edges
    ]

    return {
        "nodes": node_data,
        "edges": edge_data
    }


# =========================================================
# SEARCH GRAPH
# =========================================================

def search_graph(
    db,
    user_id: int,
    query: str
):

    query = query.strip().lower()

    nodes = (
        db.query(KnowledgeNode)
        .filter(
            KnowledgeNode.user_id == user_id,
            KnowledgeNode.name.ilike(f"%{query}%")
        )
        .all()
    )

    results = []

    for node in nodes:

        outgoing = (
            db.query(KnowledgeEdge)
            .filter(
                KnowledgeEdge.user_id == user_id,
                KnowledgeEdge.source_id == node.id
            )
            .all()
        )

        incoming = (
            db.query(KnowledgeEdge)
            .filter(
                KnowledgeEdge.user_id == user_id,
                KnowledgeEdge.target_id == node.id
            )
            .all()
        )

        results.append(
            {
                "node": {
                    "id": node.id,
                    "name": node.name,
                    "type": node.node_type,
                    "description": node.description
                },
                "outgoing": [
                    {
                        "relation": e.relation,
                        "target_id": e.target_id
                    }
                    for e in outgoing
                ],
                "incoming": [
                    {
                        "relation": e.relation,
                        "source_id": e.source_id
                    }
                    for e in incoming
                ]
            }
        )

    return results