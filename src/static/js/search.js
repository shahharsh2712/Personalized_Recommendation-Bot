function renderProductCard(rec) {
  const score = rec.similarity_score
    ? `<span class="match-score">${(rec.similarity_score * 100).toFixed(1)}% match</span>`
    : "";
  const budget = rec.budget_tier
    ? `<span class="badge">${escapeHtml(rec.budget_tier)}</span>`
    : "";
  const website = rec.website
    ? `<a href="${escapeHtml(rec.website)}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="padding: 0.4rem 1rem; font-size: 0.8125rem;">Visit site</a>`
    : "";
  const desc = rec.description
    ? `<p class="product-card__desc">${escapeHtml(rec.description)}</p>`
    : "";

  return `
    <div class="product-card">
      <div class="product-card__header">
        <h3 class="product-card__title">${escapeHtml(rec.name)}</h3>
        ${score}
      </div>
      <p class="product-card__tagline">${escapeHtml(rec.tagline || "")}</p>
      ${desc}
      <div class="product-card__footer">
        ${budget}
        ${website}
      </div>
    </div>
  `;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}

function renderSkeletons(count = 3) {
  let html = "";
  for (let i = 0; i < count; i++) {
    html += `
      <div class="skeleton-card">
        <div class="skeleton skeleton-line short"></div>
        <div class="skeleton skeleton-line medium"></div>
        <div class="skeleton skeleton-line"></div>
      </div>
    `;
  }
  return html;
}

function renderEmptyState() {
  return `
    <div class="empty-state">
      <p class="empty-state__title">No products found</p>
      <p>Try describing your workflow or what you want to accomplish.</p>
      <div class="example-queries">
        <button type="button" class="example-query" data-query="project management for small teams">Project management for small teams</button>
        <button type="button" class="example-query" data-query="AI writing assistant">AI writing assistant</button>
        <button type="button" class="example-query" data-query="email marketing automation">Email marketing automation</button>
      </div>
    </div>
  `;
}

function renderErrorState(message) {
  return `
    <div class="alert alert-error" role="alert">
      <span aria-hidden="true">⚠</span>
      <span>${escapeHtml(message)}</span>
    </div>
  `;
}

function getRecommendations() {
  const input = document.getElementById("query");
  const resultsEl = document.getElementById("results");
  if (!input || !resultsEl) return;

  const query = input.value.trim();
  if (!query) return;

  resultsEl.innerHTML = renderSkeletons();
  fetch("/api/recommendations?query=" + encodeURIComponent(query))
    .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
    .then(({ ok, data }) => {
      if (!ok || data.error) {
        resultsEl.innerHTML = renderErrorState(data.error || "Search failed");
        return;
      }
      if (!data.recommendations || !data.recommendations.length) {
        resultsEl.innerHTML = renderEmptyState();
        bindExampleQueries();
        return;
      }
      resultsEl.innerHTML = data.recommendations.map(renderProductCard).join("");
    })
    .catch(() => {
      resultsEl.innerHTML = renderErrorState("Something went wrong. Please try again.");
    });
}

function bindExampleQueries() {
  document.querySelectorAll(".example-query").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = document.getElementById("query");
      if (input) {
        input.value = btn.dataset.query;
        getRecommendations();
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("query");
  if (input) {
    input.addEventListener("keypress", (e) => {
      if (e.key === "Enter") getRecommendations();
    });
  }
  const searchBtn = document.getElementById("search-btn");
  if (searchBtn) {
    searchBtn.addEventListener("click", getRecommendations);
  }
});
