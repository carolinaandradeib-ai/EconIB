/* app.js
   this is all the frontend behaviour - plain javascript, no libraries.
   it does the clicking/typing stuff on the page and talks to my flask API when it
   needs to save something. */

/* ---------------- tiny helpers ---------------- */

// $ and $all are just short ways to grab elements so i don't type querySelector every time
function $(sel, root) { return (root || document).querySelector(sel); }
function $all(sel, root) { return [...(root || document).querySelectorAll(sel)]; }

// little popup message at the bottom that disappears after 2.2s
function toast(msg, isError) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast show" + (isError ? " error" : "");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => (t.className = "toast"), 2200);
}

// AI help (Claude): I used Claude to help me get this fetch + async/await wrapper
// right, especially the error handling. I understood it and reused it everywhere.
// what it does: sends a request to my flask API and gives back the answer. if something
// went wrong it shows the error as a toast and returns null so the calling code can stop.
// EVERY add/edit/delete goes through this one function so error handling lives in one place.
async function api(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,   // turn my JS object into json text to send
  });
  const data = await res.json().catch(() => ({}));    // read the json that came back
  if (!res.ok) {                                       // res.ok is false for 400/403/etc
    toast((data.errors || ["Something went wrong"]).join(" "), true);
    return null;
  }
  return data;
}

// shows the red error box inside a form (used by the study kit form)
function showErrors(boxId, errors) {
  const box = $("#" + boxId);
  if (!box) return;
  box.textContent = errors.join(" ");
  box.classList.add("show");
}

/* ---------------- modals (the pop up forms) ---------------- */

// NOTE: instead of putting a click listener on every single button, i put ONE listener on
// the whole page and use closest() to check what got clicked. Claude showed me this trick.
// it's way less code and it even works for buttons that get added after the page loads.
document.addEventListener("click", (e) => {
  const opener = e.target.closest("[data-open-modal]");
  if (opener) $("#" + opener.dataset.openModal).classList.add("open");

  // close if you click the X or click the dark background outside the box
  if (e.target.closest("[data-close-modal]") ||
      e.target.classList.contains("modal-overlay")) {
    $all(".modal-overlay.open").forEach((m) => m.classList.remove("open"));
  }
});

/* ---------------- filters (SC-03) ---------------- */

// remember what's currently selected. empty string = "show everything"
const filterState = { subtopic: "", level: "", country: "", text: "" };

// this hides/shows the cards based on the filters. it's all done here in the browser so it
// feels instant (i don't ask the server again just to filter).
function applyFilters() {
  let visible = 0;
  $all(".filterable").forEach((el) => {
    const okSubtopic = !filterState.subtopic || el.dataset.subtopic === filterState.subtopic;
    // same "Both" rule as the backend: picking SL still keeps the Both items
    const lvl = el.dataset.level || "Both";
    const okLevel = !filterState.level || lvl === filterState.level || lvl === "Both";
    const okCountry = !filterState.country || el.dataset.country === filterState.country;
    const okText = !filterState.text || (el.dataset.text || "").includes(filterState.text);
    const show = okSubtopic && okLevel && okCountry && okText;   // must pass ALL filters
    el.classList.toggle("hidden", !show);
    if (show) visible++;
  });
  const count = $("#visible-count");
  if (count) count.textContent = visible;
  const empty = $("#no-results");
  if (empty) empty.classList.toggle("hidden", visible > 0);   // show "no results" if 0 left
}

// clicking a filter pill updates the state and re-runs the filter
document.addEventListener("click", (e) => {
  const pill = e.target.closest("[data-filter]");
  if (!pill) return;
  filterState[pill.dataset.filter] = pill.dataset.value;
  $all(`[data-filter="${pill.dataset.filter}"]`).forEach((p) =>
    p.classList.toggle("active", p === pill));   // highlight the one i clicked
  applyFilters();
});

// live search box - filters as i type
const searchBox = $("#search");
if (searchBox) searchBox.addEventListener("input", () => {
  filterState.text = searchBox.value.trim().toLowerCase();
  applyFilters();
});

