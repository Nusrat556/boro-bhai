const state = { sessionId: 'boro-bhai-session' };

const setStatus = (elementId, message, type = '') => {
  const node = document.getElementById(elementId);
  if (!node) return;
  node.textContent = message || '';
  node.className = `status ${type}`.trim();
};

const escapeHtml = (value = '') =>
  String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\"/g, '&quot;')
    .replace(/'/g, '&#039;');

const renderMarkdown = (text = '') => {
  const safeText = String(text ?? '');
  const normalized = safeText
    .replace(/\r/g, '')
    .replace(/\n\n+/g, '\n\n');

  const blocks = normalized.split(/\n\n+/).map((block) => block.trim()).filter(Boolean);

  const renderInline = (chunk) =>
    escapeHtml(chunk)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\[(.+?)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');

  return blocks
    .map((block) => {
      if (block.startsWith('```')) {
        const code = block.replace(/^```[a-zA-Z]*\n?/, '').replace(/```$/, '').trim();
        return `<pre><code>${escapeHtml(code)}</code></pre>`;
      }

      if (/^[-*] /.test(block)) {
        const items = block
          .split('\n')
          .map((line) => line.replace(/^[-*] /, '').trim())
          .filter(Boolean)
          .map((line) => `<li>${renderInline(line)}</li>`)
          .join('');
        return `<ul>${items}</ul>`;
      }

      const paragraphs = block
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => `<p>${renderInline(line)}</p>`)
        .join('');

      return paragraphs;
    })
    .join('');
};

const showChatView = () => {
  const home = document.getElementById('home-view');
  const chat = document.getElementById('chat-view');
  if (home) home.style.display = 'none';
  if (chat) chat.classList.add('visible');
};

const showHomeView = () => {
  const home = document.getElementById('home-view');
  const chat = document.getElementById('chat-view');
  if (home) home.style.display = 'flex';
  if (chat) chat.classList.remove('visible');
};

const addChatMessage = (role, text) => {
  const output = document.getElementById('chat-output');
  if (!output) return;

  const entry = document.createElement('div');
  entry.className = `message ${role}`;
  entry.innerHTML = `<div class="message-content">${renderMarkdown(text)}</div>`;
  output.appendChild(entry);
  output.scrollTop = output.scrollHeight;
};

const renderHistory = (history) => {
  const output = document.getElementById('chat-output');
  if (!output) return;

  output.innerHTML = '';
  history.forEach((entry) => {
    addChatMessage(entry.role, entry.content);
  });
  if ((history || []).length > 0) {
    showChatView();
  }
};

const fetchJson = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok || payload.success === false) {
    throw new Error(payload.error || 'Request failed.');
  }
  return payload;
};

const loadHistory = async () => {
  try {
    const payload = await fetchJson(`/api/history?session_id=${encodeURIComponent(state.sessionId)}`);
    renderHistory(payload.history || []);
  } catch (error) {
    console.error(error);
  }
};

const clearHistory = async () => {
  try {
    const payload = await fetchJson(`/api/clear-history?session_id=${encodeURIComponent(state.sessionId)}`, {
      method: 'POST',
    });
    renderHistory(payload.history || []);
  } catch (error) {
    console.error(error);
  }
};

document.getElementById('new-chat').addEventListener('click', () => {
  showHomeView();
  const input = document.getElementById('chat-input');
  if (input) input.focus();
});

document.getElementById('open-home').addEventListener('click', () => {
  showHomeView();
});

document.getElementById('clear-history').addEventListener('click', async () => {
  await clearHistory();
});

document.querySelectorAll('[data-prompt]').forEach((button) => {
  button.addEventListener('click', () => {
    const input = document.getElementById('chat-input');
    if (!input) return;
    input.value = button.dataset.prompt || '';
    input.focus();
    showChatView();
  });
});

