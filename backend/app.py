import os
import time

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from pydantic import ValidationError

from .db import init_db, SessionLocal
from .models import Alert
from .schemas import AnalyzeRequest, AlertOut
from .preprocess import clean_text, extract_iocs
from .services.llm_service import get_llm_service, LLMService
from .alert_engine import build_alert

load_dotenv()


def create_app():
    app = Flask(__name__)
    origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
    CORS(app, origins=origins, methods=["GET", "POST", "DELETE", "OPTIONS"])
    init_db()

    @app.teardown_appcontext
    def remove_session(exception=None):
        SessionLocal.remove()

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/api/analyze", methods=["POST"])
    # TODO(stretch): rate limit decorator, see docs/implementation_notes.md decision #5
    def analyze():
        try:
            payload = AnalyzeRequest.model_validate(request.get_json(force=True, silent=True) or {})
        except ValidationError as e:
            return jsonify({"error": "invalid_request", "details": e.errors(include_url=False, include_context=False)}), 400

        start = time.time()
        cleaned = clean_text(payload.text)
        regex_iocs = extract_iocs(cleaned)

        try:
            if payload.provider:
                llm_result = LLMService(provider=payload.provider).summarize(cleaned)
            else:
                llm_result = get_llm_service().summarize(cleaned)
        except ValueError as e:
            # unknown provider name, raised synchronously at LLMService construction --
            # this means the request was invalid, not that a real provider failed
            return jsonify({"error": "invalid_request", "details": str(e)}), 400
        except Exception as e:
            # covers both provider construction failures (e.g. missing API key)
            # and invoke-time failures (e.g. malformed output, network error)
            return jsonify({"error": "llm_failure", "details": str(e)}), 502

        alert_fields = build_alert(
            raw_input=payload.text,
            cleaned_text=cleaned,
            regex_iocs=regex_iocs,
            llm_result=llm_result,
            processing_ms=int((time.time() - start) * 1000),
        )

        session = SessionLocal()
        alert = Alert(**alert_fields)
        session.add(alert)
        session.commit()
        session.refresh(alert)

        return jsonify(_serialize(alert)), 201

    @app.route("/api/alerts", methods=["GET"])
    def list_alerts():
        session = SessionLocal()
        alerts = session.query(Alert).order_by(Alert.created_at.desc()).all()
        return jsonify([_serialize(a) for a in alerts]), 200

    @app.route("/api/alerts/<alert_id>", methods=["GET"])
    def get_alert(alert_id):
        session = SessionLocal()
        alert = session.get(Alert, alert_id)
        if alert is None:
            return jsonify({"error": "not_found"}), 404
        return jsonify(_serialize(alert)), 200

    @app.route("/api/alerts/<alert_id>", methods=["DELETE"])
    def delete_alert(alert_id):
        session = SessionLocal()
        alert = session.get(Alert, alert_id)
        if alert is None:
            return jsonify({"error": "not_found"}), 404
        session.delete(alert)
        session.commit()
        return "", 204

    return app


def _serialize(alert: Alert) -> dict:
    flat_iocs = alert.ioc_list
    if isinstance(flat_iocs, dict):
        flat_iocs = sorted({v for vs in flat_iocs.values() for v in vs})
    out = AlertOut(
        id=alert.id,
        summary=alert.summary,
        threat_type=alert.threat_type,
        severity=alert.severity,
        ioc_list=flat_iocs or [],
        recommended_action=alert.recommended_action,
        processing_ms=alert.processing_ms,
        created_at=alert.created_at,
    )
    return out.model_dump(mode="json")


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
