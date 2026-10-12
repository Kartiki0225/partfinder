// PartFinder page: sends what is typed to the API and shows the answer.

const $ = (selector) => document.querySelector(selector);
const input = $("#query");
const suggestionList = $("#suggestions");

const escapeHtml = (text) => String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const number = (value) => value.toLocaleString("en-IN");

// ------------------------------------------------------------ searching

let latest = 0; // answers can arrive out of order, so only the newest one is shown

async function search() {
  const query = input.value;
  const ticket = ++latest;
  if (!query.trim()) {
    $("#body").hidden = true;
    return;
  }
  const response = await fetch("/api/search?q=" + encodeURIComponent(query));
  const result = await response.json();
  if (ticket !== latest) return; // a newer search has started
  showResults(result);
  showSteps(result);
}

function showResults(result) {
  $("#body").hidden = false;
  const time = result.microseconds < 1000 ? `${result.microseconds} microseconds` : `${(result.microseconds / 1000).toFixed(1)} milliseconds`;
  $("#status").innerHTML = `<b>${number(result.total)}</b> ${result.total === 1 ? "part" : "parts"} found in <b>${time}</b>` +
    (result.total > result.results.length ? `, showing the best ${result.results.length}` : "");

  $("#showing").hidden = !result.corrected;
  $("#showing").innerHTML = `Showing results for <b>${escapeHtml(result.showing)}</b>`;

  $("#results").innerHTML = result.results.length === 0
    ? `<li class="empty">No part matches that. Check the spelling, or try fewer words.</li>`
    : result.results.map((part) => `
      <li>
        <div class="main">
          <h3>${highlight(part.name, result.steps)}</h3>
          <p><span class="mono">${part.number}</span><span>${part.category}</span><span>${part.engine} engine</span><span>${part.application}</span></p>
        </div>
        <div class="side">
          <strong>₹${number(part.price)}</strong>
          <span class="stock ${part.stock ? "in" : "out"}">${part.stock ? `In stock · ${part.stock}` : "Out of stock"}</span>
        </div>
      </li>`).join("");
}

// Mark the words of a part name that the query matched.
function highlight(name, steps) {
  return name.split(" ").map((word) => {
    const lower = word.toLowerCase();
    const matched = steps.some((step) =>
      step.kind === "prefix" ? lower.startsWith(step.typed) : step.words.includes(lower));
    return matched ? `<mark>${escapeHtml(word)}</mark>` : escapeHtml(word);
  }).join(" ");
}

// ------------------------------------------------------------ "How this search worked"

const KIND_LABEL = { exact: "exact word", prefix: "starts with", corrected: "spelling fixed", unknown: "not in catalog" };

function showSteps(result) {
  const steps = [];

  if (result.mode === "part number") {
    steps.push(`<h3>Part number</h3><p>The query is a part number, so it was looked up directly in a dictionary (hash map). One step, no searching.</p>`);
  } else {
    steps.push(`<h3>Split into words</h3><p class="chips">${result.steps.map((step) => `<code>${escapeHtml(step.typed)}</code>`).join("") || "No words to search for."}</p>`);

    for (const step of result.steps) {
      steps.push(`
        <h3><code>${escapeHtml(step.typed)}</code> <span class="badge ${step.kind}">${KIND_LABEL[step.kind]}</span></h3>
        ${explainWord(step)}`);
    }

    if (result.mode === "all words") {
      steps.push(`<h3>Combine</h3><p>Intersecting the sets leaves <b>${number(result.total)}</b> parts that contain every word.</p>`);
    } else if (result.mode === "any word") {
      steps.push(`<h3>Combine</h3><p>No part contains every word, so parts containing <b>any</b> of them are shown: ${number(result.total)}.</p>`);
    }
    if (result.total > 0) {
      steps.push(`<h3>Rank</h3><p>A heap keeps only the best ${result.results.length}: most words matched, then words in the name, then in stock, then shorter names.</p>`);
    }
  }

  steps.push(`<h3>Cache</h3><p>${result.cached
    ? "This query was asked recently, so the answer came straight from the LRU cache."
    : "Not asked recently. The answer is now stored in the LRU cache."}</p>`);

  $("#steps").innerHTML = steps.map((step) => `<li>${step}</li>`).join("");
}

