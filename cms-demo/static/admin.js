const TOKEN_KEY = "taro_cms_bearer_token";

function authHeaders() {
  const t = localStorage.getItem(TOKEN_KEY) || "";
  return {
    "Content-Type": "application/json",
    Authorization: t ? `Bearer ${t}` : "",
  };
}

async function api(path, opts = {}) {
  const r = await fetch(path, {
    ...opts,
    headers: { ...authHeaders(), ...opts.headers },
  });
  const text = await r.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  if (!r.ok) {
    const msg = data?.detail || data?.message || text || r.statusText;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
}

function setStatus(el, msg, ok) {
  el.textContent = msg;
  el.className = "status " + (ok ? "ok" : "err");
}

document.addEventListener("DOMContentLoaded", () => {
  const tokenInput = document.getElementById("token");
  const fileSelect = document.getElementById("file");
  const editor = document.getElementById("editor");
  const status = document.getElementById("status");
  const btnLoad = document.getElementById("btnLoad");
  const btnSave = document.getElementById("btnSave");
  const btnPublish = document.getElementById("btnPublish");
  const btnList = document.getElementById("btnList");

  /** True after user types; cleared after Save or successful Reload. */
  let editorDirty = false;
  editor.addEventListener("input", () => {
    editorDirty = true;
  });

  tokenInput.value = localStorage.getItem(TOKEN_KEY) || "";
  tokenInput.addEventListener("change", () => {
    localStorage.setItem(TOKEN_KEY, tokenInput.value.trim());
  });

  async function listFiles() {
    setStatus(status, "Loading file list…", true);
    const data = await api("/api/policies");
    fileSelect.innerHTML = "";
    for (const f of data.files || []) {
      const o = document.createElement("option");
      o.value = f;
      o.textContent = f;
      fileSelect.appendChild(o);
    }
    setStatus(status, `Found ${(data.files || []).length} file(s). Dir: ${data.policy_dir}`, true);
  }

  async function loadFile() {
    const name = fileSelect.value;
    if (!name) return;
    if (editorDirty) {
      const ok = window.confirm(
        "Reload from disk replaces the editor with the saved file. Unsaved changes will be lost. Continue?",
      );
      if (!ok) return;
    }
    setStatus(status, `Loading ${name}…`, true);
    const data = await api(`/api/policies/${encodeURIComponent(name)}`);
    editor.value = data.content || "";
    editorDirty = false;
    setStatus(status, `Reloaded ${data.name} from disk`, true);
  }

  btnList.addEventListener("click", () => listFiles().catch((e) => setStatus(status, String(e), false)));
  btnLoad.addEventListener("click", () => loadFile().catch((e) => setStatus(status, String(e), false)));

  btnSave.addEventListener("click", async () => {
    const name = fileSelect.value;
    if (!name) {
      setStatus(status, "Select a file first.", false);
      return;
    }
    try {
      setStatus(status, "Saving…", true);
      await api(`/api/policies/${encodeURIComponent(name)}`, {
        method: "PUT",
        body: JSON.stringify({ content: editor.value }),
      });
      editorDirty = false;
      setStatus(status, `Saved ${name}`, true);
    } catch (e) {
      setStatus(status, String(e), false);
    }
  });

  btnPublish.addEventListener("click", async () => {
    const name = fileSelect.value;
    if (!name) {
      setStatus(status, "Select a file first.", false);
      return;
    }
    try {
      setStatus(status, "Publishing (ingest)…", true);
      const data = await api(`/api/publish/${encodeURIComponent(name)}`, { method: "POST" });
      if (data.ok) editorDirty = false;
      const lines = JSON.stringify(data, null, 2);
      setStatus(status, lines, !!data.ok);
    } catch (e) {
      setStatus(status, String(e), false);
    }
  });

  listFiles().catch((e) => setStatus(status, String(e), false));
});
