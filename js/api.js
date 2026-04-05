// API Configuration
const API_URL = 'https://web-production-2526b.up.railway.app';

// Currency symbols
const CURRENCY_SYMBOLS = {
  KZT: '₸',
  RUB: '₽',
  USD: '$'
};

// Format currency
function formatCurrency(amount, currency = 'KZT') {
  const symbol = CURRENCY_SYMBOLS[currency] || currency;
  return `${amount.toLocaleString()} ${symbol}`;
}

// Format date
function formatDate(dateString) {
  const date = new Date(dateString);
  const lang = localStorage.getItem('language') || 'en';
  return date.toLocaleDateString(lang === 'kk' ? 'kk-KZ' : lang === 'ru' ? 'ru-RU' : 'en-US');
}

// API Error Handler
function formatApiErrorDetail(detail) {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

// Fetch with credentials
async function apiFetch(endpoint, options = {}) {
  const defaultOptions = {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  };
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...defaultOptions,
    ...options
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(formatApiErrorDetail(error.detail || 'Request failed'));
  }
  
  return response.json();
}

// Transaction categories
const EXPENSE_CATEGORIES = {
  en: ['Food', 'Transport', 'Health', 'Entertainment', 'Housing', 'Clothing', 'Education', 'Credit', 'Other'],
  ru: ['Еда', 'Транспорт', 'Здоровье', 'Развлечения', 'Жилье', 'Одежда', 'Образование', 'Кредиты', 'Прочее'],
  kk: ['Тамақ', 'Көлік', 'Денсаулық', 'Ойын-сауық', 'Тұрғын үй', 'Киім', 'Білім', 'Несиелер', 'Басқа']
};

const INCOME_CATEGORIES = {
  en: ['Salary', 'Freelance', 'Side Job', 'Investments', 'Other'],
  ru: ['Зарплата', 'Фриланс', 'Подработка', 'Инвестиции', 'Прочее'],
  kk: ['Жалақы', 'Фриланс', 'Қосымша жұмыс', 'Инвестициялар', 'Басқа']
};

function getCategories(type, lang = 'en') {
  lang = lang || localStorage.getItem('language') || 'en';
  return type === 'expense' ? EXPENSE_CATEGORIES[lang] : INCOME_CATEGORIES[lang];
}