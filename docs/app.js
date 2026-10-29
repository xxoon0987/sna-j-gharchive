const ROLE = {
  issues: { label: 'Issue', color: '#72d7c4' },
  discussion: { label: '討論', color: '#d5e58d' },
  pulls: { label: 'PR', color: '#f0b08f' },
  reviews: { label: 'Review', color: '#7aa6c4' },
};
const ROLE_ORDER = ['issues', 'discussion', 'pulls', 'reviews'];
const number = new Intl.NumberFormat('zh-TW');
const SVG_NS = 'http://www.w3.org/2000/svg';
let DATA;
let activeLayer = 'all';
let selected = null;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);
}

function svg(tag, attributes = {}, content = null) {
  const element = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
  if (content !== null) element.textContent = content;
  return element;
}

function renderSummary() {
  document.getElementById('statRepos').textContent = DATA.metadata.repoCount;
  document.getElementById('statRows').textContent = number.format(DATA.metadata.rawRows);
  document.getElementById('statActors').textContent = number.format(DATA.views.all.actors);
  document.getElementById('statBridges').textContent = number.format(DATA.views.all.multiRepoActors);
  document.getElementById('crossRoleCount').textContent = DATA.overlap.crossRoleBridgeActors;
  document.getElementById('directedReviews').textContent = number.format(DATA.reviewNetwork.directedEvents);
  document.getElementById('reviewPairs').textContent = number.format(DATA.reviewNetwork.reviewerAuthorPairs);

  document.getElementById('repoChips').innerHTML = DATA.repositories.map((repo, i) =>
    `<a class="repo-chip" href="${repo.url}" target="_blank" rel="noopener noreferrer"><b>${String(i + 1).padStart(2, '0')}</b>${escapeHtml(repo.label)}<span class="external" aria-hidden="true">↗</span></a>`
  ).join('');
  document.getElementById('eventLayers').innerHTML = ROLE_ORDER.map(key =>
    `<div class="event-line"><i class="event-dot" style="background:${ROLE[key].color}"></i><strong>${ROLE[key].label}</strong><span class="event-count">${number.format(DATA.views[key].events)} EVENTS</span></div>`
  ).join('');
  document.getElementById('limitations').innerHTML = DATA.definitions.limitations.map(item => `<li>${escapeHtml(item)}</li>`).join('');
}

function renderOverlap() {
  const comparisons = [
    ['issues-pulls', 'Issue ↔ PR'],
    ['issues-reviews', 'Issue ↔ Review'],
    ['pulls-reviews', 'PR ↔ Review'],
  ];
  document.getElementById('overlapList').innerHTML = comparisons.map(([key, label]) => {
    const value = DATA.overlap.actorJaccard[key];
    return `<div class="overlap-item"><span>${label}</span><div class="overlap-track" title="Jaccard ${value}"><i style="width:${value * 100}%"></i></div><b>${value.toFixed(3)}</b></div>`;
  }).join('');
}

function renderCentrality() {
  const core = DATA.views.all.centrality;
  document.getElementById('coreActors').textContent = core.coreActors;
  document.getElementById('coreRepos').textContent = core.coreRepos;
  document.getElementById('coreEdges').textContent = core.coreEdges;
  const counts = DATA.overlap.actorOverlapCounts['issues-pulls'];
  document.getElementById('overlapIntersection').textContent = counts.intersection;
  document.getElementById('overlapUnion').textContent = counts.union;
  document.getElementById('overlapWorked').textContent = `${counts.intersection} ÷ ${counts.union} = ${DATA.overlap.actorJaccard['issues-pulls'].toFixed(3)}`;
  const metrics = [
    ['degree', 'DEGREE', '直接連結數', '帳號連到幾個選定專案；同一專案事件再多也只算一條邊。'],
    ['closeness', 'CLOSENESS', '接近中心度', '到這張核心網絡其他節點的最短路徑越短，分數越高。'],
    ['betweenness', 'BETWEENNESS', '中介中心度', '位於其他節點最短路徑中間的程度，描述橋接位置。'],
    ['eigenvector', 'EIGENVECTOR', '特徵向量中心度', 'A x = λ x；連到結構上也重要的節點，分數較高。帳號最高分縮為 1。'],
  ];
  document.getElementById('centralityGrid').innerHTML = metrics.map(([key, code, title, description]) =>
    `<article class="centrality-card"><span class="metric-code">${code}</span><h4>${title}</h4><p>${description}</p><ol>${core.rankings[key].map(item => `<li><span>${escapeHtml(item.actor)}</span><b>${key === 'degree' ? item.score : item.score.toFixed(3)}</b></li>`).join('')}</ol></article>`
  ).join('');
}

