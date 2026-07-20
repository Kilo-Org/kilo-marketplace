import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from obsidian_cli_plugins.git_ops import git_commit_push, git_is_clean_synced, git_status, sync_pull


class GitOpsTests(unittest.TestCase):
    def test_clean_repo_without_upstream_is_not_synced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            (repo / ".obsidian").mkdir()
            (repo / "note.md").write_text("hello\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            status = git_status(repo)

            self.assertIsNone(status["upstream"])
            self.assertFalse(status["counts_ok"])
            self.assertFalse(git_is_clean_synced(repo))

    def test_commit_push_force_adds_ignored_video_attachment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            remote = root / "remote.git"
            vault = root / "vault"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "init", str(vault)], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=vault, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=vault, check=True)
            subprocess.run(["git", "checkout", "-b", "main"], cwd=vault, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=vault, check=True)
            (vault / ".obsidian").mkdir()
            (vault / "README.md").write_text("# vault\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=vault, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=vault, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], cwd=vault, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            (vault / ".gitignore").write_text("*.mp4\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=vault, check=True)
            subprocess.run(["git", "commit", "-m", "ignore videos"], cwd=vault, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "push"], cwd=vault, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            note = vault / "00_inbox/fleeting/record.md"
            video = vault / "00_inbox/fleeting/assets/record/clip.mp4"
            note.parent.mkdir(parents=True)
            video.parent.mkdir(parents=True)
            note.write_text("# record\n\n- 附件：[clip](assets/record/clip.mp4)\n", encoding="utf-8")
            video.write_bytes(b"video")

            result = git_commit_push(vault, "record with video", force_add_paths=[str(video)])

            self.assertTrue(result["ok"], result)
            tracked = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", "HEAD"],
                cwd=vault,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            ).stdout.splitlines()
            self.assertIn("00_inbox/fleeting/assets/record/clip.mp4", tracked)

    def test_sync_pull_uses_host_git_pull(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            remote = root / "remote.git"
            vault = root / "vault"
            other = root / "other"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "init", str(vault)], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=vault, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=vault, check=True)
            subprocess.run(["git", "checkout", "-b", "main"], cwd=vault, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=vault, check=True)
            (vault / ".obsidian").mkdir()
            (vault / "README.md").write_text("# vault\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=vault, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=vault, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], cwd=vault, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], cwd=remote, check=True)

            subprocess.run(["git", "clone", str(remote), str(other)], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=other, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=other, check=True)
            (other / "remote-note.md").write_text("remote update\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=other, check=True)
            subprocess.run(["git", "commit", "-m", "remote update"], cwd=other, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            subprocess.run(["git", "push"], cwd=other, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            result = sync_pull("ignored-vault-name", vault, 0)

            self.assertTrue(result["ok"], result)
            commands = [item["cmd"] for item in result["commands"]]
            self.assertEqual(commands, ["git pull --no-rebase"])
            self.assertNotIn("obsidian-git", str(result))
            self.assertTrue((vault / "remote-note.md").exists())

    def test_sync_pull_falls_back_to_obsidian_git_plugin_when_host_git_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp)
            (vault / ".obsidian").mkdir()
            completed = subprocess.CompletedProcess(
                args=["obsidian", "command", "vault=obsidian-2026", "id=obsidian-git:pull"],
                returncode=0,
                stdout="Executed: obsidian-git:pull\n",
            )

            with patch("obsidian_cli_plugins.git_ops.shutil.which", return_value=None), patch(
                "obsidian_cli_plugins.git_ops.obsidian_bin",
                return_value="obsidian",
            ), patch("obsidian_cli_plugins.git_ops.run", Mock(return_value=completed)) as mocked_run:
                result = sync_pull("obsidian-2026", vault, 0)

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["fallback"], "obsidian-git-plugin")
            self.assertEqual(result["reason"], "host-git-not-found-used-obsidian-git-plugin")
            commands = [item["cmd"] for item in result["commands"]]
            self.assertEqual(commands, ["obsidian command vault=obsidian-2026 id=obsidian-git:pull"])
            mocked_run.assert_called_once_with(["obsidian", "command", "vault=obsidian-2026", "id=obsidian-git:pull"])


if __name__ == "__main__":
    unittest.main()
