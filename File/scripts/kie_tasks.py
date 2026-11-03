#!/usr/bin/env python3
"""Optional local Kie Market task runner. Preview is offline; submission never retries."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid

if os.name == "nt":
    import msvcrt
else:
    import fcntl

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "File" / "generation"
API = "https://api.kie.ai"
UPLOAD_API = "https://kieai.redpandaai.co/api/file-stream-upload"
UPLOAD_LIFETIME_HOURS = 24      # Kie deletes uploaded files 24 hours after upload.
UPLOAD_MIN_REMAINING_HOURS = 6  # Re-upload instead of reusing a URL that may expire mid-run.
MAX_UPLOAD_BYTES = 200 * 1024 * 1024
UPLOAD_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
                ".mp4": "video/mp4", ".mov": "video/quicktime", ".wav": "audio/wav", ".mp3": "audio/mpeg",
                ".m4a": "audio/mp4"}

class Refused(Exception):
    pass

def now():
    return datetime.now(timezone.utc).isoformat()

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)

def amount(value, positive=False):
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise Refused("Credits must be numeric.") from None
    if not result.is_finite() or result < 0 or (positive and result == 0) or result.as_tuple().exponent < -4:
        raise Refused("Credits require a nonnegative amount with at most four decimals.")
    return result

def directory():
    for folder in (ROOT / "File", STATE):
        if folder.is_symlink():
            raise Refused("Refusing a symlinked state folder.")
        folder.mkdir(mode=0o700, exist_ok=True)

def write_new(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as file:
        file.write(canonical(value) + "\n")
        file.flush()
        os.fsync(file.fileno())

def replace(path, value):
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=".state-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(canonical(value) + "\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

@contextmanager
def locked():
    directory()
    lock = STATE / ".lock"
    if lock.is_symlink():
        raise Refused("Refusing a symlinked state lock.")
    with os.fdopen(os.open(lock, os.O_CREAT | os.O_RDWR, 0o600), "r+b") as file:
        if os.name == "nt":
            file.seek(0, os.SEEK_END)
            if file.tell() == 0:
                file.write(b"0")
                file.flush()
            file.seek(0)
            msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == "nt":
                file.seek(0)
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(file, fcntl.LOCK_UN)

def config():
    result = {}
    # Credentials belong to this project. Never inherit another account's key.
    env_file = ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            key = key.strip().removeprefix("export ").strip()
            if separator and key in ("KIE_API_KEY", "KIE_PROJECT_CAP_CREDITS"):
                result[key] = value.strip().strip("\"'")
    # Keep scoped, authorized budget overrides separate from credential selection.
    if "KIE_PROJECT_CAP_CREDITS" in os.environ:
        result["KIE_PROJECT_CAP_CREDITS"] = os.environ["KIE_PROJECT_CAP_CREDITS"]
    return result

def load(path):
    if path.is_symlink():
        raise Refused("Refusing a symlinked record.")
    return json.loads(path.read_text(encoding="utf-8"))

def paths(identifier):
    identifier = str(uuid.UUID(identifier))
    return STATE / (identifier + ".preview.json"), STATE / (identifier + ".operation.json")

def hash_preview(preview):
    return hashlib.sha256(canonical({"payload": preview["payload"], "capCredits": preview["capCredits"]}).encode()).hexdigest()

def preview(payload_path, cap):
    path = Path(payload_path)
    path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_relative_to(ROOT):
        raise Refused("Keep payloads inside this local project.")
    if path.stat().st_size > 200000:
        raise Refused("Payload exceeds the local preview size limit.")
    payload = load(path)
    if not isinstance(payload, dict) or set(payload) != {"model", "input"}:
        raise Refused("Use a Market task object containing only model and input; callbacks are not used locally.")
    if not isinstance(payload["model"], str) or not payload["model"].strip() or not isinstance(payload["input"], dict):
        raise Refused("Provide the documented model and its input object.")
    if "asset://" in canonical(payload):
        raise Refused("Local/backend asset placeholders are not provider reference URLs.")
    record = {"id": str(uuid.uuid4()), "createdAt": now(), "payload": payload,
              "capCredits": str(amount(cap, positive=True))}
    record["approvalHash"] = hash_preview(record)
    with locked():
        path, _ = paths(record["id"])
        write_new(path, record)
    return record

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def api(method, path, key, body=None):
    request = urllib.request.Request(API + path, method=method,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        data=canonical(body).encode() if body is not None else None)
    # No retry, redirect, response-body logging or credential-bearing output.
    with urllib.request.build_opener(NoRedirect).open(request, timeout=60) as response:
        data = response.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024:
            raise Refused("Provider response exceeds the local limit.")
    return json.loads(data)

def redact(value, key):
    # Provider-returned text is not trusted to be free of a reflected credential.
    return json.loads(canonical(value).replace(key, "[REDACTED]")) if key else value

def save_submission_receipt(identifier, evidence, key):
    """Retain redacted diagnostics without changing exactly-once or recovery rules."""
    path = STATE / "submission_receipts" / (identifier + ".json")
    write_new(path, {"operationId": identifier, "checkedAt": now(),
                     **redact(evidence, key)})
    return str(path.relative_to(ROOT))

def submit(identifier, approved_hash):
    with locked():
        preview_path, operation_path = paths(identifier)
        proposal = load(preview_path)
        if hash_preview(proposal) != proposal["approvalHash"] or approved_hash != proposal["approvalHash"]:
            raise Refused("The exact reviewed preview hash does not match.")
        if operation_path.exists():
            previous = load(operation_path)
            return {"reused": True, "id": proposal["id"], "status": previous["status"], "paidRequests": 0}
        settings = config()
        key = settings.get("KIE_API_KEY", "")
        if not key:
            raise Refused("Set KIE_API_KEY privately in the project .env before submission.")
        budget = amount(settings.get("KIE_PROJECT_CAP_CREDITS", "0"))
        used = Decimal(0)
        for path in STATE.glob("*.operation.json"):
            operation = load(path)
            if operation["status"] in ("submitting", "unknown"):
                raise Refused("An unresolved submission blocks new tasks. Reconcile it without deleting history.")
            reported = operation.get("reportedCredits")
            reserved = amount(operation["capCredits"])
            # An early zero-credit status is not the final charge for active work.
            used += amount(reported) if operation["status"] in ("succeeded", "failed") and reported is not None else max(reserved, amount(reported or "0"))
        if used + amount(proposal["capCredits"]) > budget:
            raise Refused("The local project reservation budget would be exceeded.")
        operation = {"id": proposal["id"], "createdAt": now(), "status": "submitting",
                     "approvalHash": approved_hash, "capCredits": proposal["capCredits"],
                     "reportedCredits": None}
        write_new(operation_path, operation)
        try:
            response = api("POST", "/api/v1/jobs/createTask", key, proposal["payload"])
            operation["submissionReceipt"] = save_submission_receipt(
                proposal["id"], {"response": response}, key)
            task_id = (response.get("data") or {}).get("taskId")
            if response.get("code") != 200 or not isinstance(task_id, str) or not task_id or len(task_id) > 250 or key in task_id:
                raise Refused("No trustworthy task ID returned.")
            operation.update(status="submitted", taskId=task_id, updatedAt=now())
            replace(operation_path, operation)
        except Exception as error:
            if not operation.get("submissionReceipt"):
                evidence = {"errorType": type(error).__name__}
                try:
                    if isinstance(error, urllib.error.HTTPError):
                        evidence["httpStatus"] = error.code
                        body = error.read(2 * 1024 * 1024 + 1)
                        if len(body) > 2 * 1024 * 1024:
                            evidence["responseBodyOmitted"] = "over local size limit"
                        else:
                            decoded = body.decode("utf-8", errors="replace")
                            try:
                                evidence["response"] = json.loads(decoded)
                            except ValueError:
                                evidence["responseText"] = decoded
                    operation["submissionReceipt"] = save_submission_receipt(
                        proposal["id"], evidence, key)
                except Exception:
                    operation["submissionReceiptUnavailable"] = True
            operation.update(status="unknown", updatedAt=now())
            replace(operation_path, operation)
            raise Refused("Submission outcome is unknown. No retry was made; reconcile in Kie logs.") from None
        return {"id": proposal["id"], "status": operation["status"], "taskId": task_id, "paidRequests": 1}

def status(identifier):
    with locked():
        _, path = paths(identifier)
        operation = load(path)
        if not operation.get("taskId"):
            raise Refused("No known task ID. Reconcile the unknown submission in Kie logs.")
        key = config().get("KIE_API_KEY", "")
        if not key:
            raise Refused("Set KIE_API_KEY privately in the project .env before querying.")
        try:
            response = api("GET", "/api/v1/jobs/recordInfo?" + urllib.parse.urlencode({"taskId": operation["taskId"]}), key)
            data = response.get("data") or {}
            if response.get("code") != 200 or data.get("taskId") != operation["taskId"]:
                raise Refused("Provider task query could not be verified.")
            receipt = {field: data[field] for field in ("taskId", "model", "state", "resultJson", "failCode", "creditsConsumed", "credits_consumed") if field in data}
            receipt = redact(receipt, key)
            receipt_path = STATE / "receipts" / (str(uuid.uuid4()) + ".json")
            write_new(receipt_path,
                      {"operationId": operation["id"], "checkedAt": now(), "receipt": receipt})
            credits = data.get("creditsConsumed", data.get("credits_consumed"))
            if credits is not None:
                operation["reportedCredits"] = str(amount(credits))
            operation.update(status={"success": "succeeded", "fail": "failed"}.get(data.get("state"), "submitted"),
                             latestReceipt=str(receipt_path.relative_to(ROOT)), updatedAt=now())
            replace(path, operation)
            return {"id": operation["id"], "status": operation["status"],
                    "reportedCredits": operation["reportedCredits"], "capCredits": operation["capCredits"],
                    "overReservation": None if operation["reportedCredits"] is None else amount(operation["reportedCredits"]) > amount(operation["capCredits"]),
                    "receiptSaved": True}
        except Exception:
            raise Refused("Task query could not complete. Existing submission and history are preserved.") from None

def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def upload_post(data, content_type, key):
    request = urllib.request.Request(UPLOAD_API, method="POST", data=data,
        headers={"Authorization": "Bearer " + key, "Content-Type": content_type})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=180) as response:
        body = response.read(256 * 1024 + 1)
        if len(body) > 256 * 1024:
            raise Refused("Upload response exceeds the local limit.")
    return json.loads(body)

def upload_valid(record, sha, min_hours=UPLOAD_MIN_REMAINING_HOURS):
    expires = datetime.fromisoformat(record["expiresAt"])
    return record["file"]["sha256"] == sha and (expires - datetime.now(timezone.utc)).total_seconds() > min_hours * 3600

def upload(file_path, min_hours=UPLOAD_MIN_REMAINING_HOURS):
    """Upload one project file to Kie's temporary file storage (no generation credits). Reuses a fresh receipt."""
    path = Path(file_path)
    path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file() or path.is_symlink():
        raise Refused("Upload only regular files inside this local project.")
    if path.suffix.lower() not in UPLOAD_TYPES:
        raise Refused("Unsupported upload type; use an image, video or audio reference.")
    if not 0 < path.stat().st_size <= MAX_UPLOAD_BYTES:
        raise Refused("Upload must be nonempty and within the local size limit.")
    sha = file_sha256(path)
    folder = STATE / "uploads"
    with locked():
        latest = folder / (sha + ".json")
        if latest.is_file():
            record = load(latest)
            if upload_valid(record, sha, min_hours):
                return record | {"reused": True}
        key = config().get("KIE_API_KEY", "")
        if not key:
            raise Refused("Set KIE_API_KEY privately in the project .env before uploading.")
        boundary = "----local-" + uuid.uuid4().hex
        name = sha[:24] + path.suffix.lower()
        parts = []
        for field, value in (("uploadPath", "references"), ("fileName", name)):
            parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, field, value)).encode())
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
                      % (boundary, name, UPLOAD_TYPES[path.suffix.lower()])).encode())
        parts.append(path.read_bytes())
        parts.append(("\r\n--%s--\r\n" % boundary).encode())
        uploaded_at = datetime.now(timezone.utc)
        try:
            response = upload_post(b"".join(parts), "multipart/form-data; boundary=" + boundary, key)
        except Exception:
            raise Refused("Upload could not complete. No generation was submitted.") from None
        data = response.get("data") or {}
        url = data.get("downloadUrl")
        if response.get("code") != 200 or not isinstance(url, str) or not url.startswith("https://") or key in url:
            raise Refused("Upload was not confirmed by the provider.")
        if ap_size(data) not in (None, path.stat().st_size):
            raise Refused("Provider-reported upload size does not match the local file.")
        record = {"file": {"path": str(path.relative_to(ROOT)), "sha256": sha}, "downloadUrl": url,
                  "uploadedAt": uploaded_at.isoformat(),
                  "expiresAt": (uploaded_at + timedelta(hours=UPLOAD_LIFETIME_HOURS)).isoformat(),
                  "providerResponse": redact({k: data.get(k) for k in ("fileName", "filePath", "fileSize", "mimeType", "uploadedAt")}, key)}
        write_new(folder / (sha + "-" + uuid.uuid4().hex + ".json"), record)
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        replace(latest, record)
        return record | {"reused": False}

def ap_size(data):
    size = data.get("fileSize")
    return size if isinstance(size, int) and not isinstance(size, bool) else None

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    draft = commands.add_parser("preview")
    draft.add_argument("--payload", required=True)
    draft.add_argument("--cap-credits", required=True)
    execute = commands.add_parser("submit")
    execute.add_argument("--preview", required=True)
    execute.add_argument("--approved-hash", required=True)
    query = commands.add_parser("status")
    query.add_argument("--preview", required=True)
    send = commands.add_parser("upload")
    send.add_argument("--file", required=True)
    args = parser.parse_args()
    try:
        if args.command == "upload":
            result = upload(args.file)
        else:
            result = preview(args.payload, args.cap_credits) if args.command == "preview" else submit(args.preview, args.approved_hash) if args.command == "submit" else status(args.preview)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except Refused as error:
        parser.exit(1, str(error) + "\n")
    except Exception:
        parser.exit(1, "Local operation failed. Secrets and provider response contents suppressed; no automatic submission retry.\n")

if __name__ == "__main__":
    main()

