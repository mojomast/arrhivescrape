from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import ConfigError, load_config
from .context import create_run_context, initialize_run
from .pipeline.captures_browser import run_captures_browser
from .pipeline.dependencies import run_dependencies
from .pipeline.download import run_download
from .pipeline.inventory import run_inventory
from .pipeline.normalization import run_normalize
from .pipeline.selection import run_selection
from .pipeline.validation import run_validate
from .state import init_db, register_run


HOST_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])$", re.I)
TARGET_MODES = ("latest-good", "date-specific", "full-captures", "selected-eras")
THIRD_PARTY_MODES = ("off", "audit-only", "recover-capped", "recover-full-with-approval")
PUBLICATION_POLICIES = ("private-local", "private-tailnet", "public-noindex", "public-indexable")
SERVING_PREFERENCES = ("none", "caddy-local", "caddy-tailnet", "tailscale-serve", "tailscale-funnel", "public-caddy")


@dataclass
class InterviewConfig:
    domain: str
    aliases: list[str] = field(default_factory=list)
    target_mode: str = "latest-good"
    target_date: str = ""
    cdx_endpoint: str = "https://web.archive.org/cdx/search/cdx"
    cdx_filters: list[str] = field(default_factory=lambda: ["statuscode:200"])
    cdx_limit: int = 1000
    cdx_min_interval_seconds: float = 1.1
    content_workers: int = 4
    content_timeout_seconds: int = 30
    third_party_mode: str = "audit-only"
    recover_third_party_hosts: list[str] = field(default_factory=list)
    config_path: str = ""
    runs_root: str = "runs"
    raw_root: str = "raw/sha256"
    data_dir: str = "data"
    recovered_root: str = ""
    publication_policy: str = "private-tailnet"
    serving_preference: str = "caddy-local"
    bind_host: str = "127.0.0.1"
    bind_port: int = 18080
    public_hostname: str = ""

    @property
    def slug(self) -> str:
        return self.domain.lower()

    def new_run_id(self) -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{stamp}-{self.target_mode}"


