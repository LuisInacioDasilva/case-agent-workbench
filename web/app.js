const output = document.querySelector('#output');
const textarea = document.querySelector('#case');
const button = document.querySelector('#analyze');

function block(className, text) {
  const element = document.createElement('div');
  element.className = className;
  element.textContent = text;
  return element;
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
