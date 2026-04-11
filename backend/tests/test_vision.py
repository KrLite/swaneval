"""Tests for vision helper — image extraction and OpenAI content build."""

import unittest

from app.services.vision import (
    build_vision_content,
    extract_image_uris,
    is_vision_task,
)


class TestExtractImageUris(unittest.TestCase):
    def test_text_only_row(self):
        self.assertEqual(extract_image_uris({"query": "What is 2+2?"}), [])

    def test_single_image_string(self):
        row = {"query": "Describe this.", "image": "https://example.com/cat.jpg"}
        self.assertEqual(extract_image_uris(row), ["https://example.com/cat.jpg"])

    def test_images_list(self):
        row = {"query": "Compare", "images": ["a.png", "b.png", "c.png"]}
        self.assertEqual(extract_image_uris(row), ["a.png", "b.png", "c.png"])

    def test_image_url_alias(self):
        row = {"query": "See", "image_url": "https://x.png"}
        self.assertEqual(extract_image_uris(row), ["https://x.png"])

    def test_combines_multiple_keys(self):
        row = {
            "query": "See",
            "image": "a.png",
            "images": ["b.png", "c.png"],
        }
        self.assertEqual(extract_image_uris(row), ["a.png", "b.png", "c.png"])

    def test_skips_non_strings_in_list(self):
        row = {"images": ["a.png", 42, None, "b.png"]}
        self.assertEqual(extract_image_uris(row), ["a.png", "b.png"])

    def test_strips_whitespace(self):
        row = {"image": "  a.png  "}
        self.assertEqual(extract_image_uris(row), ["a.png"])

    def test_empty_string_ignored(self):
        row = {"image": ""}
        self.assertEqual(extract_image_uris(row), [])


class TestBuildVisionContent(unittest.TestCase):
    def test_text_only(self):
        content = build_vision_content("Hello", [])
        self.assertEqual(content, [{"type": "text", "text": "Hello"}])

    def test_single_image(self):
        content = build_vision_content("Describe", ["a.png"])
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0], {"type": "text", "text": "Describe"})
        self.assertEqual(
            content[1],
            {"type": "image_url", "image_url": {"url": "a.png"}},
        )

    def test_multiple_images(self):
        content = build_vision_content("Compare", ["a.png", "b.png"])
        self.assertEqual(len(content), 3)
        self.assertEqual(
            [p["type"] for p in content],
            ["text", "image_url", "image_url"],
        )


class TestIsVisionTask(unittest.TestCase):
    def test_default_text(self):
        self.assertFalse(is_vision_task(None))
        self.assertFalse(is_vision_task(""))
        self.assertFalse(is_vision_task("text"))

    def test_vision_text(self):
        self.assertTrue(is_vision_task("vision_text"))

    def test_unknown_modality(self):
        self.assertFalse(is_vision_task("audio"))


if __name__ == "__main__":
    unittest.main()
