document.addEventListener("DOMContentLoaded", () => {
  const library = document.querySelector("[data-object-library]");
  if (library) {
    const search = library.querySelector("[data-object-search]");
    const kind = library.querySelector("[data-object-kind]");
    const stage = library.querySelector("[data-object-stage]");
    const preview = library.querySelector("[data-object-preview]");
    const renderer = library.querySelector("[data-object-renderer]");
    const rows = Array.from(library.querySelectorAll("[data-object-row]"));
    const groups = Array.from(library.querySelectorAll("[data-object-group]"));
    const count = library.querySelector("[data-object-visible-count]");
    const empty = library.querySelector("[data-object-empty]");
    const matches = (row) => {
      const text = (search?.value || "").trim().toLowerCase();
      return (!text || (row.dataset.search || "").includes(text)) && (!kind?.value || row.dataset.kind === kind.value) && (!stage?.value || row.dataset.stage === stage.value) && (!preview?.value || row.dataset.preview === preview.value) && (!renderer?.value || row.dataset.renderer === renderer.value);
    };
    const updateGroups = () => {
      groups.forEach((group) => {
        let next = group.nextElementSibling;
        let visible = false;
        while (next && !next.hasAttribute("data-object-group")) {
          if (next.hasAttribute("data-object-row") && !next.hidden) visible = true;
          next = next.nextElementSibling;
        }
        group.hidden = !visible;
      });
    };
    const applyFilters = () => {
      let visible = 0;
      rows.forEach((row) => {
        const show = matches(row);
        row.hidden = !show;
        if (show) visible += 1;
      });
      updateGroups();
      if (count) count.textContent = String(visible);
      if (empty) empty.hidden = visible !== 0;
    };
    [search, kind, stage, preview, renderer].forEach((control) => control?.addEventListener("input", applyFilters));
    applyFilters();
  }

  const list = document.querySelector("[data-events-url]");
  const status = document.querySelector("[data-sse-status]");
  if (!list || typeof EventSource === "undefined") return;
  const source = new EventSource(list.dataset.eventsUrl);
  const setStatus = (text, className) => {
    if (!status) return;
    status.textContent = text;
    status.className = `sse-status ${className}`;
  };
  source.addEventListener("open", () => setStatus("live", "connected"));
  source.addEventListener("error", () => setStatus("reconnecting", "disconnected"));
  source.addEventListener("progress", (message) => {
    setStatus("live", "connected");
    let event;
    try {
      event = JSON.parse(message.data);
    } catch {
      return;
    }
    const item = document.createElement("li");
    const time = document.createElement("time");
    const level = document.createElement("span");
    time.textContent = event.created_at || "";
    level.className = `level ${event.level || "info"}`;
    level.textContent = event.level || "info";
    item.append(time, level, document.createTextNode(event.message || "event"));
    list.appendChild(item);
    list.scrollTop = list.scrollHeight;
  });
});
