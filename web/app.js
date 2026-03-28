const form = document.getElementById("analyze-form");
const tickersInput = document.getElementById("tickers");
const submitButton = document.getElementById("submit-button");
const statusBanner = document.getElementById("status-banner");
const signalTitle = document.getElementById("signal-title");
const resultGrid = document.getElementById("result-grid");
const signalAction = document.getElementById("signal-action");
const signalConfidence = document.getElementById("signal-confidence");
const signalTickers = document.getElementById("signal-tickers");
const signalTime = document.getElementById("signal-time");
const reasonsList = document.getElementById("reasons-list");
const jsonOutput = document.getElementById("json-output");
const defaultTickers = document.getElementById("default-tickers");
const modePill = document.getElementById("mode-pill");
const sourcePill = document.getElementById("source-pill");
const tickerBreakdown = document.getElementById("ticker-breakdown");

function setStatus(message, tone) {
  statusBanner.style.animation = 'none';
  setTimeout(() => {
    statusBanner.textContent = message;
    statusBanner.className = `status-banner ${tone}`;
    statusBanner.style.animation = 'slideDown 0.4s ease-out';
  }, 10);
}

function updateQuickPick(value) {
  tickersInput.value = value;
  tickersInput.style.transform = 'scale(1.02)';
  setTimeout(() => {
    tickersInput.style.transition = 'transform 0.2s ease';
    tickersInput.style.transform = 'scale(1)';
  }, 100);
  tickersInput.focus();
}

function summarizeMode(data) {
  const parts = [];
  parts.push(data.tinyfish_enabled ? "TinyFish live" : "TinyFish missing");
  parts.push(data.openai_enabled ? "OpenAI live" : "OpenAI missing");
  return parts.join(" + ");
}

async function loadHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    defaultTickers.textContent = data.default_tickers.join(", ");
    sourcePill.textContent = (data.sources || []).join(" + ");
    modePill.textContent = summarizeMode(data);
    if (!tickersInput.value) {
      tickersInput.value = data.default_tickers.join(", ");
    }
  } catch (error) {
    defaultTickers.textContent = "Unavailable";
    sourcePill.textContent = "Unavailable";
    modePill.textContent = "Unavailable";
  }
}

function createNewsCard(item) {
  const article = document.createElement("article");
  article.className = `news-card ${item.stance || "neutral"}`;

  const title = document.createElement("h4");
  title.textContent = item.title || "Untitled news item";
  article.appendChild(title);

  const meta = document.createElement("p");
  meta.className = "news-meta";
  meta.textContent = (item.source || "source").replaceAll("_", " ");
  article.appendChild(meta);

  const summary = document.createElement("p");
  summary.className = "news-summary";
  summary.textContent = item.text || "No summary available.";
  article.appendChild(summary);

  if (item.rationale) {
    const rationale = document.createElement("p");
    rationale.className = "news-rationale";
    rationale.textContent = item.rationale;
    article.appendChild(rationale);
  }

  if (item.url) {
    const link = document.createElement("a");
    link.href = item.url;
    link.target = "_blank";
    link.rel = "noreferrer noopener";
    link.textContent = "Open source";
    article.appendChild(link);
  }

  return article;
}

