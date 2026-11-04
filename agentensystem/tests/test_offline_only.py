import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent
import context_review_v16
import diagnose_single_v162
import resume_context_v161
import sourcecheck


@patch.dict(os.environ, {"ALI_OFFLINE_ONLY": "1", "OPENAI_API_KEY": "dummy"})
class OfflineOnlyTests(unittest.TestCase):
    def test_model_blocked_before_transport(self):
        with patch("urllib.request.urlopen") as transport:
            with self.assertRaisesRegex(agent.ApiProblem, "ALI_OFFLINE_ONLY"):
                agent.call_openai(instructions="test", input_text="test", model="test",
                                  api_key=os.environ["OPENAI_API_KEY"], max_tokens=1)
            transport.assert_not_called()

    def test_allowed_source_blocked_before_transport(self):
        source = {"id": "S02", "url": sourcecheck.ALLOWED_PAGES["S02"]}
        opener = Mock()
        with patch("urllib.request.build_opener") as build:
            for transport in (None, opener):
                result = sourcecheck.fetch_original(source, opener=transport)
                self.assertEqual(result["status"], "BLOCKIERT_OFFLINE")
                self.assertEqual(result["blocks"], [])
            build.assert_not_called()
            opener.open.assert_not_called()

    def test_live_commands_exit_before_prompting(self):
        entries = [(agent.cli, ["--mode", "live"]),
                   (context_review_v16.cli, ["--mode", "live"]),
                   (resume_context_v161.cli, ["--live"]),
                   (diagnose_single_v162.main, ["--live"])]
        with patch("builtins.input") as prompt, patch("getpass.getpass") as key:
            for entry, args in entries:
                with self.subTest(command=entry.__module__):
                    self.assertEqual(entry(args), 2)
            prompt.assert_not_called()
            key.assert_not_called()

    def test_source_command_preserves_existing_report(self):
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / "report.json"
            report.write_bytes(b"{}")
            with patch("builtins.input") as prompt:
                self.assertEqual(sourcecheck.run(report), 2)
                prompt.assert_not_called()
            self.assertEqual(report.read_bytes(), b"{}")
            self.assertEqual(list(report.parent.iterdir()), [report])
