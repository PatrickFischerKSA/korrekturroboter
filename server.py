import base64
import json
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from docx_pipeline import build_reviewed_docx, read_docx_paragraphs, read_reference_paragraphs
from review_engine import (
    LANGUAGETOOL_BASE_URL,
    LM_STUDIO_BASE_URL,
    LMStudioHTTPError,
    ReviewError,
    check_languagetool_health,
    fetch_model,
    infer_context_from_dossier,
    list_models,
    run_review,
)


ROOT_DIR = Path(__file__).resolve().parent
STATIC_DIR = ROOT_DIR / "static"
HOST = os.environ.get("KORREKTURROBOTER_HOST", "127.0.0.1")
PORT = int(os.environ.get("KORREKTURROBOTER_PORT", "8090"))
ALLOWED_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
PRIVACY_NOTICE = "Datenschutzmodus aktiv: Der Dienst arbeitet ausschließlich mit lokalem LM Studio und lokalem LanguageTool auf localhost."


class KorrekturHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._handle_health()
            return
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/dossier-detect":
            self._handle_dossier_detect()
            return
        if parsed.path == "/api/review":
            self._handle_review()
            return
        self._send_json({"error": "Unbekannter Endpunkt."}, status=HTTPStatus.NOT_FOUND)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path: str) -> str:
        if path.endswith(".js"):
            return "application/javascript; charset=utf-8"
        if path.endswith(".css"):
            return "text/css; charset=utf-8"
        return mimetypes.guess_type(path)[0] or "application/octet-stream"

    def _handle_health(self) -> None:
        base_url = _strict_local_base_url(LM_STUDIO_BASE_URL)
        lt_base_url = _strict_local_base_url(LANGUAGETOOL_BASE_URL)
        try:
            models = [entry.get("id", "") for entry in list_models(base_url) if entry.get("id")]
            if not models:
                raise ReviewError("LM Studio ist erreichbar, liefert aber keine geladenen Modelle.")
            lt_payload: dict[str, object]
            try:
                lt_health = check_languagetool_health(lt_base_url)
                lt_payload = {
                    "ok": True,
                    "base_url": lt_health["base_url"],
                    "languages": lt_health["languages"],
                }
            except Exception as lt_exc:
                lt_payload = {
                    "ok": False,
                    "base_url": lt_base_url,
                    "error": str(lt_exc),
                }
            self._send_json(
                {
                    "ok": True,
                    "base_url": base_url,
                    "models": models,
                    "selected_model": models[0],
                    "languagetool": lt_payload,
                    "privacy_notice": PRIVACY_NOTICE,
                }
            )
        except Exception as exc:
            self._send_json(
                {
                    "ok": False,
                    "base_url": base_url,
                    "languagetool": {
                        "ok": False,
                        "base_url": lt_base_url,
                    },
                    "error": str(exc),
                    "privacy_notice": PRIVACY_NOTICE,
                },
                status=HTTPStatus.BAD_GATEWAY,
            )

    def _handle_review(self) -> None:
        try:
            payload = self._read_json()
            file_name = str(payload.get("filename", "aufsatz.docx"))
            document_base64 = str(payload.get("document_base64", ""))
            dossier_name = str(payload.get("dossier_name", "")).strip()
            dossier_base64 = str(payload.get("dossier_base64", "")).strip()
            document_type = str(payload.get("document_type", "auto"))
            topic = str(payload.get("topic", "")).strip()
            thesis = str(payload.get("thesis", "")).strip()
            assignment_text = str(payload.get("assignment_text", "")).strip()
            gym_level = str(payload.get("gym_level", "1"))
            school_mode = bool(payload.get("school_mode", False))
            requested_base_url = str(payload.get("base_url", "")).strip()
            base_url = _strict_local_base_url(LM_STUDIO_BASE_URL)
            model_name = str(payload.get("model", "")).strip() or None

            if not document_base64:
                raise ReviewError("Es wurde kein DOCX-Dokument übermittelt.")
            if requested_base_url and requested_base_url.rstrip("/") != base_url:
                raise ReviewError("Externe LM-Studio-URLs sind im Datenschutzmodus gesperrt.")

            raw_document = base64.b64decode(document_base64)
            paragraphs = read_docx_paragraphs(raw_document)
            dossier_context = self._read_dossier_context(dossier_name, dossier_base64, paragraphs, school_mode=school_mode)
            if not topic:
                topic = dossier_context.get("topic", "")
            if not assignment_text:
                assignment_text = dossier_context.get("assignment_text", "")
            if document_type == "auto" and dossier_context.get("document_type"):
                document_type = str(dossier_context["document_type"])
            review = run_review(
                paragraphs=paragraphs,
                requested_type=document_type,
                gym_level=gym_level,
                assignment_text=assignment_text,
                topic=topic,
                thesis=thesis,
                base_url=base_url,
                model_name=model_name or fetch_model(base_url),
                school_mode=school_mode,
            )
            review["privacy_notice"] = PRIVACY_NOTICE
            reviewed_docx = build_reviewed_docx(file_name, paragraphs, review)
            download_name = f"{Path(file_name).stem}_korrigiert.docx"

            self._send_json(
                {
                    "ok": True,
                    "review": review,
                    "download_name": download_name,
                    "reviewed_document_base64": base64.b64encode(reviewed_docx).decode("ascii"),
                    "dossier_context": dossier_context,
                }
            )
        except ReviewError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except LMStudioHTTPError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)
        except Exception as exc:
            self._send_json({"ok": False, "error": f"Interner Fehler: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_dossier_detect(self) -> None:
        try:
            payload = self._read_json()
            document_name = str(payload.get("filename", "aufsatz.docx"))
            document_base64 = str(payload.get("document_base64", "")).strip()
            dossier_name = str(payload.get("dossier_name", "")).strip()
            dossier_base64 = str(payload.get("dossier_base64", "")).strip()
            school_mode = bool(payload.get("school_mode", False))

            if not document_base64:
                raise ReviewError("Für die Themen-Erkennung fehlt der Aufsatz.")
            if not dossier_base64 or not dossier_name:
                raise ReviewError("Für die Themen-Erkennung fehlt das Prüfungsdossier.")

            essay_paragraphs = read_docx_paragraphs(base64.b64decode(document_base64))
            dossier_context = self._read_dossier_context(dossier_name, dossier_base64, essay_paragraphs, school_mode=school_mode)
            if not dossier_context.get("topic") and not dossier_context.get("assignment_text"):
                raise ReviewError("Im Prüfungsdossier konnte kein passendes Thema zum Aufsatz erkannt werden.")

            self._send_json(
                {
                    "ok": True,
                    "filename": document_name,
                    "dossier_context": dossier_context,
                }
            )
        except ReviewError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            self._send_json({"ok": False, "error": f"Interner Fehler: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _read_dossier_context(
        self,
        dossier_name: str,
        dossier_base64: str,
        essay_paragraphs: list[str],
        *,
        school_mode: bool = False,
    ) -> dict:
        if not dossier_base64 or not dossier_name:
            return {}
        dossier_bytes = base64.b64decode(dossier_base64)
        dossier_paragraphs = read_reference_paragraphs(dossier_name, dossier_bytes)
        return infer_context_from_dossier(essay_paragraphs, dossier_paragraphs, school_mode=school_mode)

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ReviewError("Die Anfrage enthält keinen JSON-Body.")
        body = self.rfile.read(content_length)
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ReviewError("Der JSON-Body ist ungültig.") from exc

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def _strict_local_base_url(candidate: str) -> str:
    normalized = (candidate or LM_STUDIO_BASE_URL).rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ReviewError("Die LM-Studio-URL ist ungültig.")
    if parsed.hostname not in ALLOWED_LOCAL_HOSTS:
        raise ReviewError("Im Datenschutzmodus sind nur lokale LM-Studio-Endpunkte erlaubt.")
    return normalized


def _strict_local_bind_host(candidate: str) -> str:
    if candidate not in ALLOWED_LOCAL_HOSTS:
        raise ReviewError("Im Datenschutzmodus darf der Webserver nur an localhost gebunden werden.")
    return candidate


def main() -> None:
    bind_host = _strict_local_bind_host(HOST)
    server = ThreadingHTTPServer((bind_host, PORT), KorrekturHandler)
    print(PRIVACY_NOTICE)
    print("Hinweis: LM Studio wird erst in der Weboberfläche geprüft.")
    print(f"Korrekturroboter läuft auf http://{bind_host}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    try:
        main()
    except ReviewError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
