from __future__ import annotations

from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from archive_recovery.cli import InterviewConfig, render_toml
from archive_recovery.config import load_config
from archive_recovery.context import create_run_context
from archive_recovery.pipeline.inventory import build_dependency_query, build_query
from archive_recovery.pipeline.normalization import rewrite_html


def test_path_prefix_config_drives_cdx_prefix_query(tmp_path: Path):
    config_path = tmp_path / "scoped.toml"
    config_path.write_text(render_toml(InterviewConfig(domain="www.example.com", aliases=["example.com"], path_prefix="/blog", config_path=str(config_path), runs_root=str(tmp_path / "runs"), raw_root=str(tmp_path / "raw"), data_dir=str(tmp_path / "data"), recovered_root=str(tmp_path / "recovered"))), encoding="utf-8")
    config = load_config(config_path)
    context = create_run_context(config, "run-1")
    query = build_query(context, "www.example.com")
    assert "url=www.example.com%2Fblog" in query
    assert "matchType=prefix" in query
    alias_query = build_query(context, "example.com")
    assert "url=example.com%2Fblog" in alias_query
    assert "matchType=prefix" in alias_query
    assert config.path_prefix == "/blog"


def test_dependency_cdx_query_url_is_exact(tmp_path: Path):
    config_path = tmp_path / "scoped.toml"
    config_path.write_text(render_toml(InterviewConfig(domain="www.example.com", aliases=["example.com"], path_prefix="/blog", cdx_endpoint="https://archive.example.test/cdx", cdx_filters=["statuscode:200"], cdx_limit=1000, config_path=str(config_path), runs_root=str(tmp_path / "runs"), raw_root=str(tmp_path / "raw"), data_dir=str(tmp_path / "data"), recovered_root=str(tmp_path / "recovered"))), encoding="utf-8")
    context = create_run_context(load_config(config_path), "run-1")
    query = build_dependency_query(context, "https://www.example.com/blog/app.css?v=1&x=2", "resume-token")
    parts = urlsplit(query)
    assert parts.scheme == "https"
    assert parts.netloc == "archive.example.test"
    assert parts.path == "/cdx"
    assert parse_qsl(parts.query, keep_blank_values=True) == [
        ("url", "https://www.example.com/blog/app.css?v=1&x=2"),
        ("output", "json"),
        ("fl", "urlkey,timestamp,original,mimetype,statuscode,digest,length"),
        ("showResumeKey", "true"),
        ("matchType", "exact"),
        ("collapse", "digest"),
        ("limit", "1000"),
        ("filter", "statuscode:200"),
        ("resumeKey", "resume-token"),
    ]


def test_normalization_rewrites_only_recovered_first_party_routes():
    stats: Counter[str] = Counter()
    unresolved: set[str] = set()
    html = '<a href="http://example.com/blog/post.html#c1">Post</a><img src="http://www.example.com/blog/missing.jpg"><a href="https://cdn.example.net/lib.js">CDN</a>'
    route_map = {"http://www.example.com/blog/post.html": "blog/post/index.html"}
    out = rewrite_html(html, "http://www.example.com/blog/", "blog/index.html", route_map, "www.example.com", {"example.com"}, "/blog", stats, unresolved)
    assert 'href="post/index.html#c1"' in out
    assert 'src="http://www.example.com/blog/missing.jpg"' in out
    assert 'href="https://cdn.example.net/lib.js"' in out
    assert stats["links_rewritten"] == 1
    assert stats["unresolved_links_localized"] == 0
    assert "http://www.example.com/blog/missing.jpg" in unresolved


def test_unrecovered_first_party_assets_do_not_become_local_404s():
    stats: Counter[str] = Counter()
    unresolved: set[str] = set()
    html = '<img src="https://www.example.com/blog/missing.jpg"><link href="/blog/missing.css" rel="stylesheet"><script src="/blog/missing.js"></script>'
    out = rewrite_html(html, "https://www.example.com/blog/", "blog/index.html", {}, "www.example.com", {"example.com"}, "/blog", stats, unresolved)
    assert 'src="https://www.example.com/blog/missing.jpg"' in out
    assert 'href="https://www.example.com/blog/missing.css"' in out
    assert 'src="https://www.example.com/blog/missing.js"' in out
    assert 'src="missing.jpg"' not in out
    assert 'href="missing.css"' not in out
    assert 'src="missing.js"' not in out
    assert stats["unresolved_links_localized"] == 0


def test_unresolved_root_relative_first_party_links_become_absolute_old_domain_urls():
    stats: Counter[str] = Counter()
    unresolved: set[str] = set()
    html = '<a href="/blog/missing.html">Missing</a><img src="/blog/missing.png">'
    out = rewrite_html(html, "https://www.example.com/blog/", "blog/index.html", {}, "www.example.com", {"example.com"}, "/blog", stats, unresolved)
    assert 'href="https://www.example.com/blog/missing.html"' in out
    assert 'src="https://www.example.com/blog/missing.png"' in out
    assert 'href="missing.html"' not in out
    assert 'src="missing.png"' not in out
    assert stats["unresolved_links_localized"] == 0


def test_out_of_scope_first_party_link_is_not_localized():
    stats: Counter[str] = Counter()
    unresolved: set[str] = set()
    html = '<a href="http://example.com/about.html">About</a>'
    out = rewrite_html(html, "http://www.example.com/blog/", "blog/index.html", {}, "www.example.com", {"example.com"}, "/blog", stats, unresolved)
    assert 'href="http://example.com/about.html"' in out
    assert "../about/index.html" not in out
    assert stats["unresolved_links_localized"] == 0


def test_recovered_route_rewrites_without_fallback_localization():
    stats: Counter[str] = Counter()
    unresolved: set[str] = set()
    html = '<a href="http://example.com/blog/post.html">Post</a>'
    out = rewrite_html(html, "http://www.example.com/blog/", "blog/index.html", {"http://www.example.com/blog/post.html": "blog/post/index.html"}, "www.example.com", {"example.com"}, "/blog", stats, unresolved)
    assert 'href="post/index.html"' in out
    assert stats["links_rewritten"] == 1
    assert not unresolved
