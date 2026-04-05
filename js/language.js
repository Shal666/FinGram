let currentLang = localStorage.getItem('language') || 'en';

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('language', lang);
  updatePageContent();
  updateLanguageSelector();
}

function updateLanguageSelector() {
  const langButtons = document.querySelectorAll('[data-lang]');
  langButtons.forEach(btn => {
    if (btn.dataset.lang === currentLang) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

function updatePageContent() {
  const elements = document.querySelectorAll('[data-i18n]');
  elements.forEach(el => {
    const key = el.dataset.i18n;
    if (translations[currentLang] && translations[currentLang][key]) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = translations[currentLang][key];
      } else {
        el.textContent = translations[currentLang][key];
      }
    }
  });
  
  const planSelect = document.getElementById('planSelect');
  if (planSelect) {
    planSelect.options[0].text = translations[currentLang].selectPlan;
    planSelect.options[1].text = `${translations[currentLang].basicPlan} - ${translations[currentLang].free}`;
    planSelect.options[2].text = `${translations[currentLang].premiumPlan} - $9.99${translations[currentLang].perMonth}`;
    planSelect.options[3].text = `${translations[currentLang].vipPlan} - $19.99${translations[currentLang].perMonth}`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  updatePageContent();
  updateLanguageSelector();
  
  const langButtons = document.querySelectorAll('[data-lang]');
  langButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      setLanguage(btn.dataset.lang);
    });
  });
});