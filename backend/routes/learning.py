from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from typing import List, Optional

from backend.models.learning import (
    LessonResponse, QuizQuestion, QuizSubmit, QuizResult,
    UserProgress, Achievement, DailyCheckinResponse
)
from backend.utils.auth_utils import get_current_user
from backend.utils.db import get_database

router = APIRouter(prefix="/api/learning", tags=["learning"])

# Level thresholds
LEVELS = [
    {"level": 1, "min_xp": 0, "name": "Новичок", "name_en": "Beginner", "name_kk": "Жаңадан бастаушы"},
    {"level": 2, "min_xp": 500, "name": "Ученик", "name_en": "Student", "name_kk": "Оқушы"},
    {"level": 3, "min_xp": 1500, "name": "Знаток", "name_en": "Expert", "name_kk": "Білгір"},
    {"level": 4, "min_xp": 3000, "name": "Мастер", "name_en": "Master", "name_kk": "Шебер"},
    {"level": 5, "min_xp": 5000, "name": "Гуру финансов", "name_en": "Finance Guru", "name_kk": "Қаржы гуруы"},
]

# Achievements definitions
ACHIEVEMENTS = [
    {"id": "first_lesson", "name_ru": "Первый шаг", "name_en": "First Step", "name_kk": "Алғашқы қадам", 
     "desc_ru": "Пройди первый урок", "desc_en": "Complete first lesson", "desc_kk": "Алғашқы сабақты өт",
     "icon": "🎯", "xp": 50, "type": "lessons", "value": 1},
    {"id": "five_lessons", "name_ru": "Студент", "name_en": "Student", "name_kk": "Студент",
     "desc_ru": "Пройди 5 уроков", "desc_en": "Complete 5 lessons", "desc_kk": "5 сабақты өт",
     "icon": "📚", "xp": 100, "type": "lessons", "value": 5},
    {"id": "all_lessons", "name_ru": "Выпускник", "name_en": "Graduate", "name_kk": "Түлек",
     "desc_ru": "Пройди все уроки", "desc_en": "Complete all lessons", "desc_kk": "Барлық сабақтарды өт",
     "icon": "🎓", "xp": 500, "type": "lessons", "value": 10},
    {"id": "first_quiz", "name_ru": "Испытатель", "name_en": "Challenger", "name_kk": "Сынақшы",
     "desc_ru": "Пройди первый квиз", "desc_en": "Pass first quiz", "desc_kk": "Алғашқы квизді өт",
     "icon": "✅", "xp": 50, "type": "quizzes", "value": 1},
    {"id": "quiz_master", "name_ru": "Мастер квизов", "name_en": "Quiz Master", "name_kk": "Квиз шебері",
     "desc_ru": "Пройди 10 квизов", "desc_en": "Pass 10 quizzes", "desc_kk": "10 квизді өт",
     "icon": "🏆", "xp": 200, "type": "quizzes", "value": 10},
    {"id": "streak_3", "name_ru": "На волне", "name_en": "On Fire", "name_kk": "Толқында",
     "desc_ru": "3 дня подряд", "desc_en": "3 day streak", "desc_kk": "3 күн қатарынан",
     "icon": "🔥", "xp": 50, "type": "streak", "value": 3},
    {"id": "streak_7", "name_ru": "Неделя силы", "name_en": "Power Week", "name_kk": "Күш апталығы",
     "desc_ru": "7 дней подряд", "desc_en": "7 day streak", "desc_kk": "7 күн қатарынан",
     "icon": "💪", "xp": 150, "type": "streak", "value": 7},
    {"id": "streak_30", "name_ru": "Легенда", "name_en": "Legend", "name_kk": "Аңыз",
     "desc_ru": "30 дней подряд", "desc_en": "30 day streak", "desc_kk": "30 күн қатарынан",
     "icon": "👑", "xp": 500, "type": "streak", "value": 30},
    {"id": "xp_1000", "name_ru": "Тысячник", "name_en": "Thousander", "name_kk": "Мыңдық",
     "desc_ru": "Набери 1000 XP", "desc_en": "Earn 1000 XP", "desc_kk": "1000 XP жина",
     "icon": "⭐", "xp": 100, "type": "xp", "value": 1000},
    {"id": "first_goal", "name_ru": "Целеустремлённый", "name_en": "Goal Setter", "name_kk": "Мақсатқа ұмтылушы",
     "desc_ru": "Создай первую цель", "desc_en": "Create first goal", "desc_kk": "Алғашқы мақсатты құр",
     "icon": "🎯", "xp": 50, "type": "goals", "value": 1},
]