function renderWeeks() {
  const rows = DATA.weeks.map(week => {
    const days = (new Date(`${week.endExclusive}T00:00:00Z`) - new Date(`${week.start}T00:00:00Z`)) / 86400000;
    const average = ROLE_ORDER.reduce((sum, key) => sum + week.roles[key], 0) / days;
    return { ...week, days, average };
  });
  const maximum = Math.max(...rows.map(row => row.average));
  document.getElementById('weeklyChart').innerHTML = rows.map((row, i) => {
    const segments = ROLE_ORDER.map(key => {
      const width = row.roles[key] / row.days / maximum * 100;
      return `<i style="width:${width}%;background:${ROLE[key].color}" title="${ROLE[key].label}：${Math.round(row.roles[key] / row.days)} 筆/日"></i>`;
    }).join('');
    return `<div class="week-row"><span>${i === 3 ? '01/22–31' : row.start.slice(5) + '–' + String(Number(row.endExclusive.slice(-2)) - 1).padStart(2, '0')}</span><div class="week-track">${segments}</div><b>${Math.round(row.average)}/日</b></div>`;
  }).join('') + `<div class="week-legend">${ROLE_ORDER.map(key => `<span><i style="background:${ROLE[key].color}"></i>${ROLE[key].label}</span>`).join('')}</div>`;
}

function updateGraphHighlight() {
  const graph = document.getElementById('networkGraph');
  graph.querySelectorAll('.graph-edge').forEach(edge => {
    edge.classList.toggle('active', Boolean(selected) && (
      (selected.type === 'repo' && edge.dataset.repo === selected.id) ||
      (selected.type === 'actor' && edge.dataset.actor === selected.id)
    ));
  });
  graph.querySelectorAll('.graph-repo,.graph-actor').forEach(node => {
    node.classList.toggle('selected', Boolean(selected) && node.dataset.type === selected.type && node.dataset.id === selected.id);
  });
}

function choose(type, id) {
  selected = { type, id };
  updateGraphHighlight();
  renderDetail();
}

function addKeyboardActivation(node, action) {
  node.addEventListener('click', action);
  node.addEventListener('keydown', event => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      action();
    }
  });
}

