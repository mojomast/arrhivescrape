document.addEventListener("DOMContentLoaded", () => {
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
    const event = JSON.parse(message.data);
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
