import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib import error, request


LM_STUDIO_BASE_URL = os.environ.get("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
LM_STUDIO_MODEL = os.environ.get("LM_STUDIO_MODEL", "").strip()


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
    lowered = f"{assignment_text}\n{topic}\n{text}".lower()
    speech_hits = sum(lowered.count(token) for token in ["publikum", "wir", "rede", "appell", "zuhörer", "meine damen"])
    dialectical_hits = sum(
        lowered.count(token)
        for token in ["vor- und nachteile", "vor und nachteile", "nehmen sie stellung", "pro und contra", "fluch und segen"]
    )
    linear_hits = sum(lowered.count(token) for token in ["warum", "was macht", "gute gründe", "gute gruende", "weshalb"])
    if speech_hits >= 4:
        return "speech"
    if dialectical_hits >= 1:
        return "dialectical_discussion"
    if linear_hits >= 1:
        return "linear_discussion"
    return "essay"


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

    system_prompt = (
        "Du bist ein streng genauer, aber lernförderlicher Korrekturroboter für deutschsprachige "
        "Maturaufsatztexte. Du antwortest ausschließlich mit validem JSON. Die Kommentare müssen "
        "in einwandfreiem Deutsch, als volle Sätze und ohne Stichworte formuliert sein. "
        "Wenn es sich um eine lineare oder dialektische Erörterung handelt, musst du die "
        "spezifische Form konsequent anwenden."
    )

    user_payload = {
        "auftrag": (
            "Bewerte den hochgeladenen Text nach den ersten drei Kriterien mit sehr ausführlichen, "
            "konstruktiven und lernförderlichen Kommentaren. Markiere konkrete Textstellen mit "
            "präzisen Überarbeitungshinweisen. Zähle für das vierte Kriterium ausschließlich "
            "Grammatik- und Rechtschreibfehler; Zeichensetzungsfehler werden nicht mitgezählt. "
            "Prüfe den Text konsequent daran, ob er die angegebene Leitfrage oder These einlöst."
        ),
        "dokumenttyp": type_label,
        "thema": topic or "nicht vorgegeben",
        "leitfrage_oder_these": thesis or "nicht zusätzlich angegeben",
        "aufgabenstellung": assignment_text or "nicht zusätzlich angegeben",
        "gym_stufe_für_sprache": gym_level,
        "bewertungskriterien_1_bis_3": rubric,
        "argumentationslehre_gradmesser": ARGUMENTATION_MEASURE,
        "rhetorische_formen_gradmesser": RHETORICAL_FORMS,
        "formspezifische_hinweise": structure_notes,
        "absatzanzahl": paragraph_count,
        "ausgabeformat": {
            "document_type": "essay|speech|linear_discussion|dialectical_discussion",
            "summary": "2-4 Sätze",
            "criteria_comments": {
                "inhalt": {"score": "1.0-6.0", "comment": "ganzer Absatz"},
                "aufbau": {"score": "1.0-6.0", "comment": "ganzer Absatz"},
                "ausdruck": {"score": "1.0-6.0", "comment": "ganzer Absatz"},
            },
            "annotations": [
                {
                    "paragraph_index": 0,
                    "snippet": "exakte Textstelle",
                    "category": "inhalt|aufbau|ausdruck|rhetorik",
                    "action": "kommentieren|ueberarbeiten",
                    "comment": "ganzer Satz",
                    "suggestion": "präziser Verbesserungsvorschlag in ganzen Sätzen",
                }
            ],
            "language_errors": [
                {
                    "paragraph_index": 0,
                    "snippet": "exakte fehlerhafte Formulierung",
                    "category": "grammatik|rechtschreibung",
                    "comment": "kurze Erklärung in vollem Satz",
                    "suggestion": "korrekte Form",
                }
            ],
        },
        "regeln": [
            "Gib maximal 18 annotations für Inhalt, Aufbau, Ausdruck und Rhetorik aus.",
            "Gib maximal 80 language_errors aus.",
            "Jede annotation und jeder language_error muss mit einem im Text wirklich vorhandenen snippet arbeiten.",
            "Jede criteria_comment muss sehr ausführlich, konstruktiv und lernförderlich sein.",
            "Die Kommentare dürfen keine Aufzählungen enthalten.",
        ],
        "text": text,
    }

    return system_prompt, json.dumps(user_payload, ensure_ascii=False)


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


def run_review(
    paragraphs: list[str],
    requested_type: str,
    gym_level: str,
    assignment_text: str = "",
    topic: str = "",
    thesis: str = "",
    base_url: str | None = None,
    model_name: str | None = None,
) -> dict[str, Any]:
    full_text = "\n\n".join(paragraphs).strip()
    if not full_text:
        raise ReviewError("Das Word-Dokument enthält keinen auswertbaren Text.")

    base_url = (base_url or LM_STUDIO_BASE_URL).rstrip("/")
    model_name = model_name or fetch_model(base_url)
    detected_type = detect_document_type(full_text, requested_type, assignment_text, topic)
    system_prompt, user_prompt = build_prompt(
        full_text,
        detected_type,
        len(paragraphs),
        gym_level,
        assignment_text=assignment_text,
        topic=topic,
        thesis=thesis,
    )

    payload = _http_post_json(
        f"{base_url}/chat/completions",
        {
            "model": model_name,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=180,
    )
    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    normalized = normalize_review(
        parse_json_response(content),
        paragraphs,
        requested_type,
        gym_level,
        assignment_text=assignment_text,
        topic=topic,
        thesis=thesis,
    )
    normalized["model"] = model_name
    normalized["base_url"] = base_url
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
            return str(inner["message"])
        if isinstance(inner, str):
            return inner
    return f"LM Studio antwortete mit HTTP {exc.code}."