function renderTickerBreakdown(payload) {
  tickerBreakdown.innerHTML = "";
  const entries = Object.entries(payload.per_ticker || {});

  if (!entries.length) {
    tickerBreakdown.innerHTML = '<p class="empty-state">No ticker breakdown was returned.</p>';
    return;
  }

  entries.forEach(([ticker, details], entryIndex) => {
    setTimeout(() => {
    const section = document.createElement("section");
    section.className = "ticker-panel";

    const header = document.createElement("div");
    header.className = "ticker-panel-header";
    header.innerHTML = `
      <div>
        <p class="section-tag">${ticker}</p>
        <h3>${details.score?.sentiment || "NEUTRAL"} outlook</h3>
      </div>
      <div class="ticker-scores">
        <span>Bull ${(details.score?.bull_score * 100 || 0).toFixed(0)}%</span>
        <span>Bear ${(details.score?.bear_score * 100 || 0).toFixed(0)}%</span>
      </div>
    `;
    section.appendChild(header);

    const summary = document.createElement("p");
    summary.className = "ticker-summary";
    summary.textContent = details.score?.summary || "No summary returned for this ticker.";
    section.appendChild(summary);

    const columns = document.createElement("div");
    columns.className = "news-columns";

    const bullColumn = document.createElement("div");
    bullColumn.className = "news-column bull-column";
    bullColumn.innerHTML = '<h4>Bullish news</h4>';
    (details.bullish_news || []).forEach((item) => bullColumn.appendChild(createNewsCard(item)));
    if (!(details.bullish_news || []).length) {
      bullColumn.innerHTML += '<p class="empty-state small">No bullish items found.</p>';
    }

    const bearColumn = document.createElement("div");
    bearColumn.className = "news-column bear-column";
    bearColumn.innerHTML = '<h4>Bearish news</h4>';
    (details.bearish_news || []).forEach((item) => bearColumn.appendChild(createNewsCard(item)));
    if (!(details.bearish_news || []).length) {
      bearColumn.innerHTML += '<p class="empty-state small">No bearish items found.</p>';
    }

    columns.appendChild(bullColumn);
    columns.appendChild(bearColumn);
    section.appendChild(columns);

    const neutralItems = details.neutral_news || [];
    if (neutralItems.length) {
      const neutralBlock = document.createElement("div");
      neutralBlock.className = "neutral-block";
      const neutralTitle = document.createElement("h4");
      neutralTitle.textContent = "Neutral watchlist";
      neutralBlock.appendChild(neutralTitle);
      neutralItems.forEach((item) => neutralBlock.appendChild(createNewsCard(item)));
      section.appendChild(neutralBlock);
    }

    section.style.opacity = '0';
    section.style.transform = 'translateY(20px)';
    tickerBreakdown.appendChild(section);
    
    setTimeout(() => {
      section.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      section.style.opacity = '1';
      section.style.transform = 'translateY(0)';
    }, 50);
    }, entryIndex * 150);
  });
}

function renderResult(payload) {
  const { signal } = payload;
  
  // Animate the signal title update
  signalTitle.style.opacity = '0';
  setTimeout(() => {
    signalTitle.textContent = `${signal.action} signal ready`;
    signalTitle.style.opacity = '1';
    signalTitle.style.transition = 'opacity 0.4s ease';
  }, 200);
  
  resultGrid.classList.remove("hidden");
  
  // Animate metrics with stagger
  const metrics = [
    { elem: signalAction, value: signal.action },
    { elem: signalConfidence, value: `${(signal.confidence * 100).toFixed(1)}%` },
    { elem: signalTickers, value: signal.ticker },
    { elem: signalTime, value: new Date(signal.timestamp).toLocaleString() }
  ];
  
  metrics.forEach((metric, index) => {
    setTimeout(() => {
      metric.elem.style.opacity = '0';
      metric.elem.style.transform = 'translateY(10px)';
      setTimeout(() => {
        metric.elem.textContent = metric.value;
        metric.elem.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        metric.elem.style.opacity = '1';
        metric.elem.style.transform = 'translateY(0)';
      }, 50);
    }, index * 80);
  });

  reasonsList.innerHTML = "";
  signal.reasons.forEach((reason, index) => {
    setTimeout(() => {
      const item = document.createElement("li");
      item.textContent = reason;
      item.style.opacity = '0';
      item.style.transform = 'translateX(-10px)';
      reasonsList.appendChild(item);
      
      setTimeout(() => {
        item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        item.style.opacity = '1';
        item.style.transform = 'translateX(0)';
      }, 50);
    }, index * 100);
  });

  renderTickerBreakdown(payload);
  jsonOutput.textContent = JSON.stringify(payload, null, 2);

  const tone = signal.action === "BUY" ? "buy" : signal.action === "SELL" ? "sell" : "hold";
  setStatus(
    `${signal.action} with ${(signal.confidence * 100).toFixed(1)}% confidence for ${signal.ticker}.`,
    tone,
  );
  
  // Smooth scroll to results
  setTimeout(() => {
    document.querySelector('.result-card').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 400);
}

async function submitAnalysis(event) {
  event.preventDefault();
  const tickers = tickersInput.value
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);

  if (!tickers.length) {
    setStatus("Enter at least one ticker to analyze.", "error");
    return;
  }

  submitButton.disabled = true;
  submitButton.innerHTML = '<span>Analyzing...</span>';
  setStatus("Using TinyFish to collect Yahoo Finance SG and Bloomberg Asia coverage...", "loading");

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ tickers }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || payload.details || "Analysis failed");
    }

    renderResult(payload);
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = '<span>Analyze</span>';
  }
}

document.querySelectorAll(".chip").forEach((button) => {
  button.addEventListener("click", () => updateQuickPick(button.dataset.tickers));
});

form.addEventListener("submit", submitAnalysis);
loadHealth();
