from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