/* ---------------- click a diagram to show its explanation (SC-09) ---------------- */

document.addEventListener("click", (e) => {
  const card = e.target.closest("[data-diagram-toggle]");
  if (!card || e.target.closest("button")) return;   // ignore if a button inside was clicked
  card.classList.toggle("open");                     // css shows/hides the explanation
});

/* ---------------- save / unsave to library ---------------- */

document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-toggle-library]");
  if (!btn) return;
  const data = await api("POST", "/api/library/toggle",
    { type: btn.dataset.toggleLibrary, id: btn.dataset.id });
  if (data) {
    toast(data.saved ? "Saved to your Library 🔖" : "Removed from Library");
    setTimeout(() => location.reload(), 450);   // reload so the button updates
  }
});

/* ---------------- make a flashcard ---------------- */

document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-make-flashcard]");
  if (!btn || btn.disabled) return;
  const data = await api("POST", "/api/flashcards",
    { source_type: btn.dataset.makeFlashcard, source_id: btn.dataset.id });
  if (data) {
    toast("Flashcard created — due today 🗂️");
    setTimeout(() => location.reload(), 450);
  }
});

/* ---------------- delete anything ---------------- */

document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-delete]");
  if (!btn) return;
  if (!confirm("Delete this item? This cannot be undone.")) return;   // ask first!
  const data = await api("DELETE", `/api/${btn.dataset.delete}/${btn.dataset.id}`);
  if (data) { toast("Deleted"); setTimeout(() => location.reload(), 400); }
});

/* ---------------- private notes on examples ---------------- */

document.addEventListener("click", async (e) => {
  const toggle = e.target.closest("[data-toggle-notes]");
  if (toggle) $("#notes-" + toggle.dataset.toggleNotes).classList.toggle("hidden");

  const add = e.target.closest("[data-add-note]");
  if (add) {
    const input = $("#note-input-" + add.dataset.addNote);
    const data = await api("POST", `/api/examples/${add.dataset.addNote}/notes`,
      { text: input.value });
    if (data) { toast("Private note added 💬"); setTimeout(() => location.reload(), 450); }
  }
});

/* ---------------- definitions page (add / edit form) ---------------- */

function setupDefinitionForm(section) {
  // clicking "edit" fills the form with the item's current values first
  document.addEventListener("click", (e) => {
    const edit = e.target.closest("[data-edit-def]");
    if (!edit) return;
    $("#def-modal-title").textContent = "Edit Definition";
    $("#def-id").value = edit.dataset.editDef;
    $("#def-term").value = edit.dataset.term;
    $("#def-definition").value = edit.dataset.definition;
    $("#def-subtopic").value = edit.dataset.subtopic;
    $("#def-level").value = edit.dataset.level;
    $("#modal-def").classList.add("open");
  });

  $("#def-save").addEventListener("click", async () => {
    const id = $("#def-id").value;
    const body = {
      term: $("#def-term").value, definition: $("#def-definition").value,
      subtopic: $("#def-subtopic").value, level: $("#def-level").value,
      section,
    };
    // if there's an id i'm editing (PUT), if not i'm adding a new one (POST)
    const data = id ? await api("PUT", "/api/definitions/" + id, body)
                    : await api("POST", "/api/definitions", body);
    if (data) { toast(id ? "Definition updated" : "Definition added 📖"); location.reload(); }
  });
}

/* ---------------- diagrams page (add form) ---------------- */

function setupDiagramForm(section) {
  $("#dia-save").addEventListener("click", async () => {
    const body = {
      title: $("#dia-title").value, image: $("#dia-image").value,
      explanation: $("#dia-explanation").value,
      subtopic: $("#dia-subtopic").value, level: $("#dia-level").value,
      section,
    };
    const data = await api("POST", "/api/diagrams", body);
    if (data) { toast("Diagram added 📈"); location.reload(); }
  });
}

/* ---------------- examples page (add / edit form) ---------------- */

