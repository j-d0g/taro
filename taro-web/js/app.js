/**
 * app.js — Main entry point. Wires everything together on DOMContentLoaded.
 */

document.addEventListener('DOMContentLoaded', async () => {
  // Bind chat keyboard shortcuts
  initChatKeyboard();

  // Build dynamic filter tabs from API verticals, then render products
  await initDynamicTabs();

  // Close modal on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
      if (profileOpen) toggleProfile();
    }
  });

  // Check API health, fetch model name, and log status
  const apiUp = await checkApiHealth();
  if (apiUp) {
    try {
      const res = await fetch(`${API_BASE}/models`);
      const data = await res.json();
      const el = document.getElementById('modelName');
      if (el && data.default_model) el.textContent = data.default_model;
    } catch (_) {}
  }
  console.log(
    '%c Taro.ai %c Powered by SurrealDB ',
    'background: #1C1C1E; color: #C9A96E; padding: 4px 8px; border-radius: 4px 0 0 4px; font-weight: bold;',
    'background: #F5F0EA; color: #6B6B6F; padding: 4px 8px; border-radius: 0 4px 4px 0;'
  );
  console.log(`API: ${API_BASE} | Status: ${apiUp ? 'Connected' : 'Offline (using mock data)'}`);
});