function renderGraph(view) {
  const graph = document.getElementById('networkGraph');
  graph.replaceChildren();
  const repos = DATA.repositories;
  const people = view.sampleActors;
  const repoY = Object.fromEntries(repos.map((repo, i) => [repo.id, 74 + i * 59]));
  const actorY = Object.fromEntries(people.map((actor, i) => [actor.id, people.length === 1 ? 335 : 48 + i * 595 / (people.length - 1)]));

  const backdrop = svg('g');
  backdrop.append(svg('line', { x1: 574, y1: 35, x2: 574, y2: 650, stroke: '#365259', 'stroke-width': 1, 'stroke-dasharray': '3 8' }));
  backdrop.append(svg('text', { x: 574, y: 28, 'text-anchor': 'middle', fill: '#72938f', 'font-size': 10, 'font-family': 'DM Mono, monospace', 'letter-spacing': 2 }, 'PARTICIPATION'));
  graph.append(backdrop);

  const lines = svg('g');
  for (const actor of people) {
    for (const repo of actor.repos) {
      const path = svg('path', {
        d: `M 282 ${repoY[repo]} C 510 ${repoY[repo]}, 618 ${actorY[actor.id]}, 842 ${actorY[actor.id]}`,
        fill: 'none', class: 'graph-edge',
      });
      path.dataset.actor = actor.id;
      path.dataset.repo = repo;
      lines.append(path);
    }
  }
  graph.append(lines);

  const repositoryNodes = svg('g');
  repos.forEach(repo => {
    const group = svg('g', { class: 'graph-repo', role: 'button', tabindex: '0', 'aria-label': `${repo.label}，${view.repoActors[repo.id]} 位參與帳號` });
    group.dataset.type = 'repo';
    group.dataset.id = repo.id;
    const y = repoY[repo.id];
    group.append(svg('text', { x: 246, y: y + 6, 'text-anchor': 'end' }, repo.label));
    group.append(svg('circle', { cx: 269, cy: y, r: 10 }));
    group.append(svg('text', { x: 291, y: y + 4, class: 'repo-count' }, `${view.repoActors[repo.id]} accounts`));
    addKeyboardActivation(group, () => choose('repo', repo.id));
    repositoryNodes.append(group);
  });
  graph.append(repositoryNodes);

  const actorNodes = svg('g');
  people.forEach(actor => {
    const y = actorY[actor.id];
    const group = svg('g', { class: 'graph-actor', role: 'button', tabindex: '0', 'aria-label': `${actor.id}，參與 ${actor.repos.length} 個專案` });
    group.dataset.type = 'actor';
    group.dataset.id = actor.id;
    group.append(svg('circle', { cx: 853, cy: y, r: 5.5 + Math.min(4, actor.repos.length * .4) }));
    group.append(svg('text', { x: 870, y: y + 4 }, actor.id));
    group.append(svg('title', {}, `${actor.id} · ${actor.repos.length} repos · ${actor.events} events`));
    addKeyboardActivation(group, () => choose('actor', actor.id));
    actorNodes.append(group);
  });
  graph.append(actorNodes);
  updateGraphHighlight();
}

function roleBars(roles) {
  const max = Math.max(1, ...ROLE_ORDER.map(key => roles[key] || 0));
  return `<div class="role-bars">${ROLE_ORDER.map(key => `<div class="role-bar"><span>${ROLE[key].label}</span><div class="role-bar-track"><i style="width:${(roles[key] || 0) / max * 100}%;background:${ROLE[key].color}"></i></div><b>${number.format(roles[key] || 0)}</b></div>`).join('')}</div>`;
}

