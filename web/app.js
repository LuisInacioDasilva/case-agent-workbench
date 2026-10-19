const output = document.querySelector('#output');
const textarea = document.querySelector('#case');
const button = document.querySelector('#analyze');
const queue = document.querySelector('#queue');
const actor = document.querySelector('#actor');
const reason = document.querySelector('#reason');

function block(className, text) {
  const element = document.createElement('div');
  element.className = className;
  element.textContent = text;
  return element;
}

async function decide(id, decision) {
  if (actor.value.trim().length < 2 || reason.value.trim().length < 5) {
    queue.prepend(block('meta', 'Informe seu nome e um motivo com pelo menos 5 caracteres.'));
    return;
  }
  const response = await fetch(`/api/reviews/${encodeURIComponent(id)}/decision`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, actor: actor.value.trim(), reason: reason.value.trim() }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Não foi possível registrar a decisão.');
  await refreshQueue();
  queue.prepend(block('meta', `Decisão registrada: ${data.status}. Nenhuma ação externa foi executada.`));
}

async function refreshQueue() {
  try {
    const response = await fetch('/api/reviews');
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Fila indisponível.');
    queue.replaceChildren();
    if (!data.pending.length) {
      queue.append(block('meta', 'Nenhum rascunho aguardando revisão.'));
      return;
    }
    for (const item of data.pending) {
      const card = block('ticket', '');
      card.append(block('eyebrow', `REVISÃO ${item.id.slice(0, 8)}`));
      card.append(block('answer', item.draft.answer));
      card.append(block('meta', `Categoria: ${item.draft.category} · Fontes: ${item.draft.citations.join(', ')}`));
      const actions = block('ticket-actions', '');
      for (const [decision, label] of [['approve', 'Aprovar para exibição'], ['reject', 'Rejeitar']]) {
        const control = document.createElement('button');
        control.type = 'button';
        control.textContent = label;
        if (decision === 'reject') control.className = 'reject';
        control.addEventListener('click', async () => {
          control.disabled = true;
          try { await decide(item.id, decision); }
          catch (error) { queue.prepend(block('meta', error.message)); }
          finally { control.disabled = false; }
        });
        actions.append(control);
      }
      card.append(actions);
      queue.append(card);
    }
  } catch (error) {
    queue.replaceChildren(block('meta', error.message));
  }
}

async function analyze() {
  button.disabled = true;
  output.className = 'empty';
  output.textContent = 'Analisando e validando evidências…';
  try {
    const response = await fetch('/api/analyze', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case: textarea.value }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Falha na análise');
    output.className = '';
    output.replaceChildren();
    output.append(block(`status ${data.status === 'blocked' ? 'blocked' : ''}`, data.status === 'blocked' ? 'BLOQUEADO' : 'REVISÃO HUMANA NECESSÁRIA'));
    output.append(block('answer', data.status === 'blocked' ? data.reason : data.draft.answer));
    output.append(block('meta', `Modo: ${data.mode}. Nenhuma ação externa executada.`));
    const trace = block('flow', '');
    for (const step of data.trace) trace.append(block('', step));
    output.append(trace);
    const evidence = block('evidence', '');
    evidence.append(block('eyebrow', 'EVIDÊNCIAS CONSULTADAS'));
    for (const item of data.evidence) evidence.append(block('', `${item.id} · ${item.title}`));
    output.append(evidence);
    if (data.review_id) await refreshQueue();
  } catch (error) {
    output.className = 'empty';
    output.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

button.addEventListener('click', analyze);
for (const sample of document.querySelectorAll('[data-case]')) {
  sample.addEventListener('click', () => { textarea.value = sample.dataset.case; });
}
fetch('/health').then((response) => response.json()).then((data) => {
  document.querySelector('#mode').textContent = data.mode === 'ollama' ? 'LLM LOCAL / OLLAMA' : 'DEMO DETERMINÍSTICA';
});
refreshQueue();
