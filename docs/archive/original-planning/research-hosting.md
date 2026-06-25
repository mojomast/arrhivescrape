# Static Site Hosting Research For Flat-File Wayback Mirror

## Context

The target is a flat-file Wayback-style mirror intended for local testing and reverse-proxy exposure through Tailscale at `pwned.ussyco.de`. The mirror likely contains a mix of archived HTML pages, CSS, JavaScript, images, fonts, media, JSON, XML, and possibly files saved with Wayback-style paths or normalized `.html` outputs.

The hosting layer should support:

- Static file serving from a local directory.
- URL path rewriting from extensionless paths to `.html` files.
- Sensible trailing slash behavior.
- Directory index behavior for local inspection.
- Correct MIME types for mixed assets.
- Predictable behavior behind `tailscale serve` or a Tailscale-accessible reverse proxy.
- Minimal operational complexity.

## Recommendation

Use Caddy for the default local/static host if simple configuration and automatic HTTPS are valuable. Use nginx if exact rewrite ordering, high-volume static serving behavior, or familiarity with traditional web server controls matters more.

For this project, Caddy is the pragmatic default because:

- Static hosting and extension fallback are concise.
- MIME type handling is automatic and good for common assets.
- Directory browsing can be enabled for testing with one directive.
- It can run plain HTTP locally and let Tailscale terminate HTTPS, or it can manage public HTTPS itself if DNS points directly at the host.
- Its config is easier to audit and adjust during archive reconstruction.

nginx remains a strong choice when rewrite behavior needs to be very explicit or when matching existing production hosting semantics.

## Comparison Matrix

| Area | nginx | Caddy |
| --- | --- | --- |
| URL path rewriting | Very powerful with `try_files`, `rewrite`, named locations, and regex locations. More verbose but highly deterministic. | Simple with `try_files` and `handle` blocks. Easier to read, less boilerplate. |
| `.html` fallback | Excellent with `try_files $uri $uri.html $uri/ ...`. | Excellent with `try_files {path} {path}.html {path}/ ...`. |
| Trailing slash handling | Explicit redirects/rewrite rules available. Directory requests usually redirect to slash when using indexes. | Generally sane defaults. Can explicitly redirect slash or non-slash forms with matchers. |
| MIME types | Requires `include mime.types;` or distro default. Easy to customize with `types`. | Built-in MIME detection via Go and Caddy defaults. Usually sufficient. |
| Directory index | `index index.html;` plus optional `autoindex on;` for browsing. | `file_server browse` enables directory listing. Without `browse`, serves index files only. |
| Local testing | Very common, easy with `python`-like static patterns but more config. | Very easy: one small Caddyfile. |
| HTTPS auto-provisioning | Not built in. Use certbot, acme.sh, or terminate HTTPS elsewhere. | Built in for public DNS names; automatic ACME certs when reachable. |
| Tailscale integration | Common pattern: nginx on localhost, `tailscale serve` forwards HTTPS to it. | Same pattern works. Caddy can also be the reverse proxy behind Tailscale. |
| Operational complexity | Higher. More knobs and edge cases. | Lower. Fewer lines and safer defaults. |

## Flat-File URL Behavior

Archived mirrors often need to resolve several request shapes:

- `/about` -> `/about.html`
- `/about/` -> `/about/index.html`
- `/blog/post` -> `/blog/post.html`
- `/assets/site.css` -> exact static file
- `/images/logo.png` -> exact static file
- `/` -> `/index.html`

A good static host should prefer exact files before fallbacks, otherwise real assets can be incorrectly rewritten to HTML.

Preferred fallback order:

1. Exact path as requested.
2. Directory index if request maps to a directory.
3. `.html` version of the path.
4. Optional `/index.html` fallback only if this is a single-page app. For a Wayback mirror, avoid SPA fallback unless explicitly needed.

For a Wayback mirror, do not blindly rewrite every 404 to `index.html`. That hides missing archived files and makes validation harder.

## nginx Configuration Pattern

