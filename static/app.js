const form = document.getElementById('generateForm');
const subjectInput = document.getElementById('subject');
const urlsInput = document.getElementById('urls');
const generateButton = document.getElementById('generateButton');
const loadingState = document.getElementById('loadingState');
const notice = document.getElementById('notice');
const results = document.getElementById('results');
const emptyState = document.getElementById('emptyState');
let currentPack = null;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}
function showNotice(message, success=false) {
  notice.textContent = message;
  notice.className = `notice${success ? ' success' : ''}`;
  notice.hidden = false;
}
function hideNotice() { notice.hidden = true; }

const savedTheme = localStorage.getItem('syllabus-studio-theme');
if (savedTheme === 'dark') document.documentElement.dataset.theme = 'dark';
function updateThemeButton() {
  const dark = document.documentElement.dataset.theme === 'dark';
  document.getElementById('themeIcon').textContent = dark ? '☀' : '☾';
  document.getElementById('themeToggle').setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
}
updateThemeButton();
document.getElementById('themeToggle').addEventListener('click', () => {
  const dark = document.documentElement.dataset.theme !== 'dark';
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  localStorage.setItem('syllabus-studio-theme', dark ? 'dark' : 'light');
  updateThemeButton();
});

document.getElementById('clearButton').addEventListener('click', () => {
  form.reset(); currentPack = null; results.hidden = true; results.innerHTML = '';
  emptyState.hidden = false; hideNotice(); window.scrollTo({top: 0, behavior: 'smooth'});
});

