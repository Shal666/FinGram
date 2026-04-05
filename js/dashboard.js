// Dashboard Logic
let currentUser = null;
let monthlyStats = null;
let yearlyStats = null;

async function initDashboard() {
  // Check auth
  currentUser = await requireAuth();
  if (!currentUser) return;

  // Update user info
  updateUserInfo();

  // Load data
  await Promise.all([
    loadMonthlyStats(),
    loadYearlyStats(),
    loadGoals()
  ]);

  // Initialize charts after data is loaded
  initCharts();
}

function updateUserInfo() {
  const userName = document.getElementById('userName');
  const userEmail = document.getElementById('userEmail');
  const userAvatar = document.getElementById('userAvatar');

  if (userName) {
    userName.textContent = `${currentUser.name} ${currentUser.surname}`;
  }
  
  if (userEmail) {
    userEmail.textContent = currentUser.email;
  }
  
  if (userAvatar) {
    userAvatar.textContent = currentUser.name.charAt(0).toUpperCase();
  }
}

async function loadMonthlyStats() {
  try {
    const now = new Date();
    monthlyStats = await apiFetch(`/api/transactions/stats?year=${now.getFullYear()}&month=${now.getMonth() + 1}`);
    
    // Update stat cards
    document.getElementById('incomeValue').textContent = formatCurrency(monthlyStats.income, currentUser.currency);
    document.getElementById('expenseValue').textContent = formatCurrency(monthlyStats.expense, currentUser.currency);
    document.getElementById('balanceValue').textContent = formatCurrency(monthlyStats.balance, currentUser.currency);
    
    // Change balance color based on positive/negative
    const balanceCard = document.querySelector('.stat-card.balance');
    if (monthlyStats.balance < 0) {
      balanceCard.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
    }
  } catch (error) {
    console.error('Error loading monthly stats:', error);
  }
}

async function loadYearlyStats() {
  try {
    const now = new Date();
    yearlyStats = await apiFetch(`/api/transactions/yearly-stats?year=${now.getFullYear()}`);
  } catch (error) {
    console.error('Error loading yearly stats:', error);
  }
}

async function loadGoals() {
  try {
    const goals = await apiFetch('/api/goals');
    const goalsGrid = document.getElementById('goalsGrid');
    const lang = localStorage.getItem('language') || 'en';
    
    if (goals.length === 0) {
      goalsGrid.innerHTML = `<p style="text-align: center; color: #999; grid-column: 1/-1;" data-i18n="noGoals">У вас пока нет целей</p>`;
      return;
    }

    // Show only first 3 goals
    const displayGoals = goals.slice(0, 3);
    
    goalsGrid.innerHTML = displayGoals.map(goal => `
      <div class="goal-card">
        <div class="goal-header">
          <h4>${goal.title}</h4>
        </div>
        
        <div class="goal-amount" style="margin-bottom: 10px;">
          <strong>${formatCurrency(goal.current_amount, currentUser.currency)}</strong> из ${formatCurrency(goal.target_amount, currentUser.currency)}
        </div>
        
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${goal.progress}%"></div>
        </div>
        
        <div class="progress-text" style="margin-top: 8px;">
          ${Math.round(goal.progress)}% ${translations[lang].completed || 'завершено'}
        </div>
      </div>
    `).join('');
  } catch (error) {
    console.error('Error loading goals:', error);
  }
}

function initCharts() {
  if (yearlyStats && yearlyStats.months) {
    initYearlyChart();
  }
  
  if (monthlyStats && monthlyStats.categories) {
    initCategoryChart();
  }
}

function initYearlyChart() {
  const ctx = document.getElementById('yearlyChart');
  if (!ctx) return;

  const lang = localStorage.getItem('language') || 'en';
  const monthNames = {
    en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    ru: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
    kk: ['Қаң', 'Ақп', 'Нау', 'Сәу', 'Мам', 'Мау', 'Шіл', 'Там', 'Қыр', 'Қаз', 'Қар', 'Жел']
  };

  const labels = monthNames[lang] || monthNames.en;
  const incomeData = yearlyStats.months.map(m => m.income);
  const expenseData = yearlyStats.months.map(m => m.expense);

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: translations[lang].income || 'Income',
          data: incomeData,
          borderColor: '#4facfe',
          backgroundColor: 'rgba(79, 172, 254, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: translations[lang].expense || 'Expense',
          data: expenseData,
          borderColor: '#f5576c',
          backgroundColor: 'rgba(245, 87, 108, 0.1)',
          tension: 0.4,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

function initCategoryChart() {
  const ctx = document.getElementById('categoryChart');
  if (!ctx || !monthlyStats.categories || monthlyStats.categories.length === 0) {
    if (ctx) {
      ctx.parentElement.innerHTML = '<p style="text-align: center; color: #999; padding: 40px;">Нет данных о расходах за этот месяц</p>';
    }
    return;
  }

  const categories = monthlyStats.categories.map(c => c.category);
  const amounts = monthlyStats.categories.map(c => c.total);

  const colors = [
    '#667eea', '#764ba2', '#f093fb', '#f5576c',
    '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
    '#fa709a', '#fee140', '#30cfd0', '#330867'
  ];

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: categories,
      datasets: [{
        data: amounts,
        backgroundColor: colors.slice(0, categories.length),
        borderWidth: 2,
        borderColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });
}

// Initialize dashboard when page loads
if (document.getElementById('yearlyChart') || document.getElementById('categoryChart')) {
  window.addEventListener('DOMContentLoaded', initDashboard);
}