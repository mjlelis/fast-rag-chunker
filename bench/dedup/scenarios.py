import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"
MANIFEST_PATH = CORPUS_DIR / "manifest.json"


@dataclass(frozen=True)
class DocumentPair:
    doc_id: str
    lang: str
    old_bytes: bytes
    new_bytes: bytes


def load_corpus_pairs() -> List[DocumentPair]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    pairs: List[DocumentPair] = []
    for entry in manifest["documents"]:
        old_bytes = (CORPUS_DIR / entry["old_file"]).read_bytes()
        new_bytes = (CORPUS_DIR / entry["new_file"]).read_bytes()
        pairs.append(
            DocumentPair(
                doc_id=entry["doc_id"],
                lang=entry["lang"],
                old_bytes=old_bytes,
                new_bytes=new_bytes,
            )
        )
    return pairs


def apply_top_insert(text: str, rng: random.Random) -> str:
    tag = rng.randint(1000, 9999)
    header = (
        f"[Revision Notice #{tag}] This section was prepended at the top of the document "
        "to evaluate content-defined chunk boundary resynchronization after an offset-0 edit.\n\n"
    )
    return header + text


def apply_mid_sentence_insert(text: str, rng: random.Random) -> str:
    target_pos = int(len(text) * 0.30)
    space_idx = text.find(" ", target_pos)
    if space_idx == -1:
        space_idx = target_pos
    clause = f" (including additional context verified in revision #{rng.randint(100, 999)})"
    return text[:space_idx] + clause + text[space_idx:]


def apply_deletion(text: str, _rng: random.Random) -> str:
    paragraphs = text.split("\n\n")
    if len(paragraphs) >= 4:
        del_idx = max(1, len(paragraphs) // 4)
        kept = paragraphs[:del_idx] + paragraphs[del_idx + 1 :]
        return "\n\n".join(kept)
    start = int(len(text) * 0.25)
    end = min(len(text), start + 180)
    return text[:start] + text[end:]


def apply_scattered_edits(text: str, rng: random.Random, num_edits: int = 5) -> str:
    lines = text.splitlines(keepends=True)
    if len(lines) < num_edits * 2:
        return apply_mid_sentence_insert(text, rng)
    step = len(lines) // (num_edits + 1)
    mutated = list(lines)
    for k in range(1, num_edits + 1):
        idx = min(len(mutated) - 1, k * step)
        marker = f" [ inline-edit-{k}-{rng.randint(10, 99)} ] "
        line = mutated[idx]
        mid = len(line) // 2
        space_pos = line.find(" ", mid)
        if space_pos == -1:
            space_pos = mid
        mutated[idx] = line[:space_pos] + marker + line[space_pos:]
    return "".join(mutated)


def apply_moved_paragraph(text: str, _rng: random.Random) -> str:
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) < 5:
        mid = len(text) // 2
        return text[mid:] + "\n\n" + text[:mid]
    src_idx = len(paragraphs) // 4
    dst_idx = (len(paragraphs) * 3) // 4
    moved = paragraphs.pop(src_idx)
    paragraphs.insert(dst_idx, moved)
    return "\n\n".join(paragraphs) + "\n"


def apply_whitespace_only(text: str, _rng: random.Random) -> str:
    # Replace sentence spacing ". " with ".  " and double blank lines with triple blank lines
    mutated = re.sub(r"\. ([A-ZÀ-Ú])", r".  \1", text)
    mutated = mutated.replace("\n\n", "\n\n\n", 8)
    return mutated


def build_all_scenarios(seed: int = 42) -> List[Tuple[str, str, List[DocumentPair]]]:
    """
    Returns ordered list of `(scenario_id, scenario_label, document_pairs)`.
    Every scenario contains at least 30 document pairs.
    """
    base_pairs = load_corpus_pairs()
    assert len(base_pairs) >= 30, f"Expected >= 30 corpus documents, found {len(base_pairs)}"

    synthetic_specs = [
        ("top_insert", "Top Insertion (Offset 0)", apply_top_insert),
        ("mid_sentence_insert", "Mid-Sentence Insertion", apply_mid_sentence_insert),
        ("deletion", "Paragraph / Span Deletion", apply_deletion),
        ("scattered_edits", "5 Scattered Inline Edits", apply_scattered_edits),
        ("moved_paragraph", "Moved Paragraph", apply_moved_paragraph),
        ("whitespace_only", "Whitespace-Only Formatting Edit", apply_whitespace_only),
    ]

    scenarios: List[Tuple[str, str, List[DocumentPair]]] = []

    for scen_id, scen_label, transform_fn in synthetic_specs:
        rng = random.Random(seed)
        scen_pairs: List[DocumentPair] = []
        for item in base_pairs:
            base_text = item.old_bytes.decode("utf-8")
            edited_text = transform_fn(base_text, rng)
            scen_pairs.append(
                DocumentPair(
                    doc_id=item.doc_id,
                    lang=item.lang,
                    old_bytes=item.old_bytes,
                    new_bytes=edited_text.encode("utf-8"),
                )
            )
        scenarios.append((scen_id, scen_label, scen_pairs))

    # Real consecutive Wikipedia revisions (30 pairs: 15 EN + 15 PT)
    scenarios.append(
        ("real_revisions", "Real Wiki Revisions (EN + PT, 30 pairs)", base_pairs)
    )

    return scenarios
