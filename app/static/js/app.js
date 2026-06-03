/**
 * StockRadar — app.js
 * Handles: dark mode, auto-refresh, sparklines, stock detail charts, period selector
 */

/* ================================================================
   1. DARK MODE
   ================================================================ */
(function initDarkMode() {
  const stored = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const theme = stored || (prefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', theme);
  document.body.setAttribute('data-theme', theme);
})();

function toggleDarkMode() {
  const current = document.body.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  document.body.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateDarkModeIcon(next);
}

function updateDarkModeIcon(theme) {
  const btn = document.getElementById('dark-mode-toggle');
  if (!btn) return;
  btn.innerHTML = theme === 'dark'
    ? '<i class="fa-solid fa-sun"></i>'
    : '<i class="fa-solid fa-moon"></i>';
  btn.title = theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
}

document.addEventListener('DOMContentLoaded', () => {
  const theme = document.body.getAttribute('data-theme') || 'light';
  updateDarkModeIcon(theme);
  const toggleBtn = document.getElementById('dark-mode-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', toggleDarkMode);
  }
});

/* ================================================================
   2. AUTO-REFRESH WITH COUNTDOWN
   ================================================================ */
let refreshCountdown = 60;
let refreshTimer = null;
let isRefreshing = false;

function startAutoRefresh() {
  if (!window.REFRESH_API_URL) return;
  refreshTimer = setInterval(() => {
    refreshCountdown--;
    const el = document.getElementById('refresh-countdown');
    if (el) el.textContent = refreshCountdown;
    if (refreshCountdown <= 0) {
      refreshCountdown = 60;
      doRefresh();
    }
  }, 1000);
}

async function doRefresh() {
  if (isRefreshing || !window.REFRESH_API_URL) return;
  isRefreshing = true;
  const spinner = document.getElementById('refresh-spinner');
  if (spinner) spinner.classList.remove('d-none');

  try {
    const resp = await fetch(window.REFRESH_API_URL);
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    updateDOMWithRefreshData(data);

    const updEl = document.getElementById('last-updated');
    if (updEl) {
      updEl.textContent = new Date().toLocaleTimeString('ko-KR');
    }
  } catch (e) {
    console.warn('Auto-refresh failed:', e);
  } finally {
    isRefreshing = false;
    if (spinner) spinner.classList.add('d-none');
  }
}

function updateDOMWithRefreshData(data) {
  // Update index cards
  if (data.indices && Array.isArray(data.indices)) {
    data.indices.forEach(idx => {
      const el = document.getElementById('idx-close-' + idx.name.replace(/[^a-z0-9]/gi, '_'));
      if (el) el.textContent = Number(idx.close).toLocaleString();
      const pctEl = document.getElementById('idx-pct-' + idx.name.replace(/[^a-z0-9]/gi, '_'));
      if (pctEl) {
        const pct = idx.change_pct;
        pctEl.className = 'badge ' + (pct > 0 ? 'bg-danger' : pct < 0 ? 'bg-primary' : 'bg-secondary');
        const arrow = pct > 0 ? '▲' : pct < 0 ? '▼' : '';
        pctEl.textContent = arrow + ' ' + Math.abs(pct).toFixed(2) + '%';
      }
    });
  }

  // Update gainers/losers tbody
  if (data.gainers) updateMoversTable('gainers-tbody', data.gainers, window.MARKET_TYPE);
  if (data.losers)  updateMoversTable('losers-tbody',  data.losers,  window.MARKET_TYPE);

  // Update volume leaders
  if (data.vol_leaders) updateMoversTable('vol-tbody', data.vol_leaders, window.MARKET_TYPE);

  // Update breadth counters
  if (data.breadth) {
    const { advancers, decliners, unchanged } = data.breadth;
    const aEl = document.getElementById('breadth-adv');
    const dEl = document.getElementById('breadth-dec');
    const uEl = document.getElementById('breadth-unc');
    if (aEl) aEl.textContent = advancers;
    if (dEl) dEl.textContent = decliners;
    if (uEl) uEl.textContent = unchanged;

    // Update breadth donut chart
    if (window._breadthChart) {
      window._breadthChart.data.datasets[0].data = [advancers, decliners, unchanged];
      window._breadthChart.update();
    }
  }

  // Fear & Greed
  if (data.fear_greed) {
    const fgLabel = document.getElementById('fg-label');
    const fgVix   = document.getElementById('fg-vix');
    if (fgLabel) fgLabel.textContent = data.fear_greed.label;
    if (fgVix)   fgVix.textContent   = data.fear_greed.value ? 'VIX: ' + data.fear_greed.value : '';
  }
}

