import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class StaticKnowledgeCacheConfigTest(unittest.TestCase):
    @unittest.skipUnless(
        (ROOT / "nginx" / "default.conf").exists(),
        "admin 容器测试未挂载 nginx 目录",
    )
    def test_versioned_knowledge_cache_contract(self):
        config = (ROOT / "nginx" / "default.conf").read_text(encoding="utf-8")
        self.assertIn("location = /knowledge/manifest.json", config)
        self.assertIn('Cache-Control "no-store, max-age=0"', config)
        self.assertIn("location ^~ /knowledge/", config)
        self.assertIn('Cache-Control "public, max-age=31536000, immutable"', config)
        self.assertIn("proxy_set_header X-Forwarded-For $remote_addr", config)
        self.assertIn("frame-ancestors 'none'", config)


if __name__ == "__main__":
    unittest.main()