document.getElementById('chat-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const input = document.getElementById('chat-input');
  const message = input.value.trim();

  if (!message) {
    setStatus('chat-status', 'Please enter a message.', 'error');
    return;
  }

  showChatView();
  setStatus('chat-status', 'Thinking...', 'success');

  try {
    const payload = await fetchJson(`/api/chat?session_id=${encodeURIComponent(state.sessionId)}`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    const data = payload.data || {};
    renderHistory(data.history || []);
    setStatus('chat-status', 'Reply ready.', 'success');
    input.value = '';
  } catch (error) {
    setStatus('chat-status', error.message, 'error');
  }
});

document.getElementById('research-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const query = document.getElementById('research-query').value.trim();
  if (!query) {
    document.getElementById('research-output').textContent = 'Please enter a research query.';
    return;
  }

  try {
    document.getElementById('research-output').textContent = 'Researching...';
    const payload = await fetchJson('/api/research', {
      method: 'POST',
      body: JSON.stringify({ query, max_results: 5 }),
    });
    const data = payload.data || {};
    const sources = (data.sources || []).map((item) => `- ${item.title}: ${item.url}`).join('\n');
    document.getElementById('research-output').textContent = `${data.answer}\n\nSources:\n${sources || 'No sources.'}`;
  } catch (error) {
    document.getElementById('research-output').textContent = error.message;
  }
});

document.getElementById('upload-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const fileInput = document.getElementById('upload-file');
  const file = fileInput.files[0];
  if (!file) {
    document.getElementById('upload-output').textContent = 'Please choose a file to upload.';
    return;
  }

  try {
    document.getElementById('upload-output').textContent = 'Uploading...';
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`/api/upload?session_id=${encodeURIComponent(state.sessionId)}`, {
      method: 'POST',
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok || payload.success === false) {
      throw new Error(payload.error || 'Upload failed.');
    }
    document.getElementById('upload-output').textContent = `Uploaded ${payload.data.filename} successfully.`;
  } catch (error) {
    document.getElementById('upload-output').textContent = error.message;
  }
});

document.getElementById('job-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const jobText = document.getElementById('job-text').value.trim();
  if (!jobText) {
    document.getElementById('job-output').textContent = 'Please enter a job description.';
    return;
  }

  const userSkills = document.getElementById('user-skills').value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean);

  try {
    document.getElementById('job-output').textContent = 'Analyzing job description...';
    const payload = await fetchJson('/api/job-analysis', {
      method: 'POST',
      body: JSON.stringify({ job_text: jobText, user_skills: userSkills }),
    });
    const data = payload.data || {};
    document.getElementById('job-output').textContent = JSON.stringify(data.analysis, null, 2);
  } catch (error) {
    document.getElementById('job-output').textContent = error.message;
  }
});

document.getElementById('skill-gap-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const jobText = document.getElementById('skill-gap-text').value.trim();
  if (!jobText) {
    document.getElementById('skill-gap-output').textContent = 'Please enter a role description.';
    return;
  }

  const userSkills = document.getElementById('skill-gap-skills').value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean);

  try {
    document.getElementById('skill-gap-output').textContent = 'Checking skill gaps...';
    const payload = await fetchJson('/api/skill-gap', {
      method: 'POST',
      body: JSON.stringify({ job_text: jobText, user_skills: userSkills }),
    });
    const data = payload.data || {};
    document.getElementById('skill-gap-output').textContent = JSON.stringify(data.analysis, null, 2);
  } catch (error) {
    document.getElementById('skill-gap-output').textContent = error.message;
  }
});

document.getElementById('load-reports').addEventListener('click', async () => {
  try {
    const payload = await fetchJson('/api/reports');
    const reports = payload.reports || [];
    if (!reports.length) {
      document.getElementById('reports-output').textContent = 'No reports generated yet.';
      return;
    }
    const items = reports.map((report) => `- ${report.name}`).join('\n');
    document.getElementById('reports-output').textContent = items;
  } catch (error) {
    document.getElementById('reports-output').textContent = error.message;
  }
});

showHomeView();
loadHistory();
