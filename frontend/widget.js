
// // Tiny embeddable widget. Usage:
// // <script src="https://YOUR_HOST/widget.js" data-client="CLIENT_ID" data-api-key="KEY"></script>

// (function(){
//   const scriptEl = document.currentScript;
//   const hostOfScript = (new URL(scriptEl.src)).origin;

//   const apiBase = scriptEl.getAttribute('data-api-base')
//                  || hostOfScript              // if you host widget from API origin
//                  || window.location.origin;   // last resort
//   // const host = (new URL(document.currentScript.src)).origin;
//   const client = document.currentScript.getAttribute('data-client') || '';
//   const apiKey = document.currentScript.getAttribute('data-api-key') || '';
//   if(!client || !apiKey){ console.warn('widget: missing data-client or data-api-key'); }

//   // Styles
//   const style = document.createElement('style');
//   style.textContent = `
//     .rag-widget-btn{position:fixed;right:20px;bottom:20px;padding:12px 16px;border-radius:999px;background:#111;color:#fff;cursor:pointer;z-index:99999}
//     .rag-widget{position:fixed;right:20px;bottom:70px;width:360px;height:520px;border:1px solid #ddd;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.15);background:#fff;display:none;flex-direction:column;z-index:99999}
//     .rag-head{padding:10px 12px;border-bottom:1px solid #eee;font-weight:600}
//     .rag-body{flex:1;overflow:auto;padding:10px 12px;font-family:system-ui, sans-serif;font-size:14px}
//     .rag-input{display:flex;border-top:1px solid #eee}
//     .rag-input input{flex:1;padding:10px;border:0}
//     .rag-input button{padding:10px 12px;border:0;background:#111;color:#fff;cursor:pointer}
//     .rag-msg-user{margin:8px 0;text-align:right}
//     .rag-msg-bot{margin:8px 0;text-align:left}
//     .rag-src{font-size:12px;color:#666;margin-top:8px}
//   `;
//   document.head.appendChild(style);

//   // UI
//   const btn = document.createElement('div'); btn.className='rag-widget-btn'; btn.textContent='Chat';
//   const wrap = document.createElement('div'); wrap.className='rag-widget';
//   wrap.innerHTML = '<div class="rag-head">Ask me anything about Reginald</div><div class="rag-body" id="ragBody"></div><div class="rag-input"><input id="ragInput" placeholder="Type your question..."><button id="ragSend">Send</button></div>';
//   document.body.appendChild(btn); document.body.appendChild(wrap);
//   const body = wrap.querySelector('#ragBody'); const input = wrap.querySelector('#ragInput'); const send = wrap.querySelector('#ragSend');

//   btn.onclick = ()=>{ wrap.style.display = (wrap.style.display==='flex'?'none':'flex'); if(wrap.style.display==='flex'){wrap.style.display='flex';} };
//   send.onclick = async ()=>{
//     const q = input.value.trim(); if(!q) return;
//     body.innerHTML += '<div class="rag-msg-user">'+q+'</div>';
//     input.value='';
//     // const res = await fetch(`${apiBase}/chat`, {method:'POST', headers:{'Content-Type':'application/json','x-api-key': apiKey}, body: JSON.stringify({client_id: client, question: q, top_k: 4, stream: false})});
//     const res = await fetch(`${apiBase}/chat`, {
//       method:'POST',
//       headers:{'Content-Type':'application/json','x-api-key': apiKey},
//       body: JSON.stringify({client_id: client, question: q, top_k: 4, stream: false})
//     });
//     if(!res.ok){ body.innerHTML += '<div class="rag-msg-bot">Error: '+res.status+'</div>'; return; }
//     const data = await res.json();
//     body.innerHTML += '<div class="rag-msg-bot">'+data.answer+'<div class="rag-src">Sources: '+(data.sources||[]).join(', ')+'</div></div>';
//     body.scrollTop = body.scrollHeight;
//   };
// })();

