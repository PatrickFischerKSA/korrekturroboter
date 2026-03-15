import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib import error, request


LM_STUDIO_BASE_URL = os.environ.get("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
LM_STUDIO_MODEL = os.environ.get("LM_STUDIO_MODEL", "").strip()
DEFAULT_MODEL_ID = "mistral-small-3.2-24b-instruct-2506-mlx"
MAX_REVIEW_TEXT_CHARS = 9000
MAX_DOSSIER_SCAN_PARAGRAPHS = 120
MAX_CHUNK_CHARS = 2400
MAX_CHUNK_PARAGRAPHS = 4
SCHOOL_MODE_REVIEW_TEXT_CHARS = 7200
SCHOOL_MODE_DOSSIER_SCAN_PARAGRAPHS = 80
SCHOOL_MODE_CHUNK_CHARS = 1800
SCHOOL_MODE_CHUNK_PARAGRAPHS = 3
SCHOOL_MODE_STAGE1_MAX_TOKENS = 700
SCHOOL_MODE_STAGE2_MAX_TOKENS = 1100


ESSAY_GUIDELINES = {
    "inhalt": [
        "klare Auseinandersetzung mit der Fragestellung",
        "eigenständige Position oder These",
        "nachvollziehbare Argumentation",
        "differenzierte Betrachtung des Themas",
        "Einbezug von Beispielen, Erfahrungen oder Wissen",
        "relevante und präzise Gedanken ohne Abschweifungen",
        "kritisches Denken und gedankliche Tiefe",
        "verschiedene Perspektiven werden berücksichtigt",
    ],
    "aufbau": [
        "klarer Einstieg, der zum Thema hinführt",
        "logischer Gedankengang",
        "sinnvolle Absätze",
        "nachvollziehbare Übergänge",
        "runder Schluss",
        "roter Faden im gesamten Text",
        "Gedanken bauen aufeinander auf",
    ],
    "ausdruck": [
        "präziser Wortschatz",
        "abwechslungsreicher Satzbau",
        "angemessener, essayistischer Stil",
        "verständliche und klare Formulierungen",
        "originelle Gedanken und persönliche Stimme",
        "Wiederholungen werden vermieden",
        "sprachliche Bilder oder Beispiele sind möglich",
    ],
}


SPEECH_GUIDELINES = {
    "inhalt": [
        "klare Botschaft oder zentrale These",
        "Thema wird verständlich entfaltet",
        "relevante Beispiele oder Bezüge",
        "Argumente sind nachvollziehbar",
        "Publikum wird gedanklich angesprochen",
        "zentrale Botschaft bleibt im Gedächtnis",
    ],
    "aufbau": [
        "klarer Einstieg mit Hinführung",
        "logischer Aufbau des Hauptteils",
        "roter Faden im Gedankengang",
        "überzeugender Schluss mit Zusammenführung oder Appell",
        "erkennbare Gliederung als Rede",
        "Absätze unterstützen den Gedankengang",
    ],
    "ausdruck": [
        "präzise und verständliche Ausdrucksweise",
        "abwechslungsreicher Satzbau",
        "passender Ton für eine Rede",
        "anschauliche Formulierungen oder sprachliche Bilder",
        "direkte Ansprachen oder rhetorische Fragen möglich",
        "redeartiger, wirkungsorientierter Stil",
        "Einsatz rhetorischer Mittel wie Wiederholung, Parallelismus, Bildsprache oder Appell",
    ],
}


LINEAR_DISCUSSION_GUIDELINES = {
    "inhalt": [
        "klare Erfassung der vorgegebenen Frage oder Aussage",
        "eigene Grundhaltung ist eindeutig und tragfähig formuliert",
        "die Argumente stützen den vorgegebenen Sachverhalt konsequent",
        "die Aussage des Themas wird nicht umgangen, sondern gezielt entfaltet",
        "jedes zentrale Argument wird mit Beispielen, Fakten, Zitaten oder Erfahrungen gestützt",
        "die Gedanken führen zu einem klaren Gesamturteil",
    ],
    "aufbau": [
        "Einleitung führt über Aktualität, Problem oder Fragestellung ins Thema ein",
        "im Hauptteil ist die eigene Grundhaltung klar erkennbar",
        "die Argumente sind steigernd geordnet: wichtig, wichtiger, am wichtigsten",
        "die Gedankenschritte bauen logisch aufeinander auf",
        "der Schluss formuliert ein abgerundetes Gesamturteil und einen Ausblick",
    ],
    "ausdruck": [
        "der argumentative Stil ist klar, präzise und führend",
        "Übergänge markieren die Steigerung der Argumentation deutlich",
        "Beispiele und Belege werden sprachlich sauber in die Argumentation eingebunden",
        "die Formulierungen sind sachlich, aber persönlich verantwortet",
        "Wiederholungen, Sprünge und unklare Verweise werden vermieden",
    ],
}


DIALECTICAL_DISCUSSION_GUIDELINES = {
    "inhalt": [
        "die strittige Ausgangsfrage wird klar herausgearbeitet",
        "Pro- und Contra-Positionen werden fair und differenziert dargestellt",
        "Argumente werden nicht nur genannt, sondern kritisch geprüft",
        "Entkräftungen, Abwägungen oder Zuspitzungen sind nachvollziehbar",
        "der eigene Standpunkt ergibt sich schlüssig aus der Auseinandersetzung",
        "die Behandlung der Gegenseite bleibt sachlich und präzise",
    ],
    "aufbau": [
        "die Einleitung benennt Problem, Widerspruch oder Leitfrage deutlich",
        "der Hauptteil folgt erkennbar einer dialektischen Ordnung",
        "ein Wendepunkt oder ein klarer Übergang zwischen den Positionen ist sichtbar",
        "die Reihenfolge der Argumente ist bewusst gesetzt und steigert die Wirkung",
        "das schlussnahe Argument trägt das Endurteil",
        "der Schluss fasst abwägend zusammen und formuliert einen klaren Standpunkt",
    ],
    "ausdruck": [
        "die Sprache markiert deutlich, ob ein Argument Pro oder Contra ist",
        "abwägende Konnektoren und logische Verknüpfungen werden präzise eingesetzt",
        "Unterscheidungen, Einschränkungen und Gewichtungen sind sprachlich sauber formuliert",
        "die Ausdrucksweise bleibt argumentativ sachlich und trotzdem pointiert",
        "der Leser wird durch klare Signale sicher durch den Perspektivenwechsel geführt",
    ],
}


ARGUMENTATION_MEASURE = [
    "klare These",
    "schlüssige Begründung",
    "konkreter Beleg oder Beispiel",
    "Berücksichtigung eines möglichen Einwands",
    "Abwägung oder Entkräftung",
    "folgerichtiges Zwischenfazit oder Schluss",
]


RHETORICAL_FORMS = [
    "rhetorische Frage",
    "Anapher",
    "Antithese",
    "Parallelismus",
    "Klimax",
    "Metapher",
    "Vergleich",
    "Wiederholung",
    "Appell",
]


FORM_LABELS = {
    "essay": "Essay",
    "speech": "Redemanuskript",
    "linear_discussion": "Lineare Erörterung",
    "dialectical_discussion": "Dialektische Erörterung",
}


FORM_GUIDELINES = {
    "essay": ESSAY_GUIDELINES,
    "speech": SPEECH_GUIDELINES,
    "linear_discussion": LINEAR_DISCUSSION_GUIDELINES,
    "dialectical_discussion": DIALECTICAL_DISCUSSION_GUIDELINES,
}


GERMAN_STOPWORDS = {
    "aber", "alle", "alles", "auch", "auf", "aus", "bei", "beim", "bin", "bis", "bist", "damit",
    "dann", "das", "dass", "dein", "deine", "dem", "den", "der", "des", "dessen", "deshalb", "die",
    "dies", "diese", "dieser", "doch", "dort", "du", "durch", "ein", "eine", "einem", "einen",
    "einer", "eines", "er", "es", "euch", "euer", "eure", "für", "hat", "hatte", "hier", "hinter",
    "ich", "ihm", "ihn", "ihr", "ihre", "im", "in", "ist", "ja", "jede", "jeder", "jedes", "kein",
    "keine", "können", "man", "mit", "muss", "nach", "nicht", "noch", "nun", "oder", "ohne", "sehr",
    "sein", "seine", "sich", "sie", "sind", "soll", "sollen", "sollte", "sollten", "sondern", "so",
    "um", "und", "uns", "unter", "vom", "von", "vor", "war", "waren", "was", "weil", "wenn", "wer",
    "wie", "wir", "wird", "wurde", "zu", "zum", "zur", "zwar",
}


DISCUSSION_STRUCTURE_NOTES = {
    "linear_discussion": [
        "Ordne die Argumente steigernd von wichtig über wichtiger bis zum zentralen Schlussargument.",
        "Formuliere früh eine erkennbare Grundhaltung und führe sie konsequent aus.",
        "Schließe mit Gesamturteil und Ausblick.",
    ],
    "dialectical_discussion": [
        "Arbeite den strittigen Charakter der Frage offen heraus.",
        "Nutze eine klare Pro-/Contra-Struktur oder eine wechselnde Argumentation mit sichtbarem Wendepunkt.",
        "Das schlussnahe, stärkste Argument soll das Endurteil tragen.",
    ],
}


LANGUAGE_TABLES = {
    "1": [(1.0, 6.0), (1.75, 5.75), (2.5, 5.5), (3.25, 5.25), (4.0, 5.0), (4.75, 4.75), (5.5, 4.5), (6.25, 4.25), (7.0, 4.0), (7.75, 3.75), (8.5, 3.5), (9.25, 3.25), (10.0, 3.0), (10.75, 2.75), (11.5, 2.5), (12.25, 2.25), (13.0, 2.0), (13.75, 1.75), (14.5, 1.5), (15.25, 1.25), (16.0, 1.0)],
    "2": [(1.0, 6.0), (1.625, 5.75), (2.25, 5.5), (2.875, 5.25), (3.5, 5.0), (4.125, 4.75), (4.75, 4.5), (5.375, 4.25), (6.0, 4.0), (6.625, 3.75), (7.25, 3.5), (7.875, 3.25), (8.5, 3.0), (9.125, 2.75), (9.75, 2.5), (10.375, 2.25), (11.0, 2.0), (11.625, 1.75), (12.25, 1.5), (12.875, 1.25), (13.5, 1.0)],
    "3": [(1.0, 6.0), (1.5, 5.75), (2.0, 5.5), (2.5, 5.25), (3.0, 5.0), (3.5, 4.75), (4.0, 4.5), (4.5, 4.25), (5.0, 4.0), (5.5, 3.75), (6.0, 3.5), (6.5, 3.25), (7.0, 3.0), (7.5, 2.75), (8.0, 2.5), (8.5, 2.25), (9.0, 2.0), (9.5, 1.75), (10.0, 1.5), (10.5, 1.25), (11.0, 1.0)],
    "4": [(1.0, 6.0), (1.375, 5.75), (1.75, 5.5), (2.125, 5.25), (2.5, 5.0), (2.875, 4.75), (3.25, 4.5), (3.625, 4.25), (4.0, 4.0), (4.375, 3.75), (4.75, 3.5), (5.125, 3.25), (5.5, 3.0), (5.875, 2.75), (6.25, 2.5), (6.625, 2.25), (7.0, 2.0), (7.375, 1.75), (7.75, 1.5), (8.125, 1.25), (8.5, 1.0)],
    "1_m_KP": [(0.5, 6.0), (1.125, 5.75), (1.75, 5.5), (2.375, 5.25), (3.0, 5.0), (3.625, 4.75), (4.25, 4.5), (4.875, 4.25), (5.5, 4.0), (6.125, 3.75), (6.75, 3.5), (7.375, 3.25), (8.0, 3.0), (8.625, 2.75), (9.25, 2.5), (9.875, 2.25), (10.5, 2.0), (11.125, 1.75), (11.75, 1.5), (12.375, 1.25), (13.0, 1.0)],
    "2_m_KP": [(0.5, 6.0), (1.0, 5.75), (1.5, 5.5), (2.0, 5.25), (2.5, 5.0), (3.0, 4.75), (3.5, 4.5), (4.0, 4.25), (4.5, 4.0), (5.0, 3.75), (5.5, 3.5), (6.0, 3.25), (6.5, 3.0), (7.0, 2.75), (7.5, 2.5), (8.0, 2.25), (8.5, 2.0), (9.0, 1.75), (9.5, 1.5), (10.0, 1.25), (10.5, 1.0)],
    "3_m_KP": [(0.5, 6.0), (0.875, 5.75), (1.25, 5.5), (1.625, 5.25), (2.0, 5.0), (2.375, 4.75), (2.75, 4.5), (3.125, 4.25), (3.5, 4.0), (3.875, 3.75), (4.25, 3.5), (4.625, 3.25), (5.0, 3.0), (5.375, 2.75), (5.75, 2.5), (6.125, 2.25), (6.5, 2.0), (6.875, 1.75), (7.25, 1.5), (7.625, 1.25), (8.0, 1.0)],
    "4_m_KP": [(0.5, 6.0), (0.75, 5.75), (1.0, 5.5), (1.25, 5.25), (1.5, 5.0), (1.75, 4.75), (2.0, 4.5), (2.25, 4.25), (2.5, 4.0), (2.75, 3.75), (3.0, 3.5), (3.25, 3.25), (3.5, 3.0), (3.75, 2.75), (4.0, 2.5), (4.25, 2.25), (4.5, 2.0), (4.75, 1.75), (5.0, 1.5), (5.25, 1.25), (5.5, 1.0)],
}


class ReviewError(RuntimeError):
    pass


class LMStudioHTTPError(ReviewError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class OrthographyResult:
    error_count: int
    word_count: int
    errors_per_200: float
    grade: float


def get_runtime_limits(school_mode: bool) -> dict[str, int]:
    if school_mode:
        return {
            "max_review_text_chars": SCHOOL_MODE_REVIEW_TEXT_CHARS,
            "max_dossier_scan_paragraphs": SCHOOL_MODE_DOSSIER_SCAN_PARAGRAPHS,
            "max_chunk_chars": SCHOOL_MODE_CHUNK_CHARS,
            "max_chunk_paragraphs": SCHOOL_MODE_CHUNK_PARAGRAPHS,
            "stage1_max_tokens": SCHOOL_MODE_STAGE1_MAX_TOKENS,
            "stage2_max_tokens": SCHOOL_MODE_STAGE2_MAX_TOKENS,
            "combined_token_warning": 3000,
        }
    return {
        "max_review_text_chars": MAX_REVIEW_TEXT_CHARS,
        "max_dossier_scan_paragraphs": MAX_DOSSIER_SCAN_PARAGRAPHS,
        "max_chunk_chars": MAX_CHUNK_CHARS,
        "max_chunk_paragraphs": MAX_CHUNK_PARAGRAPHS,
        "stage1_max_tokens": 900,
        "stage2_max_tokens": 1400,
        "combined_token_warning": 3500,
    }


def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-zA-ÖØ-öø-ÿÄÖÜäöüß]+", text))


def calculate_orthography_grade(level: str, error_count: int, word_count: int) -> OrthographyResult:
    if level not in LANGUAGE_TABLES:
        raise ReviewError(f"Unbekannte Gym-/FMS-Stufe: {level}")
    if word_count <= 0:
        raise ReviewError("Die Wortzahl muss größer als 0 sein.")

    errors_per_200 = (error_count / word_count) * 200
    table = LANGUAGE_TABLES[level]
    grade = table[-1][1]
    for threshold, value in table:
        if errors_per_200 <= threshold:
            grade = value
            break

    return OrthographyResult(
        error_count=error_count,
        word_count=word_count,
        errors_per_200=errors_per_200,
        grade=grade,
    )


def detect_document_type(text: str, requested_type: str, assignment_text: str = "", topic: str = "") -> str:
    if requested_type in FORM_LABELS:
        return requested_type
    lowered_assignment = f"{assignment_text}\n{topic}".lower()
    lowered_text = text.lower()
    speech_hits = sum(lowered_assignment.count(token) for token in ["rede", "publikum", "zuhörer", "meine damen", "ansprache", "redepublikum"])
    speech_hits += sum(lowered_text.count(token) for token in ["publikum", "zuhörer", "meine damen"])
    dialectical_hits = sum(
        lowered_assignment.count(token)
        for token in ["vor- und nachteile", "vor und nachteile", "nehmen sie stellung", "pro und contra", "fluch und segen"]
    )
    linear_hits = sum(lowered_assignment.count(token) for token in ["warum", "was macht", "gute gründe", "gute gruende", "weshalb"])
    if speech_hits >= 2:
        return "speech"
    if dialectical_hits >= 1:
        return "dialectical_discussion"
    if linear_hits >= 1:
        return "linear_discussion"
    return "essay"


def infer_context_from_dossier(
    essay_paragraphs: list[str],
    dossier_paragraphs: list[str],
    school_mode: bool = False,
) -> dict[str, Any]:
    essay_text = "\n".join(essay_paragraphs).strip()
    limits = get_runtime_limits(school_mode)
    dossier_scan = dossier_paragraphs[: limits["max_dossier_scan_paragraphs"]]
    dossier_text = "\n".join(dossier_scan).strip()
    warnings = build_input_warnings(essay_paragraphs, dossier_paragraphs=dossier_paragraphs, school_mode=school_mode)
    if not essay_text or not dossier_text:
        return {
            "topic": "",
            "assignment_text": "",
            "document_type": "auto",
            "match_label": "",
            "candidates": [],
            "warnings": warnings,
            "pipeline": {},
        }

    candidates = _build_dossier_candidates(dossier_scan)
    if not candidates:
        return {
            "topic": "",
            "assignment_text": "",
            "document_type": "auto",
            "match_label": "",
            "candidates": [],
            "warnings": warnings,
            "pipeline": {
                "mode": "two_stage_local",
                "stage_1": "Keine tragfähigen Themenblöcke im Dossier gefunden.",
                "stage_2": "Abgleich mit dem Aufsatz konnte nicht starten.",
            },
        }

    scored = []
    for candidate in candidates:
        score = _score_candidate_against_essay(candidate["assignment_text"], essay_text)
        scored.append((score, candidate))
    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best = scored[0]
    if best_score <= 0:
        return {
            "topic": "",
            "assignment_text": "",
            "document_type": "auto",
            "match_label": "",
            "candidates": [],
            "warnings": warnings,
            "pipeline": {
                "mode": "two_stage_local",
                "stage_1": f"{len(candidates)} Themenblöcke aus dem Dossier extrahiert.",
                "stage_2": "Kein Themenblock passt ausreichend zum hochgeladenen Aufsatz.",
            },
        }

    normalized_candidates = []
    for score, candidate in scored[:6]:
        if score <= 0:
            continue
        assignment_text = normalize_sentence(candidate["assignment_text"])
        topic = _derive_topic_from_candidate(candidate["topic"], assignment_text)
        document_type = detect_document_type(essay_text, "auto", assignment_text, topic)
        normalized_candidates.append(
            {
                "topic": topic,
                "assignment_text": assignment_text,
                "document_type": document_type,
                "document_type_label": FORM_LABELS.get(document_type, document_type),
                "match_score": score,
                "match_label": f"Trefferwert {score}",
            }
        )

    assignment_text = normalize_sentence(best["assignment_text"])
    topic = _derive_topic_from_candidate(best["topic"], assignment_text)
    document_type = detect_document_type(essay_text, "auto", assignment_text, topic)
    return {
        "topic": topic,
        "assignment_text": assignment_text,
        "document_type": document_type,
        "match_label": f"Thema aus Prüfungsdossier erkannt (Trefferwert {best_score}).",
        "candidates": normalized_candidates,
        "warnings": warnings,
            "pipeline": {
                "mode": "two_stage_local",
                "stage_1": f"{len(candidates)} Themenblöcke aus dem Prüfungsdossier extrahiert.",
                "stage_2": f"Bester Themenblock mit Trefferwert {best_score} zum Aufsatz abgeglichen.",
            },
        }


def _build_dossier_candidates(paragraphs: list[str]) -> list[dict[str, str]]:
    numbered_candidates = _extract_numbered_topic_candidates(paragraphs)
    if numbered_candidates:
        return numbered_candidates

    candidates: list[dict[str, str]] = []
    preface = _collect_instruction_preface(paragraphs)
    for index, paragraph in enumerate(paragraphs):
        cleaned = re.sub(r"\s+", " ", paragraph).strip()
        if not cleaned:
            continue
        if _is_generic_instruction(cleaned):
            continue

        block = [cleaned]
        if index + 1 < len(paragraphs):
            next_paragraph = re.sub(r"\s+", " ", paragraphs[index + 1]).strip()
            if next_paragraph and len(next_paragraph) < 420 and not _is_generic_instruction(next_paragraph):
                block.append(next_paragraph)

        combined = " ".join(block).strip()
        if _looks_like_assignment(combined):
            candidates.append(
                {
                    "topic": _derive_topic_from_candidate(cleaned, combined),
                    "assignment_text": f"{preface} {combined}".strip(),
                }
            )

    if candidates:
        return _dedupe_candidates(candidates)

    windows: list[dict[str, str]] = []
    for index in range(len(paragraphs)):
        combined = " ".join(re.sub(r"\s+", " ", value).strip() for value in paragraphs[index : index + 2]).strip()
        if combined and not _is_generic_instruction(combined):
            windows.append({"topic": _derive_topic_from_candidate(paragraphs[index].strip(), combined), "assignment_text": combined})
    return _dedupe_candidates(windows)


def _extract_numbered_topic_candidates(paragraphs: list[str]) -> list[dict[str, str]]:
    cleaned_paragraphs = [re.sub(r"\s+", " ", paragraph).strip() for paragraph in paragraphs if paragraph.strip()]
    joined = "\n".join(cleaned_paragraphs)
    pattern = re.compile(
        r"(?is)(Thema\s*\d+\s*[:.)-]\s*)(.+?)(?=(?:\n\s*Thema\s*\d+\s*[:.)-]\s*)|$)"
    )
    matches = list(pattern.finditer(joined))
    if not matches:
        return []

    preface = _collect_instruction_preface(cleaned_paragraphs)
    candidates: list[dict[str, str]] = []
    for match in matches:
        body = re.sub(r"\s+", " ", match.group(2)).strip()
        if not body:
            continue
        topic = _derive_topic_from_candidate(body, body)
        assignment_text = f"{preface} {match.group(1).strip()} {body}".strip()
        candidates.append({"topic": topic, "assignment_text": assignment_text})
    return _dedupe_candidates(candidates)


def _collect_instruction_preface(paragraphs: list[str]) -> str:
    parts = []
    for paragraph in paragraphs[:8]:
        cleaned = re.sub(r"\s+", " ", paragraph).strip()
        if not cleaned:
            continue
        if _is_generic_instruction(cleaned):
            parts.append(cleaned)
    return " ".join(dict.fromkeys(parts))


def _is_generic_instruction(text: str) -> bool:
    lowered = text.lower()
    cues = [
        "wählen sie eines der themen",
        "verfassen sie einen text von etwa",
        "anzahl der wörter am schluss",
        "lassen sie sich genug zeit",
        "setzen sie selbst eine passende überschrift",
        "zur auseinandersetzung mit der fragestellung",
    ]
    return any(cue in lowered for cue in cues)


def _dedupe_candidates(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (
            re.sub(r"\s+", " ", candidate.get("topic", "")).strip().lower(),
            re.sub(r"\s+", " ", candidate.get("assignment_text", "")).strip().lower(),
        )
        if not key[0] or key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def _shorten_context_text(text: str, max_chars: int) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return f"{cleaned[: max_chars - 1].rstrip()}…"


def build_input_warnings(
    essay_paragraphs: list[str],
    dossier_paragraphs: list[str] | None = None,
    assignment_text: str = "",
    topic: str = "",
    thesis: str = "",
    school_mode: bool = False,
) -> list[str]:
    warnings: list[str] = []
    limits = get_runtime_limits(school_mode)
    essay_text = "\n\n".join(essay_paragraphs).strip()
    dossier_text = "\n\n".join(dossier_paragraphs or []).strip()

    if school_mode:
        warnings.append(
            "Schulmodus aktiv: Das System arbeitet mit stabilen Standardgrenzen und einem festen lokalen Modellprofil."
        )
    if len(essay_text) > limits["max_review_text_chars"]:
        warnings.append(
            "Der Aufsatz ist sehr lang. Für die KI-Bewertung wird bei lokalen Modellen ein gekürzter Analyseauszug verwendet, "
            "damit der Lauf stabil bleibt."
        )
    if dossier_paragraphs and len(dossier_paragraphs) > limits["max_dossier_scan_paragraphs"]:
        warnings.append(
            f"Das Prüfungsdossier ist umfangreich. Die Dossieranalyse nutzt deshalb nur die ersten {limits['max_dossier_scan_paragraphs']} Absätze "
            "für die automatische Themenwahl."
        )
    combined_tokens = estimate_tokens(essay_text) + estimate_tokens(dossier_text) + estimate_tokens(assignment_text) + estimate_tokens(topic) + estimate_tokens(thesis)
    if combined_tokens > limits["combined_token_warning"]:
        warnings.append(
            "Die Gesamteingabe ist für kleinere lokale Modelle sehr umfangreich. Ein Modell mit größerem Kontextfenster bleibt hier robuster."
        )
    return warnings


def estimate_tokens(text: str) -> int:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if not cleaned:
        return 0
    return max(1, len(cleaned) // 4)


def _looks_like_assignment(text: str) -> bool:
    lowered = text.lower()
    cues = [
        "verfassen sie", "schreiben sie", "erörtern sie", "nehmen sie", "analysieren sie",
        "interpretieren sie", "setzen sie sich", "diskutieren sie", "begründen sie",
        "thema", "aufgabe", "essay", "rede", "stellungnahme",
    ]
    return any(cue in lowered for cue in cues) or text.rstrip().endswith("?")


def _score_candidate_against_essay(candidate_text: str, essay_text: str) -> int:
    candidate_tokens = set(_keyword_tokens(candidate_text))
    essay_tokens = set(_keyword_tokens(essay_text))
    if not candidate_tokens or not essay_tokens:
        return 0
    return len(candidate_tokens & essay_tokens)


def _keyword_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-zA-ÖØ-öø-ÿÄÖÜäöüß]{4,}", text.lower())
    return [token for token in tokens if token not in GERMAN_STOPWORDS]


def _derive_topic_from_candidate(topic: str, assignment_text: str) -> str:
    source = re.sub(r"\s+", " ", (topic or assignment_text).strip())
    source = re.sub(r"(?i)^thema\s*\d+\s*[:.)-]?\s*", "", source)
    if "?" in source:
        question = source.split("?", 1)[0].strip()
        if question:
            return normalize_sentence(f"{question}?").rstrip(".")
    parts = re.split(r"(?<=[.!?])\s+|:\s+", source)
    for part in parts:
        cleaned = part.strip()
        if not cleaned or _is_generic_instruction(cleaned):
            continue
        if len(cleaned) > 140:
            continue
        return normalize_sentence(cleaned).rstrip(".")
    return normalize_sentence(source[:140]).rstrip(".")


def list_models(base_url: str) -> list[dict[str, Any]]:
    payload = _http_get_json(f"{base_url}/models", timeout=10)
    models = payload.get("data", [])
    if not isinstance(models, list):
        raise ReviewError("LM Studio hat ein ungültiges Modellformat geliefert.")
    return models


def fetch_model(base_url: str) -> str:
    if LM_STUDIO_MODEL:
        return LM_STUDIO_MODEL

    models = list_models(base_url)
    if not models:
        raise ReviewError("LM Studio liefert keine Modelle. Bitte in LM Studio ein Modell laden.")
    preferred = next((entry["id"] for entry in models if entry.get("id") == DEFAULT_MODEL_ID), "")
    if preferred:
        return preferred
    return models[0]["id"]


def build_prompt(
    text: str,
    document_type: str,
    paragraph_count: int,
    gym_level: str,
    assignment_text: str = "",
    topic: str = "",
    thesis: str = "",
) -> tuple[str, str]:
    rubric = FORM_GUIDELINES[document_type]
    type_label = FORM_LABELS[document_type]
    structure_notes = DISCUSSION_STRUCTURE_NOTES.get(document_type, [])
    assignment_text = _shorten_context_text(assignment_text, 500)
    topic = _shorten_context_text(topic, 180)
    thesis = _shorten_context_text(thesis, 220)
    text = _shorten_context_text(text, 9000)
    rubric_lines = {
        key: "; ".join(values[:5])
        for key, values in rubric.items()
    }

    system_prompt = (
        "Du bist ein genauer, lernförderlicher Korrekturassistent für deutschsprachige Maturaufsätze. "
        "Antworte nur mit gültigem JSON. Schreibe vollständige deutsche Sätze ohne Stichworte."
    )
    user_prompt = "\n".join(
        [
            f"Dokumenttyp: {type_label}",
            f"Thema: {topic or 'nicht vorgegeben'}",
            f"Leitfrage/These: {thesis or 'nicht vorgegeben'}",
            f"Aufgabenstellung: {assignment_text or 'nicht vorgegeben'}",
            f"Gym-Stufe: {gym_level}",
            f"Absätze: {paragraph_count}",
            f"Kriterium Inhalt: {rubric_lines['inhalt']}",
            f"Kriterium Aufbau: {rubric_lines['aufbau']}",
            f"Kriterium Ausdruck: {rubric_lines['ausdruck']}",
            f"Formhinweise: {'; '.join(structure_notes[:3]) if structure_notes else 'keine'}",
            "Zähle für Kriterium 4 nur Grammatik- und Rechtschreibfehler, keine Zeichensetzung.",
            "Gib genau dieses JSON zurück:",
            '{"document_type":"essay|speech|linear_discussion|dialectical_discussion","summary":"2-4 Sätze","criteria_comments":{"inhalt":{"score":4.5,"comment":"..."}, "aufbau":{"score":4.5,"comment":"..."}, "ausdruck":{"score":4.5,"comment":"..."}},"annotations":[{"paragraph_index":0,"snippet":"...","category":"inhalt|aufbau|ausdruck|rhetorik","action":"kommentieren|ueberarbeiten","comment":"...","suggestion":"..."}],"language_errors":[{"paragraph_index":0,"snippet":"...","category":"grammatik|rechtschreibung","comment":"...","suggestion":"..."}]}',
            "Maximal 8 annotations und maximal 35 language_errors.",
            "Text:",
            text,
        ]
    )

    return system_prompt, user_prompt


def build_stage1_prompt(
    chunk_text: str,
    document_type: str,
    chunk_index: int,
    chunk_count: int,
    gym_level: str,
    assignment_text: str = "",
    topic: str = "",
    thesis: str = "",
) -> tuple[str, str]:
    rubric = FORM_GUIDELINES[document_type]
    type_label = FORM_LABELS[document_type]
    assignment_text = _shorten_context_text(assignment_text, 320)
    topic = _shorten_context_text(topic, 140)
    thesis = _shorten_context_text(thesis, 160)

    system_prompt = (
        "Du analysierst einen Teil eines deutschsprachigen Maturaufsatzes. "
        "Antworte nur mit gültigem JSON in knapper Form."
    )
    user_prompt = "\n".join(
        [
            f"Dokumenttyp: {type_label}",
            f"Teilabschnitt: {chunk_index + 1} von {chunk_count}",
            f"Thema: {topic or 'nicht vorgegeben'}",
            f"Leitfrage/These: {thesis or 'nicht vorgegeben'}",
            f"Aufgabenstellung: {assignment_text or 'nicht vorgegeben'}",
            f"Gym-Stufe: {gym_level}",
            f"Inhalt-Fokus: {'; '.join(rubric['inhalt'][:4])}",
            f"Aufbau-Fokus: {'; '.join(rubric['aufbau'][:4])}",
            f"Ausdruck-Fokus: {'; '.join(rubric['ausdruck'][:4])}",
            "Gib genau dieses JSON zurück:",
            '{"chunk_summary":"1-2 Sätze","criteria_signals":{"inhalt":{"score":4.5,"evidence":"..."}, "aufbau":{"score":4.5,"evidence":"..."}, "ausdruck":{"score":4.5,"evidence":"..."}},"annotations":[{"paragraph_index":0,"snippet":"...","category":"inhalt|aufbau|ausdruck|rhetorik","action":"kommentieren|ueberarbeiten","comment":"...","suggestion":"..."}],"language_errors":[{"paragraph_index":0,"snippet":"...","category":"grammatik|rechtschreibung","comment":"...","suggestion":"..."}]}',
            "Maximal 4 annotations und maximal 12 language_errors.",
            "Abschnitt:",
            chunk_text,
        ]
    )
    return system_prompt, user_prompt


def build_stage2_prompt(
    document_type: str,
    gym_level: str,
    assignment_text: str = "",
    topic: str = "",
    thesis: str = "",
    chunk_summaries: list[str] | None = None,
    criteria_signals: dict[str, dict[str, Any]] | None = None,
) -> tuple[str, str]:
    rubric = FORM_GUIDELINES[document_type]
    type_label = FORM_LABELS[document_type]
    structure_notes = DISCUSSION_STRUCTURE_NOTES.get(document_type, [])
    assignment_text = _shorten_context_text(assignment_text, 320)
    topic = _shorten_context_text(topic, 140)
    thesis = _shorten_context_text(thesis, 160)
    chunk_summaries = chunk_summaries or []
    criteria_signals = criteria_signals or {}

    signal_lines = []
    for key in ("inhalt", "aufbau", "ausdruck"):
        entry = criteria_signals.get(key, {})
        score = entry.get("score", 4.0)
        evidence = _shorten_context_text(str(entry.get("evidence", "")), 280)
        signal_lines.append(f"{key}: Teilnote {score:.2f}; Hinweise {evidence or 'keine'}")

    system_prompt = (
        "Du erstellst das Gesamtfeedback eines deutschsprachigen Maturaufsatzes aus bereits vorbereiteten Teilanalysen. "
        "Antworte nur mit gültigem JSON."
    )
    user_prompt = "\n".join(
        [
            f"Dokumenttyp: {type_label}",
            f"Thema: {topic or 'nicht vorgegeben'}",
            f"Leitfrage/These: {thesis or 'nicht vorgegeben'}",
            f"Aufgabenstellung: {assignment_text or 'nicht vorgegeben'}",
            f"Gym-Stufe: {gym_level}",
            f"Kriterium Inhalt: {'; '.join(rubric['inhalt'][:5])}",
            f"Kriterium Aufbau: {'; '.join(rubric['aufbau'][:5])}",
            f"Kriterium Ausdruck: {'; '.join(rubric['ausdruck'][:5])}",
            f"Formhinweise: {'; '.join(structure_notes[:3]) if structure_notes else 'keine'}",
            "Teilanalysen:",
            *[f"- {summary}" for summary in chunk_summaries[:8]],
            "Verdichtete Hinweise:",
            *signal_lines,
            "Gib genau dieses JSON zurück:",
            '{"document_type":"essay|speech|linear_discussion|dialectical_discussion","summary":"2-4 Sätze","criteria_comments":{"inhalt":{"score":4.5,"comment":"..."}, "aufbau":{"score":4.5,"comment":"..."}, "ausdruck":{"score":4.5,"comment":"..."}}}',
        ]
    )
    return system_prompt, user_prompt


def parse_json_response(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if not raw:
        raise ReviewError("LM Studio hat eine leere Antwort geliefert.")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ReviewError("LM Studio hat kein gültiges JSON geliefert.")
        return json.loads(raw[start : end + 1])


def clamp_score(value: Any, fallback: float = 4.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = fallback
    return max(1.0, min(6.0, round(number * 4) / 4))


def normalize_annotations(paragraphs: list[str], items: list[dict[str, Any]], allowed_categories: set[str]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[int, str, str]] = set()

    for item in items or []:
        snippet = str(item.get("snippet", "")).strip()
        if not snippet:
            continue

        try:
            paragraph_index = int(item.get("paragraph_index", -1))
        except (TypeError, ValueError):
            paragraph_index = -1

        category = str(item.get("category", "")).strip().lower()
        if category not in allowed_categories:
            continue

        if paragraph_index < 0 or paragraph_index >= len(paragraphs):
            paragraph_index = next((idx for idx, paragraph in enumerate(paragraphs) if snippet in paragraph), -1)
        if paragraph_index == -1 or snippet not in paragraphs[paragraph_index]:
            continue

        key = (paragraph_index, snippet, category)
        if key in seen:
            continue
        seen.add(key)

        normalized.append(
            {
                "paragraph_index": paragraph_index,
                "snippet": snippet,
                "category": category,
                "action": str(item.get("action", "kommentieren")).strip().lower() or "kommentieren",
                "comment": normalize_sentence(item.get("comment", "")),
                "suggestion": normalize_sentence(item.get("suggestion", "")),
            }
        )

    return normalized


def normalize_sentence(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return ""
    if text[-1] not in ".!?":
        text += "."
    return text


def normalize_review(
    raw_payload: dict[str, Any],
    paragraphs: list[str],
    requested_type: str,
    gym_level: str,
    assignment_text: str = "",
    topic: str = "",
    thesis: str = "",
) -> dict[str, Any]:
    full_text = "\n\n".join(paragraphs)
    word_count = count_words(full_text)
    detected_request = requested_type if requested_type != "auto" else raw_payload.get("document_type", "essay")
    document_type = detect_document_type(full_text, detected_request, assignment_text, topic)

    criteria_raw = raw_payload.get("criteria_comments", {}) or {}
    criteria_comments = {}
    for key in ("inhalt", "aufbau", "ausdruck"):
        entry = criteria_raw.get(key, {}) if isinstance(criteria_raw, dict) else {}
        criteria_comments[key] = {
            "score": clamp_score(entry.get("score")),
            "comment": normalize_sentence(entry.get("comment", "")),
        }

    language_errors = normalize_annotations(paragraphs, raw_payload.get("language_errors", []), {"grammatik", "rechtschreibung"})
    annotations = normalize_annotations(paragraphs, raw_payload.get("annotations", []), {"inhalt", "aufbau", "ausdruck", "rhetorik"})
    orthography = calculate_orthography_grade(gym_level, len(language_errors), word_count)

    return {
        "document_type": document_type,
        "document_type_label": FORM_LABELS.get(document_type, document_type),
        "topic": normalize_sentence(topic).rstrip(".") if topic else "",
        "thesis": normalize_sentence(thesis).rstrip(".") if thesis else "",
        "assignment_text": normalize_sentence(assignment_text),
        "summary": normalize_sentence(raw_payload.get("summary", "")),
        "criteria_comments": criteria_comments,
        "annotations": annotations,
        "language_errors": language_errors,
        "orthography": {
            "level": gym_level,
            "error_count": orthography.error_count,
            "word_count": orthography.word_count,
            "errors_per_200": round(orthography.errors_per_200, 2),
            "grade": orthography.grade,
            "comment": (
                f"Für das vierte Kriterium wurden ausschließlich Grammatik- und Rechtschreibfehler gezählt. "
                f"Bei {orthography.error_count} relevanten Fehlern in {orthography.word_count} Wörtern ergibt sich "
                f"eine Fehlerdichte von {orthography.errors_per_200:.2f} Fehlern pro 200 Wörter und damit "
                f"eine Teilnote von {orthography.grade:.2f}."
            ),
        },
    }


def _call_model_json(
    base_url: str,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> dict[str, Any]:
    payload = _http_post_json(
        f"{base_url}/chat/completions",
        {
            "model": model_name,
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=180,
    )
    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    return parse_json_response(content)


def _select_review_paragraphs(paragraphs: list[str], max_chars: int) -> tuple[list[str], bool]:
    selected: list[str] = []
    total = 0
    for paragraph in paragraphs:
        addition = len(paragraph) + 2
        if selected and total + addition > max_chars:
            break
        selected.append(paragraph)
        total += addition
    return selected or paragraphs[:1], len(selected) < len(paragraphs)


def _chunk_paragraphs(
    paragraphs: list[str],
    *,
    max_chunk_chars: int,
    max_chunk_paragraphs: int,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current: list[tuple[int, str]] = []
    current_chars = 0

    for index, paragraph in enumerate(paragraphs):
        addition = len(paragraph) + 2
        if current and (len(current) >= max_chunk_paragraphs or current_chars + addition > max_chunk_chars):
            chunks.append(
                {
                    "start_index": current[0][0],
                    "end_index": current[-1][0],
                    "paragraphs": [value for _, value in current],
                    "text": "\n\n".join(value for _, value in current),
                }
            )
            current = []
            current_chars = 0

        current.append((index, paragraph))
        current_chars += addition

    if current:
        chunks.append(
            {
                "start_index": current[0][0],
                "end_index": current[-1][0],
                "paragraphs": [value for _, value in current],
                "text": "\n\n".join(value for _, value in current),
            }
        )
    return chunks


def _aggregate_chunk_results(chunk_results: list[dict[str, Any]]) -> dict[str, Any]:
    summaries: list[str] = []
    annotations: list[dict[str, Any]] = []
    language_errors: list[dict[str, Any]] = []
    criteria_signals: dict[str, dict[str, Any]] = {
        "inhalt": {"scores": [], "evidence": []},
        "aufbau": {"scores": [], "evidence": []},
        "ausdruck": {"scores": [], "evidence": []},
    }
    section_reports: list[dict[str, Any]] = []

    for index, result in enumerate(chunk_results):
        summary = normalize_sentence(result.get("chunk_summary", ""))
        if summary:
            summaries.append(summary)

        raw_signals = result.get("criteria_signals", {}) or {}
        section_signal_map: dict[str, dict[str, Any]] = {}
        for key in ("inhalt", "aufbau", "ausdruck"):
            entry = raw_signals.get(key, {}) if isinstance(raw_signals, dict) else {}
            score = clamp_score(entry.get("score"), fallback=4.0)
            criteria_signals[key]["scores"].append(score)
            evidence = normalize_sentence(entry.get("evidence", ""))
            if evidence:
                criteria_signals[key]["evidence"].append(evidence)
            section_signal_map[key] = {
                "score": score,
                "evidence": evidence,
            }

        annotations.extend(result.get("annotations", []) or [])
        language_errors.extend(result.get("language_errors", []) or [])
        start_index = int(result.get("start_index", 0))
        end_index = int(result.get("end_index", start_index))
        section_reports.append(
            {
                "label": f"Abschnitt {index + 1}",
                "range_label": f"Absätze {start_index + 1}–{end_index + 1}" if end_index > start_index else f"Absatz {start_index + 1}",
                "summary": summary or "Für diesen Abschnitt liegt keine Verdichtung vor.",
                "criteria_signals": section_signal_map,
                "annotation_count": len(result.get("annotations", []) or []),
                "language_error_count": len(result.get("language_errors", []) or []),
            }
        )

    aggregated_signals = {}
    for key, value in criteria_signals.items():
        scores = value["scores"] or [4.0]
        aggregated_signals[key] = {
            "score": round(sum(scores) / len(scores), 2),
            "evidence": " ".join(value["evidence"][:4]),
        }

    return {
        "chunk_summaries": summaries,
        "criteria_signals": aggregated_signals,
        "annotations": annotations,
        "language_errors": language_errors,
        "section_reports": section_reports,
    }


def run_review(
    paragraphs: list[str],
    requested_type: str,
    gym_level: str,
    assignment_text: str = "",
    topic: str = "",
    thesis: str = "",
    base_url: str | None = None,
    model_name: str | None = None,
    school_mode: bool = False,
) -> dict[str, Any]:
    full_text = "\n\n".join(paragraphs).strip()
    if not full_text:
        raise ReviewError("Das Word-Dokument enthält keinen auswertbaren Text.")
    limits = get_runtime_limits(school_mode)
    review_paragraphs, was_trimmed = _select_review_paragraphs(paragraphs, limits["max_review_text_chars"])
    review_warnings = build_input_warnings(
        review_paragraphs,
        assignment_text=assignment_text,
        topic=topic,
        thesis=thesis,
        school_mode=school_mode,
    )
    if was_trimmed:
        review_warnings.append(
            "Für die eigentliche KI-Korrektur wurde nur der erste Teil des Aufsatzes analysiert, "
            "weil das aktuelle lokale Modell sonst instabil würde."
        )

    base_url = (base_url or LM_STUDIO_BASE_URL).rstrip("/")
    model_name = model_name or fetch_model(base_url)
    detected_type = detect_document_type("\n\n".join(review_paragraphs), requested_type, assignment_text, topic)
    chunks = _chunk_paragraphs(
        review_paragraphs,
        max_chunk_chars=limits["max_chunk_chars"],
        max_chunk_paragraphs=limits["max_chunk_paragraphs"],
    )
    chunk_results = []
    for index, chunk in enumerate(chunks):
        stage1_system, stage1_user = build_stage1_prompt(
            chunk["text"],
            detected_type,
            index,
            len(chunks),
            gym_level,
            assignment_text=assignment_text,
            topic=topic,
            thesis=thesis,
        )
        chunk_result = _call_model_json(
            base_url,
            model_name,
            stage1_system,
            stage1_user,
            max_tokens=limits["stage1_max_tokens"],
        )
        for field_name in ("annotations", "language_errors"):
            for item in chunk_result.get(field_name, []) or []:
                try:
                    item["paragraph_index"] = int(item.get("paragraph_index", 0)) + int(chunk["start_index"])
                except (TypeError, ValueError):
                    item["paragraph_index"] = int(chunk["start_index"])
        chunk_result["start_index"] = chunk["start_index"]
        chunk_result["end_index"] = chunk["end_index"]
        chunk_results.append(chunk_result)

    aggregated = _aggregate_chunk_results(chunk_results)
    stage2_system, stage2_user = build_stage2_prompt(
        detected_type,
        gym_level,
        assignment_text=assignment_text,
        topic=topic,
        thesis=thesis,
        chunk_summaries=aggregated["chunk_summaries"],
        criteria_signals=aggregated["criteria_signals"],
    )
    prompt_tokens = estimate_tokens(stage2_system) + estimate_tokens(stage2_user)
    if prompt_tokens > 3000:
        raise ReviewError(
            "Die verdichtete Gesamtauswertung ist für das aktuelle lokale Modell noch zu umfangreich. "
            "Bitte nutze ein Modell mit größerem Kontextfenster oder reduziere den Textumfang."
        )

    stage2_payload = _call_model_json(
        base_url,
        model_name,
        stage2_system,
        stage2_user,
        max_tokens=limits["stage2_max_tokens"],
    )
    stage2_payload["annotations"] = aggregated["annotations"]
    stage2_payload["language_errors"] = aggregated["language_errors"]
    normalized = normalize_review(
        stage2_payload,
        paragraphs,
        requested_type,
        gym_level,
        assignment_text=assignment_text,
        topic=topic,
        thesis=thesis,
    )
    normalized["model"] = model_name
    normalized["base_url"] = base_url
    normalized["warnings"] = review_warnings
    normalized["school_mode"] = school_mode
    normalized["section_reports"] = aggregated["section_reports"]
    normalized["pipeline"] = {
        "mode": "two_stage_review",
        "stage_1": f"{len(chunks)} Abschnittsanalysen mit kompakten Teilprompts erstellt.",
        "stage_2": "Aus den Teilanalysen wurde ein verdichtetes Gesamtfeedback berechnet.",
    }
    return normalized


def _http_get_json(url: str, timeout: int) -> dict[str, Any]:
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise LMStudioHTTPError(exc.code, _read_http_error(exc)) from exc
    except error.URLError as exc:
        raise ReviewError(f"LM Studio ist nicht erreichbar: {exc.reason}") from exc


def _http_post_json(url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise LMStudioHTTPError(exc.code, _read_http_error(exc)) from exc
    except error.URLError as exc:
        raise ReviewError(f"LM Studio ist nicht erreichbar: {exc.reason}") from exc


def _read_http_error(exc: error.HTTPError) -> str:
    try:
        payload = json.loads(exc.read().decode("utf-8"))
    except Exception:
        return f"LM Studio antwortete mit HTTP {exc.code}."
    if isinstance(payload, dict):
        inner = payload.get("error")
        if isinstance(inner, dict) and inner.get("message"):
            return _normalize_lm_error(str(inner["message"]))
        if isinstance(inner, str):
            return _normalize_lm_error(inner)
    return _normalize_lm_error(f"LM Studio antwortete mit HTTP {exc.code}.")


def _normalize_lm_error(message: str) -> str:
    normalized = str(message or "").strip()
    lowered = normalized.lower()
    if "tokens to keep" in lowered or "context length" in lowered:
        return (
            "Das geladene LM-Studio-Modell hat zu wenig Kontext für diesen Auftrag. "
            "Bitte lade ein Modell mit größerem Kontextfenster oder kürze den eingegebenen Text."
        )
    if "response_format.type" in lowered:
        return (
            "LM Studio hat den Antwortmodus abgelehnt. Bitte den Korrekturroboter neu starten, "
            "damit die aktuelle Serverversion verwendet wird."
        )
    return normalized
