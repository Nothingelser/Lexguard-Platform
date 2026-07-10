(function () {
  const STORAGE_KEY = 'lexguard:theme';
  const btn = document.getElementById('theme-toggle');
  const iconMarkup = `
    <svg class="theme-icon theme-icon-dark" width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 2.75a.75.75 0 0 1 .75.75v1.1a.75.75 0 1 1-1.5 0v-1.1a.75.75 0 0 1 .75-.75Zm6.72 2.03a.75.75 0 0 1 1.06 0l.78.78a.75.75 0 1 1-1.06 1.06l-.78-.78a.75.75 0 0 1 0-1.06ZM21.25 11.25h-1.1a.75.75 0 1 1 0-1.5h1.1a.75.75 0 1 1 0 1.5Zm-2.49 7.25a.75.75 0 0 1 0 1.06l-.78.78a.75.75 0 1 1-1.06-1.06l.78-.78a.75.75 0 0 1 1.06 0ZM12 18.15a.75.75 0 0 1 .75.75V20a.75.75 0 1 1-1.5 0v-1.1a.75.75 0 0 1 .75-.75Zm-5.66-1.88a.75.75 0 0 1 0 1.06l-.78.78a.75.75 0 1 1-1.06-1.06l.78-.78a.75.75 0 0 1 1.06 0ZM4.85 11.25h-1.1a.75.75 0 1 1 0-1.5h1.1a.75.75 0 1 1 0 1.5Zm1.49-5.73a.75.75 0 0 1-1.06 0l-.78-.78a.75.75 0 1 1 1.06-1.06l.78.78a.75.75 0 0 1 0 1.06ZM12 6.25A5.75 5.75 0 1 1 6.25 12 5.76 5.76 0 0 1 12 6.25Z" fill="currentColor"/>
    </svg>
    <svg class="theme-icon theme-icon-light" width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true" hidden>
      <path d="M21.2 14.7A8.8 8.8 0 1 1 9.3 2.8a1 1 0 0 1 1.2 1.2A6.8 6.8 0 0 0 19.2 13a1 1 0 0 1 2 .7Z" fill="currentColor"/>
      <path d="M12 7.4a.9.9 0 0 1 .9.9v.6a.9.9 0 1 1-1.8 0v-.6a.9.9 0 0 1 .9-.9Zm4.5 1.85a.9.9 0 0 1 1.27 0l.42.42a.9.9 0 1 1-1.27 1.27l-.42-.42a.9.9 0 0 1 0-1.27ZM18.6 12a.9.9 0 0 1 .9-.9h.6a.9.9 0 1 1 0 1.8h-.6a.9.9 0 0 1-.9-.9Zm-1.35 3.15a.9.9 0 0 1 1.27 0l.42.42a.9.9 0 1 1-1.27 1.27l-.42-.42a.9.9 0 0 1 0-1.27ZM12 15.8a.9.9 0 0 1 .9.9v.6a.9.9 0 1 1-1.8 0v-.6a.9.9 0 0 1 .9-.9Zm-4.5-1.85a.9.9 0 0 1 0 1.27l-.42.42A.9.9 0 1 1 5.8 14.37l.42-.42a.9.9 0 0 1 1.27 0ZM5.4 12a.9.9 0 0 1-.9.9h-.6a.9.9 0 1 1 0-1.8h.6a.9.9 0 0 1 .9.9Zm1.35-3.15a.9.9 0 0 1-1.27 0l-.42-.42a.9.9 0 1 1 1.27-1.27l.42.42a.9.9 0 0 1 0 1.27Z" fill="currentColor"/>
    </svg>
  `;
  if (btn && !btn.querySelector('svg')) btn.innerHTML = iconMarkup;
  const darkIcon = btn ? btn.querySelector('.theme-icon-dark') : null;
  const lightIcon = btn ? btn.querySelector('.theme-icon-light') : null;
  function systemPrefersDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  function getStored() { return localStorage.getItem(STORAGE_KEY); }
  function setStored(v) { if (v) localStorage.setItem(STORAGE_KEY, v); else localStorage.removeItem(STORAGE_KEY); }
  function applyTheme(theme) {
    document.body.classList.remove('dark-mode', 'light-mode');
    if (theme === 'dark') document.body.classList.add('dark-mode');
    else if (theme === 'light') document.body.classList.add('light-mode');
    if (darkIcon && lightIcon) {
      const showDarkIcon = theme !== 'dark';
      darkIcon.hidden = !showDarkIcon;
      lightIcon.hidden = showDarkIcon;
    }
  }
  function init() {
    const stored = getStored();
    if (stored) applyTheme(stored);
    else applyTheme(systemPrefersDark() ? 'dark' : 'light');
    if (btn) btn.addEventListener('click', toggle);
    // respond to system changes when no stored preference
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!getStored()) applyTheme(e.matches ? 'dark' : 'light');
      });
    }
  }
  function toggle() {
    const cur = getStored() || (systemPrefersDark() ? 'dark' : 'light');
    const next = (cur === 'dark') ? 'light' : 'dark';
    setStored(next);
    applyTheme(next);
  }
  document.addEventListener('DOMContentLoaded', init);
})();
