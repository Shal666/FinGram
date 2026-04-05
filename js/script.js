document.addEventListener('DOMContentLoaded', () => {
  const burger = document.getElementById('burger');
  const nav = document.getElementById('nav');

  burger && burger.addEventListener('click', () => {
    nav.classList.toggle('active');
    burger.classList.toggle('active');
  });

  const navLinks = nav?.querySelectorAll('a');
  navLinks && navLinks.forEach(link => {
    link.addEventListener('click', () => {
      nav.classList.remove('active');
      burger.classList.remove('active');
    });
  });

  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, observerOptions);

  document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

  const downloadGuide = document.getElementById('downloadGuide');
  downloadGuide && downloadGuide.addEventListener('click', () => {
    const lang = localStorage.getItem('language') || 'en';
    const guides = {
      en: [
        'BayQadam — Quick Guide',
        '',
        '— Enable expense tracking',
        '— Set a goal and regular transfers',
        '— Use our learning modules',
        '',
        'Thank you!'
      ],
      ru: [
        'BayQadam — Краткий гайд',
        '',
        '— Включите трекинг расходов',
        '— Настройте цель и регулярные переводы',
        '— Используйте наши учебные модули',
        '',
        'Спасибо!'
      ],
      kk: [
        'BayQadam — Жылдам нұсқаулық',
        '',
        '— Шығын қадағалауды қосыңыз',
        '— Мақсатты орнатып, тұрақты аударымдар жасаңыз',
        '— Біздің оқу модульдерін пайдаланыңыз',
        '',
        'Рахмет!'
      ]
    };
    
    const content = guides[lang].join('\n');
    const blob = new Blob([content], {type: 'text/plain;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'BayQadam_guide.txt';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });
});