function updateMoversTable(tbodyId, rows, marketType) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  tbody.innerHTML = rows.map(s => {
    const pct = s.change_pct;
    const badge = pct > 0
      ? `<span class="badge bg-danger">▲ ${pct}%</span>`
      : pct < 0
        ? `<span class="badge bg-primary">▼ ${Math.abs(pct)}%</span>`
        : `<span class="badge bg-secondary">0.00%</span>`;
    const vol = Number(s.volume).toLocaleString();
    const url = marketType === 'korean'
      ? `/stock/korean/${s.ticker}`
      : `/stock/us/${s.ticker}`;
    if (marketType === 'korean') {
      const price = Number(s.close).toLocaleString('ko-KR', {maximumFractionDigits: 0}) + '원';
      return `<tr class="clickable-row" onclick="location.href='${url}'">
        <td><span class="fw-semibold">${s.name}</span><br><small class="text-muted">${s.ticker}</small></td>
        <td>${price}</td>
        <td>${badge}</td>
        <td class="text-muted small">${vol}</td>
      </tr>`;
    } else {
      return `<tr class="clickable-row" onclick="location.href='${url}'">
        <td><span class="fw-semibold">${s.ticker}</span></td>
        <td>$${Number(s.close).toFixed(2)}</td>
        <td>${badge}</td>
        <td class="text-muted small">${vol}</td>
      </tr>`;
    }
  }).join('') || '<tr><td colspan="4" class="text-center text-muted py-3">데이터 없음</td></tr>';
}

/* ================================================================
   3. SPARKLINES
   ================================================================ */
