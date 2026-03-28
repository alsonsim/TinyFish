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
const sentimentChart = document.getElementById("sentiment-chart");
const tickerTrack = document.getElementById("tickerTrack");

let chartInstance = null;
let currentTickers = [];
let tickerRefreshInterval = null;

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
  
  // Update chart with historical data
  currentTickers = signal.ticker.split(", ");
  updateChart(30);

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

document.querySelectorAll(".chart-btn").forEach((button) => {
  button.addEventListener("click", () => {
    const days = parseInt(button.dataset.days);
    document.querySelectorAll(".chart-btn").forEach(btn => btn.classList.remove("active"));
    button.classList.add("active");
    updateChart(days);
  });
});

form.addEventListener("submit", submitAnalysis);
loadHealth();
loadWatchlist();
loadPortfolio();
loadAlerts();

// Watchlist functionality
const watchlistTicker = document.getElementById("watchlist-ticker");
const addWatchlistBtn = document.getElementById("add-watchlist-btn");
const watchlistItems = document.getElementById("watchlist-items");

addWatchlistBtn.addEventListener("click", async () => {
  const ticker = watchlistTicker.value.trim().toUpperCase();
  if (!ticker) return;

  try {
    const response = await fetch("/api/watchlist/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
    });
    
    if (response.ok) {
      watchlistTicker.value = "";
      loadWatchlist();
    }
  } catch (error) {
    console.error("Failed to add to watchlist:", error);
  }
});

async function loadWatchlist() {
  try {
    const response = await fetch("/api/watchlist", { method: "POST" });
    const data = await response.json();
    
    if (data.items && data.items.length > 0) {
      watchlistItems.innerHTML = data.items.map(item => `
        <div class="watchlist-item">
          <span class="ticker-badge">${item.ticker}</span>
          <button class="remove-btn" onclick="removeFromWatchlist('${item.ticker}')">×</button>
        </div>
      `).join("");
    } else {
      watchlistItems.innerHTML = '<p class="empty-state">No tickers in watchlist yet.</p>';
    }
  } catch (error) {
    console.error("Failed to load watchlist:", error);
  }
}

async function removeFromWatchlist(ticker) {
  try {
    await fetch("/api/watchlist/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
    });
    loadWatchlist();
  } catch (error) {
    console.error("Failed to remove from watchlist:", error);
  }
}

// Portfolio functionality
const portfolioTicker = document.getElementById("portfolio-ticker");
const portfolioQuantity = document.getElementById("portfolio-quantity");
const addPortfolioBtn = document.getElementById("add-portfolio-btn");
const portfolioItems = document.getElementById("portfolio-items");
const portfolioSummary = document.getElementById("portfolio-summary");

addPortfolioBtn.addEventListener("click", async () => {
  const ticker = portfolioTicker.value.trim().toUpperCase();
  const quantity = parseFloat(portfolioQuantity.value);
  
  if (!ticker || !quantity || quantity <= 0) return;

  try {
    const response = await fetch("/api/portfolio/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker, quantity }),
    });
    
    if (response.ok) {
      portfolioTicker.value = "";
      portfolioQuantity.value = "";
      loadPortfolio();
    }
  } catch (error) {
    console.error("Failed to add to portfolio:", error);
  }
});

async function loadPortfolio() {
  try {
    const response = await fetch("/api/portfolio");
    const data = await response.json();
    
    if (data.holdings && data.holdings.length > 0) {
      portfolioItems.innerHTML = data.holdings.map(item => `
        <div class="portfolio-item">
          <span class="ticker-badge">${item.ticker}</span>
          <span class="quantity">${item.quantity} shares</span>
          <span class="sentiment-badge ${item.sentiment?.toLowerCase() || 'neutral'}">${item.sentiment || 'N/A'}</span>
          <button class="remove-btn" onclick="removeFromPortfolio('${item.ticker}')">×</button>
        </div>
      `).join("");
      
      if (data.aggregated) {
        portfolioSummary.classList.remove("hidden");
        document.getElementById("portfolio-sentiment").textContent = data.aggregated.sentiment;
        document.getElementById("portfolio-risk").textContent = data.aggregated.risk_score.toFixed(2);
      }
    } else {
      portfolioItems.innerHTML = '<p class="empty-state">No holdings yet.</p>';
      portfolioSummary.classList.add("hidden");
    }
  } catch (error) {
    console.error("Failed to load portfolio:", error);
  }
}

async function removeFromPortfolio(ticker) {
  try {
    await fetch("/api/portfolio/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
    });
    loadPortfolio();
  } catch (error) {
    console.error("Failed to remove from portfolio:", error);
  }
}

// Alert functionality
const alertTicker = document.getElementById("alert-ticker");
const alertCondition = document.getElementById("alert-condition");
const alertThreshold = document.getElementById("alert-threshold");
const addAlertBtn = document.getElementById("add-alert-btn");
const alertItems = document.getElementById("alert-items");

