/**
 * app.js — Main entry point. Wires everything together on DOMContentLoaded.
 */

document.addEventListener('DOMContentLoaded', async () => {
  // Render initial product grid
  renderProducts();

  // Bind filter tabs and search bar
  initFilters();

  // Bind chat keyboard shortcuts
  initChatKeyboard();

  // Close modal on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
      if (profileOpen) toggleProfile();
    }
  });

  // Check API health and show status
  const apiOk = await checkApiHealth();
  const badge = document.querySelector('.navbar-badge');
  if (apiOk) {
    badge.innerHTML = '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--success);margin-right:4px"></span>Powered by SurrealDB';
    badge.style.borderColor = 'rgba(0,212,170,0.3)';
  } else {
    badge.innerHTML = '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--warning);margin-right:4px"></span>Demo mode (mock data)';
    badge.style.borderColor = 'rgba(255,170,0,0.3)';
  }

  // Log startup info
  console.log(
    '%c Taro.ai %c Powered by SurrealDB ',
    'background: linear-gradient(135deg, #9600ff, #ff00a0); color: white; padding: 4px 8px; border-radius: 4px 0 0 4px; font-weight: bold;',
    'background: #15131D; color: #9B97B0; padding: 4px 8px; border-radius: 0 4px 4px 0;'
  );
  console.log(`API: ${API_BASE} | Status: ${apiOk ? 'connected' : 'offline (using mock data)'}`);
});
