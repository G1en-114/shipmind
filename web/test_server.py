"""Local UI adapter regression tests; no model endpoint or node connection."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from web import server


class DashboardTests(unittest.TestCase):
    def test_static_and_input_validation(self):
        with TestClient(server.app) as client:
            for path in ("/", "/static/app.css", "/static/app.js"):
                self.assertEqual(client.get(path).status_code, 200)
            self.assertEqual(client.get("/api/manual", params={"q": "x" * 201}).status_code, 422)
            self.assertEqual(client.get("/api/manual", params={"q": ""}).status_code, 422)
            self.assertEqual(client.post("/api/ai/ask", json={"question": ""}).status_code, 422)
            self.assertEqual(client.post("/api/ai/log-config", json={"max_mb": 0}).status_code, 422)

    @patch("subprocess.run")
    def test_unicode_alarm_output_is_accepted(self, run):
        run.return_value = subprocess.CompletedProcess([], 1, '{"level":"critical","note":"高频异常"}\nMEDIA:x', '')
        out = server._skill_output("sample.py", [])
        self.assertEqual(out["note"], "高频异常")
        self.assertEqual(run.call_args.kwargs["encoding"], "utf-8")
        self.assertEqual(run.call_args.kwargs["env"]["PYTHONUTF8"], "1")
        self.assertEqual(run.call_args.kwargs["timeout"], 25)

    @patch("subprocess.run")
    def test_missing_failed_and_invalid_output_are_not_empty_success(self, run):
        for rc, output in ((2, '{}'), (0, ''), (0, '{bad'), (0, '{"error":"missing"}')):
            run.return_value = subprocess.CompletedProcess([], rc, output, '')
            with self.subTest(rc=rc, output=output), self.assertRaises(HTTPException) as ctx:
                server._skill_output("sample.py", [])
            self.assertEqual(ctx.exception.status_code, 503)

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired("sample", 25))
    def test_timeout(self, run):
        with self.assertRaises(HTTPException) as ctx:
            server._skill_output("sample.py", [])
        self.assertEqual(ctx.exception.status_code, 504)

    @patch.object(server, "_skill_output")
    def test_alert_sources_remain_pump_samples(self, output):
        output.return_value = {"level": "normal", "evidence": [], "possible_causes": []}
        rows = server.alerts()
        self.assertEqual(len(rows), 2)
        self.assertTrue(all("泵" in row["device"] and row["synthetic"] for row in rows))
        self.assertTrue(all("pump" in row["source"] for row in rows))
        self.assertNotEqual(rows[0]["source"], rows[1]["source"])

    @patch.object(server, "_skill_output")
    def test_manual_query_uses_argument_list(self, output):
        output.return_value = {"answers": []}
        query = "轴承磨损; sample"
        with TestClient(server.app) as client:
            self.assertEqual(client.get("/api/manual", params={"q": query}).json(), {"answers": []})
        self.assertIn(query, output.call_args.args[1])

    def test_ai_log_rotates_and_keeps_recent_entries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(server, "AI_LOG_DIR", root), \
                 patch.object(server, "AI_LOG_PATH", root / "duty.jsonl"), \
                 patch.object(server, "AI_LOG_CONFIG", root / "config.json"), \
                 patch.object(server, "_AI_LOG_MAX_BYTES", 260):
                server._append_ai_log("system", "甲" * 70)
                server._append_ai_log("ai", "乙" * 70)
                state = server.ai_log_state(10)
                self.assertTrue((root / "duty.jsonl.1").exists())
                self.assertEqual(state["entries"][-1]["kind"], "ai")
                self.assertLessEqual(len(state["entries"]), 2)


if __name__ == "__main__":
    unittest.main()