addAlertBtn.addEventListener("click", async () => {
  const ticker = alertTicker.value.trim().toUpperCase();
  const condition = alertCondition.value;
  const threshold = parseFloat(alertThreshold.value);
  
  if (!ticker || !threshold) return;

  try {
    const response = await fetch("/api/alerts/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker, condition_type: condition, threshold }),
    });
    
    if (response.ok) {
      alertTicker.value = "";
      loadAlerts();
    }
  } catch (error) {
    console.error("Failed to add alert:", error);
  }
});

async function loadAlerts() {
  try {
    const response = await fetch("/api/alerts");
    const data = await response.json();
    
    if (data.alerts && data.alerts.length > 0) {
      alertItems.innerHTML = data.alerts.map(alert => `
        <div class="alert-item">
          <span class="ticker-badge">${alert.ticker}</span>
          <span class="alert-condition">${alert.condition_type.replace('_', ' ')} ${alert.threshold}</span>
          <button class="remove-btn" onclick="removeAlert(${alert.id})">×</button>
        </div>
      `).join("");
    } else {
      alertItems.innerHTML = '<p class="empty-state">No alerts configured.</p>';
    }
  } catch (error) {
    console.error("Failed to load alerts:", error);
  }
}

async function removeAlert(alertId) {
  try {
    await fetch("/api/alerts/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ alert_id: alertId }),
    });
    loadAlerts();
  } catch (error) {
    console.error("Failed to remove alert:", error);
  }
}

// Chat functionality
const chatMessages = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const chatSendBtn = document.getElementById("chat-send-btn");

async function sendChatMessage() {
  const message = chatInput.value.trim();
  if (!message) return;

  // Add user message to UI
  const userDiv = document.createElement("div");
  userDiv.className = "chat-message user-message";
  userDiv.innerHTML = `<div class="message-content">${escapeHtml(message)}</div>`;
  chatMessages.appendChild(userDiv);
  chatInput.value = "";
  
  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Show typing indicator
  const typingDiv = document.createElement("div");
  typingDiv.className = "chat-message bot-message typing";
  typingDiv.innerHTML = '<div class="message-content"><span class="typing-dots">...</span></div>';
  chatMessages.appendChild(typingDiv);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    
    const data = await response.json();
    
    // Remove typing indicator
    typingDiv.remove();
    
    // Add bot response
    const botDiv = document.createElement("div");
    botDiv.className = "chat-message bot-message";
    botDiv.innerHTML = `<div class="message-content">${escapeHtml(data.response)}</div>`;
    chatMessages.appendChild(botDiv);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
  } catch (error) {
    typingDiv.remove();
    console.error("Chat error:", error);
  }
}

chatSendBtn.addEventListener("click", sendChatMessage);
chatInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendChatMessage();
});

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Dark mode
const darkModeToggle = document.getElementById("dark-mode-toggle");
const themeIcon = darkModeToggle.querySelector(".theme-icon");

function toggleDarkMode() {
  document.body.classList.toggle("dark-mode");
  const isDark = document.body.classList.contains("dark-mode");
  themeIcon.textContent = isDark ? "☀️" : "🌙";
  localStorage.setItem("darkMode", isDark);
}

darkModeToggle.addEventListener("click", toggleDarkMode);

// Load dark mode preference
if (localStorage.getItem("darkMode") === "true") {
  document.body.classList.add("dark-mode");
  themeIcon.textContent = "☀️";
}

// Keyboard shortcuts
document.addEventListener("keydown", (e) => {
  // Ctrl/Cmd + K: Focus search
  if ((e.ctrlKey || e.metaKey) && e.key === "k") {
    e.preventDefault();
    tickersInput.focus();
  }
  
  // Ctrl/Cmd + /: Focus chat
  if ((e.ctrlKey || e.metaKey) && e.key === "/") {
    e.preventDefault();
    chatInput.focus();
  }
  
  // Esc: Close modals
  if (e.key === "Escape") {
    document.querySelectorAll(".modal").forEach(modal => modal.classList.add("hidden"));
  }
});

// Export to CSV
function exportToCSV() {
  if (!currentTickers.length) return;
  
  const ticker = currentTickers[0];
  fetch(`/api/history/${ticker}?days=90`)
    .then(res => res.json())
    .then(data => {
      const csv = convertToCSV(data);
      downloadCSV(csv, `${ticker}_sentiment_history.csv`);
    });
}

function convertToCSV(data) {
  const headers = ["Timestamp", "Bull Score", "Bear Score", "Confidence"];
  const rows = data.timestamps.map((ts, i) => [
    ts,
    data.bull_scores[i],
    data.bear_scores[i],
    data.confidence[i]
  ]);
  
  return [headers, ...rows].map(row => row.join(",")).join("\n");
}

