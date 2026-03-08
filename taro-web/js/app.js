/**
 * app.js — Main entry point. Wires everything together on DOMContentLoaded.
 */

document.addEventListener('DOMContentLoaded', async () => {
  // Bind filter tabs and search bar (sync — needs to be ready before products load)
  initFilters();

  // Bind chat keyboard shortcuts
  initChatKeyboard();

  // Render initial product grid (async — fetches from API)
  await renderProducts();

  // Close modal on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
      if (profileOpen) toggleProfile();
    }
  });

  // Check API health and log status
  const apiUp = await checkApiHealth();
  console.log(
    '%c Taro.ai %c Powered by SurrealDB ',
    'background: #1C1C1E; color: #C9A96E; padding: 4px 8px; border-radius: 4px 0 0 4px; font-weight: bold;',
    'background: #F5F0EA; color: #6B6B6F; padding: 4px 8px; border-radius: 0 4px 4px 0;'
  );
  console.log(`API: ${API_BASE} | Status: ${apiUp ? 'Connected' : 'Offline (using mock data)'}`);
});
