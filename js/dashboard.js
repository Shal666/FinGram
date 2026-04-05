// Dashboard functionality
// Note: currentUser is already declared in auth.js, so we use it directly

async function initDashboard() {
  const user = await requireAuth();
  if (!user) return;

  // Update user info
  updateUserInfo(user);

  // Load dashboard data
  await loadDashboardStats(user);
  await loadDashboardCharts(user);
  await loadGoalsSummary(user);
}

function updateUserInfo(user) {
  const userNameEl = document.getElementById('userName');
  const userEmailEl = document.getElementById('userEmail');
  const userAvatarEl = document.getElementById('userAvatar');

  if (userNameEl) {
    userNameEl.textContent = user.name || 'User';
  }

  if (userEmailEl) {
    userEmailEl.textContent = user.email;
  }

  if (userAvatarEl) {
    userAvatarEl.textContent = (user.name || 'U')[0].toUpperCase();
  }
}

async function loadDashboardStats(user) {
  try {
    const stats = await apiFetch('/api/transactions/stats/summary');

    const incomeEl = document.getElementById('incomeValue');
    const expenseEl = document.getElementById('expenseValue');
    const balanceEl = document.getElementById('balanceValue');

    if (incomeEl) {
      incomeEl.textContent = formatCurrency(stats.income || 0, user.currency);
    }

    if (expenseEl) {
      expenseEl.textContent = formatCurrency(stats.expenses || 0, user.currency);
    }

    if (balanceEl) {
      const balance = (stats.income || 0) - (stats.expenses || 0);
      balanceEl.textContent = formatCurrency(balance, user.currency);
    }
  } catch (error) {
    console.error('Error loading dashboard stats:', error);
  }
}

async function loadDashboardCharts(user) {
  try {
    // Get yearly data
    const yearlyData = await apiFetch('/api/transactions/stats/yearly');

    // Yearly trend chart
    const yearlyCtx = document.getElementById('yearlyChart');
    if (yearlyCtx) {
      new Chart(yearlyCtx, {
        type: 'line',
        data: {
          labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
          datasets: [
            {
              label: 'Доходы',
              data: yearlyData.income || Array(12).fill(0),
              borderColor: '#4caf50',
              backgroundColor: 'rgba(76, 175, 80, 0.1)',
              tension: 0.4
            },
            {
              label: 'Расходы',
              data: yearlyData.expenses || Array(12).fill(0),
              borderColor: '#f44336',
              backgroundColor: 'rgba(244, 67, 54, 0.1)',
              tension: 0.4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top'
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

    // Category breakdown chart
    const categoryData = await apiFetch('/api/transactions/stats/category');
    const categoryCtx = document.getElementById('categoryChart');
    
    if (categoryCtx && categoryData.categories && categoryData.amounts) {
      new Chart(categoryCtx, {
        type: 'doughnut',
        data: {
          labels: categoryData.categories,
          datasets: [{
            data: categoryData.amounts,
            backgroundColor: [
              '#FF6384',
              '#36A2EB',
              '#FFCE56',
              '#4BC0C0',
              '#9966FF',
              '#FF9F40',
              '#FF6384',
              '#C9CBCF'
            ]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right'
            }
          }
        }
      });
    }
  } catch (error) {
    console.error('Error loading charts:', error);
  }
}

async function loadGoalsSummary(user) {
  try {
    const goals = await apiFetch('/api/goals?limit=3');
    const goalsGrid = document.getElementById('goalsGrid');

    if (!goalsGrid) return;

    if (goals.length === 0) {
      goalsGrid.innerHTML = `<p data-i18n="noGoals">У вас пока нет целей</p>`;
      return;
    }

    const lang = localStorage.getItem('language') || 'ru';

    goalsGrid.innerHTML = goals.map(goal => `
      <div class="goal-card" style="cursor: pointer;" onclick="window.location.href='goals.html'">
        <div class="goal-header">
          <h4>${goal.title}</h4>
        </div>
        <div class="goal-amount" style="margin-bottom: 10px;">
          <strong>${formatCurrency(goal.current_amount, user.currency)}</strong> из ${formatCurrency(goal.target_amount, user.currency)}
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

// Initialize dashboard on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboard);
} else {
  initDashboard();
}