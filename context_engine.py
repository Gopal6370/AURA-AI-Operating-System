from typing import List, Dict


def build_context(
    memories: List,
    retrieved_documents: List,
    agent: str,
) -> str:

    sections = []

    # -----------------------------------------------------
    # AGENT
    # -----------------------------------------------------

    sections.append(
        f"Current AURA agent: {agent}"
    )

    # -----------------------------------------------------
    # LONG-TERM MEMORY
    # -----------------------------------------------------

    if memories:

        memory_lines = []

        for memory in memories:

            content = getattr(
                memory,
                "content",
                str(memory)
            )

            memory_lines.append(
                f"- {content}"
            )

        sections.append(
            "LONG-TERM USER MEMORY:\n"
            + "\n".join(memory_lines)
        )

    # -----------------------------------------------------
    # DOCUMENT KNOWLEDGE
    # -----------------------------------------------------

    if retrieved_documents:

        document_lines = []

        for doc in retrieved_documents:

            if isinstance(doc, dict):

                filename = doc.get(
                    "filename",
                    "Document"
                )

                page = doc.get(
                    "page",
                    "?"
                )

                text = doc.get(
                    "text",
                    ""
                )

            else:

                filename = getattr(
                    doc,
                    "filename",
                    "Document"
                )

                page = getattr(
                    doc,
                    "page",
                    "?"
                )

                text = getattr(
                    doc,
                    "text",
                    ""
                )

            document_lines.append(
                f"[{filename}, page {page}]\n{text}"
            )

        sections.append(
            "DOCUMENT KNOWLEDGE:\n"
            + "\n\n".join(document_lines)
        )

    # -----------------------------------------------------
    # FINAL CONTEXT
    # -----------------------------------------------------

    if not sections:
        return ""

    return "\n\n====================\n\n".join(
        sections
    )