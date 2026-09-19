"use strict";
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const el = (tag, text, cls) => {
  const node = document.createElement(tag);
  if (text != null) node.textContent = text;
  if (cls) node.className = cls;
  return node;
};
function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.classList.add("icon");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS(svg.namespaceURI, "use");
  use.setAttribute("href", "#i-" + name);
  svg.append(use);
  return svg;
}
async function api(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    $("#connection").textContent = "本機服務未連線";
    $("#connection-dot").classList.remove("online");
    throw new Error("無法連線到本機服務。請確認 Start.cmd 仍在運作後重試。");
  }
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("服務回傳了無法讀取的內容，請確認服務仍在運作。");
  }
  if (!response.ok) {
    const error = new Error(
      typeof data.detail === "string"
        ? data.detail
        : "請求失敗，請確認輸入內容或查看服務記錄。",
    );
    error.status = response.status;
    throw error;
  }
  $("#connection").textContent = "本機服務運作中";
  $("#connection-dot").classList.add("online");
  return data;
}
const post = (url, data) =>
  api(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
function localUrl(value) {
  try {
    const url = new URL(value, location.origin);
    return url.origin === location.origin &&
      /^\/demo\/(source\.html|assets\/|download\/)/.test(url.pathname)
      ? url.href
      : null;
  } catch {
    return null;
  }
}
function link(text, url) {
  const a = el("a", text);
  const safe = localUrl(url);
  if (safe) {
    a.href = safe;
    a.target = "_blank";
    a.rel = "noopener";
  }
  return a;
}
const modes = { naive: "語意搜尋", mix: "圖譜＋向量", global: "圖譜全域" };
let status = null,
  intent = "answer",
  retrievalMode = "naive",
  busy = false,
  activeTab = "search",
  conversations = [],
  current = null,
  selectedTurn = null,
  library = [],
  fetchingFiles = false,
  uploading = false;
const emptyEvidence = $("#evidence-list").firstElementChild.cloneNode(true);
const narrow = matchMedia("(max-width: 1000px)");
function toggleEvidence(open, focus = false) {
  $("#evidence-panel").hidden = !open;
  $("#evidence-toggle").setAttribute("aria-expanded", String(open));
  if (focus) {
    const target = open ? $("#close-evidence") : $("#evidence-toggle");
    target.focus();
  }
}
toggleEvidence(!narrow.matches);
narrow.addEventListener("change", (e) => toggleEvidence(!e.matches));
$("#evidence-toggle").onclick = () =>
  toggleEvidence($("#evidence-panel").hidden);
$("#close-evidence").onclick = () => toggleEvidence(false, true);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !$("#image-dialog").open) {
    $("#retrieval-options").open = false;
    if (narrow.matches && !$("#evidence-panel").hidden)
      toggleEvidence(false, true);
  }
});
function tab(name) {
  activeTab = name;
  $$(".tab").forEach((x) => (x.hidden = x.id !== name));
  $$("[data-tab]").forEach((x) => {
    const on = x.dataset.tab === name;
    x.classList.toggle("active", on);
    if (on) x.setAttribute("aria-current", "page");
    else x.removeAttribute("aria-current");
  });
  $("#page-title").textContent = {
    search: "研究對話",
    files: "文件資料庫",
    settings: "模型設定",
  }[name];
  $("#evidence-toggle").hidden = name !== "search";
  if (name === "files") files();
}
$$("[data-tab]").forEach((b) => (b.onclick = () => tab(b.dataset.tab)));
function setIntent(value) {
  intent = value;
  $$("[data-intent]").forEach((b) => {
    const on = b.dataset.intent === value;
    b.classList.toggle("active", on);
    b.setAttribute("aria-pressed", String(on));
  });
  $("#composer-hint").textContent =
    value === "answer"
      ? "提問請帶上研究主題；追問可參考前面的回答。"
      : "只回傳相關片段，不產生回答；圖譜模式仍可能呼叫 LLM。";
}
$$("[data-intent]").forEach(
  (b) => (b.onclick = () => setIntent(b.dataset.intent)),
);
$$("[data-mode]").forEach(
  (b) =>
    (b.onclick = () => {
      retrievalMode = b.dataset.mode;
      $$("[data-mode]").forEach((x) => {
        const on = x === b;
        x.classList.toggle("active", on);
        x.setAttribute("aria-pressed", String(on));
      });
      $("#retrieval-label").textContent = modes[retrievalMode];
      $("#retrieval-options").open = false;
    }),
);
function setBusy(value) {
  busy = value;
  $("#send").disabled = value || !status;
  $("#new-chat").disabled = value;
  $$("[data-intent]").forEach(
    (b) =>
      (b.disabled =
        value || (b.dataset.intent === "answer" && !status?.llm_ready)),
  );
  $("#query").setAttribute("aria-busy", String(value));
}
async function load() {
  setBusy(false);
  try {
    status = await api("/demo/status");
    $("#connection").textContent = "本機服務運作中";
    $("#connection-dot").classList.add("online");
    $("#model-state").textContent = status.llm_ready
      ? "研究問答已就緒"
      : "本機搜尋已就緒";
    $("#source-count").textContent = status.source_count;
    $("#embed-info").textContent =
      `${status.embedding_mode === "local" ? "本機 CPU" : "API"} · ${status.embedding_model}`;
    if (!status.llm_ready) {
      setIntent("search");
      const notice = $("#mode-notice");
      notice.hidden = false;
      notice.replaceChildren(
        el("span", "目前尚未連接 LLM，仍可使用語意搜尋。"),
      );
      const setup = el("button", "前往模型設定");
      setup.onclick = () => tab("settings");
      notice.append(setup);
    } else setIntent(intent);
    const graphReady = status.llm_ready && status.graph_enabled;
    $$("[data-mode]").forEach(
      (b) => (b.disabled = b.dataset.mode !== "naive" && !graphReady),
    );
    $("#graph-hint").textContent = graphReady
      ? "圖譜檢索需文件已完成圖譜抽取；可在進階管理查看。"
      : "接上 LLM 並啟用圖譜抽取後，才可使用圖譜檢索。";
    const settings = await api("/demo/settings");
    $("#base-url").value = settings.base_url;
    $("#model-name").value = settings.model;
    $("#graph").checked = settings.graph_enabled;
    $("#api-key").placeholder = settings.has_api_key
      ? "已儲存金鑰；留白保留"
      : "輸入 API key／存取密碼";
  } catch (error) {
    $("#connection").textContent = "連線需要確認";
    $("#message").textContent =
      error.message + " 請啟動 Start.cmd 後重新整理頁面。";
  } finally {
    setBusy(false);
  }
}
function historyNav() {
  const list = $("#conversation-list");
  list.replaceChildren();
  if (!conversations.length) {
    list.append(el("p", "從一個研究問題開始", "history-empty"));
    return;
  }
  for (const chat of [...conversations].reverse()) {
    const button = el(
      "button",
      chat.turns[0]?.query || "新對話",
      "history-item" + (chat === current ? " active" : ""),
    );
    button.title = chat.turns[0]?.query || "新對話";
    button.onclick = () => {
      current = chat;
      tab("search");
      renderConversation();
      historyNav();
    };
    list.append(button);
  }
}
function newConversation() {
  current = null;
  selectedTurn = null;
  $("#query").value = "";
  $("#query").style.height = "";
  $("#message").textContent = "";
  tab("search");
  renderConversation();
  historyNav();
  $("#query").focus();
}
$("#new-chat").onclick = newConversation;
$$("[data-query]").forEach(
  (b) =>
    (b.onclick = () => {
      $("#query").value = b.dataset.query;
      $("#query").focus();
      resizeQuery();
    }),
);
function chooseEvidence(turn, referenceId, open = true) {
  selectedTurn = turn;
  renderEvidence(turn, referenceId);
  if (open) toggleEvidence(true);
  if (referenceId != null) {
    requestAnimationFrame(() => {
      const selected = $$(".evidence-card").find(
        (c) => c.dataset.ref === String(referenceId),
      );
      selected?.scrollIntoView({ block: "nearest" });
    });
  }
}
function renderEvidence(turn, selected) {
  const list = $("#evidence-list");
  list.replaceChildren();
  const refs = turn?.references || [];
  $("#evidence-count").textContent = refs.length;
  $("#panel-count").textContent = refs.length;
  $("#evidence-context").textContent = turn
    ? turn.query
    : "回答與檢索結果的來源會顯示在這裡。";
  if (!turn) {
    list.append(emptyEvidence.cloneNode(true));
    return;
  }
  if (!refs.length) {
    list.append(
      el(
        "p",
        turn.pending
          ? "正在尋找相關研究證據…"
          : "這次沒有取得可顯示的來源。可調整問題，或確認文件已建立索引。",
        "empty-list",
      ),
    );
    return;
  }
  refs.forEach((ref, index) => {
    const source = ref.source;
    const id = String(ref.reference_id || index + 1);
    const card = el(
      "article",
      null,
      "evidence-card" + (String(selected) === id ? " selected" : ""),
    );
    card.dataset.ref = id;
    const head = el("div", null, "source-heading");
    head.append(
      el("span", id, "reference-number"),
      source
        ? link(source.name, source.url)
        : el("span", ref.file_path || "來源片段"),
    );
    card.append(
      head,
      el("p", source?.location || "來源位置未提供", "source-location"),
    );
    const text = Array.isArray(ref.content)
      ? ref.content.join("\n\n")
      : ref.content || ref.text || "";
    if (text.length > 180) {
      card.append(el("div", text.slice(0, 180) + "…", "evidence-excerpt"));
      const details = el("details");
      details.append(
        el("summary", "展開完整片段"),
        el("div", text, "evidence-excerpt"),
      );
      card.append(details);
    } else
      card.append(
        el(
          "div",
          text || "來源未附片段文字，可開啟文件核對。",
          "evidence-excerpt",
        ),
      );
    if (source?.images?.length) {
      const images = el("div", null, "source-images");
      source.images.forEach((url) => {
        const safe = localUrl(url);
        if (!safe) return;
        const button = el("button", null, "source-image");
        button.setAttribute(
          "aria-label",
          `放大原圖：${source.name} ${source.location}`,
        );
        const img = el("img");
        img.src = safe;
        img.alt = `${source.name} ${source.location} 原圖`;
        img.loading = "lazy";
        button.append(img);
        button.onclick = () => {
          $("#image-title").textContent = `${source.name} · ${source.location}`;
          $("#image-preview").src = safe;
          $("#image-preview").alt = img.alt;
          $("#image-dialog").showModal();
        };
        images.append(button);
      });
      card.append(
        images,
        el(
          "p",
          "點擊原圖放大核對，不代表模型已理解圖片。",
          "source-image-note",
        ),
      );
    }
    if (source) {
      const actions = el("div", null, "source-actions");
      actions.append(
        link("開啟來源 ↗", source.url),
        link("下載原檔", `/demo/download/${source.id}`),
      );
      card.append(actions);
    }
    list.append(card);
  });
}
$("#close-image").onclick = () => $("#image-dialog").close();
$("#image-dialog").onclick = (e) => {
  if (e.target === $("#image-dialog")) {
    const r = e.target.getBoundingClientRect();
    if (
      e.clientX < r.left ||
      e.clientX > r.right ||
      e.clientY < r.top ||
      e.clientY > r.bottom
    )
      e.target.close();
  }
};
// Model/document text is always inserted as text nodes, never evaluated as HTML.
function inline(parent, text, turn) {
  const pattern = /\*\*([^*]+)\*\*|`([^`]+)`|\[(\d+)\]|【(\d+)】/g;
  let end = 0;
  for (const match of text.matchAll(pattern)) {
    parent.append(document.createTextNode(text.slice(end, match.index)));
    if (match[1]) {
      const strong = el("strong");
      inline(strong, match[1], turn);
      parent.append(strong);
    } else if (match[2]) parent.append(el("code", match[2]));
    else {
      const referenceId = match[3] || match[4];
      const ref = turn.references.find(
        (r, i) => String(r.reference_id || i + 1) === referenceId,
      );
      if (ref) {
        const b = el("button", referenceId, "citation");
        b.setAttribute("aria-label", `查看來源 ${referenceId}`);
        b.onclick = () => chooseEvidence(turn, referenceId);
        parent.append(b);
      } else parent.append(document.createTextNode(match[0]));
    }
    end = match.index + match[0].length;
  }
  parent.append(document.createTextNode(text.slice(end)));
}
function markdown(text, turn) {
  const out = el("div", null, "answer-body");
  for (const ref of turn.references) {
    if (!ref.source || !ref.file_path) continue;
    const label = `${ref.source.name} · ${ref.source.location}`;
    text = text.split(ref.file_path).join(label);
    const basename = ref.file_path.split(/[\\/]/).pop();
    if (basename) text = text.split(basename).join(label);
  }
  const lines = text.split(/\r?\n/);
  let i = 0;
  const cells = (line) =>
    line
      .trim()
      .replace(/^\||\|$/g, "")
      .split("|")
      .map((s) => s.trim());
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i++;
      continue;
    }
    if (/^\s*[-*_]{3,}\s*$/.test(line)) {
      out.append(el("hr"));
      i++;
      continue;
    }
    if (line.startsWith("```")) {
      const code = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```"))
        code.push(lines[i++]);
      i++;
      const pre = el("pre");
      pre.append(el("code", code.join("\n")));
      out.append(pre);
      continue;
    }
    if (
      i + 1 < lines.length &&
      line.includes("|") &&
      /^\s*\|?\s*:?-{3,}/.test(lines[i + 1])
    ) {
      const table = el("table"),
        head = el("tr");
      cells(line).forEach((s) => {
        const th = el("th");
        inline(th, s, turn);
        head.append(th);
      });
      const thead = el("thead");
      thead.append(head);
      table.append(thead);
      const tbody = el("tbody");
      i += 2;
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
        const row = el("tr");
        cells(lines[i++]).forEach((s) => {
          const td = el("td");
          inline(td, s, turn);
          row.append(td);
        });
        tbody.append(row);
      }
      table.append(tbody);
      const wrap = el("div", null, "table-scroll");
      wrap.append(table);
      out.append(wrap);
      continue;
    }
    const heading = line.match(/^(#{1,4})\s+(.+)/);
    if (heading) {
      const h = el("h" + Math.min(heading[1].length + 1, 4));
      inline(h, heading[2], turn);
      out.append(h);
      i++;
      continue;
    }
    if (/^\s*([-*]|\d+\.)\s+/.test(line)) {
      const ordered = /^\s*\d+\./.test(line),
        list = el(ordered ? "ol" : "ul");
      if (ordered) list.start = Number(line.match(/^\s*(\d+)\./)[1]);
      const re = ordered ? /^\s*\d+\.\s+/ : /^\s*[-*]\s+/;
      while (i < lines.length && re.test(lines[i])) {
        const li = el("li");
        inline(li, lines[i++].replace(re, ""), turn);
        list.append(li);
      }
      out.append(list);
      continue;
    }
    const p = el("p");
    inline(p, line, turn);
    out.append(p);
    i++;
  }
  return out;
}
function renderTurn(turn) {
  const article = el("article", null, "turn");
  const user = el("div", null, "user-message");
  user.append(el("p", turn.query));
  article.append(user);
  const heading = el("div", null, "assistant-heading");
  const mark = el("span", null, "brand-mark");
  mark.append(icon("nodes"));
  heading.append(
    mark,
    el("strong", "myRAG"),
    el(
      "span",
      `${turn.intent === "answer" ? "研究問答" : "證據檢索"} · ${modes[turn.mode]}`,
    ),
  );
  article.append(heading);
  if (turn.pending) {
    const line = el("div", null, "loading-line");
    line.append(
      el("span", null, "loading-dot"),
      el(
        "span",
        turn.waiting
          ? "仍在等待服務回應，模型限流時可能需要較長時間。"
          : turn.intent === "answer"
            ? "正在尋找證據並整理回答…"
            : "正在尋找相關研究…",
      ),
    );
    line.setAttribute("role", "status");
    article.append(line);
  } else if (turn.error) {
    article.append(el("div", turn.error, "turn-error"));
    const actions = el("div", null, "answer-meta");
    const retry = el("button", "編輯後重試", "text-button");
    retry.onclick = () => {
      $("#query").value = turn.query;
      setIntent(turn.intent);
      $("#query").focus();
    };
    actions.append(retry);
    if (turn.intent === "answer") {
      const search = el("button", "改為只找證據", "text-button");
      search.onclick = () => {
        setIntent("search");
        $("#query").value = turn.query;
        $("#query").focus();
      };
      actions.append(search);
    }
    article.append(actions);
  } else {
    article.append(markdown(turn.response, turn));
    const actions = el("div", null, "answer-meta");
    const sources = el(
      "button",
      `查看 ${turn.references.length} 個證據片段 ↗`,
      "evidence-chip",
    );
    sources.onclick = () => chooseEvidence(turn);
    actions.append(
      sources,
      el(
        "small",
        turn.intent === "answer"
          ? "請核對來源；模型推論不等同實驗結論。"
          : "這是檢索結果，尚未由 LLM 產生研究結論。",
      ),
    );
    article.append(actions);
  }
  return article;
}
function renderConversation() {
  const turns = current?.turns || [];
  $("#welcome").hidden = turns.length > 0;
  $("#messages").replaceChildren(...turns.map(renderTurn));
  const latest = turns.at(-1) || null;
  selectedTurn = latest;
  renderEvidence(latest);
}
function scrollLatest() {
  const box = $("#conversation-scroll");
  box.scrollTop = box.scrollHeight;
}
async function send(event) {
  event?.preventDefault();
  if (busy || !status) return;
  const query = $("#query").value.trim();
  if (query.length < 2) {
    $("#message").textContent = "請至少輸入兩個字，描述你要找的研究主題。";
    $("#query").focus();
    return;
  }
  if (!current) {
    current = { turns: [] };
    conversations.push(current);
  }
  const chat = current;
  const history = chat.turns
    .filter((t) => t.intent === "answer" && !t.pending && !t.error)
    .slice(-3)
    .flatMap((t) => [
      { role: "user", content: t.query.slice(0, 6000) },
      { role: "assistant", content: t.response.slice(0, 6000) },
    ]);
  const turn = {
    query,
    intent,
    mode: retrievalMode,
    references: [],
    response: "",
    pending: true,
  };
  chat.turns.push(turn);
  $("#query").value = "";
  resizeQuery();
  $("#message").textContent = "";
  $("#retrieval-options").open = false;
  setBusy(true);
  renderConversation();
  historyNav();
  scrollLatest();
  const waiting = setTimeout(() => {
    turn.waiting = true;
    if (current === chat) {
      renderConversation();
      scrollLatest();
    }
  }, 20000);
  try {
    const body = { query, limit: 6, mode: turn.mode };
    if (turn.intent === "answer") body.conversation_history = history;
    const result = await post(
      turn.intent === "answer" ? "/demo/ask" : "/demo/search",
      body,
    );
    turn.references =
      turn.intent === "answer"
        ? result.references || []
        : result.data?.chunks || [];
    turn.response =
      turn.intent === "answer"
        ? result.response || "服務未回傳回答文字。請查看來源或稍後重新提問。"
        : turn.references.length
          ? `找到 ${turn.references.length} 個相關證據片段。\n\n點選下方「查看證據片段」，核對文件位置、實驗條件與原圖。若需要整理、比較或解釋，切換成「研究問答」再提問。`
          : "目前沒有找到相關證據。請補充實驗名稱、材料或條件，或到文件資料庫確認索引已完成。";
  } catch (error) {
    turn.error = error.message;
    if (error.status === 502)
      turn.error += " 可查看模型服務的額度與連線狀態；目前輸入的問題已保留。";
  } finally {
    clearTimeout(waiting);
    turn.pending = false;
    setBusy(false);
    if (current === chat) {
      renderConversation();
      scrollLatest();
      if (turn.intent === "search" && !narrow.matches) toggleEvidence(true);
    }
    historyNav();
  }
}
$("#question-form").onsubmit = send;
function resizeQuery() {
  const q = $("#query");
  q.style.height = "auto";
  q.style.height = Math.min(q.scrollHeight, 145) + "px";
}
$("#query").oninput = resizeQuery;
$("#query").onkeydown = (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing && e.keyCode !== 229) {
    e.preventDefault();
    send();
  }
};
const stateNames = {
  processed: "可供搜尋",
  queued: "等待索引",
  processing: "正在處理",
  failed: "處理失敗",
  "partial-failure": "部分處理失敗",
  "duplicate-content": "內容重複",
  "index-removed": "索引已移除",
  "index-missing": "查無索引",
  "no-indexable-text": "無可索引文字",
  "status-unavailable": "暫無法取得狀態",
};
function stateGroup(state) {
  if (state === "processed") return "ready";
  if (["queued", "processing"].includes(state)) return "processing";
  return "attention";
}
function renderFiles() {
  const count = (group) =>
    library.filter((x) => stateGroup(x.state) === group).length;
  $("#stat-total").textContent = library.length;
  $("#stat-ready").textContent = count("ready");
  $("#stat-processing").textContent = count("processing");
  $("#stat-attention").textContent = count("attention");
  $("#source-count").textContent = library.length;
  const filter = $("#file-filter").value,
    query = $("#file-search").value.trim().toLowerCase();
  const items = library.filter(
    (x) =>
      (filter === "all" || stateGroup(x.state) === filter) &&
      x.name.toLowerCase().includes(query),
  );
  $("#file-count").textContent = `${items.length} / ${library.length}`;
  const list = $("#file-list");
  list.replaceChildren();
  if (!items.length) {
    list.append(
      el(
        "p",
        library.length
          ? "沒有符合條件的文件，試試其他檔名或狀態。"
          : "還沒有文件。選擇文件或拖曳到上方，即可開始建立知識庫。",
        "empty-list",
      ),
    );
    return;
  }
  for (const item of items) {
    const row = el("div", null, "file-row");
    row.append(
      el(
        "span",
        item.name.split(".").pop().slice(0, 5).toUpperCase(),
        "file-type",
      ),
    );
    const main = el("div", null, "file-main");
    main.append(
      link(item.name, `/demo/source.html?id=${item.id}`),
      el("p", new Date(item.created_at).toLocaleString("zh-TW"), "file-date"),
    );
    for (const warning of item.warnings || [])
      main.append(el("p", warning, "file-warning"));
    if (["failed", "partial-failure"].includes(item.state))
      main.append(
        el(
          "p",
          "原檔仍保留。確認模型額度或連線後，可在進階管理重試失敗文件。",
          "file-warning",
        ),
      );
    if (item.state === "index-removed")
      main.append(
        el("p", "原檔保留；需要重新搜尋時，可下載後再次匯入。", "file-warning"),
      );
    row.append(
      main,
      el(
        "span",
        stateNames[item.state] || item.state,
        "file-state " + stateGroup(item.state),
      ),
    );
    const actions = el("details", null, "file-actions"),
      summary = el("summary", "⋯");
    summary.setAttribute("aria-label", `${item.name} 的操作`);
    const menu = el("div");
    menu.append(
      link("查看解析內容", `/demo/source.html?id=${item.id}`),
      link("下載原始文件", `/demo/download/${item.id}`),
    );
    if (["processed", "failed"].includes(item.state)) {
      const remove = el("button", "移除索引，保留原檔");
      remove.onclick = async () => {
        if (
          !confirm(
            `移除「${item.name}」的搜尋索引？原始文件與圖片會保留，之後可下載後重新匯入。`,
          )
        )
          return;
        remove.disabled = true;
        try {
          const result = await api(`/demo/sources/${item.id}/index`, {
            method: "DELETE",
          });
          $("#upload-message").textContent = result.message;
          await files();
        } catch (error) {
          $("#upload-message").textContent = error.message;
          remove.disabled = false;
        }
      };
      menu.append(remove);
    }
    actions.append(summary, menu);
    row.append(actions);
    list.append(row);
  }
}
async function files() {
  if (fetchingFiles) return;
  fetchingFiles = true;
  $("#refresh").disabled = true;
  try {
    library = await api("/demo/sources");
    renderFiles();
  } catch (error) {
    $("#upload-message").textContent = error.message;
  } finally {
    fetchingFiles = false;
    $("#refresh").disabled = false;
  }
}
$("#refresh").onclick = files;
$("#file-search").oninput = renderFiles;
$("#file-filter").onchange = renderFiles;
setInterval(() => {
  if (
    activeTab === "files" &&
    !document.hidden &&
    !$$(".file-actions").some((x) => x.open)
  )
    files();
}, 10000);
function uploadFile(file, progress, label) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/demo/upload");
    xhr.responseType = "json";
    xhr.timeout = 600000;
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        progress.value = e.loaded / e.total;
        label.textContent = `上傳 ${Math.round((e.loaded / e.total) * 100)}%`;
      }
    };
    xhr.upload.onload = () => {
      progress.removeAttribute("value");
      label.textContent = "解析文件中…";
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve(xhr.response);
      else
        reject(
          new Error(
            typeof xhr.response?.detail === "string"
              ? xhr.response.detail
              : `匯入失敗（HTTP ${xhr.status}）`,
          ),
        );
    };
    xhr.onerror = () =>
      reject(new Error("連線中斷。先查看文件清單確認是否已匯入，再重試。"));
    xhr.ontimeout = () =>
      reject(new Error("等待逾時。請先查看文件清單，避免重複上傳。"));
    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}
async function upload(selected) {
  if (uploading) {
    $("#upload-message").textContent =
      "目前正在匯入文件，請等這一批完成後再加入。";
    return;
  }
  if (!selected.length) return;
  uploading = true;
  $("#upload").disabled = true;
  $("#upload-message").textContent = "";
  const queue = $("#upload-queue");
  queue.hidden = false;
  queue.replaceChildren();
  let failed = 0;
  try {
    for (const file of selected) {
      const row = el("div", null, "upload-item"),
        progress = el("progress"),
        label = el("span", "等待上傳");
      progress.max = 1;
      progress.value = 0;
      progress.setAttribute("aria-label", file.name + " 上傳進度");
      row.append(el("span", file.name), progress, label);
      queue.append(row);
      try {
        if (file.size > 30 * 1024 * 1024)
          throw new Error("超過 30 MB，請縮小檔案後重新選取。");
        if (!/\.(txt|md|pdf|pptx|docx|xlsx|png|jpe?g)$/i.test(file.name))
          throw new Error("不支援此格式；舊 Office 檔請另存為新格式。");
        const result = await uploadFile(file, progress, label);
        progress.remove();
        label.textContent =
          result.state === "already-imported"
            ? "已存在，未重複匯入"
            : "已接收，等待索引";
        if (result.state === "no-indexable-text") {
          label.textContent = "沒有可索引文字";
          row.classList.add("error");
          failed++;
        }
      } catch (error) {
        failed++;
        progress.remove();
        label.textContent = error.message;
        row.classList.add("error");
      }
      await files();
    }
    $("#upload-message").textContent = failed
      ? `本批有 ${failed} 份文件需要留意，請查看上方訊息；其餘文件可在清單確認狀態。`
      : "文件已接收。清單每 10 秒更新，顯示「可供搜尋」後即可提問。";
  } finally {
    uploading = false;
    $("#upload").disabled = false;
    $("#upload").value = "";
  }
}
$("#upload").onchange = () => upload([...$("#upload").files]);
const zone = $("#dropzone");
zone.ondragover = (e) => {
  e.preventDefault();
  zone.classList.add("dragover");
};
zone.ondragleave = (e) => {
  if (!zone.contains(e.relatedTarget)) zone.classList.remove("dragover");
};
zone.ondrop = (e) => {
  e.preventDefault();
  zone.classList.remove("dragover");
  upload([...e.dataTransfer.files]);
};
$("#settings-form").onsubmit = async (e) => {
  e.preventDefault();
  if ($("#graph").checked && (!$("#base-url").value.trim() || !$("#model-name").value.trim())) {
    $("#settings-message").textContent = "啟用知識圖譜前，請先填寫 LLM 的 API Base URL 與 Model name。";
    return;
  }
  $("#save-settings").disabled = true;
  try {
    const result = await post("/demo/settings", {
      base_url: $("#base-url").value,
      model: $("#model-name").value,
      api_key: $("#api-key").value,
      graph_enabled: $("#graph").checked,
    });
    $("#settings-message").textContent = result.message;
    $("#api-key").value = "";
    $("#model-state").textContent = "設定已儲存，等待重啟";
  } catch (error) {
    $("#settings-message").textContent = error.message;
  } finally {
    $("#save-settings").disabled = false;
  }
};
load();
