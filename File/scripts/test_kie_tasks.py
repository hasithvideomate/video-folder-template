"""Offline checks only: all provider requests are mocked."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("local_kie", Path(__file__).with_name("kie_tasks.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class LocalKieTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.root_patch = patch.object(runner, "ROOT", self.root)
        self.state_patch = patch.object(runner, "STATE", self.root / "File/generation")
        self.environment = patch.dict(runner.os.environ, {}, clear=True)
        self.api_patch = patch.object(runner, "api", side_effect=AssertionError("Unexpected provider request"))
        self.root_patch.start()
        self.state_patch.start()
        self.environment.start()
        self.provider = self.api_patch.start()
        (self.root / "File").mkdir()
        (self.root / "File/request.json").write_text(json.dumps({"model": "fixture-model", "input": {"prompt": "Fixture"}}))
        (self.root / ".env").write_text("KIE_API_KEY=fixture-private-key\nKIE_PROJECT_CAP_CREDITS=20\n")

    def tearDown(self):
        self.api_patch.stop()
        self.environment.stop()
        self.state_patch.stop()
        self.root_patch.stop()
        self.temp.cleanup()

    def preview(self, cap="10"):
        return runner.preview("File/request.json", cap)

    def submitted(self, proposal):
        self.provider.side_effect = None
        self.provider.return_value = {"code": 200, "data": {"taskId": "task_fixture"}}
        return runner.submit(proposal["id"], proposal["approvalHash"])

    def test_project_env_key_is_used_for_submit_and_status_despite_other_keys(self):
        (self.root / ".env.local").write_text("KIE_API_KEY=wrong-local-account\n")
        with patch.dict(runner.os.environ, {"KIE_API_KEY": "wrong-process-account"}):
            proposal = self.preview()
            self.submitted(proposal)
            self.assertEqual(self.provider.call_args.args[2], "fixture-private-key")
            self.provider.return_value = {"code": 200, "data": {"taskId": "task_fixture", "state": "success"}}
            runner.status(proposal["id"])
            self.assertEqual(self.provider.call_args.args[2], "fixture-private-key")

    def test_missing_or_empty_project_key_never_falls_back_to_another_account(self):
        (self.root / ".env.local").write_text("KIE_API_KEY=wrong-local-account\n")
        with patch.dict(runner.os.environ, {"KIE_API_KEY": "wrong-process-account", "KIE_PROJECT_CAP_CREDITS": "20"}):
            for contents in (None, "KIE_API_KEY=\n", "KIE_PROJECT_CAP_CREDITS=20\n"):
                with self.subTest(contents=contents):
                    env_file = self.root / ".env"
                    if contents is None:
                        env_file.unlink()
                    else:
                        env_file.write_text(contents)
                    proposal = self.preview()
                    with self.assertRaises(runner.Refused):
                        runner.submit(proposal["id"], proposal["approvalHash"])
        self.provider.assert_not_called()

    def test_authorized_process_budget_override_does_not_change_project_key(self):
        with patch.dict(runner.os.environ, {"KIE_PROJECT_CAP_CREDITS": "30", "KIE_API_KEY": "wrong-account"}):
            self.assertEqual(runner.config().get("KIE_PROJECT_CAP_CREDITS"), "30")
            self.assertEqual(runner.config().get("KIE_API_KEY"), "fixture-private-key")

    def test_preview_has_no_config_or_network_requirement(self):
        with patch.object(runner, "config", side_effect=AssertionError("Preview read credentials")):
            proposal = self.preview()
        self.assertEqual(proposal["capCredits"], "10")
        self.provider.assert_not_called()

    def test_submission_is_recorded_before_one_post_and_duplicate_reuses(self):
        proposal = self.preview()
        def response(*args):
            operation = runner.load(runner.paths(proposal["id"])[1])
            self.assertEqual(operation["status"], "submitting")
            return {"code": 200, "data": {"taskId": "known_task"}}
        self.provider.side_effect = response
        self.assertEqual(runner.submit(proposal["id"], proposal["approvalHash"])["paidRequests"], 1)
        self.assertEqual(runner.submit(proposal["id"], proposal["approvalHash"])["paidRequests"], 0)
        self.assertEqual(self.provider.call_count, 1)

    def test_tampered_preview_and_incorrect_hash_block_spend(self):
        proposal = self.preview()
        with self.assertRaises(runner.Refused):
            runner.submit(proposal["id"], "wrong")
        path, _ = runner.paths(proposal["id"])
        record = runner.load(path)
        record["payload"]["input"]["prompt"] = "Changed after approval"
        runner.replace(path, record)
        with self.assertRaises(runner.Refused):
            runner.submit(proposal["id"], proposal["approvalHash"])
        self.provider.assert_not_called()

    def test_unknown_submission_is_not_retried_and_blocks_new_preview_submission(self):
        first, second = self.preview(), self.preview()
        self.provider.side_effect = TimeoutError("fixture-private-key")
        with self.assertRaises(runner.Refused) as error:
            runner.submit(first["id"], first["approvalHash"])
        self.assertNotIn("fixture-private-key", str(error.exception))
        self.assertEqual(runner.submit(first["id"], first["approvalHash"])["paidRequests"], 0)
        with self.assertRaises(runner.Refused):
            runner.submit(second["id"], second["approvalHash"])
        self.assertEqual(self.provider.call_count, 1)

    def test_error_envelope_even_http_success_is_unknown(self):
        proposal = self.preview()
        self.provider.side_effect = None
        self.provider.return_value = {"code": 500, "msg": "fixture-private-key"}
        with self.assertRaises(runner.Refused):
            runner.submit(proposal["id"], proposal["approvalHash"])
        self.assertEqual(runner.load(runner.paths(proposal["id"])[1])["status"], "unknown")
        receipt = runner.load(runner.STATE / "submission_receipts" / (proposal["id"] + ".json"))
        self.assertEqual(receipt["response"], {"code": 500, "msg": "[REDACTED]"})

    def test_successful_submission_receipt_retains_task_and_is_not_overwritten(self):
        proposal = self.preview()
        self.submitted(proposal)
        path = runner.STATE / "submission_receipts" / (proposal["id"] + ".json")
        before = path.read_bytes()
        self.assertEqual(runner.load(path)["response"]["data"]["taskId"], "task_fixture")
        runner.submit(proposal["id"], proposal["approvalHash"])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.provider.call_count, 1)

    def test_http_error_body_is_retained_redacted_without_retry(self):
        for body, field in [(b'{"code":422,"msg":"fixture-private-key"}', "response"),
                            (b'<html>fixture-private-key</html>', "responseText")]:
            with self.subTest(field=field):
                proposal = self.preview()
                self.provider.side_effect = runner.urllib.error.HTTPError(
                    "https://example.invalid", 422, "fixture-private-key", {}, io.BytesIO(body))
                with self.assertRaises(runner.Refused):
                    runner.submit(proposal["id"], proposal["approvalHash"])
                operation = runner.load(runner.paths(proposal["id"])[1])
                self.assertEqual(operation["status"], "unknown")
                receipt = runner.load(self.root / operation["submissionReceipt"])
                self.assertEqual(receipt["httpStatus"], 422)
                self.assertIn(field, receipt)
                self.assertNotIn("fixture-private-key", json.dumps(receipt))
                # Clear only this isolated test fixture before the next subtest.
                runner.paths(proposal["id"])[1].unlink()
        self.assertEqual(self.provider.call_count, 2)

    def test_oversized_http_error_body_is_omitted(self):
        proposal = self.preview()
        self.provider.side_effect = runner.urllib.error.HTTPError(
            "https://example.invalid", 503, "error", {}, io.BytesIO(b'x' * (2 * 1024 * 1024 + 1)))
        with self.assertRaises(runner.Refused):
            runner.submit(proposal["id"], proposal["approvalHash"])
        receipt = runner.load(runner.STATE / "submission_receipts" / (proposal["id"] + ".json"))
        self.assertEqual(receipt["responseBodyOmitted"], "over local size limit")
        self.assertNotIn("responseText", receipt)

    def test_network_error_diagnostic_excludes_exception_message_and_blocks_more_posts(self):
        first, second = self.preview(), self.preview()
        self.provider.side_effect = TimeoutError("fixture-private-key")
        with self.assertRaises(runner.Refused):
            runner.submit(first["id"], first["approvalHash"])
        receipt = runner.load(runner.STATE / "submission_receipts" / (first["id"] + ".json"))
        self.assertEqual(receipt["errorType"], "TimeoutError")
        self.assertNotIn("fixture-private-key", json.dumps(receipt))
        with self.assertRaises(runner.Refused):
            runner.submit(second["id"], second["approvalHash"])
        self.assertEqual(self.provider.call_count, 1)

    def test_zero_budget_blocks_paid_request(self):
        proposal = self.preview()
        (self.root / ".env").write_text("KIE_API_KEY=fixture-private-key\nKIE_PROJECT_CAP_CREDITS=0\n")
        with self.assertRaises(runner.Refused):
            runner.submit(proposal["id"], proposal["approvalHash"])
        self.provider.assert_not_called()

    def test_active_zero_charge_still_reserves_scope(self):
        proposal = self.preview()
        self.submitted(proposal)
        self.provider.return_value = {"code": 200, "data": {"taskId": "task_fixture", "state": "generating", "creditsConsumed": 0}}
        runner.status(proposal["id"])
        next_proposal = self.preview("11")
        count = self.provider.call_count
        with self.assertRaises(runner.Refused):
            runner.submit(next_proposal["id"], next_proposal["approvalHash"])
        self.assertEqual(self.provider.call_count, count)

    def test_missing_billing_stays_unknown_and_status_receipts_append(self):
        proposal = self.preview()
        self.submitted(proposal)
        self.provider.return_value = {"code": 200, "data": {"taskId": "task_fixture", "state": "success", "resultJson": "{\"resultUrls\":[]}"}}
        self.assertIsNone(runner.status(proposal["id"])["reportedCredits"])
        self.provider.return_value["data"]["creditsConsumed"] = 2.5
        self.assertEqual(runner.status(proposal["id"])["reportedCredits"], "2.5")
        self.assertEqual(len(list((runner.STATE / "receipts").glob("*.json"))), 2)

    def test_provider_reflected_secret_is_redacted_from_receipt(self):
        proposal = self.preview()
        self.submitted(proposal)
        self.provider.return_value = {"code": 200, "data": {"taskId": "task_fixture", "state": "success", "resultJson": "fixture-private-key"}}
        runner.status(proposal["id"])
        for path in runner.STATE.rglob("*.json"):
            self.assertNotIn("fixture-private-key", path.read_text())

    def test_mismatched_task_id_does_not_change_operation(self):
        proposal = self.preview()
        self.submitted(proposal)
        self.provider.return_value = {"code": 200, "data": {"taskId": "another_task", "state": "success", "creditsConsumed": 0}}
        with self.assertRaises(runner.Refused):
            runner.status(proposal["id"])
        self.assertEqual(runner.load(runner.paths(proposal["id"])[1])["status"], "submitted")

    def test_negative_and_nonfinite_credits_rejected(self):
        for value in ("-1", "NaN", "Infinity", "0.00001"):
            with self.assertRaises(runner.Refused):
                self.preview(value)
        self.provider.assert_not_called()

class UploadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name, value in (("ROOT", self.root), ("STATE", self.root / "File/generation")):
            p = patch.object(runner, name, value); p.start(); self.addCleanup(p.stop)
        p = patch.dict(runner.os.environ, {}, clear=True); p.start(); self.addCleanup(p.stop)
        (self.root / "File").mkdir(); (self.root / "Assets").mkdir()
        (self.root / "Assets/avatar.png").write_bytes(b"png fixture")
        (self.root / ".env").write_text("KIE_API_KEY=fixture-private-key\n")
        self.bodies = []
        def post(data, content_type, key):
            self.bodies.append((data, content_type, key))
            return {"success": True, "code": 200, "data": {"downloadUrl": "https://tempfile.example/a.png",
                    "fileSize": len(b"png fixture"), "fileName": "a.png"}}
        p = patch.object(runner, "upload_post", side_effect=post); p.start(); self.addCleanup(p.stop)

    def test_upload_records_receipt_and_reuses_fresh_url(self):
        first = runner.upload("Assets/avatar.png")
        self.assertEqual(first["downloadUrl"], "https://tempfile.example/a.png")
        self.assertFalse(first["reused"])
        self.assertIn(b"png fixture", self.bodies[0][0])
        self.assertNotIn("fixture-private-key", json.dumps(first))
        second = runner.upload("Assets/avatar.png")
        self.assertTrue(second["reused"]); self.assertEqual(len(self.bodies), 1)

    def test_expiring_upload_is_refreshed(self):
        runner.upload("Assets/avatar.png")
        runner.upload("Assets/avatar.png", min_hours=25)
        self.assertEqual(len(self.bodies), 2)

    def test_changed_file_is_uploaded_again(self):
        runner.upload("Assets/avatar.png")
        (self.root / "Assets/avatar.png").write_bytes(b"new fixture")
        with patch.object(runner, "upload_post", return_value={"code": 200, "data": {"downloadUrl": "https://tempfile.example/b.png"}}):
            record = runner.upload("Assets/avatar.png")
        self.assertEqual(record["downloadUrl"], "https://tempfile.example/b.png")

    def test_refusals(self):
        (self.root / "Assets/notes.txt").write_text("x")
        outside = Path(self.temp.name).parent / "outside.png"
        for name in ("Assets/notes.txt", str(outside), "Assets/missing.png"):
            with self.assertRaises(runner.Refused): runner.upload(name)
        (self.root / ".env").write_text("")
        with self.assertRaises(runner.Refused): runner.upload("Assets/avatar.png")
        self.assertEqual(self.bodies, [])

    def test_unconfirmed_or_mismatched_upload_is_refused(self):
        for response in ({"code": 500, "data": {}}, {"code": 200, "data": {"downloadUrl": "http://insecure"}},
                         {"code": 200, "data": {"downloadUrl": "https://ok.example", "fileSize": 3}}):
            with patch.object(runner, "upload_post", return_value=response):
                with self.assertRaises(runner.Refused): runner.upload("Assets/avatar.png")
        self.assertFalse((self.root / "File/generation/uploads").exists() and
                         list((self.root / "File/generation/uploads").glob("*.json")))

if __name__ == "__main__":
    unittest.main()