def clean_host(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/", 1)[0].rstrip(".")
    if not HOST_RE.match(value):
        raise argparse.ArgumentTypeError(f"invalid domain or host: {value!r}")
    return value


def split_hosts(value: str) -> list[str]:
    if not value.strip():
        return []
    hosts: list[str] = []
    for item in value.split(","):
        host = clean_host(item)
        if host not in hosts:
            hosts.append(host)
    return hosts


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


def ask_choice(prompt: str, choices: tuple[str, ...], default: str) -> str:
    while True:
        answer = ask(f"{prompt} ({'/'.join(choices)})", default)
        if answer in choices:
            return answer
        print(f"Choose one of: {', '.join(choices)}")


def ask_int(prompt: str, default: int) -> int:
    while True:
        answer = ask(prompt, str(default))
        try:
            return int(answer)
        except ValueError:
            print("Enter an integer.")


def ask_float(prompt: str, default: float) -> float:
    while True:
        answer = ask(prompt, str(default))
        try:
            return float(answer)
        except ValueError:
            print("Enter a number.")


def build_config(args: argparse.Namespace, domain: str, aliases: list[str], target_mode: str, target_date: str, cdx_endpoint: str, cdx_filters: list[str], cdx_limit: int, cdx_min_interval_seconds: float, content_workers: int, content_timeout_seconds: int, third_party_mode: str, recover_third_party_hosts: list[str], publication_policy: str, serving_preference: str, bind_host: str, bind_port: int, public_hostname: str) -> InterviewConfig:
    return InterviewConfig(
        domain=domain,
        aliases=aliases,
        target_mode=target_mode,
        target_date=target_date,
        cdx_endpoint=cdx_endpoint,
        cdx_filters=cdx_filters,
        cdx_limit=cdx_limit,
        cdx_min_interval_seconds=cdx_min_interval_seconds,
        content_workers=content_workers,
        content_timeout_seconds=content_timeout_seconds,
        third_party_mode=third_party_mode,
        recover_third_party_hosts=recover_third_party_hosts,
        config_path=args.output or f"configs/{domain}.toml",
        recovered_root=f"recovered/{domain}",
        publication_policy=publication_policy,
        serving_preference=serving_preference,
        bind_host=bind_host,
        bind_port=bind_port,
        public_hostname=public_hostname,
    )


def interactive_config(args: argparse.Namespace) -> InterviewConfig:
    domain = clean_host(args.domain) if args.domain else clean_host(ask("Canonical domain"))
    aliases = split_hosts(ask("Alias hosts, comma-separated", f"www.{domain}"))
    target_mode = ask_choice("Target mode", TARGET_MODES, "latest-good")
    target_date = ask("Target date/timestamp or era notes") if target_mode in {"date-specific", "selected-eras"} else ""
    cdx_endpoint = ask("Wayback/CDX endpoint", "https://web.archive.org/cdx/search/cdx")
    cdx_filters = [item.strip() for item in ask("CDX filters, comma-separated", "statuscode:200").split(",") if item.strip()]
    cdx_limit = ask_int("CDX page limit", 1000)
    cdx_min_interval_seconds = ask_float("Minimum seconds between CDX requests", 1.1)
    content_workers = ask_int("Content download workers", 4)
    content_timeout_seconds = ask_int("Content request timeout seconds", 30)
    third_party_mode = ask_choice("Third-party asset recovery", THIRD_PARTY_MODES, "audit-only")
    recover_third_party_hosts = split_hosts(ask("Allowed third-party hosts, comma-separated")) if third_party_mode not in {"off", "audit-only"} else []
    publication_policy = ask_choice("Privacy/publication policy", PUBLICATION_POLICIES, "private-tailnet")
    serving_preference = ask_choice("Serving preference", SERVING_PREFERENCES, "caddy-local")
    bind_host = ask("Local bind host", "127.0.0.1")
    bind_port = ask_int("Local bind port", 18080)
    public_hostname = ask("Public hostname") if publication_policy.startswith("public") or serving_preference in {"tailscale-funnel", "public-caddy"} else ""
    return build_config(args, domain, aliases, target_mode, target_date, cdx_endpoint, cdx_filters, cdx_limit, cdx_min_interval_seconds, content_workers, content_timeout_seconds, third_party_mode, recover_third_party_hosts, publication_policy, serving_preference, bind_host, bind_port, public_hostname)


def non_interactive_config(args: argparse.Namespace) -> InterviewConfig:
    if not args.domain:
        raise SystemExit("--domain is required with --non-interactive")
    domain = clean_host(args.domain)
    aliases = split_hosts(args.aliases or f"www.{domain}")
    return build_config(args, domain, aliases, args.target_mode, args.target_date or "", "https://web.archive.org/cdx/search/cdx", ["statuscode:200"], 1000, 1.1, 4, 30, "audit-only", [], "private-tailnet", "caddy-local", "127.0.0.1", 18080, "")


def toml_string_list(values: list[str]) -> str:
    return "[" + ", ".join(json.dumps(value) for value in values) + "]"


def render_toml(config: InterviewConfig) -> str:
    sqlite_path = f"{config.data_dir}/{config.slug}.sqlite3"
    promoted_site = f"{config.recovered_root}/site"
    return f'''# Generated by archive-recovery new. Edit before running a recovery.
[project]
config_version = 1
name = {json.dumps(config.domain + " recovery")}

[scope]
domain = {json.dumps(config.domain)}
canonical_host = {json.dumps(config.domain)}
alias_hosts = {toml_string_list(config.aliases)}
scope_mode = "domain"

[target]
mode = {json.dumps(config.target_mode)}
target_date = {json.dumps(config.target_date)}

[cdx]
endpoint = {json.dumps(config.cdx_endpoint)}
match_type = "domain"
filters = {toml_string_list(config.cdx_filters)}
collapse = "digest"
limit = {config.cdx_limit}
show_resume_key = true
alias_inventory_enabled = true
dependency_lookup_enabled = true

[rate_limits.cdx]
concurrency = 1
min_interval_seconds = {config.cdx_min_interval_seconds}
max_attempts = 5
base_backoff_seconds = 5
cap_backoff_seconds = 300

[rate_limits.content]
workers = {config.content_workers}
per_host_concurrency = {config.content_workers}
timeout_seconds = {config.content_timeout_seconds}
max_attempts = 8
base_backoff_seconds = 5
cap_backoff_seconds = 300

[content]
fetch_modifier = "id_"
expected_mime_classes = ["html", "css", "javascript", "image", "font", "pdf", "audio", "video", "text", "json", "xml"]
active_javascript_policy = "preserve-private-only"

[third_party]
mode = {json.dumps(config.third_party_mode)}
allowed_hosts = {toml_string_list(config.recover_third_party_hosts)}
allowed_mime_classes = ["image", "css", "javascript", "font"]
max_urls = 50
max_bytes_per_asset = 10485760
rewrite_recovered_assets = true
output_prefix = "assets/recovered-external"

[paths]
data_dir = {json.dumps(config.data_dir)}
sqlite_path = {json.dumps(sqlite_path)}
raw_root = {json.dumps(config.raw_root)}
runs_root = {json.dumps(config.runs_root)}
recovered_root = {json.dumps(config.recovered_root)}
promoted_site = {json.dumps(promoted_site)}

[privacy]
publication_intent = {json.dumps(config.publication_policy)}
public_requires_approval = true
block_public_on_sensitive_queries = true
block_public_on_forms = true
neutralize_forms_for_public = true
strip_trackers_for_public = true
privacy_review_required = true

[serving]
preference = {json.dumps(config.serving_preference)}
server = "caddy"
bind_host = {json.dumps(config.bind_host)}
bind_port = {config.bind_port}
public_hostname = {json.dumps(config.public_hostname)}
directory_browsing_local = true
directory_browsing_exposed = false
spa_fallback = false
try_files = ["{{path}}", "{{path}}/index.html", "{{path}}.html"]
'''


def scaffold_run(config: InterviewConfig, dry_run: bool = False) -> Path:
    run_id = config.new_run_id()
    run_dir = Path(config.runs_root) / run_id
    if not dry_run:
        for child in ("config", "cdx/pages", "manifests", "logs", "reports", "ops", "staging/normalized-site"):
            (run_dir / child).mkdir(parents=True, exist_ok=True)
        run_config = {
            "run_id": run_id,
            "config_version": 1,
            "scope": {"domain": config.domain, "alias_hosts": config.aliases, "scope_mode": "domain"},
            "target_mode": config.target_mode,
            "paths": {
                "run_dir": str(run_dir),
                "staging_site": str(run_dir / "staging" / "normalized-site"),
                "release_site": f"{config.recovered_root}/releases/{run_id}/site",
                "promoted_site": f"{config.recovered_root}/site",
            },
            "privacy": {"publication_intent": config.publication_policy, "privacy_review_required": True},
            "serving": {"preference": config.serving_preference, "bind_host": config.bind_host, "bind_port": config.bind_port},
        }
        (run_dir / "config" / "run-config.json").write_text(json.dumps(run_config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return run_dir


def command_new(args: argparse.Namespace) -> int:
    config = non_interactive_config(args) if args.non_interactive else interactive_config(args)
    path = Path(config.config_path)
    if path.exists() and not args.force:
        raise SystemExit(f"Config already exists: {path}. Use --force to overwrite.")
    if not args.dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_toml(config), encoding="utf-8")
    run_dir = scaffold_run(config, dry_run=args.dry_run)
    print(f"Config: {path}")
    print(f"Run scaffold: {run_dir}")
    print(f"Domain: {config.domain}")
    print(f"Aliases: {', '.join(config.aliases) if config.aliases else '(none)'}")
    print(f"Target mode: {config.target_mode}")
    print(f"Publication: {config.publication_policy}")
    return 0


def command_init(args: argparse.Namespace) -> int:
    """Initialize a tracked recovery run from an existing TOML config."""

    try:
        config = load_config(args.config)
        context = initialize_run(config, args.run_id, force=args.force)
        init_db(config.sqlite_path)
        register_run(
            config.sqlite_path,
            run_id=context.run_id,
            config_path=str(config.path),
            run_dir=str(context.run_dir),
        )
    except (ConfigError, FileExistsError) as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Config: {config.path}")
    print(f"Run: {context.run_id}")
    print(f"Run directory: {context.run_dir}")
    print(f"Run config: {context.run_config_path}")
    print(f"State database: {config.sqlite_path}")
    return 0


def command_validate_config(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Config OK: {config.path}")
    print(f"Domain: {config.domain}")
    print(f"Target mode: {config.target_mode}")
    print(f"Runs root: {config.runs_root}")
    print(f"State database: {config.sqlite_path}")
    return 0


def pipeline_context(config_path: str, run_id: str | None):
    """Load config and resolve a run context without assuming old local paths."""

    config = load_config(config_path)
    context = create_run_context(config, run_id)
    context.ensure_dirs()
    if not context.run_config_path.exists():
        context.write_frozen_config()
    return context


def command_inventory(args: argparse.Namespace) -> int:
    try:
        context = pipeline_context(args.config, args.run_id)
        result = run_inventory(context, force=args.force, resume_key=args.resume_key)
    except (ConfigError, FileExistsError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Run: {context.run_id}")
    print(f"Inventory: {result.raw_path}")
    print(f"CDX pages: {result.pages_dir}")
    print(f"Pages fetched: {result.page_count}")
    print(f"Records written: {result.record_count}")
    return 0


def command_select(args: argparse.Namespace) -> int:
    try:
        context = pipeline_context(args.config, args.run_id)
        result = run_selection(
            context,
            inventory_path=Path(args.inventory) if args.inventory else None,
            selection_path=Path(args.selection_output) if args.selection_output else None,
            canonical_path=Path(args.canonical_output) if args.canonical_output else None,
            report_path=Path(args.report_output) if args.report_output else None,
        )
    except (ConfigError, FileExistsError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Run: {context.run_id}")
    print(f"Raw rows: {result.raw_rows}")
    print(f"Selected captures: {result.selected}")
    print(f"Canonical records: {result.canonical_records}")
    print(f"Selection: {result.selection_path}")
    print(f"Canonical inventory: {result.canonical_path}")
    print(f"Report: {result.report_path}")
    return 0


def command_download(args: argparse.Namespace) -> int:
    try:
        context = pipeline_context(args.config, args.run_id)
        result = run_download(
            context,
            selection_path=Path(args.selection) if args.selection else None,
            results_path=Path(args.results_output) if args.results_output else None,
            report_path=Path(args.report_output) if args.report_output else None,
        )
    except (ConfigError, FileExistsError, RuntimeError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Run: {context.run_id}")
    print(f"Attempted: {result.attempted}")
    print(f"Succeeded: {result.succeeded}")
    print(f"Failed: {result.failed}")
    print(f"Skipped: {result.skipped}")
    print(f"Results: {result.results_path}")
    print(f"Report: {result.report_path}")
    return 0


def command_dependencies(args: argparse.Namespace) -> int:
    try:
        context = pipeline_context(args.config, args.run_id)
        result = run_dependencies(
            context,
            selection_path=Path(args.selection) if args.selection else None,
            download_path=Path(args.download_results) if args.download_results else None,
            graph_path=Path(args.graph_output) if args.graph_output else None,
            missing_path=Path(args.missing_output) if args.missing_output else None,
            report_path=Path(args.report_output) if args.report_output else None,
        )
    except (ConfigError, FileExistsError, RuntimeError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Run: {context.run_id}")
    print(f"Parsed HTML/CSS files: {result.parsed_files}")
    print(f"References: {result.references}")
    print(f"Missing first-party requests: {result.missing}")
    print(f"Dependency graph: {result.graph_path}")
    print(f"Missing requests: {result.missing_path}")
    print(f"Report: {result.report_path}")
    return 0


def command_normalize(args: argparse.Namespace) -> int:
    try:
        context = pipeline_context(args.config, args.run_id)
        result = run_normalize(
            context,
            selection_path=Path(args.selection) if args.selection else None,
            canonical_path=Path(args.canonical) if args.canonical else None,
            download_path=Path(args.download_results) if args.download_results else None,
            staging_site=Path(args.staging_site) if args.staging_site else None,
            normalization_path=Path(args.normalization_output) if args.normalization_output else None,
            site_manifest_path=Path(args.site_manifest_output) if args.site_manifest_output else None,
            report_path=Path(args.report_output) if args.report_output else None,
            mime_audit_path=Path(args.mime_audit_output) if args.mime_audit_output else None,
        )
    except (ConfigError, FileExistsError, RuntimeError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Run: {context.run_id}")
    print(f"Normalized inputs: {result.normalized}")
    print(f"Public files: {result.public_files}")
    print(f"Collisions suffixed: {result.collisions}")
    print(f"Staging site: {result.staging_site}")
    print(f"Site manifest: {result.site_manifest_path}")
    print(f"Report: {result.report_path}")
    print(f"MIME audit: {result.mime_audit_path}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    try:
        context = pipeline_context(args.config, args.run_id)
        result = run_validate(
            context,
            staging_site=Path(args.staging_site) if args.staging_site else None,
            site_manifest_path=Path(args.site_manifest) if args.site_manifest else None,
            report_path=Path(args.report_output) if args.report_output else None,
            external_links_path=Path(args.external_links_output) if args.external_links_output else None,
        )
    except (ConfigError, FileExistsError, RuntimeError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Run: {context.run_id}")
    print(f"Checked files: {result.checked_files}")
    print(f"Internal references: {result.internal_references}")
    print(f"Missing references: {result.missing_references}")
    print(f"External references: {result.external_references}")
    print(f"MIME warnings: {result.mime_warnings}")
    print(f"Report: {result.report_path}")
    print(f"External links: {result.external_links_path}")
    return 0


def command_captures_browser(args: argparse.Namespace) -> int:
    try:
        context = pipeline_context(args.config, args.run_id)
        result = run_captures_browser(
            context,
            inventory_path=Path(args.inventory) if args.inventory else None,
            selection_path=Path(args.selection) if args.selection else None,
            site_manifest_path=Path(args.site_manifest) if args.site_manifest else None,
            output_dir=Path(args.output_dir) if args.output_dir else None,
        )
    except (ConfigError, FileExistsError, RuntimeError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Run: {context.run_id}")
    print(f"Groups: {result.groups}")
    print(f"Captures: {result.captures}")
    print(f"HTML: {result.html_path}")
    print(f"JSON: {result.json_path}")
    return 0


def command_web(args: argparse.Namespace) -> int:
    """Serve the optional local web UI when ASGI dependencies are installed."""

    if args.host not in {"127.0.0.1", "localhost", "::1"} and not args.allow_nonlocal:
        raise SystemExit("web UI defaults to local-only. Use --allow-nonlocal intentionally to bind outside loopback.")
    try:
        import uvicorn  # type: ignore[import-not-found]

        from .web import create_app
    except ImportError as exc:
        raise SystemExit("web UI requires optional dependencies: starlette jinja2 uvicorn") from exc

    try:
        app = create_app(runs_root=args.runs_root, config_path=args.config)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="archive-recovery", description="Wayback/CDX static-site recovery toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)
    new_parser = subparsers.add_parser("new", help="interactively create a recovery config and run scaffold")
    new_parser.add_argument("--domain", help="canonical domain for non-interactive or prefilled interactive setup")
    new_parser.add_argument("--aliases", help="comma-separated alias hosts for non-interactive setup")
    new_parser.add_argument("--target-mode", choices=TARGET_MODES, default="latest-good")
    new_parser.add_argument("--target-date", help="date, timestamp, or era notes for date-specific/selected-eras modes")
    new_parser.add_argument("--output", help="config path to write, default configs/<domain>.toml")
    new_parser.add_argument("--non-interactive", action="store_true", help="write defaults without prompts; requires --domain")
    new_parser.add_argument("--dry-run", action="store_true", help="show outputs without writing files")
    new_parser.add_argument("--force", action="store_true", help="overwrite an existing config")
    new_parser.set_defaults(func=command_new)

    init_parser = subparsers.add_parser("init", help="initialize a run from an existing recovery config")
    init_parser.add_argument("--config", required=True, help="path to recovery TOML config")
    init_parser.add_argument("--run-id", help="optional run id; defaults to a timestamp and target mode")
    init_parser.add_argument("--force", action="store_true", help="overwrite an existing frozen run config")
    init_parser.set_defaults(func=command_init)

    validate_parser = subparsers.add_parser("validate-config", help="load and validate a recovery TOML config")
    validate_parser.add_argument("--config", required=True, help="path to recovery TOML config")
    validate_parser.set_defaults(func=command_validate_config)

    inventory_parser = subparsers.add_parser("inventory", help="fetch a Wayback CDX inventory into the run manifest")
    inventory_parser.add_argument("--config", required=True, help="path to recovery TOML config")
    inventory_parser.add_argument("--run-id", required=True, help="run id to write under paths.runs_root")
    inventory_parser.add_argument("--resume-key", help="resumeKey to use for the first inventory host")
    inventory_parser.add_argument("--force", action="store_true", help="overwrite existing inventory manifest, CDX pages, and resume state")
    inventory_parser.set_defaults(func=command_inventory)

    select_parser = subparsers.add_parser("select", help="select best captures from an inventory JSONL manifest")
    select_parser.add_argument("--config", required=True, help="path to recovery TOML config")
    select_parser.add_argument("--run-id", required=True, help="run id containing or receiving manifests")
    select_parser.add_argument("--inventory", help="input inventory JSONL; defaults to run manifests/inventory.raw.jsonl")
    select_parser.add_argument("--selection-output", help="output selected JSONL; defaults to run manifests/selection.pruned.jsonl")
    select_parser.add_argument("--canonical-output", help="output canonical inventory JSONL; defaults to run manifests/inventory.canonical.jsonl")
    select_parser.add_argument("--report-output", help="selection report markdown path; defaults to run reports/selection-report.md")
    select_parser.set_defaults(func=command_select)

    download_parser = subparsers.add_parser("download", help="download selected Wayback captures into content-addressed raw storage")
    download_parser.add_argument("--config", required=True, help="path to recovery TOML config")
    download_parser.add_argument("--run-id", required=True, help="run id containing the selected manifest")
    download_parser.add_argument("--selection", help="input selected JSONL; defaults to run manifests/selection.pruned.jsonl")
    download_parser.add_argument("--results-output", help="download results JSONL; defaults to run manifests/download.results.jsonl")
    download_parser.add_argument("--report-output", help="download report markdown path; defaults to run reports/download-report.md")
    download_parser.set_defaults(func=command_download)

    deps_parser = subparsers.add_parser("dependencies", help="discover static dependencies from downloaded HTML and CSS")
    deps_parser.add_argument("--config", required=True, help="path to recovery TOML config")
    deps_parser.add_argument("--run-id", required=True, help="run id containing download results")
    deps_parser.add_argument("--selection", help="input selected JSONL; defaults to run manifests/selection.pruned.jsonl")
    deps_parser.add_argument("--download-results", help="input download results JSONL; defaults to run manifests/download.results.jsonl")
    deps_parser.add_argument("--graph-output", help="dependency graph JSONL; defaults to run manifests/dependency-graph.jsonl")
    deps_parser.add_argument("--missing-output", help="missing dependency request JSONL; defaults to run manifests/missing-dependency-requests.jsonl")
    deps_parser.add_argument("--report-output", help="dependency report markdown path; defaults to run reports/dependency-report.md")
    deps_parser.set_defaults(func=command_dependencies)

    normalize_parser = subparsers.add_parser("normalize", help="rewrite downloaded captures into a static staging site")
    normalize_parser.add_argument("--config", required=True, help="path to recovery TOML config")
    normalize_parser.add_argument("--run-id", required=True, help="run id containing download results")
    normalize_parser.add_argument("--selection", help="input selected JSONL; defaults to run manifests/selection.pruned.jsonl")
    normalize_parser.add_argument("--canonical", help="canonical inventory JSONL for alias routing; defaults to run manifests/inventory.canonical.jsonl")
    normalize_parser.add_argument("--download-results", help="input download results JSONL; defaults to run manifests/download.results.jsonl")
    normalize_parser.add_argument("--staging-site", help="output staging site directory; defaults to run staging/normalized-site")
    normalize_parser.add_argument("--normalization-output", help="normalization results JSONL; defaults to run manifests/normalization.results.jsonl")
    normalize_parser.add_argument("--site-manifest-output", help="site manifest JSONL; defaults to run manifests/site.manifest.jsonl")
    normalize_parser.add_argument("--report-output", help="normalization report markdown path; defaults to run reports/normalization-report.md")
    normalize_parser.add_argument("--mime-audit-output", help="MIME audit markdown path; defaults to run reports/mime-audit.md")
    normalize_parser.set_defaults(func=command_normalize)

    validate_site_parser = subparsers.add_parser("validate", help="validate internal links/assets and MIME basics in a normalized staging site")
    validate_site_parser.add_argument("--config", required=True, help="path to recovery TOML config")
    validate_site_parser.add_argument("--run-id", required=True, help="run id containing normalized staging site")
    validate_site_parser.add_argument("--staging-site", help="staging site directory; defaults to run staging/normalized-site")
    validate_site_parser.add_argument("--site-manifest", help="site manifest JSONL; defaults to run manifests/site.manifest.jsonl")
    validate_site_parser.add_argument("--report-output", help="validation report markdown path; defaults to run reports/validation-report.md")
    validate_site_parser.add_argument("--external-links-output", help="external links JSON path; defaults to run reports/external-links.json")
    validate_site_parser.set_defaults(func=command_validate)

    browser_parser = subparsers.add_parser("captures-browser", help="build a small static capture browser from inventory and local manifests")
    browser_parser.add_argument("--config", required=True, help="path to recovery TOML config")
    browser_parser.add_argument("--run-id", required=True, help="run id containing inventory manifests")
    browser_parser.add_argument("--inventory", help="input inventory JSONL; defaults to run manifests/inventory.raw.jsonl")
    browser_parser.add_argument("--selection", help="selection JSONL; defaults to run manifests/selection.pruned.jsonl")
    browser_parser.add_argument("--site-manifest", help="site manifest JSONL; defaults to run manifests/site.manifest.jsonl")
    browser_parser.add_argument("--output-dir", help="output directory; defaults to run reports/captures-browser")
    browser_parser.set_defaults(func=command_captures_browser)

    web_parser = subparsers.add_parser("web", help="serve the optional local web dashboard")
    web_parser.add_argument("--runs-root", default="runs", help="runs directory to browse; default: runs")
    web_parser.add_argument("--config", help="default recovery TOML config for starting stages")
    web_parser.add_argument("--host", default="127.0.0.1", help="bind host; default: 127.0.0.1")
    web_parser.add_argument("--port", type=int, default=18080, help="bind port; default: 18080")
    web_parser.add_argument("--allow-nonlocal", action="store_true", help="allow binding the web UI outside loopback")
    web_parser.set_defaults(func=command_web)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