function downloadCSV(csv, filename) {
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// Add export button to chart
document.querySelector(".chart-controls").insertAdjacentHTML("beforeend", 
  '<button class="chart-btn" onclick="exportToCSV()">Export CSV</button>'
);

// Modal functionality for article details
function showArticleModal(article) {
  const modal = document.getElementById("article-modal");
  const modalTitle = document.getElementById("modal-title");
  const modalBody = document.getElementById("modal-body");
  
  modalTitle.textContent = article.title;
  modalBody.innerHTML = `
    <p><strong>Source:</strong> ${article.source || 'Unknown'}</p>
    <p><strong>Stance:</strong> <span class="sentiment-badge ${article.stance}">${article.stance}</span></p>
    <p><strong>Summary:</strong> ${article.text}</p>
    ${article.rationale ? `<p><strong>Reasoning:</strong> ${article.rationale}</p>` : ''}
    ${article.url ? `<p><a href="${article.url}" target="_blank" rel="noopener">View Source</a></p>` : ''}
  `;
  
  modal.classList.remove("hidden");
}

document.getElementById("modal-close-btn").addEventListener("click", () => {
  document.getElementById("article-modal").classList.add("hidden");
});

// Update news cards to open modal on click
function createNewsCard(item) {
  const article = document.createElement("article");
  article.className = `news-card ${item.stance || "neutral"}`;
  article.style.cursor = "pointer";
  article.addEventListener("click", () => showArticleModal(item));

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
    link.addEventListener("click", (e) => e.stopPropagation());
    article.appendChild(link);
  }

  return article;
}

async function updateChart(days) {
  if (!currentTickers.length) return;
  
  try {
    const ticker = currentTickers[0]; // Show first ticker for now
    const response = await fetch(`/api/history/${ticker}?days=${days}`);
    const data = await response.json();
    
    if (data.timestamps && data.timestamps.length > 0) {
      renderChart(data);
    }
  } catch (error) {
    console.error("Failed to load chart data:", error);
  }
}

function renderChart(data) {
  const ctx = sentimentChart.getContext("2d");
  
  if (chartInstance) {
    chartInstance.destroy();
  }
  
  const labels = data.timestamps.map(ts => new Date(ts).toLocaleDateString());
  
  chartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels.reverse(),
      datasets: [
        {
          label: "Bull Score",
          data: data.bull_scores.reverse(),
          borderColor: "rgba(28, 139, 77, 1)",
          backgroundColor: "rgba(28, 139, 77, 0.1)",
          tension: 0.4,
          fill: true,
        },
        {
          label: "Bear Score",
          data: data.bear_scores.reverse(),
          borderColor: "rgba(183, 67, 50, 1)",
          backgroundColor: "rgba(183, 67, 50, 0.1)",
          tension: 0.4,
          fill: true,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: "index",
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
        tooltip: {
          backgroundColor: "rgba(255, 252, 245, 0.95)",
          titleColor: "#14231b",
          bodyColor: "#526359",
          borderColor: "rgba(20, 35, 27, 0.1)",
          borderWidth: 1,
          padding: 12,
          displayColors: true,
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 1,
          ticks: {
            callback: function(value) {
              return (value * 100).toFixed(0) + "%";
            }
          }
        }
      }
    }
  });
}

// ============================================
// STOCK TICKER TAPE
// ============================================

const TOP_STOCKS = [
  'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 
  'TSLA', 'META', 'BRK.B', 'V', 'JPM',
  'WMT', 'MA', 'PG', 'HD', 'DIS',
  'NFLX', 'PYPL', 'INTC', 'CSCO', 'AMD'
];

async function fetchStockPrices() {
  try {
    const response = await fetch('/api/ticker-prices', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tickers: TOP_STOCKS })
    });
    
    if (response.ok) {
      const data = await response.json();
      updateTickerTape(data.prices);
    } else {
      console.warn('Ticker price fetch failed, using mock data');
      updateTickerTape(generateMockPrices());
    }
  } catch (error) {
    console.warn('Ticker error:', error.message);
    updateTickerTape(generateMockPrices());
  }
}

function generateMockPrices() {
  return TOP_STOCKS.map(ticker => ({
    symbol: ticker,
    price: (Math.random() * 500 + 50).toFixed(2),
    change: (Math.random() * 10 - 5).toFixed(2),
    changePercent: (Math.random() * 5 - 2.5).toFixed(2)
  }));
}

function updateTickerTape(prices) {
  if (!prices || prices.length === 0) return;
  
  // Duplicate the array to create seamless loop
  const duplicatedPrices = [...prices, ...prices];
  
  const html = duplicatedPrices.map(stock => {
    const changeNum = parseFloat(stock.change || stock.changePercent || 0);
    const changeClass = changeNum > 0 ? 'positive' : changeNum < 0 ? 'negative' : 'neutral';
    const changeSymbol = changeNum > 0 ? '▲' : changeNum < 0 ? '▼' : '●';
    const changeText = `${changeSymbol} ${Math.abs(changeNum).toFixed(2)}%`;
    
    return `
      <div class="ticker-item">
        <span class="ticker-symbol">${stock.symbol}</span>
        <span class="ticker-price">$${stock.price}</span>
        <span class="ticker-change ${changeClass}">${changeText}</span>
      </div>
    `;
  }).join('');
  
  tickerTrack.innerHTML = html;
}

// Initialize ticker on page load
fetchStockPrices();

// Refresh ticker every 60 seconds
tickerRefreshInterval = setInterval(fetchStockPrices, 60000);