function setupExampleForm(section) {
  document.addEventListener("click", (e) => {
    const edit = e.target.closest("[data-edit-rwe]");
    if (!edit) return;
    const item = JSON.parse(edit.dataset.editRwe);   // the whole example was stored as json
    $("#rwe-modal-title").textContent = "Edit Real World Example";
    $("#rwe-save").textContent = "Save Changes";
    $("#rwe-id").value = item.id;
    $("#rwe-title").value = item.title;
    $("#rwe-description").value = item.description;
    $("#rwe-subtopic").value = item.subtopic;
    $("#rwe-country").value = item.country;
    $("#rwe-data").value = item.data_context || "";
    $("#rwe-diagram").value = item.linked_diagram_id || "";
    // tick the checkboxes for definitions that were already linked
    $all("#rwe-defs input").forEach((cb) =>
      cb.checked = (item.linked_definition_ids || []).includes(cb.value));
    $("#modal-rwe").classList.add("open");
  });

  $("#rwe-save").addEventListener("click", async () => {
    const id = $("#rwe-id").value;
    const body = {
      title: $("#rwe-title").value, description: $("#rwe-description").value,
      subtopic: $("#rwe-subtopic").value, country: $("#rwe-country").value,
      data_context: $("#rwe-data").value,
      linked_diagram_id: $("#rwe-diagram").value,
      // collect the ids of every ticked definition checkbox
      linked_definition_ids: $all("#rwe-defs input:checked").map((cb) => cb.value),
      section,
    };
    const data = id ? await api("PUT", "/api/examples/" + id, body)
                    : await api("POST", "/api/examples", body);
    if (data) { toast(id ? "Example updated" : "Example added 🌐"); location.reload(); }
  });
}

/* ---------------- study kits page (SC-02, SC-10) ---------------- */

function setupKitForm(definitions, diagrams, examples) {
  const sectionSel = $("#kit-section");

  // when i change the section, only show the definitions/diagrams/examples from THAT section
  function refreshKitOptions() {
    const sec = sectionSel.value;
    $("#kit-subtopic").innerHTML = SUBTOPICS_ALL[sec]
      .map((st) => `<option>${st}</option>`).join("");
    $("#kit-defs").innerHTML = definitions.filter((d) => d.section === sec)
      .map((d) => `<label><input type="checkbox" value="${d.id}"> ${d.term}</label>`).join("");
    $("#kit-diagram").innerHTML = '<option value="">— None —</option>' +
      diagrams.filter((d) => d.section === sec)
        .map((d) => `<option value="${d.id}">${d.title}</option>`).join("");
    $("#kit-rwe").innerHTML = '<option value="">— None —</option>' +
      examples.filter((x) => x.section === sec)
        .map((x) => `<option value="${x.id}">${x.title}</option>`).join("");
  }
  sectionSel.addEventListener("change", refreshKitOptions);
  refreshKitOptions();

  $("#kit-save").addEventListener("click", async () => {
    const body = {
      title: $("#kit-title").value,
      section: sectionSel.value,
      subtopic: $("#kit-subtopic").value,
      definition_ids: $all("#kit-defs input:checked").map((cb) => cb.value),
      diagram_id: $("#kit-diagram").value,
      rwe_id: $("#kit-rwe").value,
    };
    // i don't use my api() helper here because i need to show the validation errors
    // INSIDE the form instead of as a toast (SC-10)
    const res = await fetch("/api/kits", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) { showErrors("kit-errors", data.errors); return; }   // show what's missing
    toast("Study Kit created 📦");
    location.reload();
  });
}

/* ---------------- grade calculator (SC-06) ---------------- */

