/**
 * app.js — Main entry point. Wires everything together on DOMContentLoaded.
 */

document.addEventListener('DOMContentLoaded', () => {
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

  // Log startup info
  console.log(
    '%c Taro.ai %c Powered by SurrealDB ',
    'background: linear-gradient(135deg, #9600ff, #ff00a0); color: white; padding: 4px 8px; border-radius: 4px 0 0 4px; font-weight: bold;',
    'background: #15131D; color: #9B97B0; padding: 4px 8px; border-radius: 0 4px 4px 0;'
  );
  console.log(`Mock mode: ${USE_MOCK ? 'ON' : 'OFF'} | API: ${API_BASE}`);
});
