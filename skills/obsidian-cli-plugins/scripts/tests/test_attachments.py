import argparse
import json
import pathlib
import sys
import tempfile
import unittest


SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from obsidian_cli_plugins import attachments
from obsidian_cli_plugins.cli import (
    cmd_attachment_list,
    cmd_attachment_pending,
    resolve_record_attachments,
    validate_required_attachment_sources,
)


class AttachmentStageTests(unittest.TestCase):
    def test_batch_selector_loads_all_staged_attachments_for_same_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            original_stage_dir = attachments.STAGED_ATTACHMENT_DIR
            attachments.STAGED_ATTACHMENT_DIR = root / "staged"
            try:
                first = root / "wechat-pay.png"
                second = root / "reward.png"
                other = root / "other.png"
                first.write_bytes(b"first")
                second.write_bytes(b"second")
                other.write_bytes(b"other")

                first_stage = attachments.stage_attachment(str(first), "微信支付-1", "image", "wx-thread")
                second_stage = attachments.stage_attachment(str(second), "赞赏码", "image", "wx-thread")
                attachments.stage_attachment(str(other), "其他图片", "image", "other-thread")

                self.assertTrue(first_stage["ok"])
                self.assertTrue(second_stage["ok"])

                selected, error = attachments.load_staged_attachment_selector("batch:wx-thread")

                self.assertIsNone(error)
                self.assertEqual([item["label"] for item in selected], ["微信支付-1", "赞赏码"])
                self.assertEqual({item["batch_key"] for item in selected}, {"wx-thread"})
            finally:
                attachments.STAGED_ATTACHMENT_DIR = original_stage_dir

    def test_resolve_record_attachments_expands_batch_selector_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            original_stage_dir = attachments.STAGED_ATTACHMENT_DIR
            attachments.STAGED_ATTACHMENT_DIR = root / "staged"
            try:
                image_a = root / "a.png"
                image_b = root / "b.png"
                image_a.write_bytes(b"a")
                image_b.write_bytes(b"b")
                attachments.stage_attachment(str(image_a), "第一张", "image", "thread-1")
                attachments.stage_attachment(str(image_b), "第二张", "image", "thread-1")
                args = argparse.Namespace(attach=[], staged_attachment=["batch:thread-1", "batch:thread-1"])

                resolved, staged_items, error = resolve_record_attachments(args)

                self.assertIsNone(error)
                self.assertEqual(len(staged_items), 2)
                self.assertEqual(len(resolved), 2)
                self.assertTrue(resolved[0].startswith("第一张="))
                self.assertTrue(resolved[1].startswith("第二张="))
            finally:
                attachments.STAGED_ATTACHMENT_DIR = original_stage_dir

    def test_resolve_record_attachments_falls_back_to_unique_video_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            original_stage_dir = attachments.STAGED_ATTACHMENT_DIR
            attachments.STAGED_ATTACHMENT_DIR = root / "staged"
            try:
                video_a = root / "a.mp4"
                video_b = root / "b.mp4"
                video_a.write_bytes(b"a")
                video_b.write_bytes(b"b")
                attachments.stage_attachment(str(video_a), "第一段", "video", "qqbot-abc123")
                attachments.stage_attachment(str(video_b), "第二段", "video", "qqbot-abc123")
                args = argparse.Namespace(
                    attach=[],
                    staged_attachment=["batch:qqbot:c2c:legacy-openid"],
                    type="video",
                )

                resolved, staged_items, error = resolve_record_attachments(args)

                self.assertIsNone(error)
                self.assertEqual(len(staged_items), 2)
                self.assertEqual(len(resolved), 2)
                self.assertEqual({item["batch_key"] for item in staged_items}, {"qqbot-abc123"})
            finally:
                attachments.STAGED_ATTACHMENT_DIR = original_stage_dir

    def test_resolve_record_attachments_rejects_ambiguous_video_batches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            original_stage_dir = attachments.STAGED_ATTACHMENT_DIR
            attachments.STAGED_ATTACHMENT_DIR = root / "staged"
            try:
                video_a = root / "a.mp4"
                video_b = root / "b.mp4"
                video_a.write_bytes(b"a")
                video_b.write_bytes(b"b")
                attachments.stage_attachment(str(video_a), "第一段", "video", "qqbot-a")
                attachments.stage_attachment(str(video_b), "第二段", "video", "qqbot-b")
                args = argparse.Namespace(
                    attach=[],
                    staged_attachment=["batch:qqbot:c2c:legacy-openid"],
                    type="video",
                )

                resolved, staged_items, error = resolve_record_attachments(args)

                self.assertEqual(resolved, [])
                self.assertEqual(staged_items, [])
                self.assertIsNotNone(error)
                self.assertEqual(error["reason"], "ambiguous-staged-attachments")
                self.assertEqual(error["candidate_batch_keys"], ["qqbot-a", "qqbot-b"])
            finally:
                attachments.STAGED_ATTACHMENT_DIR = original_stage_dir

    def test_default_batch_selector_is_rejected_for_record_consumption(self) -> None:
        selected, error = attachments.load_staged_attachment_selector("batch:default")

        self.assertEqual(selected, [])
        self.assertIsNotNone(error)
        self.assertEqual(error["reason"], "unsafe-default-staged-attachment-selector")
        self.assertEqual(error["replacement"], "attachment-pending --ttl-hours 48")

    def test_required_attachment_sources_reject_missing_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            args = argparse.Namespace(
                attach=[str(root / "missing.m4a")],
                require_attachment=True,
                type="audio",
            )

            error = validate_required_attachment_sources(root, args)

            self.assertIsNotNone(error)
            self.assertEqual(error["reason"], "attachment-path-unavailable")

    def test_prune_removes_expired_staged_attachments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            original_stage_dir = attachments.STAGED_ATTACHMENT_DIR
            attachments.STAGED_ATTACHMENT_DIR = root / "staged"
            try:
                media = root / "old.m4a"
                media.write_bytes(b"audio")
                staged = attachments.stage_attachment(str(media), "old", "audio", "thread-1")
                manifest_path = attachments.staged_manifest_path(staged["id"])
                data = manifest_path.read_text(encoding="utf-8")
                data = data.replace(str(staged["created_at_ns"]), "1")
                manifest_path.write_text(data, encoding="utf-8")

                result = attachments.prune_staged_attachments(ttl_hours=1)

                self.assertTrue(result["ok"])
                self.assertIn(staged["id"], result["removed"])
                self.assertFalse(manifest_path.exists())
            finally:
                attachments.STAGED_ATTACHMENT_DIR = original_stage_dir

    def test_list_filters_by_media_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            original_stage_dir = attachments.STAGED_ATTACHMENT_DIR
            attachments.STAGED_ATTACHMENT_DIR = root / "staged"
            try:
                video = root / "clip.mp4"
                image = root / "shot.png"
                video.write_bytes(b"video")
                image.write_bytes(b"image")
                attachments.stage_attachment(str(video), "clip", "video", "thread-1")
                attachments.stage_attachment(str(image), "shot", "image", "thread-1")

                selected = attachments.list_staged_attachments("thread-1", "video")

                self.assertEqual(len(selected), 1)
                self.assertEqual(selected[0]["label"], "clip")
                self.assertEqual(selected[0]["type"], "video")
            finally:
                attachments.STAGED_ATTACHMENT_DIR = original_stage_dir

    def test_clear_removes_only_matching_media_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            original_stage_dir = attachments.STAGED_ATTACHMENT_DIR
            attachments.STAGED_ATTACHMENT_DIR = root / "staged"
            try:
                video = root / "clip.mp4"
                image = root / "shot.png"
                video.write_bytes(b"video")
                image.write_bytes(b"image")
                removed_stage = attachments.stage_attachment(str(video), "clip", "video", "thread-1")
                kept_stage = attachments.stage_attachment(str(image), "shot", "image", "thread-1")

                result = attachments.clear_staged_attachments(media_type="video")

                self.assertTrue(result["ok"])
                self.assertIn(removed_stage["id"], result["removed"])
                self.assertFalse(attachments.staged_manifest_path(removed_stage["id"]).exists())
                self.assertTrue(attachments.staged_manifest_path(kept_stage["id"]).exists())
            finally:
                attachments.STAGED_ATTACHMENT_DIR = original_stage_dir

    def test_default_stage_ttl_is_48_hours(self) -> None:
        self.assertEqual(attachments.DEFAULT_STAGE_TTL_HOURS, 48)

    def test_attachment_pending_command_lists_matching_videos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            original_stage_dir = attachments.STAGED_ATTACHMENT_DIR
            attachments.STAGED_ATTACHMENT_DIR = root / "staged"
            try:
                first = root / "first.mp4"
                second = root / "second.mp4"
                image = root / "shot.png"
                first.write_bytes(b"first")
                second.write_bytes(b"second")
                image.write_bytes(b"image")
                first_stage = attachments.stage_attachment(str(first), "first", "video", "thread-1")
                second_stage = attachments.stage_attachment(str(second), "second", "video", "thread-1")
                attachments.stage_attachment(str(image), "shot", "image", "thread-1")
                args = argparse.Namespace(batch_key="thread-1", type="video", ttl_hours=48, limit=None, verbose=False)

                with tempfile.TemporaryFile("w+", encoding="utf-8") as output:
                    original_stdout = sys.stdout
                    sys.stdout = output
                    try:
                        cmd_attachment_pending(args)
                    finally:
                        sys.stdout = original_stdout
                    output.seek(0)
                    result = json.loads(output.read())

                self.assertTrue(result["ok"])
                self.assertEqual(result["count"], 2)
                self.assertEqual(result["ids"], [first_stage["id"], second_stage["id"]])
                self.assertEqual(result["selector"], "batch:thread-1")
                self.assertEqual([item["type"] for item in result["attachments"]], ["video", "video"])
            finally:
                attachments.STAGED_ATTACHMENT_DIR = original_stage_dir

    def test_attachment_pending_command_resolves_unique_pending_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            original_stage_dir = attachments.STAGED_ATTACHMENT_DIR
            attachments.STAGED_ATTACHMENT_DIR = root / "staged"
            try:
                video = root / "first.mp4"
                video.write_bytes(b"first")
                staged = attachments.stage_attachment(str(video), "first", "video", "qqbot-abc123")
                args = argparse.Namespace(
                    batch_key="qqbot:c2c:legacy-openid",
                    type="video",
                    ttl_hours=48,
                    limit=None,
                    verbose=False,
                )

                with tempfile.TemporaryFile("w+", encoding="utf-8") as output:
                    original_stdout = sys.stdout
                    sys.stdout = output
                    try:
                        cmd_attachment_pending(args)
                    finally:
                        sys.stdout = original_stdout
                    output.seek(0)
                    result = json.loads(output.read())

                self.assertTrue(result["ok"])
                self.assertEqual(result["count"], 1)
                self.assertEqual(result["ids"], [staged["id"]])
                self.assertEqual(result["resolved_batch_key"], "qqbot-abc123")
                self.assertEqual(result["selector"], "batch:qqbot-abc123")
                self.assertEqual(result["resolution"]["reason"], "staged-attachment-selector-resolved-by-unique-pending-batch")
            finally:
                attachments.STAGED_ATTACHMENT_DIR = original_stage_dir

    def test_attachment_pending_without_batch_key_returns_selector_for_unique_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            original_stage_dir = attachments.STAGED_ATTACHMENT_DIR
            attachments.STAGED_ATTACHMENT_DIR = root / "staged"
            try:
                first = root / "first.mp4"
                second = root / "second.png"
                first.write_bytes(b"first")
                second.write_bytes(b"second")
                attachments.stage_attachment(str(first), "first", "video", "thread-1")
                attachments.stage_attachment(str(second), "second", "image", "thread-1")
                args = argparse.Namespace(
                    batch_key=None,
                    type=None,
                    ttl_hours=48,
                    limit=None,
                    verbose=False,
                )

                with tempfile.TemporaryFile("w+", encoding="utf-8") as output:
                    original_stdout = sys.stdout
                    sys.stdout = output
                    try:
                        cmd_attachment_pending(args)
                    finally:
                        sys.stdout = original_stdout
                    output.seek(0)
                    result = json.loads(output.read())

                self.assertTrue(result["ok"])
                self.assertEqual(result["count"], 2)
                self.assertEqual(result["resolved_batch_key"], "thread-1")
                self.assertEqual(result["selector"], "batch:thread-1")
            finally:
                attachments.STAGED_ATTACHMENT_DIR = original_stage_dir

    def test_attachment_pending_without_batch_key_rejects_multiple_batches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            original_stage_dir = attachments.STAGED_ATTACHMENT_DIR
            attachments.STAGED_ATTACHMENT_DIR = root / "staged"
            try:
                first = root / "first.mp4"
                second = root / "second.png"
                first.write_bytes(b"first")
                second.write_bytes(b"second")
                attachments.stage_attachment(str(first), "first", "video", "thread-1")
                attachments.stage_attachment(str(second), "second", "image", "thread-2")
                args = argparse.Namespace(
                    batch_key=None,
                    type=None,
                    ttl_hours=48,
                    limit=None,
                    verbose=False,
                )

                with tempfile.TemporaryFile("w+", encoding="utf-8") as output:
                    original_stdout = sys.stdout
                    sys.stdout = output
                    try:
                        cmd_attachment_pending(args)
                    finally:
                        sys.stdout = original_stdout
                    output.seek(0)
                    result = json.loads(output.read())

                self.assertFalse(result["ok"])
                self.assertEqual(result["reason"], "ambiguous-staged-attachments")
                self.assertEqual(result["candidate_batch_keys"], ["thread-1", "thread-2"])
                self.assertIsNone(result["selector"])
            finally:
                attachments.STAGED_ATTACHMENT_DIR = original_stage_dir

    def test_attachment_list_rejects_default_batch_key(self) -> None:
        args = argparse.Namespace(batch_key="default", type=None, verbose=False)

        with tempfile.TemporaryFile("w+", encoding="utf-8") as output:
            original_stdout = sys.stdout
            sys.stdout = output
            try:
                cmd_attachment_list(args)
            finally:
                sys.stdout = original_stdout
            output.seek(0)
            result = json.loads(output.read())

        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "unsafe-default-batch-key")
        self.assertEqual(result["replacement"], "attachment-pending --ttl-hours 48")

    def test_redact_staged_attachment_hides_home_path(self) -> None:
        item = {"id": "20260701000000-abcdef1234", "path": str(pathlib.Path.home() / "secret.m4a")}

        redacted = attachments.redact_staged_attachment(item)

        self.assertTrue(redacted["path"].startswith("~"))

    def test_safe_attachment_name_replaces_windows_reserved_characters(self) -> None:
        self.assertEqual(attachments.safe_attachment_name('a<b>c:d"e|f?g*h.png'), "a-b-c-d-e-f-g-h.png")


if __name__ == "__main__":
    unittest.main()