# Sample lessons data
LESSONS_DATA = [
    {
        "id": "lesson_1",
        "title_en": "Basics of Budgeting",
        "title_ru": "Основы бюджета",
        "title_kk": "Бюджет негіздері",
        "desc_en": "Learn how to create and manage your personal budget",
        "desc_ru": "Научись создавать и управлять личным бюджетом",
        "desc_kk": "Жеке бюджетті құруды және басқаруды үйрен",
        "content_en": "A budget is a plan for your money...",
        "content_ru": """
# Основы бюджета

## Что такое бюджет?
Бюджет — это план ваших доходов и расходов. Он помогает контролировать деньги и достигать финансовых целей.

## Правило 50/30/20
- **50%** — необходимые расходы (жильё, еда, транспорт)
- **30%** — желания (развлечения, хобби)
- **20%** — сбережения и погашение долгов

## Как начать?
1. Посчитайте все доходы за месяц
2. Запишите все расходы
3. Разделите расходы по категориям
4. Найдите где можно сэкономить

## Советы
- Записывайте ВСЕ расходы, даже мелкие
- Проверяйте бюджет каждую неделю
- Используйте приложения для учёта (например, BayQadam!)
        """,
        "content_kk": "Бюджет - бұл ақшаңызға арналған жоспар...",
        "category": "basics",
        "difficulty": "beginner",
        "xp_reward": 50,
        "order": 1
    },
    {
        "id": "lesson_2",
        "title_en": "How to Save Money",
        "title_ru": "Как копить деньги",
        "title_kk": "Ақша қалай жинауға болады",
        "desc_en": "Effective strategies for saving money",
        "desc_ru": "Эффективные стратегии накопления денег",
        "desc_kk": "Ақша жинаудың тиімді стратегиялары",
        "content_en": "Saving money is essential...",
        "content_ru": """
# Как копить деньги

## Почему важно копить?
- Финансовая подушка на случай непредвиденных расходов
- Достижение больших целей (машина, квартира, путешествие)
- Спокойствие и уверенность в завтрашнем дне

## Метод "Заплати себе первым"
Как только получаете зарплату, сразу откладывайте 10-20% на сбережения. Не ждите конца месяца!

## Автоматизация
Настройте автоматический перевод на накопительный счёт в день зарплаты.

## Правило 24 часов
Перед крупной покупкой подождите 24 часа. Часто желание купить проходит.

## Цели копления
1. Экстренный фонд (3-6 месяцев расходов)
2. Краткосрочные цели (отпуск, техника)
3. Долгосрочные цели (квартира, образование)
        """,
        "content_kk": "Ақша жинау маңызды...",
        "category": "saving",
        "difficulty": "beginner",
        "xp_reward": 50,
        "order": 2
    },
    {
        "id": "lesson_3",
        "title_en": "Understanding Credit",
        "title_ru": "Понимание кредитов",
        "title_kk": "Несиелерді түсіну",
        "desc_en": "Learn about loans and how to use them wisely",
        "desc_ru": "Узнай о займах и как использовать их разумно",
        "desc_kk": "Несиелер туралы және оларды қалай дұрыс пайдалану керектігін біліңіз",
        "content_en": "Credit can be helpful but dangerous...",
        "content_ru": """
# Понимание кредитов

## Что такое кредит?
Кредит — это деньги, которые банк даёт вам в долг под проценты.

## Виды кредитов
- **Потребительский** — на любые цели
- **Ипотека** — на покупку жилья
- **Автокредит** — на покупку машины
- **Кредитная карта** — возобновляемый кредит

## Как рассчитать переплату
Используйте формулу или калькулятор. Обращайте внимание на:
- Процентную ставку (годовую)
- Срок кредита
- Дополнительные комиссии

## Правила безопасного кредитования
1. Ежемесячный платёж не больше 30% дохода
2. Всегда читайте договор полностью
3. Сравнивайте предложения разных банков
4. Имейте план погашения

## Когда кредит оправдан?
✅ Ипотека (жильё дорожает)
✅ Образование (инвестиция в себя)
❌ Отпуск или развлечения
❌ Погашение других кредитов
        """,
        "content_kk": "Несие пайдалы, бірақ қауіпті болуы мүмкін...",
        "category": "credit",
        "difficulty": "intermediate",
        "xp_reward": 75,
        "order": 3
    },
    {
        "id": "lesson_4",
        "title_en": "Setting Financial Goals",
        "title_ru": "Финансовые цели",
        "title_kk": "Қаржылық мақсаттар",
        "desc_en": "How to set and achieve financial goals",
        "desc_ru": "Как ставить и достигать финансовых целей",
        "desc_kk": "Қаржылық мақсаттарды қалай қою және оларға жету керек",
        "content_en": "Goals give direction to your finances...",
        "content_ru": """
# Финансовые цели

## Зачем нужны цели?
Без цели деньги утекают незаметно. Цель даёт мотивацию и направление.

## SMART цели
- **S**pecific (Конкретная) — "Накопить 500,000₸", а не "накопить денег"
- **M**easurable (Измеримая) — можно отслеживать прогресс
- **A**chievable (Достижимая) — реальная, не фантастика
- **R**elevant (Актуальная) — важная для вас
- **T**ime-bound (Ограниченная во времени) — есть дедлайн

## Примеры целей
- Накопить экстренный фонд 300,000₸ за 6 месяцев
- Собрать на первый взнос по ипотеке за 2 года
- Накопить на отпуск 200,000₸ к июлю

## Как достигать?
1. Разбейте большую цель на маленькие шаги
2. Откладывайте регулярно (еженедельно/ежемесячно)
3. Отслеживайте прогресс
4. Празднуйте маленькие победы!

## Используйте BayQadam
Создайте цель в приложении и следите за прогрессом каждый день!
        """,
        "content_kk": "Мақсаттар қаржыңызға бағыт береді...",
        "category": "goals",
        "difficulty": "beginner",
        "xp_reward": 50,
        "order": 4
    },
    {
        "id": "lesson_5",
        "title_en": "Introduction to Investing",
        "title_ru": "Введение в инвестиции",
        "title_kk": "Инвестицияларға кіріспе",
        "desc_en": "Basic concepts of investing for beginners",
        "desc_ru": "Базовые концепции инвестирования для начинающих",
        "desc_kk": "Жаңадан бастаушыларға арналған инвестициялау негіздері",
        "content_en": "Investing helps grow your wealth...",
        "content_ru": """
# Введение в инвестиции

## Что такое инвестиции?
Инвестиции — это вложение денег с целью получить прибыль в будущем.

## Виды инвестиций
- **Депозиты** — низкий риск, низкая доходность
- **Облигации** — средний риск, стабильный доход
- **Акции** — высокий риск, высокая потенциальная доходность
- **Недвижимость** — требует больших вложений
- **ETF/ПИФы** — диверсифицированные портфели

## Главные правила
1. **Не инвестируй последние деньги** — сначала экстренный фонд
2. **Диверсификация** — не клади все яйца в одну корзину
3. **Долгосрочность** — время сглаживает риски
4. **Учись** — понимай куда вкладываешь

## Сложный процент
Главное чудо инвестиций! 100,000₸ под 10% годовых:
- Через 10 лет: 259,000₸
- Через 20 лет: 672,000₸
- Через 30 лет: 1,744,000₸

## С чего начать?
1. Создай экстренный фонд
2. Погаси дорогие кредиты
3. Начни с депозитов или ETF
4. Инвестируй регулярно, даже маленькие суммы
        """,
        "content_kk": "Инвестициялар байлығыңызды өсіруге көмектеседі...",
        "category": "investing",
        "difficulty": "intermediate",
        "xp_reward": 75,
        "order": 5
    }
]