function setupCalculator() {
  let level = "SL";   // start on SL

  // build the input rows for the current level (SL has 3 papers, HL has 4)
  function render() {
    $("#btn-sl").classList.toggle("active", level === "SL");
    $("#btn-hl").classList.toggle("active", level === "HL");
    $("#calc-rows").innerHTML = COMPONENTS[level].map(([key, name, max, weight]) => `
      <div class="card calc-row">
        <div class="info">
          <h3>${name}</h3>
          <p>Weight: ${Math.round(weight * 100)}% · Max marks: ${max}</p>
        </div>
        <div>
          <input type="number" min="0" max="${max}" value="0" data-mark="${key}">
          <span class="max">/ ${max}</span>
        </div>
      </div>`).join("");
    $all("[data-mark]").forEach((inp) => inp.addEventListener("input", update));
    update();
  }

  // send the marks to the backend and show the grade it returns. runs every time i type.
  async function update() {
    const marks = {};
    $all("[data-mark]").forEach((inp) => marks[inp.dataset.mark] = inp.value);
    const data = await api("POST", "/api/grade", { level, marks });
    if (!data) return;
    $("#grade-circle").textContent = data.grade;
    $("#grade-title").textContent = "Estimated Grade: " + data.grade;
    $("#grade-detail").textContent =
      `Weighted overall: ${data.overall}% · boundary for a ${data.grade}: ${data.boundary}%+`;
  }

  $("#btn-sl").addEventListener("click", () => { level = "SL"; render(); });
  $("#btn-hl").addEventListener("click", () => { level = "HL"; render(); });
  render();
}

/* ---------------- notes page (SC-08) ---------------- */

function setupNotes() {
  $("#note-save").addEventListener("click", async () => {
    const data = await api("POST", "/api/notes",
      { title: $("#note-title").value, content: $("#note-content").value });
    if (data) { toast("Note created 📝"); location.reload(); }
  });

  // auto-save: when i click away from a note (the "blur" event) it saves on its own,
  // so i never have to press a save button
  $all("[data-note-id]").forEach((ta) => {
    ta.addEventListener("blur", async () => {
      const data = await api("PUT", "/api/notes/" + ta.dataset.noteId,
        { content: ta.value });
      if (data) toast("Note saved ✓");
    });
  });
}

/* ---------------- flashcard review (SC-04) ---------------- */

function setupFlashcards() {
  let queue = [], index = 0, done = 0;   // the cards to review, where i am, how many done

  const card = $("#fc-card");

  // show the current card (or the "done" screen when i've finished the queue)
  function showCard() {
    if (index >= queue.length) {
      $("#fc-stage").innerHTML = `
        <div class="card fc-done">
          <div class="big">🎉</div>
          <h2>Review complete!</h2>
          <p style="color:var(--ink-soft);margin-top:6px">
            You reviewed ${done} card${done === 1 ? "" : "s"}. The Leitner system has
            scheduled each one based on how well you knew it.</p>
        </div>`;
      return;
    }
    const c = queue[index];
    $("#fc-progress").textContent = `Card ${index + 1} of ${queue.length} · Leitner box ${c.box}`;
    $("#fc-tag").textContent = c.tag || "";
    $("#fc-front").textContent = c.front;
    $("#fc-back").textContent = c.back;
    const img = $("#fc-image");
    if (c.image) { img.src = "/static/diagrams/" + c.image; img.classList.remove("hidden"); }
    else img.classList.add("hidden");
    card.classList.remove("revealed");           // start with the answer hidden
    $("#fc-buttons").classList.remove("show");
    $("#fc-hint").classList.remove("hidden");
  }

  // click the card to flip it and show the answer + the 4 buttons
  card.addEventListener("click", () => {
    card.classList.add("revealed");
    $("#fc-buttons").classList.add("show");
    $("#fc-hint").classList.add("hidden");
  });

  // pressing again/hard/good/easy sends the rating, then moves to the next card
  $all("[data-rate]").forEach((btn) => btn.addEventListener("click", async () => {
    const c = queue[index];
    const data = await api("POST", `/api/flashcards/${c.id}/review`,
      { rating: btn.dataset.rate });
    if (!data) return;
    done++;
    index++;
    showCard();
  }));

  // get the due cards from the backend when the page loads, then show the first one
  api("GET", "/api/flashcards/due").then((cards) => {
    queue = cards || [];
    showCard();
  });
}