Assume the mirror root is `/home/mojo/projects/archivebackup/mirror`.

### Local HTTP Static Server

```nginx
server {
    listen 127.0.0.1:8080;
    server_name localhost;

    root /home/mojo/projects/archivebackup/mirror;
    index index.html index.htm;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Useful for local archive inspection. Disable before public exposure if unwanted.
    autoindex on;
    autoindex_exact_size off;
    autoindex_localtime on;

    # Exact assets and files are served first. Then try directory index, then .html fallback.
    location / {
        try_files $uri $uri/ $uri.html =404;
    }
}
```

Behavior:

- `/asset.css` serves `/asset.css` exactly.
- `/about` serves `/about.html` if present.
- `/about/` serves `/about/index.html` if present.
- Missing files return `404`.
- Directory listings are enabled for testing when no index exists.

### nginx With Explicit Directory Index Fallback

If directory handling needs to be more explicit:

```nginx
server {
    listen 127.0.0.1:8080;
    server_name localhost;

    root /home/mojo/projects/archivebackup/mirror;
    index index.html index.htm;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    autoindex on;

    location / {
        try_files $uri $uri/index.html $uri.html =404;
    }
}
```

This avoids relying on `$uri/` internal directory processing and makes the fallback order obvious.

### nginx Trailing Slash Canonicalization

If the archive prefers extensionless file URLs without trailing slash, use a conservative redirect only for non-directory paths. Be careful: over-aggressive slash redirects can break archived URLs.

```nginx
server {
    listen 127.0.0.1:8080;
    server_name localhost;

    root /home/mojo/projects/archivebackup/mirror;
    index index.html index.htm;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    autoindex on;

    # If /foo/ exists only as /foo.html, redirect /foo/ to /foo.
    location ~ ^(.+)/$ {
        try_files $uri $uri/index.html @strip_trailing_slash;
    }

    location @strip_trailing_slash {
        return 301 $scheme://$host$1$is_args$args;
    }

    location / {
        try_files $uri $uri/index.html $uri.html =404;
    }
}
```

Use this only after testing. Many archived sites rely on slash URLs.

### nginx Reverse Proxy Behind Tailscale

Usually, keep nginx bound to loopback and let Tailscale expose it:

```nginx
server {
    listen 127.0.0.1:8080;
    server_name pwned.ussyco.de localhost;

    root /home/mojo/projects/archivebackup/mirror;
    index index.html index.htm;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    autoindex off;

    location / {
        try_files $uri $uri/index.html $uri.html =404;
    }
}
```

Then expose through Tailscale:

```bash
tailscale serve --bg --https=443 http://127.0.0.1:8080
```

Check status:

```bash
tailscale serve status
```

Stop serving:

```bash
tailscale serve reset
```

If public internet access through Tailscale Funnel is desired and enabled for the tailnet:

```bash
tailscale funnel --bg --https=443 http://127.0.0.1:8080
```

## Caddy Configuration Pattern

Assume the mirror root is `/home/mojo/projects/archivebackup/mirror`.

### Local HTTP Static Server

```caddyfile
http://127.0.0.1:8080 {
    root * /home/mojo/projects/archivebackup/mirror

    try_files {path} {path}/index.html {path}.html

    file_server browse
}
```

Behavior:

- Exact files are served first.
- Directory index files are preferred before `.html` fallback.
- Directory browsing is enabled for local testing.
- MIME types are handled automatically for common web assets.

### Caddy Without Directory Browsing

For Tailscale-exposed or semi-public use:

```caddyfile
http://127.0.0.1:8080 {
    root * /home/mojo/projects/archivebackup/mirror

    try_files {path} {path}/index.html {path}.html

    file_server
}
```

### Caddy With Public HTTPS Directly

If `pwned.ussyco.de` has public DNS pointing to the host and inbound ports `80` and `443` are reachable, Caddy can manage HTTPS automatically:

```caddyfile
pwned.ussyco.de {
    root * /home/mojo/projects/archivebackup/mirror

    try_files {path} {path}/index.html {path}.html

    file_server
}
```