// Embeddable RAG chat widget (customizable)
(function () {
  const el = document.currentScript;
  const hostOfScript = (new URL(el.src)).origin;

  // ---- Config via attributes ----
  const apiBase   = el.getAttribute('data-api-base') || hostOfScript || window.location.origin;
  const client    = el.getAttribute('data-client')   || '';
  const apiKey    = el.getAttribute('data-api-key')  || '';
  const title     = el.getAttribute('data-title')    || 'Chat Assistant';
  const accent    = el.getAttribute('data-accent')   || '#111';
  const position  = (el.getAttribute('data-position') || 'right').toLowerCase(); // 'left'|'right'
  const theme     = (el.getAttribute('data-theme')    || 'light').toLowerCase(); // 'light'|'dark'
  const collapsed = (el.getAttribute('data-collapsed') || 'false').toLowerCase() === 'true';

  if (!client || !apiKey) console.warn('widget: missing data-client or data-api-key');

  // ---- Persistent UI state (minimized/expanded) ----
  const STATE_KEY = `ragWidgetState:${client}`;
  const saved = (() => { try { return JSON.parse(localStorage.getItem(STATE_KEY) || '{}'); } catch { return {}; } })();
  let isOpen = saved.isOpen ?? !collapsed;

  // ---- Styles ----
  const darkBg = '#1e1e1e', darkText = '#e6e6e6', darkBorder = '#333';
  const lightBg = '#fff', lightText = '#333', lightBorder = '#ddd';
  const bg = theme === 'dark' ? darkBg : lightBg;
  const fg = theme === 'dark' ? darkText : lightText;
  const bd = theme === 'dark' ? darkBorder : lightBorder;

  const style = document.createElement('style');
  style.textContent = `
    .rag-widget-btn{
      position:fixed; ${position}:20px; bottom:20px;
      padding:12px 16px; border-radius:999px;
      background:${accent}; color:#fff; cursor:pointer; z-index:99999; border:none;
      font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif; font-weight:600;
      box-shadow:0 6px 20px rgba(0,0,0,.2);
    }
    .rag-widget{
      position:fixed; ${position}:20px; bottom:80px;
      width:360px; max-width:90vw; height:520px; max-height:70vh;
      border:1px solid ${bd}; border-radius:12px;
      box-shadow:0 10px 30px rgba(0,0,0,.15);
      background:${bg}; color:${fg};
      display:none; flex-direction:column; z-index:99999;
      font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      overflow:hidden;
    }
    .rag-head{
      padding:10px 12px; border-bottom:1px solid ${bd};
      background:${accent}; color:#fff; display:flex; align-items:center; justify-content:space-between;
    }
    .rag-title{ font-weight:700; font-size:14px }
    .rag-controls{ display:flex; gap:6px }
    .rag-iconbtn{ background:rgba(255,255,255,.2); border:none; color:#fff; border-radius:8px; padding:4px 8px; cursor:pointer }
    .rag-body{ flex:1; overflow:auto; padding:12px; font-size:14px }
    .rag-input{ display:flex; border-top:1px solid ${bd}; gap:6px; padding:8px }
    .rag-input textarea{
      flex:1; padding:10px; border:1px solid ${bd}; border-radius:8px; background:${bg}; color:${fg};
      font-family:inherit; font-size:14px; resize:vertical; min-height:40px; max-height:140px;
    }
    .rag-input button{
      padding:10px 14px; border:0; background:${accent}; color:#fff; cursor:pointer; border-radius:8px; font-weight:600;
    }
    .rag-msg-user{ margin:8px 0; text-align:right; color:${accent}; white-space:pre-wrap }
    .rag-msg-bot{ margin:8px 0; text-align:left; color:${fg}; white-space:pre-wrap }
    .rag-src{ font-size:12px; color:${theme==='dark' ? '#aaa' : '#666'}; margin-top:6px }
  `;
  document.head.appendChild(style);

  // ---- UI ----
  const btn = document.createElement('button');
  btn.className = 'rag-widget-btn';
  btn.textContent = 'Chat';

  const wrap = document.createElement('div');
  wrap.className = 'rag-widget';
  wrap.innerHTML = `
    <div class="rag-head">
      <span class="rag-title">${title}</span>
      <div class="rag-controls">
        <button class="rag-iconbtn" data-action="minimize" title="Minimize">–</button>
        <button class="rag-iconbtn" data-action="close" title="Close">×</button>
      </div>
    </div>
    <div class="rag-body" id="ragBody"></div>
    <div class="rag-input">
      <textarea id="ragInput" placeholder="Type your question..."></textarea>
      <button id="ragSend">Send</button>
    </div>
  `;

  document.body.appendChild(btn);
  document.body.appendChild(wrap);

  const body = wrap.querySelector('#ragBody');
  const input = wrap.querySelector('#ragInput');
  const send = wrap.querySelector('#ragSend');
  const minimizeBtn = wrap.querySelector('[data-action="minimize"]');
  const closeBtn = wrap.querySelector('[data-action="close"]');

  // ---- Behavior ----
  function renderOpenState() {
    wrap.style.display = isOpen ? 'flex' : 'none';
    localStorage.setItem(STATE_KEY, JSON.stringify({ isOpen }));
  }
  btn.onclick = () => { isOpen = true; renderOpenState(); input?.focus(); };
  minimizeBtn.onclick = () => { isOpen = false; renderOpenState(); };
  closeBtn.onclick = () => { isOpen = false; renderOpenState(); };

  // Keyboard: Enter = send, Shift+Enter = newline, ESC = minimize
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { isOpen = false; renderOpenState(); return; }
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send.click(); }
  });

  send.onclick = async () => {
    const q = (input.value || '').trim(); if (!q) return;
    body.innerHTML += `<div class="rag-msg-user">${escapeHtml(q)}</div>`;
    input.value = '';
    body.scrollTop = body.scrollHeight;

    try {
      const res = await fetch(`${apiBase}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': apiKey },
        body: JSON.stringify({ client_id: client, question: q, top_k: 4, stream: false })
      });
      if (!res.ok) {
        body.innerHTML += `<div class="rag-msg-bot">Error: ${res.status}</div>`;
      } else {
        const data = await res.json();
        const ans = (data && data.answer) ? data.answer : '';
        const src = (data && data.sources && data.sources.length) ? `<div class="rag-src">Sources: ${data.sources.join(', ')}</div>` : '';
        body.innerHTML += `<div class="rag-msg-bot">${escapeHtml(ans)}${src}</div>`;
      }
    } catch (err) {
      body.innerHTML += `<div class="rag-msg-bot">Network error</div>`;
    }
    body.scrollTop = body.scrollHeight;
  };

  // Start minimized or open based on saved state
  renderOpenState();

  // ---- Helpers ----
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }
})();