form.addEventListener('submit', async event => {
  event.preventDefault();
  hideNotice();
  const subject = subjectInput.value.trim();
  const urls = urlsInput.value.split(/\r?\n/).map(url => url.trim()).filter(Boolean);
  if (!subject) return showNotice('Please enter a subject name.');
  if (!urls.length) return showNotice('Add at least one educational website URL.');
  if (urls.length > 10) return showNotice('Please enter no more than 10 URLs.');
  if (urls.some(url => !/^https?:\/\//i.test(url))) return showNotice('Each URL must begin with http:// or https://.');
  generateButton.disabled = true; loadingState.hidden = false; emptyState.hidden = true;
  results.hidden = true;
  try {
    const response = await fetch('/api/generate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({subject, urls})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'The study pack could not be generated.');
    currentPack = data;
    if (!data.success) {
      renderSources(data.sources || []);
      results.innerHTML = `<div class="result-card wide"><h3 class="card-title">Source verification</h3>${sourceMarkup(data.sources || [])}</div>`;
      results.hidden = false;
      showNotice(data.error || 'No sources could be processed. Please check the URLs and try again.');
      results.scrollIntoView({behavior:'smooth', block:'start'});
      return;
    }
    renderResults(data);
    showNotice('Your study pack is ready. Results are based on the content extracted from the sources shown below.', true);
    results.scrollIntoView({behavior:'smooth', block:'start'});
  } catch (error) {
    showNotice(error.message || 'A network error occurred. Please try again.');
    emptyState.hidden = false;
  } finally {
    generateButton.disabled = false; loadingState.hidden = true;
  }
});

function sourceMarkup(sources) {
  return sources.map(source => `<div class="source"><div class="source-url">${escapeHtml(source.url)}</div><span class="source-status ${source.ok?'ok':'bad'}">${source.ok?'✓ Processed':'✕ Not processed'}</span><div class="source-detail">${escapeHtml(source.message || source.title || '')}${source.title ? ` · ${escapeHtml(source.title)}` : ''}</div></div>`).join('') || '<p class="method">No source status is available.</p>';
}
function renderSources(sources) { return sourceMarkup(sources); }
function renderResults(data) {
  const stats = data.stats || {};
  const units = (data.syllabus || []).map((unit, index) => `<div class="unit"><h4>Unit ${index+1} · ${escapeHtml(unit.title)}</h4><div class="topic-list">${(unit.topics||[]).map(topic => `<span class="topic-chip">${escapeHtml(topic.name)}</span>`).join('')}</div></div>`).join('');
  const relevance = (data.syllabus || []).flatMap(unit => unit.topics || []).map(topic => `<div class="relevance-row"><div class="relevance-label"><span>${escapeHtml(topic.name)}</span><span>${Math.max(0,Math.min(100,Number(topic.relevance)||0))}%</span></div><div class="bar"><i style="width:${Math.max(0,Math.min(100,Number(topic.relevance)||0))}%"></i></div></div>`).join('');
  const questions = (data.questions || []).map((item, index) => `<div class="question-card"><div class="question-top"><span class="q-number">${String(index+1).padStart(2,'0')}</span><div class="q-content"><div class="q-text">${escapeHtml(item.question)}</div><div class="q-topic">TOPIC · ${escapeHtml(item.topic)}</div><button class="reveal-btn" type="button" data-answer="${index}" aria-expanded="false">Reveal answer</button><div class="answer" id="answer-${index}" hidden>${escapeHtml(item.answer)}</div></div></div></div>`).join('');
  results.innerHTML = `
    <div class="results-heading"><div><div class="results-kicker">YOUR STUDY PACK</div><h2>${escapeHtml(data.subject)}</h2><p>Generated from the publicly accessible page content we could extract.</p></div></div>
    <div class="export-row"><button class="export-btn" data-export="syllabus">↓ Export syllabus PDF</button><button class="export-btn" data-export="qa">↓ Export Q&amp;A PDF</button><button class="export-btn" data-export="complete">↓ Export complete pack</button></div>
    <div class="stats"><div class="stat"><strong>${Number(stats.units)||0}</strong><span>Learning units</span></div><div class="stat"><strong>${Number(stats.questions)||10}</strong><span>Practice questions</span></div><div class="stat"><strong>${Number(stats.sources)||0}/${(data.sources||[]).length}</strong><span>Sources processed</span></div><div class="stat"><strong>${Number(stats.words)||0}</strong><span>Words analyzed</span></div></div>
    <div class="result-grid">
      <article class="result-card"><h3 class="card-title"><span class="mini-icon">▤</span>Generated syllabus</h3><div class="method">${escapeHtml(data.method)}</div>${units||'<p class="method">No units could be generated from this content.</p>'}</article>
      <article class="result-card"><h3 class="card-title"><span class="mini-icon">◒</span>Estimated content relevance</h3><p class="method">Estimated keyword frequency in extracted text—not a measure of verified academic importance.</p>${relevance||'<p class="method">No topics available.</p>'}</article>
      <article class="result-card wide"><div class="qa-head"><h3 class="card-title"><span class="mini-icon">✎</span>Practice questions <span class="q-topic">· exactly 10</span></h3><button class="global-toggle" id="globalAnswers" type="button">Reveal all answers</button></div><div>${questions}</div></article>
      <article class="result-card wide"><h3 class="card-title"><span class="mini-icon">◎</span>Source verification</h3>${sourceMarkup(data.sources||[])}</article>
    </div>`;
  results.hidden = false;
  results.querySelectorAll('.reveal-btn').forEach(button => button.addEventListener('click', () => {
    const answer = document.getElementById(`answer-${button.dataset.answer}`);
    const opening = answer.hidden; answer.hidden = !opening;
    button.textContent = opening ? 'Hide answer' : 'Reveal answer'; button.setAttribute('aria-expanded', String(opening));
    updateGlobalButton();
  }));
  results.querySelector('#globalAnswers').addEventListener('click', () => {
    const buttons = [...results.querySelectorAll('.reveal-btn')];
    const reveal = buttons.some(button => document.getElementById(`answer-${button.dataset.answer}`).hidden);
    buttons.forEach(button => {
      document.getElementById(`answer-${button.dataset.answer}`).hidden = !reveal;
      button.textContent = reveal ? 'Hide answer' : 'Reveal answer';
      button.setAttribute('aria-expanded', String(reveal));
    });
    updateGlobalButton();
  });
  results.querySelectorAll('[data-export]').forEach(button => button.addEventListener('click', () => exportPdf(button.dataset.export, button)));
}
function updateGlobalButton() {
  const button = results.querySelector('#globalAnswers');
  if (!button) return;
  const answers = [...results.querySelectorAll('.answer')];
  button.textContent = answers.length && answers.every(answer => !answer.hidden) ? 'Hide all answers' : 'Reveal all answers';
}
async function exportPdf(kind, button) {
  if (!currentPack?.success) return showNotice('Create a successful study pack before exporting.');
  button.disabled = true; const oldText = button.textContent; button.textContent = 'Preparing PDF…';
  try {
    const response = await fetch(`/api/export/${kind}`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(currentPack)});
    if (!response.ok) { const data = await response.json(); throw new Error(data.error || 'PDF export failed.'); }
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || `syllabus-studio-${kind}.pdf`;
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = filename; link.click(); URL.revokeObjectURL(link.href);
    showNotice('Your PDF download is ready.', true);
  } catch (error) { showNotice(error.message); }
  finally { button.disabled = false; button.textContent = oldText; }
}