function explainWord(step) {
  const parts = `<b>${number(step.parts)}</b> parts`;
  if (step.kind === "exact") {
    return `<p>Found in the index. ${parts} contain it.</p>`;
  }
  if (step.kind === "prefix") {
    const more = step.word_count > step.words.length ? ` and ${step.word_count - step.words.length} more` : "";
    return `<p>Not a whole word. The trie has ${step.word_count} ${step.word_count === 1 ? "word" : "words"} that start with it:
      ${step.words.map((word) => `<code>${word}</code>`).join(" ")}${more}. ${parts} contain one of them.</p>`;
  }
  if (step.kind === "corrected") {
    const word = step.words[0];
    const distance = step.table[step.typed.length][word.length];
    return `<p>Not in the catalog. The nearest word is <code>${word}</code>, ${distance} typing ${distance === 1 ? "mistake" : "mistakes"} away. ${parts} contain it.</p>
      ${distanceTable(step.typed, word, step.table)}`;
  }
  return `<p>No word in the catalog is close to this, so it was ignored.</p>`;
}

// The dynamic programming table. The bottom-right cell is the answer.
function distanceTable(typed, word, table) {
  const head = `<tr><th></th><th></th>${[...word].map((letter) => `<th>${letter}</th>`).join("")}</tr>`;
  const rows = table.map((row, i) => {
    const cells = row.map((value, j) => {
      const last = i === typed.length && j === word.length;
      return `<td class="${last ? "answer" : ""}">${value}</td>`;
    }).join("");
    return `<tr><th>${i === 0 ? "" : typed[i - 1]}</th>${cells}</tr>`;
  }).join("");
  return `<table class="dp"><caption>Edit distance table</caption>${head}${rows}</table>`;
}

// ------------------------------------------------------------ autocomplete

let suggestions = [];
let selected = -1;

async function suggest() {
  const typed = input.value;
  const response = await fetch("/api/suggest?q=" + encodeURIComponent(typed));
  const answer = await response.json();
  if (typed !== input.value) return;
  suggestions = answer;
  selected = -1;
  drawSuggestions();
}

function drawSuggestions() {
  suggestionList.hidden = suggestions.length === 0;
  $("#tab-hint").hidden = suggestions.length === 0;
  const typedLength = input.value.length;
  suggestionList.innerHTML = suggestions.map((text, i) => `
    <li role="option" class="${i === selected ? "selected" : ""}" data-index="${i}">
      ${escapeHtml(text.slice(0, typedLength))}<b>${escapeHtml(text.slice(typedLength))}</b>
    </li>`).join("");
}

function choose(text) {
  input.value = text + " ";
  suggestions = [];
  drawSuggestions();
  input.focus();
  search();
}

input.addEventListener("input", () => {
  search();
  suggest();
});

input.addEventListener("keydown", (event) => {
  if (suggestions.length === 0) return;
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    const step = event.key === "ArrowDown" ? 1 : -1;
    selected = (selected + step + suggestions.length) % suggestions.length;
    drawSuggestions();
  } else if (event.key === "Tab" || (event.key === "Enter" && selected >= 0)) {
    event.preventDefault();
    choose(suggestions[Math.max(selected, 0)]);
  } else if (event.key === "Escape") {
    suggestions = [];
    drawSuggestions();
  }
});

suggestionList.addEventListener("mousedown", (event) => {
  const item = event.target.closest("li");
  if (item) {
    event.preventDefault();
    choose(suggestions[Number(item.dataset.index)]);
  }
});

input.addEventListener("blur", () => {
  suggestions = [];
  drawSuggestions();
});

for (const button of document.querySelectorAll("#examples button")) {
  button.addEventListener("click", () => {
    input.value = button.textContent;
    input.focus();
    search();
  });
}