Caddy will attempt ACME certificate provisioning automatically. This is separate from Tailscale HTTPS and requires normal public internet reachability unless DNS challenge automation is configured.

### Caddy With Explicit Trailing Slash Redirect

Avoid slash canonicalization unless the archive has a known canonical form. If needed, redirect slash URLs to extensionless HTML paths only where a corresponding `.html` file exists.

```caddyfile
http://127.0.0.1:8080 {
    root * /home/mojo/projects/archivebackup/mirror

    @slashHtml {
        path_regexp slash ^(.+)/$
        file {re.slash.1}.html
    }
    redir @slashHtml {re.slash.1} 301

    try_files {path} {path}/index.html {path}.html
    file_server browse
}
```

This preserves real directories while canonicalizing only slash paths backed by `.html` files.

### Caddy Behind Tailscale

Run Caddy on loopback:

```caddyfile
http://127.0.0.1:8080 {
    root * /home/mojo/projects/archivebackup/mirror

    try_files {path} {path}/index.html {path}.html
    file_server
}
```

Expose it with Tailscale Serve:

```bash
tailscale serve --bg --https=443 http://127.0.0.1:8080
```

For public Funnel exposure:

```bash
tailscale funnel --bg --https=443 http://127.0.0.1:8080
```

## Tailscale Serve And Funnel Notes

`tailscale serve` exposes a local service over the tailnet using HTTPS on the node's MagicDNS name or configured HTTPS endpoint. It is appropriate for private testing among tailnet members.

`tailscale funnel` exposes the service publicly through Tailscale Funnel, if enabled by tailnet policy. It is appropriate only if the archive can be public.

Useful commands:

```bash
# Show current Tailscale serving config.
tailscale serve status

# Serve local HTTP service privately over tailnet HTTPS.
tailscale serve --bg --https=443 http://127.0.0.1:8080

# Serve local HTTP service publicly through Funnel.
tailscale funnel --bg --https=443 http://127.0.0.1:8080

# Reset all serve/funnel config on this node.
tailscale serve reset

# Confirm node identity and Tailscale IPs.
tailscale status

# Check whether Funnel is available and enabled in the environment.
tailscale funnel status
```

Hostname considerations:

- Tailscale Serve normally uses the node's Tailscale HTTPS name, commonly under `*.ts.net`.
- A custom hostname like `pwned.ussyco.de` needs DNS and certificate handling to align with the chosen exposure path.
- If `pwned.ussyco.de` is public DNS pointing directly to the machine, Caddy can terminate public HTTPS directly.
- If `pwned.ussyco.de` is a CNAME or alias into Tailscale-managed Funnel infrastructure, use `tailscale funnel` and confirm the tailnet's Funnel/custom-domain capabilities.
- If `pwned.ussyco.de` is only intended inside the tailnet, use split DNS, MagicDNS, or local DNS to point it at the node's Tailscale IP and serve via nginx/Caddy directly or via `tailscale serve` where compatible.

## MIME Type Handling

### nginx

Use:

```nginx
include /etc/nginx/mime.types;
default_type application/octet-stream;
```

This covers common assets such as:

- `.html` as `text/html`
- `.css` as `text/css`
- `.js` as JavaScript MIME types depending on distro config
- `.png`, `.jpg`, `.gif`, `.webp`, `.svg`
- `.woff`, `.woff2`, `.ttf`
- `.json`, `.xml`, `.txt`

If archived assets have unusual extensions, add explicit `types` entries:

```nginx
types {
    application/wasm wasm;
    font/woff2 woff2;
    image/avif avif;
}
```

### Caddy

Caddy generally handles MIME types automatically. For unusual archived extensions, Caddy can set response headers with matchers, but most mirrors will not need this.

Example override:

```caddyfile
@wasm path *.wasm
header @wasm Content-Type application/wasm
```

## Directory Index Behavior For Testing

Directory browsing is useful during archive validation because it reveals missing index files, unexpected path layouts, and duplicate archive outputs.

Recommended local testing behavior:

