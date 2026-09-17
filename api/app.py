"""Flask application for BORO BHAI web UI."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

from api.service import (
    add_history_entry,
    error_response,
    get_history,
    get_report_text,
    handle_chat,
    handle_job_analysis,
    handle_research,
    handle_skill_gap,
    handle_upload,
    list_reports,
)
from config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "web"


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(WEB_ROOT / "templates"),
        static_folder=str(WEB_ROOT / "static"),
    )
    app.config["MAX_CONTENT_LENGTH"] = settings.api_max_content_length

    @app.errorhandler(413)
    def request_too_large(_error):
        return error_response("Request payload is too large.", status=413, code="payload_too_large")

    @app.errorhandler(500)
    def internal_error(_error):
        return error_response("Internal server error.", status=500, code="internal_error")

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/api/health")
    def health() -> Response:
        return jsonify({"success": True, "status": "ok"})

    @app.get("/api/history")
    def history() -> Response:
        session_id = request.args.get("session_id")
        return jsonify({"success": True, "history": get_history(session_id)})

    @app.post("/api/chat")
    def chat() -> Response:
        try:
            payload = request.get_json(silent=True) or {}
            session_id = request.args.get("session_id") or payload.get("session_id")
            result = handle_chat(payload, session_id=session_id)
            return jsonify({"success": True, "data": result})
        except ValueError as exc:
            return error_response(str(exc), status=400, code="validation_error")
        except Exception as exc:  # pragma: no cover - defensive guard
            return error_response(f"Chat failed: {exc}", status=500, code="chat_error")

    @app.post("/api/research")
    def research() -> Response:
        try:
            payload = request.get_json(silent=True) or {}
            result = handle_research(payload)
            return jsonify({"success": True, "data": result})
        except ValueError as exc:
            return error_response(str(exc), status=400, code="validation_error")
        except RuntimeError as exc:
            return error_response(str(exc), status=502, code="research_error")
        except Exception as exc:  # pragma: no cover - defensive guard
            return error_response(f"Research failed: {exc}", status=500, code="research_error")

    @app.post("/api/job-analysis")
    def job_analysis() -> Response:
        try:
            payload = request.get_json(silent=True) or {}
            result = handle_job_analysis(payload)
            return jsonify({"success": True, "data": result})
        except ValueError as exc:
            return error_response(str(exc), status=400, code="validation_error")
        except RuntimeError as exc:
            return error_response(str(exc), status=502, code="job_analysis_error")

    @app.post("/api/skill-gap")
    def skill_gap() -> Response:
        try:
            payload = request.get_json(silent=True) or {}
            result = handle_skill_gap(payload)
            return jsonify({"success": True, "data": result})
        except ValueError as exc:
            return error_response(str(exc), status=400, code="validation_error")
        except RuntimeError as exc:
            return error_response(str(exc), status=502, code="skill_gap_error")

    @app.post("/api/upload")
    def upload() -> Response:
        try:
            session_id = request.args.get("session_id")
            file_storage = request.files.get("file")
            result = handle_upload(file_storage, session_id)
            return jsonify({"success": True, "data": result})
        except ValueError as exc:
            return error_response(str(exc), status=400, code="upload_error")
        except Exception as exc:  # pragma: no cover - defensive guard
            return error_response(f"Upload failed: {exc}", status=500, code="upload_error")

    @app.get("/api/reports")
    def reports() -> Response:
        try:
            return jsonify({"success": True, "reports": list_reports()})
        except Exception as exc:  # pragma: no cover - defensive guard
            return error_response(f"Report listing failed: {exc}", status=500, code="report_error")

    @app.get("/api/reports/<path:filename>")
    def report_detail(filename: str) -> Response:
        try:
            content = get_report_text(filename)
            return jsonify({"success": True, "filename": filename, "content": content})
        except (ValueError, FileNotFoundError) as exc:
            return error_response(str(exc), status=404 if isinstance(exc, FileNotFoundError) else 400, code="report_error")

    @app.post("/api/clear-history")
    def clear_history() -> Response:
        session_id = request.args.get("session_id") or (request.get_json(silent=True) or {}).get("session_id")
        history = get_history(session_id)
        history.clear()
        add_history_entry(session_id, "system", "Conversation history cleared.")
        return jsonify({"success": True, "history": history})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