# Quiz data for each lesson
QUIZZES_DATA = {
    "lesson_1": {
        "questions": [
            {
                "id": "q1_1",
                "question_ru": "Что такое правило 50/30/20?",
                "question_en": "What is the 50/30/20 rule?",
                "question_kk": "50/30/20 ережесі дегеніміз не?",
                "options_ru": [
                    "50% сбережения, 30% расходы, 20% развлечения",
                    "50% необходимое, 30% желания, 20% сбережения",
                    "50% еда, 30% транспорт, 20% жильё",
                    "50% доходы, 30% расходы, 20% налоги"
                ],
                "options_en": [
                    "50% savings, 30% expenses, 20% entertainment",
                    "50% needs, 30% wants, 20% savings",
                    "50% food, 30% transport, 20% housing",
                    "50% income, 30% expenses, 20% taxes"
                ],
                "options_kk": [
                    "50% жинақ, 30% шығындар, 20% ойын-сауық",
                    "50% қажеттіліктер, 30% тілектер, 20% жинақ",
                    "50% тамақ, 30% көлік, 20% тұрғын үй",
                    "50% табыс, 30% шығындар, 20% салықтар"
                ],
                "correct": 1
            },
            {
                "id": "q1_2",
                "question_ru": "Как часто нужно проверять бюджет?",
                "question_en": "How often should you check your budget?",
                "question_kk": "Бюджетті қаншалықты жиі тексеру керек?",
                "options_ru": ["Раз в год", "Раз в месяц", "Каждую неделю", "Никогда"],
                "options_en": ["Once a year", "Once a month", "Every week", "Never"],
                "options_kk": ["Жылына бір рет", "Айына бір рет", "Әр апта сайын", "Ешқашан"],
                "correct": 2
            },
            {
                "id": "q1_3",
                "question_ru": "Что нужно записывать в бюджет?",
                "question_en": "What should you record in your budget?",
                "question_kk": "Бюджетке нені жазу керек?",
                "options_ru": [
                    "Только крупные расходы",
                    "Только доходы",
                    "Все расходы, даже мелкие",
                    "Только кредиты"
                ],
                "options_en": [
                    "Only large expenses",
                    "Only income",
                    "All expenses, even small ones",
                    "Only loans"
                ],
                "options_kk": [
                    "Тек үлкен шығындар",
                    "Тек табыстар",
                    "Барлық шығындар, тіпті ұсақтары да",
                    "Тек несиелер"
                ],
                "correct": 2
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    },
    "lesson_2": {
        "questions": [
            {
                "id": "q2_1",
                "question_ru": "Что означает 'Заплати себе первым'?",
                "question_en": "What does 'Pay yourself first' mean?",
                "question_kk": "'Алдымен өзіңе төле' дегеніміз не?",
                "options_ru": [
                    "Купить себе подарок",
                    "Сначала отложить на сбережения, потом тратить",
                    "Погасить все долги",
                    "Заплатить за жильё"
                ],
                "options_en": [
                    "Buy yourself a gift",
                    "Save first, then spend",
                    "Pay off all debts",
                    "Pay for housing"
                ],
                "options_kk": [
                    "Өзіңе сыйлық сатып алу",
                    "Алдымен жинақта, содан кейін жұмса",
                    "Барлық қарыздарды өтеу",
                    "Тұрғын үй үшін төлеу"
                ],
                "correct": 1
            },
            {
                "id": "q2_2",
                "question_ru": "Сколько месяцев расходов должен покрывать экстренный фонд?",
                "question_en": "How many months of expenses should an emergency fund cover?",
                "question_kk": "Төтенше қор шығындардың қанша айын жабуы керек?",
                "options_ru": ["1 месяц", "3-6 месяцев", "12 месяцев", "24 месяца"],
                "options_en": ["1 month", "3-6 months", "12 months", "24 months"],
                "options_kk": ["1 ай", "3-6 ай", "12 ай", "24 ай"],
                "correct": 1
            },
            {
                "id": "q2_3",
                "question_ru": "Что такое правило 24 часов?",
                "question_en": "What is the 24-hour rule?",
                "question_kk": "24 сағат ережесі дегеніміз не?",
                "options_ru": [
                    "Спать 24 часа",
                    "Подождать 24 часа перед крупной покупкой",
                    "Работать 24 часа",
                    "Копить 24 часа"
                ],
                "options_en": [
                    "Sleep for 24 hours",
                    "Wait 24 hours before a big purchase",
                    "Work for 24 hours",
                    "Save for 24 hours"
                ],
                "options_kk": [
                    "24 сағат ұйықтау",
                    "Үлкен сатып алу алдында 24 сағат күту",
                    "24 сағат жұмыс істеу",
                    "24 сағат жинақтау"
                ],
                "correct": 1
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    },
    "lesson_3": {
        "questions": [
            {
                "id": "q3_1",
                "question_ru": "Какой процент дохода должен составлять максимальный ежемесячный платёж по кредиту?",
                "question_en": "What percentage of income should the maximum monthly loan payment be?",
                "question_kk": "Несие бойынша ең жоғары айлық төлем табыстың қанша пайызын құрауы керек?",
                "options_ru": ["10%", "30%", "50%", "70%"],
                "options_en": ["10%", "30%", "50%", "70%"],
                "options_kk": ["10%", "30%", "50%", "70%"],
                "correct": 1
            },
            {
                "id": "q3_2",
                "question_ru": "Когда кредит НЕ оправдан?",
                "question_en": "When is a loan NOT justified?",
                "question_kk": "Несие қашан ақталмайды?",
                "options_ru": [
                    "На покупку жилья",
                    "На образование",
                    "На отпуск и развлечения",
                    "На лечение"
                ],
                "options_en": [
                    "For buying a house",
                    "For education",
                    "For vacation and entertainment",
                    "For medical treatment"
                ],
                "options_kk": [
                    "Тұрғын үй сатып алуға",
                    "Білім алуға",
                    "Демалыс пен ойын-сауыққа",
                    "Емделуге"
                ],
                "correct": 2
            }
        ],
        "pass_threshold": 1,
        "xp_reward": 100
    },
    "lesson_4": {
        "questions": [
            {
                "id": "q4_1",
                "question_ru": "Что означает буква S в SMART целях?",
                "question_en": "What does the S in SMART goals stand for?",
                "question_kk": "SMART мақсаттарындағы S әрпі нені білдіреді?",
                "options_ru": ["Simple (Простая)", "Specific (Конкретная)", "Strong (Сильная)", "Smart (Умная)"],
                "options_en": ["Simple", "Specific", "Strong", "Smart"],
                "options_kk": ["Қарапайым", "Нақты", "Күшті", "Ақылды"],
                "correct": 1
            },
            {
                "id": "q4_2",
                "question_ru": "Какая цель является SMART?",
                "question_en": "Which goal is SMART?",
                "question_kk": "Қай мақсат SMART болып табылады?",
                "options_ru": [
                    "Хочу быть богатым",
                    "Накопить много денег",
                    "Накопить 500,000₸ за 6 месяцев на отпуск",
                    "Когда-нибудь куплю машину"
                ],
                "options_en": [
                    "I want to be rich",
                    "Save a lot of money",
                    "Save 500,000₸ in 6 months for vacation",
                    "Someday I'll buy a car"
                ],
                "options_kk": [
                    "Бай болғым келеді",
                    "Көп ақша жинау",
                    "Демалысқа 6 айда 500,000₸ жинау",
                    "Бір күні машина сатып аламын"
                ],
                "correct": 2
            }
        ],
        "pass_threshold": 1,
        "xp_reward": 100
    },
    "lesson_5": {
        "questions": [
            {
                "id": "q5_1",
                "question_ru": "С чего лучше начать инвестирование новичку?",
                "question_en": "What's the best way for a beginner to start investing?",
                "question_kk": "Жаңадан бастаушыға инвестициялауды неден бастаған дұрыс?",
                "options_ru": [
                    "Сразу купить акции",
                    "Вложить все в криптовалюту",
                    "Сначала создать экстренный фонд",
                    "Взять кредит и инвестировать"
                ],
                "options_en": [
                    "Buy stocks immediately",
                    "Invest everything in crypto",
                    "First create an emergency fund",
                    "Take a loan and invest"
                ],
                "options_kk": [
                    "Бірден акциялар сатып алу",
                    "Барлығын криптовалютаға салу",
                    "Алдымен төтенше қор құру",
                    "Несие алып, инвестициялау"
                ],
                "correct": 2
            },
            {
                "id": "q5_2",
                "question_ru": "Что такое диверсификация?",
                "question_en": "What is diversification?",
                "question_kk": "Әртараптандыру дегеніміз не?",
                "options_ru": [
                    "Вложить все деньги в одну акцию",
                    "Распределить инвестиции по разным активам",
                    "Продать все инвестиции",
                    "Инвестировать только в депозиты"
                ],
                "options_en": [
                    "Put all money in one stock",
                    "Spread investments across different assets",
                    "Sell all investments",
                    "Invest only in deposits"
                ],
                "options_kk": [
                    "Барлық ақшаны бір акцияға салу",
                    "Инвестицияларды әртүрлі активтерге бөлу",
                    "Барлық инвестицияларды сату",
                    "Тек депозиттерге инвестициялау"
                ],
                "correct": 1
            },
            {
                "id": "q5_3",
                "question_ru": "Что такое сложный процент?",
                "question_en": "What is compound interest?",
                "question_kk": "Күрделі пайыз дегеніміз не?",
                "options_ru": [
                    "Очень высокий процент",
                    "Проценты начисляются на проценты",
                    "Сложные математические расчёты",
                    "Процент за просрочку"
                ],
                "options_en": [
                    "Very high interest",
                    "Interest earned on interest",
                    "Complex math calculations",
                    "Late payment interest"
                ],
                "options_kk": [
                    "Өте жоғары пайыз",
                    "Пайызға пайыз есептеледі",
                    "Күрделі математикалық есептеулер",
                    "Кешіктіргені үшін пайыз"
                ],
                "correct": 1
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    }
}


def get_level_info(xp: int) -> dict:
    """Get level info based on XP"""
    current_level = LEVELS[0]
    for level in LEVELS:
        if xp >= level["min_xp"]:
            current_level = level
    return current_level


async def get_or_create_progress(db, user_id: str) -> dict:
    """Get or create user progress document"""
    progress = await db.user_progress.find_one({"user_id": user_id})
    
    if not progress:
        progress = {
            "user_id": user_id,
            "xp": 0,
            "level": 1,
            "level_name": "Новичок",
            "level_name_en": "Beginner",
            "level_name_kk": "Жаңадан бастаушы",
            "completed_lessons": [],
            "completed_quizzes": [],
            "achievements": [],
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
            "total_quizzes_passed": 0,
            "total_lessons_completed": 0
        }
        await db.user_progress.insert_one(progress)
    
    return progress


async def update_streak(db, user_id: str, progress: dict) -> tuple:
    """Update user streak and return (new_streak, xp_earned)"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    
    last_activity = progress.get("last_activity_date")
    current_streak = progress.get("current_streak", 0)
    xp_earned = 0
    
    if last_activity == today:
        # Already checked in today
        return current_streak, 0
    elif last_activity == yesterday:
        # Continuing streak
        current_streak += 1
        xp_earned = 10 + (current_streak * 2)  # Bonus for longer streaks
    else:
        # Streak broken or first time
        current_streak = 1
        xp_earned = 10
    
    longest_streak = max(progress.get("longest_streak", 0), current_streak)
    
    await db.user_progress.update_one(
        {"user_id": user_id},
        {"$set": {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_activity_date": today
        }}
    )
    
    return current_streak, xp_earned


async def check_achievements(db, user_id: str, progress: dict) -> List[str]:
    """Check and award new achievements"""
    new_achievements = []
    current_achievements = progress.get("achievements", [])
    
    for ach in ACHIEVEMENTS:
        if ach["id"] in current_achievements:
            continue
            
        earned = False
        
        if ach["type"] == "lessons":
            if progress.get("total_lessons_completed", 0) >= ach["value"]:
                earned = True
        elif ach["type"] == "quizzes":
            if progress.get("total_quizzes_passed", 0) >= ach["value"]:
                earned = True
        elif ach["type"] == "streak":
            if progress.get("current_streak", 0) >= ach["value"]:
                earned = True
        elif ach["type"] == "xp":
            if progress.get("xp", 0) >= ach["value"]:
                earned = True
        elif ach["type"] == "goals":
            goals_count = await db.goals.count_documents({"user_id": user_id})
            if goals_count >= ach["value"]:
                earned = True
        
        if earned:
            new_achievements.append(ach["id"])
            # Award XP for achievement
            await add_xp(db, user_id, ach["xp"])
    
    if new_achievements:
        await db.user_progress.update_one(
            {"user_id": user_id},
            {"$push": {"achievements": {"$each": new_achievements}}}
        )
    
    return new_achievements


async def add_xp(db, user_id: str, xp_amount: int):
    """Add XP to user and update level"""
    progress = await db.user_progress.find_one({"user_id": user_id})
    new_xp = progress.get("xp", 0) + xp_amount
    level_info = get_level_info(new_xp)
    
    await db.user_progress.update_one(
        {"user_id": user_id},
        {"$set": {
            "xp": new_xp,
            "level": level_info["level"],
            "level_name": level_info["name"],
            "level_name_en": level_info["name_en"],
            "level_name_kk": level_info["name_kk"]
        }}
    )


# API Routes

@router.get("/lessons")
async def get_lessons(request: Request):
    """Get all lessons with completion status"""
    db = get_database()
    user = await get_current_user(request, db)
    progress = await get_or_create_progress(db, user["id"])
    
    completed = progress.get("completed_lessons", [])
    
    lessons = []
    for lesson in LESSONS_DATA:
        lessons.append({
            "id": lesson["id"],
            "title": lesson["title_ru"],
            "title_en": lesson["title_en"],
            "title_kk": lesson["title_kk"],
            "description": lesson["desc_ru"],
            "description_en": lesson["desc_en"],
            "description_kk": lesson["desc_kk"],
            "category": lesson["category"],
            "difficulty": lesson["difficulty"],
            "xp_reward": lesson["xp_reward"],
            "order": lesson["order"],
            "is_completed": lesson["id"] in completed
        })
    
    return sorted(lessons, key=lambda x: x["order"])


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str, request: Request):
    """Get single lesson content"""
    db = get_database()
    user = await get_current_user(request, db)
    progress = await get_or_create_progress(db, user["id"])
    
    lesson = next((l for l in LESSONS_DATA if l["id"] == lesson_id), None)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    completed = progress.get("completed_lessons", [])
    
    return {
        "id": lesson["id"],
        "title": lesson["title_ru"],
        "title_en": lesson["title_en"],
        "title_kk": lesson["title_kk"],
        "content": lesson["content_ru"],
        "content_en": lesson["content_en"],
        "content_kk": lesson["content_kk"],
        "category": lesson["category"],
        "difficulty": lesson["difficulty"],
        "xp_reward": lesson["xp_reward"],
        "is_completed": lesson["id"] in completed,
        "has_quiz": lesson["id"] in QUIZZES_DATA
    }


@router.post("/lessons/{lesson_id}/complete")
async def complete_lesson(lesson_id: str, request: Request):
    """Mark lesson as completed and award XP"""
    db = get_database()
    user = await get_current_user(request, db)
    progress = await get_or_create_progress(db, user["id"])
    
    lesson = next((l for l in LESSONS_DATA if l["id"] == lesson_id), None)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    completed = progress.get("completed_lessons", [])
    xp_earned = 0
    
    if lesson_id not in completed:
        xp_earned = lesson["xp_reward"]
        await db.user_progress.update_one(
            {"user_id": user["id"]},
            {
                "$push": {"completed_lessons": lesson_id},
                "$inc": {"total_lessons_completed": 1}
            }
        )
        await add_xp(db, user["id"], xp_earned)
    
    # Update streak
    streak, streak_xp = await update_streak(db, user["id"], progress)
    xp_earned += streak_xp
    
    # Check for new achievements
    updated_progress = await db.user_progress.find_one({"user_id": user["id"]})
    new_achievements = await check_achievements(db, user["id"], updated_progress)
    
    return {
        "success": True,
        "xp_earned": xp_earned,
        "new_achievements": new_achievements,
        "streak": streak
    }


@router.get("/lessons/{lesson_id}/quiz")
async def get_quiz(lesson_id: str, request: Request):
    """Get quiz questions for a lesson"""
    db = get_database()
    user = await get_current_user(request, db)
    
    if lesson_id not in QUIZZES_DATA:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    quiz = QUIZZES_DATA[lesson_id]
    
    # Return questions without correct answers
    questions = []
    for q in quiz["questions"]:
        questions.append({
            "id": q["id"],
            "question": q["question_ru"],
            "question_en": q["question_en"],
            "question_kk": q["question_kk"],
            "options": q["options_ru"],
            "options_en": q["options_en"],
            "options_kk": q["options_kk"]
        })
    
    return {
        "lesson_id": lesson_id,
        "questions": questions,
        "total_questions": len(questions),
        "pass_threshold": quiz["pass_threshold"],
        "xp_reward": quiz["xp_reward"]
    }


@router.post("/lessons/{lesson_id}/quiz/submit")
async def submit_quiz(lesson_id: str, submission: QuizSubmit, request: Request):
    """Submit quiz answers and get results"""
    db = get_database()
    user = await get_current_user(request, db)
    progress = await get_or_create_progress(db, user["id"])
    
    if lesson_id not in QUIZZES_DATA:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    quiz = QUIZZES_DATA[lesson_id]
    questions = quiz["questions"]
    
    if len(submission.answers) != len(questions):
        raise HTTPException(status_code=400, detail="Invalid number of answers")
    
    # Calculate score
    correct = 0
    for i, q in enumerate(questions):
        if submission.answers[i] == q["correct"]:
            correct += 1
    
    passed = correct >= quiz["pass_threshold"]
    xp_earned = 0
    
    completed_quizzes = progress.get("completed_quizzes", [])
    
    if passed and lesson_id not in completed_quizzes:
        xp_earned = quiz["xp_reward"]
        await db.user_progress.update_one(
            {"user_id": user["id"]},
            {
                "$push": {"completed_quizzes": lesson_id},
                "$inc": {"total_quizzes_passed": 1}
            }
        )
        await add_xp(db, user["id"], xp_earned)
    
    # Update streak
    streak, streak_xp = await update_streak(db, user["id"], progress)
    xp_earned += streak_xp
    
    # Check for new achievements
    updated_progress = await db.user_progress.find_one({"user_id": user["id"]})
    new_achievements = await check_achievements(db, user["id"], updated_progress)
    
    return {
        "correct": correct,
        "total": len(questions),
        "passed": passed,
        "xp_earned": xp_earned,
        "new_achievements": new_achievements,
        "streak": streak
    }


@router.get("/progress")
async def get_progress(request: Request):
    """Get user's learning progress"""
    db = get_database()
    user = await get_current_user(request, db)
    progress = await get_or_create_progress(db, user["id"])
    
    # Calculate next level XP
    current_xp = progress.get("xp", 0)
    current_level = progress.get("level", 1)
    
    next_level_xp = None
    for level in LEVELS:
        if level["level"] > current_level:
            next_level_xp = level["min_xp"]
            break
    
    # Get achievement details
    user_achievements = progress.get("achievements", [])
    achievements_details = []
    for ach in ACHIEVEMENTS:
        achievements_details.append({
            "id": ach["id"],
            "name": ach["name_ru"],
            "name_en": ach["name_en"],
            "name_kk": ach["name_kk"],
            "description": ach["desc_ru"],
            "description_en": ach["desc_en"],
            "description_kk": ach["desc_kk"],
            "icon": ach["icon"],
            "earned": ach["id"] in user_achievements
        })
    
    return {
        "xp": current_xp,
        "level": current_level,
        "level_name": progress.get("level_name", "Новичок"),
        "level_name_en": progress.get("level_name_en", "Beginner"),
        "level_name_kk": progress.get("level_name_kk", "Жаңадан бастаушы"),
        "next_level_xp": next_level_xp,
        "current_streak": progress.get("current_streak", 0),
        "longest_streak": progress.get("longest_streak", 0),
        "total_lessons_completed": progress.get("total_lessons_completed", 0),
        "total_quizzes_passed": progress.get("total_quizzes_passed", 0),
        "completed_lessons": progress.get("completed_lessons", []),
        "completed_quizzes": progress.get("completed_quizzes", []),
        "achievements": achievements_details,
        "total_lessons": len(LESSONS_DATA)
    }


@router.post("/daily-checkin")
async def daily_checkin(request: Request):
    """Daily check-in for streak"""
    db = get_database()
    user = await get_current_user(request, db)
    progress = await get_or_create_progress(db, user["id"])
    
    streak, xp_earned = await update_streak(db, user["id"], progress)
    
    # Check for streak achievements
    updated_progress = await db.user_progress.find_one({"user_id": user["id"]})
    new_achievements = await check_achievements(db, user["id"], updated_progress)
    
    return {
        "streak": streak,
        "xp_earned": xp_earned,
        "new_achievements": new_achievements
    }


@router.get("/achievements")
async def get_achievements(request: Request):
    """Get all achievements with user's progress"""
    db = get_database()
    user = await get_current_user(request, db)
    progress = await get_or_create_progress(db, user["id"])
    
    user_achievements = progress.get("achievements", [])
    
    achievements = []
    for ach in ACHIEVEMENTS:
        achievements.append({
            "id": ach["id"],
            "name": ach["name_ru"],
            "name_en": ach["name_en"],
            "name_kk": ach["name_kk"],
            "description": ach["desc_ru"],
            "description_en": ach["desc_en"],
            "description_kk": ach["desc_kk"],
            "icon": ach["icon"],
            "xp_reward": ach["xp"],
            "earned": ach["id"] in user_achievements
        })
    
    return achievements