- Enable directory browsing locally.
- Return `404` for missing files.
- Avoid SPA-style catch-all fallback.
- Prefer exact assets before HTML rewrites.

Recommended exposed behavior:

- Disable directory browsing unless intentional.
- Keep exact-file and `.html` fallback behavior.
- Preserve `404` responses for missing archived assets.

nginx local:

```nginx
autoindex on;
```

nginx exposed:

```nginx
autoindex off;
```

Caddy local:

```caddyfile
file_server browse
```

Caddy exposed:

```caddyfile
file_server
```

## HTTPS Options

### Option 1: Tailscale Terminates HTTPS

Run nginx or Caddy on local HTTP and expose with Tailscale:

```bash
tailscale serve --bg --https=443 http://127.0.0.1:8080
```

Pros:

- Simple local server config.
- No local certificate management.
- Good for private tailnet testing.

Cons:

- Hostname behavior depends on Tailscale Serve/Funnel capabilities.
- Public custom-domain behavior may require additional Tailscale configuration.

### Option 2: Caddy Terminates Public HTTPS

Use Caddy directly with `pwned.ussyco.de`:

```caddyfile
pwned.ussyco.de {
    root * /home/mojo/projects/archivebackup/mirror
    try_files {path} {path}/index.html {path}.html
    file_server
}
```

Pros:

- Automatic public certificates.
- Clean public-hostname behavior.

Cons:

- Requires public DNS and inbound network reachability.
- Not Tailscale-private by default.

### Option 3: nginx Terminates Public HTTPS

Use nginx with certbot/acme.sh-managed certificates:

```nginx
server {
    listen 80;
    server_name pwned.ussyco.de;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name pwned.ussyco.de;

    ssl_certificate /etc/letsencrypt/live/pwned.ussyco.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/pwned.ussyco.de/privkey.pem;

    root /home/mojo/projects/archivebackup/mirror;
    index index.html index.htm;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    autoindex off;

    location / {
        try_files $uri $uri/index.html $uri.html =404;
    }
}
```

Pros:

- Traditional and explicit.
- Works well in existing nginx deployments.

Cons:

- More certificate and renewal management.
- More config surface area.

## Suggested Validation Commands

After starting either server locally:

```bash
curl -I http://127.0.0.1:8080/
curl -I http://127.0.0.1:8080/index.html
curl -I http://127.0.0.1:8080/about
curl -I http://127.0.0.1:8080/about.html
curl -I http://127.0.0.1:8080/assets/site.css
curl -I http://127.0.0.1:8080/missing-file
```

Expected results:

- Existing HTML paths return `200` and `Content-Type: text/html`.
- Existing CSS/JS/image/font assets return `200` with appropriate content type.
- Extensionless paths backed by `.html` return `200`.
- Missing files return `404`.
- Directories with `index.html` return `200`.
- Directories without index show a listing only when browsing is enabled.

## Final Operational Pattern

Recommended default for this archive:

```caddyfile
http://127.0.0.1:8080 {
    root * /home/mojo/projects/archivebackup/mirror
    try_files {path} {path}/index.html {path}.html
    file_server browse
}
```

For Tailscale private exposure:

```bash
tailscale serve --bg --https=443 http://127.0.0.1:8080
```

For public Funnel exposure if intentionally enabled:

```bash
tailscale funnel --bg --https=443 http://127.0.0.1:8080
```

For a stricter exposed Caddy configuration, remove `browse`:

```caddyfile
http://127.0.0.1:8080 {
    root * /home/mojo/projects/archivebackup/mirror
    try_files {path} {path}/index.html {path}.html
    file_server
}
```

Use nginx instead if exact rewrite behavior or existing nginx operations are a stronger requirement:

```nginx
server {
    listen 127.0.0.1:8080;
    server_name localhost pwned.ussyco.de;

    root /home/mojo/projects/archivebackup/mirror;
    index index.html index.htm;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    autoindex off;

    location / {
        try_files $uri $uri/index.html $uri.html =404;
    }
}
```
