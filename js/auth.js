// Authentication Manager
let currentUser = null;

// Check if user is logged in
async function checkAuth() {
  try {
    currentUser = await apiFetch('/api/auth/me');
    return currentUser;
  } catch (error) {
    currentUser = null;
    return null;
  }
}

// Logout
async function logout() {
  try {
    await apiFetch('/api/auth/logout', { method: 'POST' });
    currentUser = null;
    window.location.href = '/index.html';
  } catch (error) {
    console.error('Logout error:', error);
    window.location.href = '/index.html';
  }
}

// Redirect to login if not authenticated
async function requireAuth() {
  const user = await checkAuth();
  if (!user) {
    window.location.href = '/login.html';
    return null;
  }
  return user;
}

// Get current user
function getCurrentUser() {
  return currentUser;
}

// Update auth UI in header
function updateAuthUI() {
  const authButtons = document.getElementById('authButtons');
  const userMenu = document.getElementById('userMenu');
  
  if (!authButtons || !userMenu) return;
  
  if (currentUser) {
    authButtons.style.display = 'none';
    userMenu.style.display = 'flex';
    
    const userName = document.getElementById('userName');
    if (userName) {
      userName.textContent = currentUser.name;
    }
  } else {
    authButtons.style.display = 'flex';
    userMenu.style.display = 'none';
  }
}

// Initialize auth on page load
window.addEventListener('DOMContentLoaded', async () => {
  await checkAuth();
  updateAuthUI();
});