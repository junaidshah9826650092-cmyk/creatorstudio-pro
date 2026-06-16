// rulebook.js - Handles side navigation and AI help box interactions
// Assumes global variables TOTAL, flipped (Set), and updateUI() from rules.html

(function() {
  // Cache page elements
  const pages = document.querySelectorAll('.page');
  const aiQueryEl = document.querySelector('.ai-query');
  const aiResponseEl = document.querySelector('.ai-response');
  const aiSubmitBtn = document.querySelector('.ai-submit');

  // ---- Navigation ----
  window.prevPage = function() {
    // Find the highest-index flipped page and turn it back
    for (let i = pages.length - 1; i >= 0; i--) {
      if (pages[i].classList.contains('flipped')) {
        pages[i].classList.remove('flipped');
        // Adjust the global flipped Set (page numbers are 1‑based)
        if (typeof flipped !== 'undefined') flipped.delete(i + 1);
        if (typeof updateUI === 'function') updateUI();
        break;
      }
    }
  };

  window.nextPage = function() {
    // Find the first not‑flipped page and flip it
    for (let i = 0; i < pages.length; i++) {
      if (!pages[i].classList.contains('flipped')) {
        pages[i].classList.add('flipped');
        if (typeof flipped !== 'undefined') flipped.add(i + 1);
        if (typeof updateUI === 'function') updateUI();
        break;
      }
    }
  };

  // ---- AI Help Box ----
  function simulateAIResponse(prompt) {
    // Placeholder: echo the prompt with a friendly note.
    return `🧠 AI says: "${prompt}" (this is a mock response).`;
  }

  window.handleAI = function() {
    if (!aiQueryEl || !aiResponseEl) return;
    const query = aiQueryEl.value.trim();
    if (!query) {
      aiResponseEl.textContent = '🤔 Please type a question.';
      return;
    }
    aiResponseEl.textContent = '🔄 Thinking...';
    // Simulate async response
    setTimeout(() => {
      const answer = simulateAIResponse(query);
      aiResponseEl.textContent = answer;
    }, 600);
  };

  // Optional: allow pressing Enter to submit AI query
  if (aiQueryEl) {
    aiQueryEl.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleAI();
      }
    });
  }
})();