function renderDetail() {
  const panel = document.getElementById('detailPanel');
  const kicker = '<span class="detail-kicker">NODE INSPECTOR</span>';
  if (!selected) {
    panel.innerHTML = `${kicker}<div class="detail-empty"><span class="detail-symbol">✳</span><h3>選一個節點</h3><p>點選專案或帳號，就能看見它在這個網絡中的位置與事件組成。</p></div>`;
    return;
  }
  const view = DATA.views[activeLayer];
  if (selected.type === 'repo') {
    const repo = DATA.repositories.find(item => item.id === selected.id);
    if (!repo) return;
    const connected = view.edges.filter(edge => edge.source === repo.id || edge.target === repo.id)
      .sort((a, b) => b.shared - a.shared).slice(0, 3);
    panel.innerHTML = `${kicker}<h3 class="detail-title">${escapeHtml(repo.label)}</h3><p class="detail-sub">${escapeHtml(repo.id)}</p><div class="detail-row"><span>所選類型的參與帳號</span><strong>${number.format(view.repoActors[repo.id])}</strong></div><div class="detail-row"><span>全月各類事件總數</span><strong>${number.format(repo.events)}</strong></div><hr class="detail-rule" /><span class="card-index">全部事件組成</span>${roleBars(repo.roles)}<hr class="detail-rule" /><span class="card-index">共同參與者最多的專案</span><div class="repo-list">${connected.map(edge => { const other = edge.source === repo.id ? edge.target : edge.source; const label = DATA.repositories.find(item => item.id === other).label; return `<span>${escapeHtml(label)} · ${edge.shared}</span>`; }).join('') || '<span>本類型無共同參與者</span>'}</div><a class="detail-link" href="${repo.url}" target="_blank" rel="noopener noreferrer">前往 GitHub 專案 ↗</a>`;
    return;
  }
  const actor = view.sampleActors.find(item => item.id === selected.id);
  if (!actor) {
    selected = null;
    renderDetail();
    return;
  }
  const labels = actor.repos.map(id => DATA.repositories.find(repo => repo.id === id).label);
  const allMetrics = activeLayer === 'all' && actor.centrality
    ? `<div class="detail-row"><span>專案連結數 · degree</span><strong>${actor.centrality.degree}</strong></div><div class="detail-row"><span>接近中心度</span><strong>${actor.centrality.closeness.toFixed(3)}</strong></div><div class="detail-row"><span>中介中心度</span><strong>${actor.centrality.betweenness.toFixed(3)}</strong></div><div class="detail-row"><span>特徵向量中心度</span><strong>${actor.centrality.eigenvector.toFixed(3)}</strong></div>`
    : `<div class="detail-row"><span>所選類型二模核心中介中心度</span><strong>${actor.betweenness.toFixed(3)}</strong></div>`;
  panel.innerHTML = `${kicker}<h3 class="detail-title">${escapeHtml(actor.id)}</h3><p class="detail-sub">公開 GitHub 帳號 · 示例節點</p><div class="detail-row"><span>本圖參與專案</span><strong>${actor.repos.length}</strong></div><div class="detail-row"><span>所選類型事件</span><strong>${number.format(actor.events)}</strong></div>${allMetrics}<p class="detail-small">中心度只描述這張界定網絡的路徑位置，不衡量能力或貢獻價值。</p><hr class="detail-rule" /><span class="card-index">全月各類事件</span>${roleBars(actor.roles)}<hr class="detail-rule" /><span class="card-index">參與專案</span><div class="repo-list">${labels.map(label => `<span>${escapeHtml(label)}</span>`).join('')}</div><a class="detail-link" href="https://github.com/${encodeURIComponent(actor.id)}" target="_blank" rel="noopener noreferrer">查看公開 GitHub 帳號 ↗</a>`;
}

function renderExplorer() {
  const view = DATA.views[activeLayer];
  document.querySelectorAll('#layerFilters button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.layer === activeLayer)));
  document.getElementById('viewEvents').textContent = number.format(view.events);
  document.getElementById('viewActors').textContent = number.format(view.actors);
  document.getElementById('viewBridgeCount').textContent = number.format(view.multiRepoActors);
  if (selected?.type === 'actor' && !view.sampleActors.some(actor => actor.id === selected.id)) selected = null;
  renderGraph(view);
  renderDetail();
}

async function init() {
  try {
    const response = await fetch('./data.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    DATA = await response.json();
    renderSummary();
    renderOverlap();
    renderCentrality();
    renderWeeks();
    renderExplorer();
  } catch (error) {
    document.getElementById('networkGraph').setAttribute('aria-label', '研究資料載入失敗');
    document.getElementById('detailPanel').innerHTML = `<span class="detail-kicker">DATA UNAVAILABLE</span><h3 class="detail-title">資料暫時無法載入</h3><p class="detail-small">請確認網站是透過 HTTP 伺服器開啟，並重新整理頁面。</p>`;
    console.error('Failed to load research data:', error);
  }
}

document.getElementById('layerFilters').addEventListener('click', event => {
  const button = event.target.closest('button[data-layer]');
  if (!button || !DATA) return;
  activeLayer = button.dataset.layer;
  renderExplorer();
});
document.getElementById('resetSelection').addEventListener('click', () => { selected = null; updateGraphHighlight(); renderDetail(); });
document.getElementById('fullscreenBtn').addEventListener('click', async () => {
  if (document.fullscreenElement) await document.exitFullscreen();
  else await document.documentElement.requestFullscreen();
});
document.addEventListener('fullscreenchange', () => {
  document.querySelector('#fullscreenBtn span').textContent = document.fullscreenElement ? '離開全螢幕' : '簡報模式';
});
init();
