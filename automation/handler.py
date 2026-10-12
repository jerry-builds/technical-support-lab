import json
import logging
import os
import time
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAX_BODY_BYTES = 64 * 1024


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    """Inbound webhook: validate JSON, log it, acknowledge."""
    request_id = getattr(context, "aws_request_id", str(uuid.uuid4()))
    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        import base64
        raw = base64.b64decode(raw).decode("utf-8", "replace")

    if len(raw.encode("utf-8")) > MAX_BODY_BYTES:
        return _response(413, {"ok": False, "error": "body too large", "request_id": request_id})

    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return _response(400, {"ok": False, "error": "body must be JSON", "request_id": request_id})

    if not isinstance(payload, dict):
        return _response(400, {"ok": False, "error": "body must be a JSON object", "request_id": request_id})

    source = payload.get("source", "unknown")
    event_type = payload.get("event", "unknown")
    logger.info(json.dumps({
        "request_id": request_id,
        "source": source,
        "event": event_type,
        "keys": sorted(payload.keys()),
        "received_at": int(time.time()),
    }))

    return _response(200, {
        "ok": True,
        "request_id": request_id,
        "source": source,
        "event": event_type,
        "received_at": int(time.time()),
        "stage": os.environ.get("STAGE", "lab"),
    })