function initSparklines() {
  document.querySelectorAll('[data-sparkline]').forEach(canvas => {
    try {
      const raw = canvas.getAttribute('data-sparkline');
      const values = JSON.parse(raw);
      if (!values || values.length === 0) return;

      const first = values[0];
      const last  = values[values.length - 1];
      const color = last >= first ? 'rgba(220,53,69,0.9)' : 'rgba(13,110,253,0.9)';
      const fillColor = last >= first ? 'rgba(220,53,69,0.1)' : 'rgba(13,110,253,0.1)';

      new Chart(canvas, {
        type: 'line',
        data: {
          labels: values.map((_, i) => i),
          datasets: [{
            data: values,
            borderColor: color,
            backgroundColor: fillColor,
            borderWidth: 1.5,
            fill: true,
            pointRadius: 0,
            tension: 0.3,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: {
            x: { display: false },
            y: { display: false }
          },
          animation: false,
        }
      });
    } catch (e) {
      // ignore bad data
    }
  });
}

/* ================================================================
   4. BREADTH DONUT CHART
   ================================================================ */
function initBreadthChart(advancers, decliners, unchanged) {
  const canvas = document.getElementById('breadthChart');
  if (!canvas) return;
  window._breadthChart = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['상승', '하락', '보합'],
      datasets: [{
        data: [advancers, decliners, unchanged],
        backgroundColor: ['#dc3545', '#0d6efd', '#6c757d'],
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { size: 11 }, padding: 8 }
        },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.parsed}`
          }
        }
      }
    }
  });
}

/* ================================================================
   5. STOCK DETAIL PAGE — CHARTS
   ================================================================ */

const _detailCharts = {};

function getChartColors() {
  const isDark = document.body.getAttribute('data-theme') === 'dark';
  return {
    grid:      isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
    text:      isDark ? '#8b949e' : '#6c757d',
    close:     '#0d6efd',
    ma5:       '#fd7e14',
    ma20:      '#0dcaf0',
    ma60:      '#6f42c1',
    bbFill:    isDark ? 'rgba(13,110,253,0.06)' : 'rgba(13,110,253,0.08)',
    bbLine:    'rgba(13,110,253,0.35)',
    volUp:     'rgba(220,53,69,0.7)',
    volDown:   'rgba(13,110,253,0.7)',
    rsi:       '#198754',
    macd:      '#0d6efd',
    signal:    '#fd7e14',
    histPos:   'rgba(220,53,69,0.6)',
    histNeg:   'rgba(13,110,253,0.6)',
    refLine70: 'rgba(220,53,69,0.5)',
    refLine30: 'rgba(25,135,84,0.5)',
    refLine0:  'rgba(108,117,125,0.4)',
  };
}

function destroyChart(id) {
  if (_detailCharts[id]) {
    _detailCharts[id].destroy();
    delete _detailCharts[id];
  }
}

function buildPriceChart(data, colors) {
  destroyChart('price');
  const canvas = document.getElementById('priceChart');
  if (!canvas) return;

  // Build Bollinger band area as two datasets with fill between
  _detailCharts['price'] = new Chart(canvas, {
    type: 'line',
    data: {
      labels: data.dates,
      datasets: [
        {
          label: 'BB Upper',
          data: data.bb_upper,
          borderColor: colors.bbLine,
          borderWidth: 1,
          borderDash: [4, 3],
          pointRadius: 0,
          fill: '+1',
          backgroundColor: colors.bbFill,
          tension: 0.2,
          order: 5,
        },
        {
          label: 'BB Lower',
          data: data.bb_lower,
          borderColor: colors.bbLine,
          borderWidth: 1,
          borderDash: [4, 3],
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          order: 6,
        },
        {
          label: 'Close',
          data: data.close,
          borderColor: colors.close,
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          tension: 0.1,
          order: 1,
        },
        {
          label: 'MA5',
          data: data.ma5,
          borderColor: colors.ma5,
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          order: 2,
        },
        {
          label: 'MA20',
          data: data.ma20,
          borderColor: colors.ma20,
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          order: 3,
        },
        {
          label: 'MA60',
          data: data.ma60,
          borderColor: colors.ma60,
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          order: 4,
        },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          labels: { font: { size: 11 }, color: colors.text }
        },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: {
          ticks: { maxTicksLimit: 8, color: colors.text, font: { size: 10 } },
          grid: { color: colors.grid }
        },
        y: {
          ticks: { color: colors.text, font: { size: 10 } },
          grid: { color: colors.grid }
        }
      }
    }
  });
}

function buildVolumeChart(data, colors) {
  destroyChart('volume');
  const canvas = document.getElementById('volumeChart');
  if (!canvas) return;

  const closes = data.close;
  const barColors = data.volume.map((_, i) => {
    if (i === 0) return colors.volUp;
    return (closes[i] || 0) >= (closes[i - 1] || 0) ? colors.volUp : colors.volDown;
  });

  _detailCharts['volume'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: data.dates,
      datasets: [{
        label: 'Volume',
        data: data.volume,
        backgroundColor: barColors,
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: colors.text, font: { size: 11 } } },
      },
      scales: {
        x: {
          ticks: { maxTicksLimit: 8, color: colors.text, font: { size: 10 } },
          grid: { color: colors.grid }
        },
        y: {
          ticks: {
            color: colors.text,
            font: { size: 10 },
            callback: v => v >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : v >= 1e3 ? (v / 1e3).toFixed(0) + 'K' : v
          },
          grid: { color: colors.grid }
        }
      }
    }
  });
}

function buildRSIChart(data, colors) {
  destroyChart('rsi');
  const canvas = document.getElementById('rsiChart');
  if (!canvas) return;

  _detailCharts['rsi'] = new Chart(canvas, {
    type: 'line',
    data: {
      labels: data.dates,
      datasets: [
        {
          label: 'RSI(14)',
          data: data.rsi,
          borderColor: colors.rsi,
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          tension: 0.2,
        },
        {
          label: 'Overbought (70)',
          data: data.dates.map(() => 70),
          borderColor: colors.refLine70,
          borderWidth: 1,
          borderDash: [5, 3],
          pointRadius: 0,
          fill: false,
          tension: 0,
        },
        {
          label: 'Oversold (30)',
          data: data.dates.map(() => 30),
          borderColor: colors.refLine30,
          borderWidth: 1,
          borderDash: [5, 3],
          pointRadius: 0,
          fill: false,
          tension: 0,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: colors.text, font: { size: 11 } } },
      },
      scales: {
        x: {
          ticks: { maxTicksLimit: 8, color: colors.text, font: { size: 10 } },
          grid: { color: colors.grid }
        },
        y: {
          min: 0, max: 100,
          ticks: { color: colors.text, font: { size: 10 }, stepSize: 20 },
          grid: { color: colors.grid }
        }
      }
    }
  });
}

function buildMACDChart(data, colors) {
  destroyChart('macd');
  const canvas = document.getElementById('macdChart');
  if (!canvas) return;

  _detailCharts['macd'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: data.dates,
      datasets: [
        {
          label: 'Histogram',
          data: data.macd_hist,
          backgroundColor: data.macd_hist.map(v =>
            v === null ? 'transparent' : v >= 0 ? colors.histPos : colors.histNeg
          ),
          borderWidth: 0,
          order: 3,
          type: 'bar',
        },
        {
          label: 'MACD',
          data: data.macd,
          borderColor: colors.macd,
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          order: 1,
          type: 'line',
        },
        {
          label: 'Signal',
          data: data.macd_signal,
          borderColor: colors.signal,
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          order: 2,
          type: 'line',
        },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: colors.text, font: { size: 11 } } },
      },
      scales: {
        x: {
          ticks: { maxTicksLimit: 8, color: colors.text, font: { size: 10 } },
          grid: { color: colors.grid }
        },
        y: {
          ticks: { color: colors.text, font: { size: 10 } },
          grid: { color: colors.grid }
        }
      }
    }
  });
}

function renderAllCharts(data) {
  const colors = getChartColors();
  buildPriceChart(data, colors);
  buildVolumeChart(data, colors);
  buildRSIChart(data, colors);
  buildMACDChart(data, colors);
}

async function loadChartData(period) {
  if (!window.CHART_API_URL) return;
  const url = window.CHART_API_URL + '?period=' + period;

  // Disable buttons, show loading
  document.querySelectorAll('.period-btn').forEach(b => {
    b.disabled = true;
    b.classList.remove('active', 'btn-primary');
    b.classList.add('btn-outline-secondary');
    if (b.dataset.period === period) {
      b.classList.add('active', 'btn-primary');
      b.classList.remove('btn-outline-secondary');
    }
  });

  const loadingEl = document.getElementById('chart-loading');
  if (loadingEl) loadingEl.classList.remove('d-none');

  try {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    renderAllCharts(data);
  } catch (e) {
    console.error('Chart load failed:', e);
  } finally {
    if (loadingEl) loadingEl.classList.add('d-none');
    document.querySelectorAll('.period-btn').forEach(b => b.disabled = false);
  }
}

/* ================================================================
   6. MARKET CLOCKS (Home page)
   ================================================================ */
function startMarketClocks() {
  const kstEl = document.getElementById('clock-kst');
  const estEl = document.getElementById('clock-est');
  if (!kstEl && !estEl) return;

  function tick() {
    const now = new Date();
    if (kstEl) {
      const kst = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Seoul' }));
      kstEl.textContent = kst.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    if (estEl) {
      const est = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));
      estEl.textContent = est.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    }
  }
  tick();
  setInterval(tick, 1000);
}

function checkMarketStatus() {
  const now = new Date();
  const utcH = now.getUTCHours();
  const utcM = now.getUTCMinutes();
  const utcTotalMin = utcH * 60 + utcM;
  const day = now.getUTCDay(); // 0=Sun, 6=Sat
  const isWeekday = day >= 1 && day <= 5;

  // KOSPI: 00:00-06:30 UTC
  const krOpen = isWeekday && utcTotalMin >= 0 && utcTotalMin < 390;
  // US: 13:30-20:00 UTC
  const usOpen = isWeekday && utcTotalMin >= 810 && utcTotalMin < 1200;

  const krEl = document.getElementById('kr-status');
  const usEl = document.getElementById('us-status');
  if (krEl) {
    krEl.textContent = krOpen ? '개장중' : '휴장';
    krEl.className   = krOpen ? 'market-status-open' : 'market-status-closed';
  }
  if (usEl) {
    usEl.textContent = usOpen ? 'Open' : 'Closed';
    usEl.className   = usOpen ? 'market-status-open' : 'market-status-closed';
  }
}

/* ================================================================
   7. DOMContentLoaded BOOTSTRAP
   ================================================================ */
document.addEventListener('DOMContentLoaded', () => {
  // Dark mode icon
  const theme = document.body.getAttribute('data-theme') || 'light';
  updateDarkModeIcon(theme);

  // Sparklines
  initSparklines();

  // Breadth donut (market pages)
  const breadthCanvas = document.getElementById('breadthChart');
  if (breadthCanvas) {
    const adv = parseInt(breadthCanvas.dataset.adv || 0, 10);
    const dec = parseInt(breadthCanvas.dataset.dec || 0, 10);
    const unc = parseInt(breadthCanvas.dataset.unc || 0, 10);
    initBreadthChart(adv, dec, unc);
  }

  // Auto-refresh
  startAutoRefresh();

  // Market clocks
  startMarketClocks();
  checkMarketStatus();
  setInterval(checkMarketStatus, 60000);

  // Period selector (stock detail page)
  document.querySelectorAll('.period-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      loadChartData(btn.dataset.period);
    });
  });

  // Initial chart load (stock detail page)
  if (window.CHART_API_URL && window.DEFAULT_PERIOD) {
    loadChartData(window.DEFAULT_PERIOD);
  }
});
