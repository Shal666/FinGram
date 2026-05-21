from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from typing import List, Optional

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
    {"level": 6, "min_xp": 8000, "name": "Легенда", "name_en": "Legend", "name_kk": "Аңыз"},
]

# Achievements
ACHIEVEMENTS = [
    {"id": "first_lesson", "name_ru": "Первый шаг", "name_en": "First Step", "name_kk": "Алғашқы қадам",
     "desc_ru": "Пройди первый урок", "desc_en": "Complete first lesson", "desc_kk": "Алғашқы сабақты өт",
     "icon": "🎯", "xp": 50, "type": "lessons", "value": 1},
    {"id": "five_lessons", "name_ru": "Студент", "name_en": "Student", "name_kk": "Студент",
     "desc_ru": "Пройди 5 уроков", "desc_en": "Complete 5 lessons", "desc_kk": "5 сабақты өт",
     "icon": "📚", "xp": 100, "type": "lessons", "value": 5},
    {"id": "all_lessons", "name_ru": "Выпускник", "name_en": "Graduate", "name_kk": "Түлек",
     "desc_ru": "Пройди все 9 уроков", "desc_en": "Complete all 9 lessons", "desc_kk": "9 сабақтың барлығын өт",
     "icon": "🎓", "xp": 300, "type": "lessons", "value": 9},
    {"id": "first_quiz", "name_ru": "Испытатель", "name_en": "Challenger", "name_kk": "Сынақшы",
     "desc_ru": "Пройди первый квиз", "desc_en": "Pass first quiz", "desc_kk": "Алғашқы квизді өт",
     "icon": "✅", "xp": 50, "type": "quizzes", "value": 1},
    {"id": "five_quizzes", "name_ru": "Знаток", "name_en": "Expert", "name_kk": "Білгір",
     "desc_ru": "Пройди 5 квизов", "desc_en": "Pass 5 quizzes", "desc_kk": "5 квизді өт",
     "icon": "🧠", "xp": 150, "type": "quizzes", "value": 5},
    {"id": "all_quizzes", "name_ru": "Мастер квизов", "name_en": "Quiz Master", "name_kk": "Квиз шебері",
     "desc_ru": "Пройди все 9 квизов", "desc_en": "Pass all 9 quizzes", "desc_kk": "9 квиздің барлығын өт",
     "icon": "🏆", "xp": 300, "type": "quizzes", "value": 9},
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
    {"id": "xp_5000", "name_ru": "Богач", "name_en": "Wealthy", "name_kk": "Бай",
     "desc_ru": "Набери 5000 XP", "desc_en": "Earn 5000 XP", "desc_kk": "5000 XP жина",
     "icon": "💎", "xp": 500, "type": "xp", "value": 5000},
    {"id": "first_goal", "name_ru": "Целеустремлённый", "name_en": "Goal Setter", "name_kk": "Мақсатқа ұмтылушы",
     "desc_ru": "Создай первую цель", "desc_en": "Create first goal", "desc_kk": "Алғашқы мақсатты құр",
     "icon": "🎯", "xp": 50, "type": "goals", "value": 1},
]

# 9 Lessons matching real videos
LESSONS_DATA = [
    {
        "id": "lesson_1",
        "title_en": "Why The Rich Are Getting Richer",
        "title_ru": "Почему богатые становятся ещё богаче",
        "title_kk": "Байлар неге одан сайын байи түседі",
        "desc_en": "Discover why the wealthy keep growing their fortune while others stay broke.",
        "desc_ru": "Узнай почему богатые продолжают богатеть, а остальные остаются без денег.",
        "desc_kk": "Байлардың неліктен үнемі байи түсетінін, ал басқалардың ақшасыз қалатынын біл.",
        "video_url": "videos/lesson1.mp4",
        "video_poster": "videos/posters/lesson1.png",
        "video_description_en": "In this lesson you will learn the real difference between how the rich and the poor think about money — and why wealth compounds for those who own assets.",
        "video_description_ru": "В этом уроке ты узнаешь реальную разницу в том, как богатые и бедные думают о деньгах, и почему капитал растёт у тех, кто владеет активами.",
        "video_description_kk": "Бұл сабақта байлар мен кедейлердің ақша туралы ойлауындағы нақты айырмашылықты және капитал актив иелерінде неліктен өсетінін білесің.",
        "content_ru": """
# Почему богатые становятся ещё богаче

## Главный секрет

Богатые покупают **активы**, а бедные — **обязательства**, которые маскируются под активы.

## 3 принципа богатых

1. **Деньги работают на них** — а не наоборот
2. **Долгосрочное мышление** — горизонт 10-20 лет
3. **Реинвестирование** — прибыль снова в дело

## Что делают бедные

- Тратят всю зарплату
- Берут кредиты на потребление
- Покупают вещи, чтобы казаться богаче
- Думают только о следующей зарплате

## Что делают богатые

- Сначала откладывают, потом тратят
- Берут кредиты только на активы
- Покупают вещи только тогда, когда могут это себе позволить дважды
- Думают десятилетиями

## 💡 Главный урок

Богатство — это не размер зарплаты, а **разница между доходами и расходами**, умноженная на время.
""",
        "content_en": """
# Why The Rich Are Getting Richer

## The main secret

The rich buy **assets**, the poor buy **liabilities** disguised as assets.

## 3 principles of the wealthy

1. **Money works for them** — not the other way around
2. **Long-term thinking** — 10-20 year horizon
3. **Reinvesting** — profits back into the game

## What the poor do

- Spend the entire paycheck
- Take consumer loans
- Buy things to look richer
- Think only about the next paycheck

## What the rich do

- Save first, spend what's left
- Borrow only to buy assets
- Buy things only when they can afford them twice
- Think in decades

## 💡 Key takeaway

Wealth is not the size of your salary — it's the **gap between income and expenses**, multiplied by time.
""",
        "content_kk": """
# Байлар неге одан сайын байи түседі

## Басты құпия

Байлар **активтерді**, ал кедейлер активтерге ұқсайтын **міндеттемелерді** сатып алады.

## Байлардың 3 қағидасы

1. **Ақша оларға жұмыс істейді** — керісінше емес
2. **Ұзақ мерзімді ойлау** — 10-20 жылға дейін
3. **Қайта инвестициялау** — пайданы қайта іске қосу

## Кедейлер не істейді

- Бүкіл айлықты жұмсайды
- Тұтыну несиелерін алады
- Бай болып көріну үшін заттар сатып алады

## Байлар не істейді

- Алдымен жинақтайды, сосын жұмсайды
- Тек активтерге ғана несие алады
- Заттарды екі рет алуға қаражаты болғанда сатып алады

## 💡 Басты сабақ

Байлық — бұл айлықтың мөлшері емес, ал **табыс пен шығынның арасындағы айырмашылық** уақытқа көбейтілген.
""",
        "category": "basics",
        "difficulty": "beginner",
        "xp_reward": 50,
        "order": 1
    },
    {
        "id": "lesson_2",
        "title_en": "The 50/30/20 Rule",
        "title_ru": "Правило 50/30/20",
        "title_kk": "50/30/20 ережесі",
        "desc_en": "The simplest budgeting rule to control your money.",
        "desc_ru": "Самое простое правило бюджета для контроля своих денег.",
        "desc_kk": "Ақшаңды бақылауға арналған ең қарапайым бюджет ережесі.",
        "video_url": "videos/lesson2.mp4",
        "video_poster": "videos/posters/lesson2.png",
        "video_description_en": "Learn how to split your income into needs, wants and savings using the famous 50/30/20 rule — and why it works for any salary.",
        "video_description_ru": "Узнай как разделить доход на нужды, желания и накопления по знаменитому правилу 50/30/20 — и почему оно работает при любой зарплате.",
        "video_description_kk": "Әйгілі 50/30/20 ережесі бойынша табысты қажеттіліктер, тілектер және жинақтарға қалай бөлуге болатынын және оның кез келген айлықта неге жұмыс істейтінін біл.",
        "content_ru": """
# Правило 50/30/20

## Формула

| Категория | % | Что включает |
|-----------|---|--------------|
| **50% Нужды** | Половина | Жильё, еда, транспорт, коммуналка |
| **30% Желания** | Треть | Рестораны, развлечения, хобби |
| **20% Накопления** | Пятая часть | Сбережения, погашение долгов, инвестиции |

## Пример при доходе 300,000₸

- **Нужды:** 150,000₸
- **Желания:** 90,000₸
- **Накопления:** 60,000₸

## Почему именно так?

- **50%** — реальный минимум для жизни в большом городе
- **30%** — нужны для качества жизни (иначе сорвёшься)
- **20%** — минимум для накопления капитала за разумный срок

## Главная ошибка

Большинство людей живут по схеме **80/20/0** — тратят всё, а копят "когда останется". Не остаётся никогда.

## 💡 Лайфхак

Откладывай **20% автоматом** в день зарплаты — до того, как начнёшь тратить.
""",
        "content_en": """
# The 50/30/20 Rule

## The formula

| Category | % | What it covers |
|----------|---|----------------|
| **50% Needs** | Half | Housing, food, transport, utilities |
| **30% Wants** | Third | Restaurants, entertainment, hobbies |
| **20% Savings** | Fifth | Savings, debt payoff, investing |

## Example on a $1,000 income

- **Needs:** $500
- **Wants:** $300
- **Savings:** $200

## Why this works

- **50%** — realistic survival minimum in a city
- **30%** — quality of life buffer (otherwise you crash)
- **20%** — the minimum to build real wealth in a reasonable time

## The biggest mistake

Most people live on the **80/20/0** model — spending everything and saving "what's left". Nothing is ever left.

## 💡 Pro tip

Move that **20% automatically** on payday — before you start spending.
""",
        "content_kk": """
# 50/30/20 ережесі

## Формула

- **50% қажеттіліктер** — тұрғын үй, тамақ, көлік, коммуналдық
- **30% тілектер** — мейрамхана, ойын-сауық, хобби
- **20% жинақ** — жинақ, қарызды өтеу, инвестициялар

## 300,000₸ табысқа мысал

- Қажеттіліктер: 150,000₸
- Тілектер: 90,000₸
- Жинақ: 60,000₸

## 💡 Кеңес

Айлық алған күні **20%-ды автоматты түрде** жинақ шотыңа аудар — жұмсауды бастамастан бұрын.
""",
        "category": "basics",
        "difficulty": "beginner",
        "xp_reward": 50,
        "order": 2
    },
    {
        "id": "lesson_3",
        "title_en": "Why Credits Make People Poorer",
        "title_ru": "Почему кредиты делают людей беднее",
        "title_kk": "Несиелер адамдарды неге кедейлендіреді",
        "desc_en": "The dark side of credit cards and consumer loans.",
        "desc_ru": "Тёмная сторона кредитных карт и потребительских кредитов.",
        "desc_kk": "Несие карталары мен тұтыну несиелерінің қараңғы жағы.",
        "video_url": "videos/lesson3.mp4",
        "video_poster": "videos/posters/lesson3.png",
        "video_description_en": "Find out how interest, minimum payments and consumer loans silently drain your future income — and how to break the cycle.",
        "video_description_ru": "Узнай как проценты, минимальные платежи и потребительские кредиты тихо забирают твой будущий доход — и как разорвать этот круг.",
        "video_description_kk": "Пайыздар, минималды төлемдер және тұтыну несиелері келешек табысыңды қалай үнсіз тартып алатынын және бұл шеңберді қалай үзуге болатынын біл.",
        "content_ru": """
# Почему кредиты делают людей беднее

## Главный обман

Кредит даёт тебе **сегодня** то, что ты пока **не заработал**. Но забирает потом **больше**.

## Математика проигрыша

Телефон за **300,000₸** в рассрочку 24 месяца под 25%:
- Платёж: ~16,000₸/мес
- Итого: **384,000₸**
- Переплата: **84,000₸**

За 2 года телефон **устарел и стоит 100,000₸** на вторичке. Ты потерял **284,000₸**.

## Почему люди берут кредиты

- 😤 "Хочу прямо сейчас"
- 📺 Реклама создаёт иллюзию доступности
- 💳 Карта = не воспринимаются как настоящие деньги
- 🔁 Один кредит закрывают другим

## Долговая ловушка

1. Взял кредит на телефон
2. Платишь минимум
3. Карта снова "доступна" — берёшь ещё
4. Платишь по двум
5. Не хватает — берёшь третий
6. **Долговая яма**

## Выход

1. **Стоп новым кредитам**
2. Метод **снежного кома**: гаси самый маленький долг первым
3. Все лишние деньги — на долги
4. Откажись от подписок и доставки на время

## 💡 Правило

> Если не можешь купить дважды — не покупай ни разу в кредит.
""",
        "content_en": """
# Why Credits Make People Poorer

## The hidden trick

Credit gives you **today** what you **haven't earned yet**. Then it takes back **more**.

## The math of losing

A $1,500 phone, 24-month installment at 25%:
- Payment: ~$80/mo
- Total paid: **$1,920**
- Overpayment: **$420**

After 2 years the phone is **outdated and worth $400**. You lost **$1,520**.

## Why people borrow

- "I want it now"
- Ads create the illusion of affordability
- Credit cards don't feel like real money
- One loan closes another

## The debt trap

1. Loan for a phone
2. You pay the minimum
3. Card is "available" again — borrow more
4. Pay on two
5. Can't afford it — take a third
6. **Debt spiral**

## The way out

1. **Stop new loans**
2. **Snowball method**: smallest debt first
3. All extra cash → debt payoff
4. Cut subscriptions and delivery temporarily

## 💡 Rule

> If you can't afford to buy it twice — don't buy it on credit.
""",
        "content_kk": """
# Несиелер адамдарды неге кедейлендіреді

## Басты алдау

Несие саған **бүгін** саған әлі **табылмаған** нәрсені береді. Ал кейін **көбірек** қайтарып алады.

## Жеңілістің математикасы

300,000₸-лік телефон 24 айға 25% бойынша:
- Төлем: ~16,000₸/айына
- Жалпы: **384,000₸**
- Артық төлем: **84,000₸**

2 жылдан кейін телефон **ескіріп, 100,000₸-ге** ғана сатылады.

## Шығу жолы

1. **Жаңа несиелерге тоқта**
2. Ең кіші қарыздан баста
3. Артық ақшаны — қарызға
4. Жазылымдарды уақытша тоқтат

## 💡 Ереже

> Егер екі рет сатып ала алмасаң — несиеге де алма.
""",
        "category": "credit",
        "difficulty": "beginner",
        "xp_reward": 75,
        "order": 3
    },
    {
        "id": "lesson_4",
        "title_en": "How Compound Interest Works",
        "title_ru": "Как работает сложный процент",
        "title_kk": "Күрделі пайыз қалай жұмыс істейді",
        "desc_en": "The 8th wonder of the world — explained simply.",
        "desc_ru": "8-е чудо света — простыми словами.",
        "desc_kk": "Әлемнің 8-ші кереметі — қарапайым тілмен.",
        "video_url": "videos/lesson4.mp4",
        "video_poster": "videos/posters/lesson4.png",
        "video_description_en": "See how compound interest turns small monthly deposits into life-changing wealth — and why starting early matters more than starting big.",
        "video_description_ru": "Посмотри как сложный процент превращает маленькие ежемесячные вложения в богатство — и почему начать рано важнее, чем начать с большой суммы.",
        "video_description_kk": "Күрделі пайыз шағын ай сайынғы салымдарды байлыққа қалай айналдыратынын және неліктен ерте бастаудың үлкен сомадан бастаудан маңыздырақ екенін көр.",
        "content_ru": """
# Как работает сложный процент

## Простой vs сложный процент

**Простой**: 10,000₸ под 10% годовых = +1,000₸ каждый год
- Через 10 лет: 20,000₸

**Сложный**: 10,000₸ под 10%, но проценты на проценты
- Через 10 лет: **25,937₸**

## Магия времени

10,000₸ под 10% годовых:
- 5 лет: 16,100₸
- 10 лет: 25,900₸
- 20 лет: 67,300₸
- **30 лет: 174,500₸**
- **40 лет: 452,600₸**

Чем дольше — тем мощнее.

## Правило 72

**72 ÷ ставка = лет до удвоения**

- 10% → удваивается за 7.2 года
- 15% → за 4.8 года
- 20% → за 3.6 года

## Эффект раннего старта

**Айдар:** копит 50,000₸/мес с 20 до 30 лет, потом ничего → к 60 годам ~**150 млн ₸**

**Болат:** копит 50,000₸/мес с 30 до 60 лет → к 60 годам ~**113 млн ₸**

Айдар вложил **в 3 раза меньше**, но выиграл, потому что начал раньше.

## 💡 Главный урок

> Лучшее время начать инвестировать было 10 лет назад. Второе лучшее — сегодня.
""",
        "content_en": """
# How Compound Interest Works

## Simple vs compound

**Simple**: $100 at 10% = +$10 every year
- 10 years: $200

**Compound**: interest on interest
- 10 years: **$259**

## The magic of time

$100 at 10% annual:
- 5 years: $161
- 10 years: $259
- 20 years: $673
- **30 years: $1,745**
- **40 years: $4,526**

The longer — the wilder it gets.

## Rule of 72

**72 ÷ rate = years to double**

- 10% → doubles in 7.2 years
- 15% → in 4.8 years
- 20% → in 3.6 years

## Early start effect

**Adam:** saves $500/mo from 20 to 30, then stops → at 60 ≈ **$1.5M**

**Ben:** saves $500/mo from 30 to 60 → at 60 ≈ **$1.13M**

Adam invested **3× less** but won — because he started earlier.

## 💡 Key takeaway

> The best time to start investing was 10 years ago. The second best is today.
""",
        "content_kk": """
# Күрделі пайыз қалай жұмыс істейді

## Қарапайым vs күрделі пайыз

**Қарапайым**: 10,000₸ × 10% = +1,000₸ жыл сайын
- 10 жылдан кейін: 20,000₸

**Күрделі**: пайызға пайыз
- 10 жылдан кейін: **25,937₸**

## Уақыт сиқыры

10,000₸ × 10% жылдық:
- 5 жыл: 16,100₸
- 20 жыл: 67,300₸
- 30 жыл: 174,500₸
- 40 жыл: 452,600₸

## 72 ережесі

**72 ÷ мөлшерлеме = екі есе көбею жылдары**

10% → 7.2 жыл

## 💡 Басты сабақ

> Инвестициялауды бастаудың ең жақсы уақыты 10 жыл бұрын болған. Екінші ең жақсы уақыт — бүгін.
""",
        "category": "investing",
        "difficulty": "intermediate",
        "xp_reward": 75,
        "order": 4
    },
    {
        "id": "lesson_5",
        "title_en": "People Buy Things to Appear Wealthy",
        "title_ru": "Люди покупают вещи, чтобы казаться богатыми",
        "title_kk": "Адамдар бай болып көріну үшін заттар сатып алады",
        "desc_en": "The psychology of fake wealth and how to escape it.",
        "desc_ru": "Психология фальшивого богатства и как из неё выбраться.",
        "desc_kk": "Жалған байлық психологиясы және одан қалай шығу керек.",
        "video_url": "videos/lesson5.mp4",
        "video_poster": "videos/posters/lesson5.png",
        "video_description_en": "Most luxury buyers are broke. Learn the difference between looking rich and being rich — and stop spending to impress people who don't care.",
        "video_description_ru": "Большинство покупателей люкса — бедные. Узнай разницу между \"казаться богатым\" и \"быть богатым\" — и перестань тратить, чтобы впечатлить тех, кому всё равно.",
        "video_description_kk": "Сән-салтанатқа төлейтіндердің көбісі — кедейлер. \"Бай болып көріну\" мен \"шынында бай болудың\" арасындағы айырмашылықты түсін.",
        "content_ru": """
# Люди покупают вещи, чтобы казаться богатыми

## Парадокс

Реально богатые люди **не выглядят** богато. Они одеваются просто, ездят на простых машинах и не показывают свой статус.

А те, кто хочет **казаться богатым** — носят люкс, который купили в кредит.

## Эффект Веблена

Чем дороже вещь — тем больше хочется показать её другим. Это маркетинговая ловушка для бедных.

## Скрытая стоимость "статуса"

Купил машину за 15 млн в кредит на 7 лет:
- Платёж: ~250,000₸/мес
- Бензин: 50,000₸/мес  
- Страховка/ремонт: 30,000₸/мес
- **Итого: 330,000₸/мес** уходит на машину

Эти же 330,000₸ в индекс под 10%:
- Через 7 лет: **40 млн ₸**

Ты выбираешь между **видимостью богатства** и **настоящим богатством**.

## Закон тихих денег

> Настоящие деньги делают тихо. Если кто-то кричит о своих деньгах — у него их, скорее всего, нет.

## Как выбраться

1. Перестань покупать для других людей
2. Подпишись на меньше "красивых" блогеров
3. Спроси себя: "Купил бы я это, если бы никто не видел?"
4. Замени желание "казаться" на желание "быть"

## 💡 Главный урок

Никто не думает о твоей машине столько, сколько ты сам.
""",
        "content_en": """
# People Buy Things to Appear Wealthy

## The paradox

Truly rich people **don't look** rich. They dress simply, drive simple cars, and don't show off.

The ones who want to **look rich** — wear luxury bought on credit.

## The Veblen effect

The more expensive something is — the more you want to show it off. It's a marketing trap built for the poor.

## The hidden cost of "status"

A $80k car on a 7-year loan:
- Payment: $1,300/mo
- Gas: $250/mo
- Insurance/maintenance: $150/mo
- **Total: $1,700/mo** burned on the car

That same $1,700 in an index fund at 10%:
- After 7 years: **$210,000**

You're choosing between **looking rich** and **being rich**.

## The quiet money rule

> Real money is quiet. If someone is loud about their wealth — they probably don't have it.

## How to escape

1. Stop buying for other people
2. Unfollow flashy influencers
3. Ask: "Would I buy this if no one would see it?"
4. Replace "appear" with "become"

## 💡 Key takeaway

Nobody thinks about your car as much as you do.
""",
        "content_kk": """
# Адамдар бай болып көріну үшін заттар сатып алады

## Парадокс

Шын мәнінде бай адамдар **бай болып көрінбейді**. Олар қарапайым киінеді.

Ал **бай болып көргісі келетіндер** — несиеге алынған сән-салтанат киіп жүреді.

## Жасырын құн

15 млн ₸ машина 7 жылға несиеге:
- Төлем: ~250,000₸/айына
- Жанармай + сақтандыру: 80,000₸/айына
- **Барлығы: 330,000₸/айына**

Сол 330,000₸-ды 10%-бен инвестициялау 7 жылдан кейін: **40 млн ₸**

## 💡 Басты сабақ

Сенің машинаң туралы саған қарағанда басқалар сонша ойламайды.
""",
        "category": "psychology",
        "difficulty": "beginner",
        "xp_reward": 50,
        "order": 5
    },
    {
        "id": "lesson_6",
        "title_en": "The Biggest Mistake Of The Young Generation",
        "title_ru": "Главная ошибка молодого поколения",
        "title_kk": "Жас ұрпақтың басты қателігі",
        "desc_en": "Why most young people stay broke — and how not to.",
        "desc_ru": "Почему большинство молодых остаются без денег — и как этого избежать.",
        "desc_kk": "Жастардың көпшілігі неге ақшасыз қалады — және мұндайдан қалай аулақ болу керек.",
        "video_url": "videos/lesson6.mp4",
        "video_poster": "videos/posters/lesson6.png",
        "video_description_en": "Young people waste their most valuable asset — time. Learn how to use compounding, learning and small habits before everyone else.",
        "video_description_ru": "Молодые тратят свой самый ценный актив — время. Узнай как использовать сложный процент, обучение и привычки раньше остальных.",
        "video_description_kk": "Жастар ең құнды активін — уақытты ысырап етеді. Күрделі пайызды, білім алуды және әдеттерді басқалардан ертерек қалай қолдану керектігін біл.",
        "content_ru": """
# Главная ошибка молодого поколения

## Что это за ошибка?

**Откладывать жизнь "на потом".**

"Начну копить, когда получу повышение"  
"Инвестирую, когда заработаю больше"  
"Подумаю о пенсии в 40"

## Цена этой ошибки

Каждый год без накоплений в 20 лет = **сотни тысяч** к 60 годам.

Откладывать 10,000₸ в месяц с 20 лет = к 60 ~30 млн₸  
Начать в 30 = к 60 ~11 млн₸  
**Разница: 19 млн только за 10 лет промедления**

## 5 ошибок, которые крадут будущее

1. **Кредит на iPhone** — минус 200,000₸ + проценты
2. **Подписки без ограничений** — 15,000₸/мес = 180,000₸/год
3. **Такси каждый день** — 60,000₸/мес
4. **Отсутствие плана** — деньги исчезают незаметно
5. **Игнор инвестиций** — деньги съедает инфляция

## Что делать?

### В 18-25 лет:
- Получи навык, который платит
- Откладывай 20% автоматом
- Не бери потребительских кредитов
- Учись инвестированию

### В 25-30:
- Подушка безопасности на 6 месяцев
- Первые инвестиции в индекс
- Чёткие финансовые цели

### В 30+:
- Бизнес или вторая профессия
- Диверсификация
- Пассивный доход

## 💡 Главный урок

Время — твой главный актив. **Каждый день промедления стоит тебе будущего богатства.**
""",
        "content_en": """
# The Biggest Mistake Of The Young Generation

## The mistake

**Postponing life for "later".**

"I'll start saving when I get promoted"  
"I'll invest when I earn more"  
"I'll think about retirement at 40"

## The price of this mistake

Every year without saving at 20 = **hundreds of thousands** missing at 60.

Saving $100/mo from age 20 = at 60 ≈ $230k  
Starting at 30 = at 60 ≈ $85k  
**Difference: $145k for 10 years of delay**

## 5 mistakes that steal your future

1. **iPhone on credit** — overpayment + interest
2. **Unlimited subscriptions** — $50/mo = $600/yr
3. **Daily taxis** — $200/mo
4. **No plan** — money disappears silently
5. **Ignoring investing** — inflation eats it

## What to do

### Age 18-25:
- Build a paying skill
- Auto-save 20%
- No consumer loans
- Learn investing

### Age 25-30:
- 6-month emergency fund
- First index investments
- Clear financial goals

### Age 30+:
- Business or second career
- Diversification
- Passive income

## 💡 Key takeaway

Time is your biggest asset. **Every day of delay costs you future wealth.**
""",
        "content_kk": """
# Жас ұрпақтың басты қателігі

## Қателік

**Өмірді "кейінге" қалдыру.**

"Жалақы көтерілгенде бастаймын"
"Көп тапқанда инвестициялаймын"

## Не істеу керек?

### 18-25 жаста:
- Ақша әкелетін дағды үйрен
- 20%-ды автоматты түрде сал
- Тұтыну несиелерін алма

### 25-30 жаста:
- 6 айға қауіпсіздік қоры
- Алғашқы инвестициялар

## 💡 Басты сабақ

Уақыт — сенің басты активің. Әр кешіктірілген күн саған болашақ байлықты қымбатқа түсіреді.
""",
        "category": "mindset",
        "difficulty": "beginner",
        "xp_reward": 50,
        "order": 6
    },
    {
        "id": "lesson_7",
        "title_en": "Smart Savings",
        "title_ru": "Умные сбережения",
        "title_kk": "Ақылды жинақтар",
        "desc_en": "Save smarter, not harder.",
        "desc_ru": "Копи умнее, а не больше.",
        "desc_kk": "Көп емес, ақылды жина.",
        "video_url": "videos/lesson7.mp4",
        "video_poster": "videos/posters/lesson7.png",
        "video_description_en": "Saving is not about giving up coffee — it's about systems. Discover the 'pay yourself first' rule and the right place to keep your money.",
        "video_description_ru": "Копить — не значит отказываться от кофе. Это про системы. Узнай правило \"заплати себе первым\" и где правильно хранить деньги.",
        "video_description_kk": "Жинау — кофеден бас тарту емес. Бұл — жүйелер туралы. \"Алдымен өзіңе төле\" ережесін және ақшаны қайда сақтаудың дұрыс екенін біл.",
        "content_ru": """
# Умные сбережения

## Правило №1: Заплати себе первым

Получил зарплату → **сразу** отложи 10-20% → потом трать остальное.

Не наоборот. К концу месяца "остаётся" 0₸ — это аксиома.

## Где хранить деньги?

| Срок | Куда | Доходность |
|------|------|------------|
| До 1 мес | Карта | 0% |
| 1-12 мес | Накопительный счёт | 8-12% |
| 1-3 года | Депозит | 12-15% |
| 3+ года | Инвестиции | 10-20% |

## 3 уровня сбережений

### 1. Подушка (3-6 мес расходов) 🛡️
- Накопительный счёт
- Лёгкий доступ
- Цель: спокойствие

### 2. Цели (отпуск, машина) 🎯
- Депозит
- Срок 6-24 мес

### 3. Инвестиции (пенсия, свобода) 🚀
- Индексы, акции, ETF
- Срок 5+ лет

## Автоматизация

В день зарплаты:
1. Карта → 20% на накопительный счёт
2. Накопительный → 50% от него на депозит
3. Остаток на карте — на жизнь

Ты **не видишь** эти деньги — и не тратишь.

## Что НЕ работает

- ❌ "Копить, что останется"
- ❌ Держать накопления на основной карте
- ❌ Хранить наличку дома
- ❌ Копить без цели

## 💡 Главный урок

> Накопить — это не подвиг. Это **система**. Настрой её один раз — и забудь.
""",
        "content_en": """
# Smart Savings

## Rule #1: Pay yourself first

Get paid → **immediately** move 10-20% → then spend the rest.

Not the other way around. End of month "leftover" = $0. Always.

## Where to keep money

| Term | Where | Yield |
|------|-------|-------|
| < 1 month | Checking | 0% |
| 1-12 mo | Savings account | 4-5% |
| 1-3 yrs | CD / fixed deposit | 5-6% |
| 3+ yrs | Investments | 8-12% |

## 3 layers of savings

### 1. Emergency fund (3-6 months) 🛡️
- Savings account
- Quick access
- Goal: peace of mind

### 2. Goals (vacation, car) 🎯
- Fixed deposit
- 6-24 month term

### 3. Investments (retirement, freedom) 🚀
- Index funds, stocks, ETFs
- 5+ years

## Automation

On payday:
1. Checking → 20% to savings
2. Savings → 50% of that to deposit
3. What's left → life

You **don't see** those funds — so you don't spend them.

## 💡 Key takeaway

> Saving is not a heroic act. It's a **system**. Set it up once — forget it.
""",
        "content_kk": """
# Ақылды жинақтар

## №1 ереже: Алдымен өзіңе төле

Айлық алдың → **бірден** 10-20%-ды бөлек шотқа сал → қалғанын жұмса.

## 3 деңгей жинақ

### 1. Қауіпсіздік қоры (3-6 ай)
### 2. Мақсаттар (демалыс, машина)
### 3. Инвестициялар (зейнетақы, еркіндік)

## 💡 Басты сабақ

> Жинау — ерлік емес. Бұл **жүйе**. Бір рет орнат — ұмыт.
""",
        "category": "saving",
        "difficulty": "beginner",
        "xp_reward": 50,
        "order": 7
    },
    {
        "id": "lesson_8",
        "title_en": "Assets vs Liabilities",
        "title_ru": "Активы и пассивы",
        "title_kk": "Активтер мен міндеттемелер",
        "desc_en": "The most important concept in personal finance.",
        "desc_ru": "Самое важное понятие в личных финансах.",
        "desc_kk": "Жеке қаржыдағы ең маңызды ұғым.",
        "video_url": "videos/lesson8.mp4",
        "video_poster": "videos/posters/lesson8.png",
        "video_description_en": "Robert Kiyosaki's core idea: assets put money in your pocket, liabilities take it out. Learn to tell them apart and stop buying fake assets.",
        "video_description_ru": "Главная идея Кийосаки: активы кладут деньги в карман, пассивы — забирают. Научись отличать одно от другого и перестань покупать псевдо-активы.",
        "video_description_kk": "Кийосакидің басты идеясы: активтер қалтаңа ақша салады, міндеттемелер оны алып кетеді. Айырмашылықты үйрен.",
        "content_ru": """
# Активы и пассивы

## Простое определение

- **Актив** — то, что приносит тебе деньги
- **Пассив** — то, что забирает у тебя деньги

## Примеры активов 📈

- Акции и облигации
- Недвижимость в аренду
- Бизнес
- Авторские права (книги, музыка, патенты)
- Депозиты с процентом

## Примеры пассивов 📉

- Машина (бензин, ремонт, амортизация)
- Дорогая одежда
- Гаджеты в кредит
- Подписки
- Кредитные карты

## Главная ловушка

Люди называют **пассивы активами**:
- "Машина — это актив" ❌ — она теряет в цене и требует расходов
- "Квартира, в которой я живу — актив" ❌ — она забирает деньги (коммуналка, ремонт)

**Только когда что-то приносит доход** — это актив.

## Правило богатых

> Богатые **покупают активы**. Бедные **покупают пассивы**, думая, что это активы. Средний класс **покупает пассивы**, думая, что это активы.

— Роберт Кийосаки

## Как это применить?

Перед покупкой спроси:
1. Принесёт ли это мне деньги в будущем?
2. Или будет постоянно их забирать?

Если **забирать** — это пассив. Возможно, тебе он всё равно нужен (еда, аренда). Но **признавай** это пассивом, а не "инвестицией в себя".

## 💡 Главный урок

Каждый месяц **увеличивай число активов**, не пассивов. Цель: чтобы активы покрывали все твои расходы. Это и есть финансовая свобода.
""",
        "content_en": """
# Assets vs Liabilities

## Simple definition

- **Asset** — puts money in your pocket
- **Liability** — takes money out of your pocket

## Asset examples 📈

- Stocks and bonds
- Rental real estate
- A business
- Royalties (books, music, patents)
- Interest-bearing deposits

## Liability examples 📉

- A car (gas, repairs, depreciation)
- Expensive clothes
- Gadgets on credit
- Subscriptions
- Credit cards

## The big trap

People call **liabilities assets**:
- "My car is an asset" ❌ — it loses value and costs money
- "The house I live in is an asset" ❌ — it drains cash (utilities, repairs)

**Only when something generates income** — it's an asset.

## The rich rule

> The rich **buy assets**. The poor and middle class **buy liabilities** thinking they're assets.

— Robert Kiyosaki

## How to apply

Before buying ask:
1. Will this bring me money in the future?
2. Or will it keep taking?

If **taking** — it's a liability. Maybe you still need it (food, rent). Just **call it** a liability, not "investing in myself."

## 💡 Key takeaway

Every month **add more assets**, not liabilities. The goal: assets cover all your expenses. That's financial freedom.
""",
        "content_kk": """
# Активтер мен міндеттемелер

## Қарапайым анықтама

- **Актив** — саған ақша әкеледі
- **Міндеттеме** — сенен ақша алып кетеді

## Активтер

- Акциялар мен облигациялар
- Жалға беретін жылжымайтын мүлік
- Бизнес
- Авторлық құқықтар

## Міндеттемелер

- Машина
- Қымбат киім
- Несиеге алынған гаджеттер
- Жазылымдар

## 💡 Басты сабақ

Әр ай сайын **активтерді** көбейт, міндеттемелерді емес. Мақсат: активтер барлық шығындарыңды жабсын.
""",
        "category": "investing",
        "difficulty": "intermediate",
        "xp_reward": 75,
        "order": 8
    },
    {
        "id": "lesson_9",
        "title_en": "Impulse Spending Traps",
        "title_ru": "Ловушки импульсивных трат",
        "title_kk": "Импульсивті шығындар тұзақтары",
        "desc_en": "How shops, apps and ads trick you into spending.",
        "desc_ru": "Как магазины, приложения и реклама заставляют тебя тратить.",
        "desc_kk": "Дүкендер, қосымшалар мен жарнамалар саған қалай ақша жұмсатады.",
        "video_url": "videos/lesson9.mp4",
        "video_poster": "videos/posters/lesson9.png",
        "video_description_en": "From 'limited offers' to one-click checkouts — see the exact psychological tricks designed to drain your wallet, and how to fight back.",
        "video_description_ru": "От \"ограниченных предложений\" до покупок в один клик — увидь конкретные психологические трюки, которые опустошают кошелёк, и как им противостоять.",
        "video_description_kk": "\"Шектеулі ұсыныстардан\" бір рет басумен сатып алуға дейін — әмияныңды босататын психологиялық айла-шарғыларды көр.",
        "content_ru": """
# Ловушки импульсивных трат

## Что такое импульсивная трата?

Покупка, которую **ты не планировал**, и о которой через неделю **жалеешь**.

По статистике — **40% всех расходов** именно такие.

## 7 трюков, которые тебя обманывают

### 1. "Скидка только сегодня!"
Создаёт ложное чувство срочности. Скидка будет и завтра.

### 2. Перечёркнутая старая цена
Магазин сначала поднял цену, потом "снизил".

### 3. "Купи 2 — получи 3"
Ты купил то, что было не нужно, чтобы получить "бесплатно".

### 4. Товары у кассы
Шоколадки, журналы, мелочи — собраны там, где ты ждёшь очередь.

### 5. Покупка в один клик
Чем легче платить — тем больше тратишь. Apple Pay делает деньги "невидимыми".

### 6. Бесплатная доставка от Х₸
Ты докидываешь товары, чтобы "сэкономить" 1500₸ на доставке.

### 7. Подписки с пробным периодом
Забыл отменить → платишь годами.

## Как защититься

### Правило 24 часов
Хочешь купить что-то дороже 10,000₸? Подожди сутки. В 50% случаев желание пройдёт.

### Правило 30 дней
Для крупных покупок (> 50,000₸) — жди месяц.

### Список покупок
В магазин — только со списком. Что нет в списке — не покупаем.

### Удалить карту из браузера
Каждый раз вводи реквизиты вручную. Это трение спасёт тысячи.

### Отписаться от рассылок
Меньше "акций" в почте = меньше соблазнов.

## Цена за использование

Куртка 50,000₸:
- Носишь 2 сезона, 60 раз = **833₸/раз** ✅
- Носишь 3 раза = **16,666₸/раз** ❌

## 💡 Главный урок

> Лучшая покупка — это та, которую ты **не сделал**. Каждые сэкономленные 5,000₸ под 10% за 30 лет = ~87,000₸.
""",
        "content_en": """
# Impulse Spending Traps

## What is an impulse purchase?

Something you **didn't plan** to buy and **regret a week later**.

Stats say — **40% of all spending** is exactly this.

## 7 tricks fooling you

### 1. "Today only!"
Fake urgency. The deal will be there tomorrow.

### 2. Crossed-out old price
The store raised the price first, then "lowered" it.

### 3. "Buy 2 get 3"
You bought what you didn't need to get "free".

### 4. Items by the checkout
Snacks, magazines, small stuff — placed where you wait in line.

### 5. One-click checkout
The easier paying is — the more you spend. Apple Pay makes money "invisible".

### 6. Free shipping from $X
You add items to "save" $15 on shipping.

### 7. Free trial subscriptions
You forgot to cancel → you pay for years.

## How to fight back

### 24-hour rule
Want to buy something over $50? Wait a day. 50% of the time the urge will pass.

### 30-day rule
For big purchases (> $300) — wait a month.

### Shopping list
Into the store with a list only. Not on the list = don't buy.

### Remove card from browser
Type details manually every time. That friction saves thousands.

### Unsubscribe from marketing
Fewer "sales" emails = fewer temptations.

## Cost per use

A $250 jacket:
- 60 wears = **$4 per wear** ✅
- 3 wears = **$83 per wear** ❌

## 💡 Key takeaway

> The best purchase is the one you **didn't make**. Every $25 saved at 10% over 30 years = ~$435.
""",
        "content_kk": """
# Импульсивті шығындар тұзақтары

## Импульсивті сатып алу деген не?

Сен **жоспарламаған**, бір аптадан кейін **өкінетін** сатып алу.

Статистика бойынша — барлық шығындардың **40%-ы** осындай.

## Қалай қорғану керек?

### 24 сағат ережесі
10,000₸-ден қымбат нәрсе сатып алғың келе ме? Бір тәулік күт.

### 30 күн ережесі
Үлкен сатып алулар үшін (> 50,000₸) — бір ай күт.

### Сатып алу тізімі
Дүкенге тек тізіммен бар. Тізімде жоқ нәрсе — алынбайды.

## 💡 Басты сабақ

> Ең жақсы сатып алу — сен **жасамаған** сатып алу.
""",
        "category": "psychology",
        "difficulty": "beginner",
        "xp_reward": 50,
        "order": 9
    }
]

# Quizzes — custom-built for each video topic
QUIZZES_DATA = {
    "lesson_1": {  # Why The Rich Are Getting Richer
        "questions": [
            {
                "id": "q1_1",
                "question_ru": "В чём главное отличие богатых от бедных?",
                "question_en": "What's the main difference between the rich and the poor?",
                "question_kk": "Байлар мен кедейлердің басты айырмашылығы неде?",
                "options_ru": ["Размер зарплаты", "Богатые покупают активы, бедные — обязательства", "Уровень образования", "Город проживания"],
                "options_en": ["Salary size", "The rich buy assets, the poor buy liabilities", "Education level", "City of residence"],
                "options_kk": ["Айлық мөлшері", "Байлар активтерді, кедейлер міндеттемелерді сатып алады", "Білім деңгейі", "Тұратын қаласы"],
                "correct": 1
            },
            {
                "id": "q1_2",
                "question_ru": "Какой горизонт планирования у богатых людей?",
                "question_en": "What's the planning horizon of wealthy people?",
                "question_kk": "Бай адамдардың жоспарлау көкжиегі қандай?",
                "options_ru": ["До следующей зарплаты", "Месяц", "1-2 года", "10-20 лет и дольше"],
                "options_en": ["Until next paycheck", "A month", "1-2 years", "10-20 years and longer"],
                "options_kk": ["Келесі айлыққа дейін", "Бір ай", "1-2 жыл", "10-20 жыл және одан да ұзақ"],
                "correct": 3
            },
            {
                "id": "q1_3",
                "question_ru": "Богатство — это…",
                "question_en": "Wealth is…",
                "question_kk": "Байлық — бұл…",
                "options_ru": ["Высокая зарплата", "Разница между доходами и расходами, умноженная на время", "Дорогая машина", "Большая квартира"],
                "options_en": ["A high salary", "The gap between income and expenses multiplied by time", "An expensive car", "A big apartment"],
                "options_kk": ["Жоғары айлық", "Табыс пен шығынның арасындағы айырмашылықты уақытқа көбейту", "Қымбат машина", "Үлкен пәтер"],
                "correct": 1
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    },
    "lesson_2": {  # The 50/30/20 Rule
        "questions": [
            {
                "id": "q2_1",
                "question_ru": "Что означает 50 в правиле 50/30/20?",
                "question_en": "What does 50 mean in the 50/30/20 rule?",
                "question_kk": "50/30/20 ережесіндегі 50 нені білдіреді?",
                "options_ru": ["Развлечения", "Накопления", "Необходимые расходы (жильё, еда, транспорт)", "Налоги"],
                "options_en": ["Entertainment", "Savings", "Needs (housing, food, transport)", "Taxes"],
                "options_kk": ["Ойын-сауық", "Жинақ", "Қажеттіліктер (тұрғын үй, тамақ, көлік)", "Салықтар"],
                "correct": 2
            },
            {
                "id": "q2_2",
                "question_ru": "При доходе 300,000₸ сколько уйдёт на накопления по правилу 50/30/20?",
                "question_en": "On a $3,000 income, how much goes to savings under 50/30/20?",
                "question_kk": "300,000₸ табыста 50/30/20 бойынша жинаққа қанша кетеді?",
                "options_ru": ["30,000₸", "60,000₸", "90,000₸", "150,000₸"],
                "options_en": ["$300", "$600", "$900", "$1,500"],
                "options_kk": ["30,000₸", "60,000₸", "90,000₸", "150,000₸"],
                "correct": 1
            },
            {
                "id": "q2_3",
                "question_ru": "Когда лучше всего откладывать накопления?",
                "question_en": "When is the best time to save?",
                "question_kk": "Жинақты қашан салған дұрыс?",
                "options_ru": ["В конце месяца, что осталось", "Автоматом в день зарплаты", "Раз в год", "Когда захочется"],
                "options_en": ["End of month, what's left", "Automatically on payday", "Once a year", "Whenever I feel like it"],
                "options_kk": ["Ай соңында, қалғанын", "Айлық алған күні автоматты түрде", "Жылына бір рет", "Қалаған кезде"],
                "correct": 1
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    },
    "lesson_3": {  # Why Credits Make People Poorer
        "questions": [
            {
                "id": "q3_1",
                "question_ru": "Что главное забирает у тебя потребительский кредит?",
                "question_en": "What does a consumer loan mainly take from you?",
                "question_kk": "Тұтыну несиесі сенен ең бастысы нені алады?",
                "options_ru": ["Время", "Будущий доход в виде процентов", "Друзей", "Здоровье"],
                "options_en": ["Time", "Future income via interest", "Friends", "Health"],
                "options_kk": ["Уақыт", "Болашақ табысыңды пайыз түрінде", "Достарды", "Денсаулықты"],
                "correct": 1
            },
            {
                "id": "q3_2",
                "question_ru": "По какому правилу стоит решать брать ли кредит?",
                "question_en": "What rule helps decide whether to take credit?",
                "question_kk": "Несие алу-алмауды қандай ереже көмектеседі?",
                "options_ru": ["Если хочется — бери", "Если друзья берут — бери", "Бери только если можешь купить это дважды", "Никогда не бери"],
                "options_en": ["If you want it — take it", "If friends do — take it", "Only if you can afford to buy it twice", "Never take any"],
                "options_kk": ["Қаласаң — ал", "Достар алса — ал", "Тек екі рет сатып ала алсаң ғана ал", "Ешқашан алма"],
                "correct": 2
            },
            {
                "id": "q3_3",
                "question_ru": "Что такое 'долговая яма'?",
                "question_en": "What is a 'debt trap'?",
                "question_kk": "'Қарыз шұңқыры' дегеніміз не?",
                "options_ru": ["Маленький кредит", "Ситуация, когда ты берёшь новые кредиты, чтобы платить по старым", "Кредит до зарплаты", "Кредит на бизнес"],
                "options_en": ["A small loan", "Taking new loans to pay off old ones", "Payday loan", "Business loan"],
                "options_kk": ["Кішкентай несие", "Ескі несиелерді жабу үшін жаңасын алу", "Айлыққа дейінгі несие", "Бизнес-несие"],
                "correct": 1
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    },
    "lesson_4": {  # How Compound Interest Works
        "questions": [
            {
                "id": "q4_1",
                "question_ru": "В чём отличие сложного процента от простого?",
                "question_en": "How is compound interest different from simple?",
                "question_kk": "Күрделі пайыздың қарапайымнан айырмашылығы неде?",
                "options_ru": ["Он больше", "Проценты начисляются на проценты", "Он только для богатых", "Он отрицательный"],
                "options_en": ["It's bigger", "Interest is earned on interest", "Only for the rich", "It's negative"],
                "options_kk": ["Ол көбірек", "Пайызға пайыз есептеледі", "Тек байларға арналған", "Теріс"],
                "correct": 1
            },
            {
                "id": "q4_2",
                "question_ru": "По правилу 72 за сколько лет удвоится сумма под 10% годовых?",
                "question_en": "By the rule of 72, how long to double at 10%?",
                "question_kk": "72 ережесі бойынша 10%-да сома қанша жылда екі есе көбейеді?",
                "options_ru": ["3.6 года", "7.2 года", "10 лет", "20 лет"],
                "options_en": ["3.6 years", "7.2 years", "10 years", "20 years"],
                "options_kk": ["3.6 жыл", "7.2 жыл", "10 жыл", "20 жыл"],
                "correct": 1
            },
            {
                "id": "q4_3",
                "question_ru": "Что важнее для сложного процента?",
                "question_en": "What matters most for compound interest?",
                "question_kk": "Күрделі пайыз үшін не маңыздырақ?",
                "options_ru": ["Большая стартовая сумма", "Высокая ставка", "Время — начать как можно раньше", "Хороший банк"],
                "options_en": ["Big starting amount", "High rate", "Time — starting as early as possible", "A good bank"],
                "options_kk": ["Үлкен бастапқы сома", "Жоғары мөлшерлеме", "Уақыт — мүмкіндігінше ертерек бастау", "Жақсы банк"],
                "correct": 2
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    },
    "lesson_5": {  # People Buy Things to Appear Wealthy
        "questions": [
            {
                "id": "q5_1",
                "question_ru": "Как обычно выглядят по-настоящему богатые люди?",
                "question_en": "How do truly wealthy people usually look?",
                "question_kk": "Шынында бай адамдар әдетте қалай көрінеді?",
                "options_ru": ["Очень богато и заметно", "Скромно и сдержанно", "Всегда в люксе", "Всегда с дорогой техникой"],
                "options_en": ["Very flashy and visible", "Modest and quiet", "Always in luxury", "Always with expensive gadgets"],
                "options_kk": ["Өте сән-салтанатпен", "Қарапайым әрі ұстамды", "Әрқашан люкспен", "Әрқашан қымбат техникамен"],
                "correct": 1
            },
            {
                "id": "q5_2",
                "question_ru": "Что такое эффект Веблена?",
                "question_en": "What is the Veblen effect?",
                "question_kk": "Веблен эффектісі дегеніміз не?",
                "options_ru": ["Чем дешевле — тем лучше", "Чем дороже вещь, тем больше хочется её показать", "Скидки увеличивают продажи", "Реклама не работает"],
                "options_en": ["The cheaper the better", "The more expensive the item, the more we want to show it off", "Discounts boost sales", "Ads don't work"],
                "options_kk": ["Арзан болған сайын жақсы", "Зат қымбат болған сайын оны көрсеткің келеді", "Жеңілдіктер сатуды арттырады", "Жарнама жұмыс істемейді"],
                "correct": 1
            },
            {
                "id": "q5_3",
                "question_ru": "Какой правильный вопрос задать перед покупкой статусной вещи?",
                "question_en": "What's the right question before a status purchase?",
                "question_kk": "Мәртебелі затты сатып алмас бұрын дұрыс сұрақ қандай?",
                "options_ru": ["Какой цвет выбрать?", "Купил бы я это, если бы никто не видел?", "Где скидка побольше?", "Сколько лайков получу?"],
                "options_en": ["What color to pick?", "Would I buy this if no one would see?", "Where's the biggest sale?", "How many likes will I get?"],
                "options_kk": ["Қандай түсін таңдау керек?", "Ешкім көрмесе мен бұны сатып алар ма едім?", "Жеңілдік қайда көп?", "Қанша лайк аламын?"],
                "correct": 1
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    },
    "lesson_6": {  # The Biggest Mistake Of The Young Generation
        "questions": [
            {
                "id": "q6_1",
                "question_ru": "Какая главная ошибка молодого поколения?",
                "question_en": "What is the biggest mistake of the young generation?",
                "question_kk": "Жас ұрпақтың басты қателігі қандай?",
                "options_ru": ["Слишком много работать", "Откладывать накопления и инвестиции на 'потом'", "Слишком быстро инвестировать", "Учиться слишком много"],
                "options_en": ["Working too much", "Postponing saving and investing for 'later'", "Investing too fast", "Studying too much"],
                "options_kk": ["Тым көп жұмыс істеу", "Жинау мен инвестициялауды 'кейінге' қалдыру", "Тым жылдам инвестициялау", "Тым көп оқу"],
                "correct": 1
            },
            {
                "id": "q6_2",
                "question_ru": "Что самый ценный актив молодого человека?",
                "question_en": "What is the most valuable asset of a young person?",
                "question_kk": "Жас адамның ең құнды активі қандай?",
                "options_ru": ["Машина", "Время", "Айфон", "Подписчики в соцсетях"],
                "options_en": ["A car", "Time", "An iPhone", "Social media followers"],
                "options_kk": ["Машина", "Уақыт", "iPhone", "Әлеуметтік желілердегі жазылушылар"],
                "correct": 1
            },
            {
                "id": "q6_3",
                "question_ru": "Что НЕ стоит делать в возрасте 18-25?",
                "question_en": "What should you NOT do at age 18-25?",
                "question_kk": "18-25 жаста нені істемеу керек?",
                "options_ru": ["Учиться навыку", "Откладывать 20% автоматом", "Брать потребительские кредиты", "Изучать инвестиции"],
                "options_en": ["Learn a skill", "Auto-save 20%", "Take consumer loans", "Study investing"],
                "options_kk": ["Дағды үйрену", "20%-ды автоматты түрде жинау", "Тұтыну несиелерін алу", "Инвестициялауды зерттеу"],
                "correct": 2
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    },
    "lesson_7": {  # Smart Savings
        "questions": [
            {
                "id": "q7_1",
                "question_ru": "Что означает правило 'Заплати себе первым'?",
                "question_en": "What does 'Pay yourself first' mean?",
                "question_kk": "'Алдымен өзіңе төле' дегеніміз не?",
                "options_ru": ["Купить себе подарок в день зарплаты", "Сразу отложить часть зарплаты на накопления", "Сначала оплатить все счета", "Снять всю зарплату наличными"],
                "options_en": ["Buy yourself a gift on payday", "Move part of your salary to savings immediately", "Pay all bills first", "Withdraw the whole salary in cash"],
                "options_kk": ["Айлық күні өзіңе сыйлық сатып алу", "Айлықтың бір бөлігін бірден жинаққа аудару", "Алдымен барлық шоттарды төлеу", "Барлық айлықты қолма-қол алу"],
                "correct": 1
            },
            {
                "id": "q7_2",
                "question_ru": "Где лучше хранить подушку безопасности?",
                "question_en": "Where to keep your emergency fund?",
                "question_kk": "Қауіпсіздік қорын қайда сақтаған дұрыс?",
                "options_ru": ["На основной карте", "В акциях", "На отдельном накопительном счёте с лёгким доступом", "В наличных дома"],
                "options_en": ["On your main card", "In stocks", "On a separate savings account with easy access", "In cash at home"],
                "options_kk": ["Негізгі картада", "Акцияларда", "Қол жетімді бөлек жинақ шотында", "Үйде қолма-қол"],
                "correct": 2
            },
            {
                "id": "q7_3",
                "question_ru": "Что НЕ работает при накоплении?",
                "question_en": "What does NOT work for saving?",
                "question_kk": "Жинау кезінде нені істемеген жөн?",
                "options_ru": ["Автоматический перевод в день зарплаты", "Копить, что останется в конце месяца", "Иметь конкретную цель", "Использовать накопительный счёт"],
                "options_en": ["Auto-transfer on payday", "Saving what's left at month end", "Having a clear goal", "Using a savings account"],
                "options_kk": ["Айлық күні автоматты аудару", "Ай соңында қалғанын жинау", "Нақты мақсат қою", "Жинақ шотын пайдалану"],
                "correct": 1
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    },
    "lesson_8": {  # Assets vs Liabilities
        "questions": [
            {
                "id": "q8_1",
                "question_ru": "Что такое актив?",
                "question_en": "What is an asset?",
                "question_kk": "Актив дегеніміз не?",
                "options_ru": ["Любая дорогая вещь", "То, что приносит тебе деньги", "Машина", "Одежда"],
                "options_en": ["Any expensive thing", "Something that brings you money", "A car", "Clothes"],
                "options_kk": ["Кез келген қымбат зат", "Саған ақша әкелетін нәрсе", "Машина", "Киім"],
                "correct": 1
            },
            {
                "id": "q8_2",
                "question_ru": "Машина, на которой ты ездишь — это…",
                "question_en": "The car you drive is…",
                "question_kk": "Сен жүретін машина — бұл…",
                "options_ru": ["Актив", "Пассив, потому что требует расходов", "Инвестиция", "Накопление"],
                "options_en": ["An asset", "A liability, because it costs money", "An investment", "A saving"],
                "options_kk": ["Актив", "Міндеттеме, өйткені шығын талап етеді", "Инвестиция", "Жинақ"],
                "correct": 1
            },
            {
                "id": "q8_3",
                "question_ru": "Какая цель финансовой свободы по принципу 'активы и пассивы'?",
                "question_en": "What's the goal of financial freedom in this principle?",
                "question_kk": "Бұл принципте қаржылық еркіндіктің мақсаты қандай?",
                "options_ru": ["Купить дорогую машину", "Чтобы активы покрывали все твои расходы", "Иметь много пассивов", "Платить меньше налогов"],
                "options_en": ["Buy an expensive car", "Have assets cover all your expenses", "Own many liabilities", "Pay less taxes"],
                "options_kk": ["Қымбат машина сатып алу", "Активтер барлық шығындарды жабуы керек", "Көптеген міндеттемелер болуы", "Аз салық төлеу"],
                "correct": 1
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    },
    "lesson_9": {  # Impulse Spending Traps
        "questions": [
            {
                "id": "q9_1",
                "question_ru": "Какой процент трат — импульсивные?",
                "question_en": "What % of spending is impulsive?",
                "question_kk": "Шығындардың қанша пайызы импульсивті?",
                "options_ru": ["10%", "20%", "40%", "70%"],
                "options_en": ["10%", "20%", "40%", "70%"],
                "options_kk": ["10%", "20%", "40%", "70%"],
                "correct": 2
            },
            {
                "id": "q9_2",
                "question_ru": "Что такое правило 24 часов?",
                "question_en": "What is the 24-hour rule?",
                "question_kk": "24 сағат ережесі дегеніміз не?",
                "options_ru": ["Магазин работает 24 часа", "Подождать сутки перед крупной покупкой", "Можно вернуть товар за 24 часа", "Спать 24 часа после шопинга"],
                "options_en": ["Shop is open 24/7", "Wait 24 hours before a big purchase", "Return within 24 hours", "Sleep 24 hours after shopping"],
                "options_kk": ["Дүкен 24 сағат жұмыс істейді", "Үлкен сатып алу алдында бір тәулік күту", "24 сағат ішінде қайтару", "Шопингтен кейін 24 сағат ұйықтау"],
                "correct": 1
            },
            {
                "id": "q9_3",
                "question_ru": "Почему оплата в один клик опасна?",
                "question_en": "Why is one-click checkout dangerous?",
                "question_kk": "Бір рет басу арқылы төлеу неліктен қауіпті?",
                "options_ru": ["Это медленно", "Чем легче платить, тем больше тратишь — деньги становятся 'невидимыми'", "Только для богатых", "Не работает в Казахстане"],
                "options_en": ["It's slow", "The easier paying is — the more you spend; money becomes 'invisible'", "Only for the rich", "Doesn't work in Kazakhstan"],
                "options_kk": ["Бұл баяу", "Төлеу оңай болған сайын көп жұмсайсың — ақша 'көрінбейтін' болады", "Тек байларға арналған", "Қазақстанда жұмыс істемейді"],
                "correct": 1
            }
        ],
        "pass_threshold": 2,
        "xp_reward": 100
    }
}


# Helper functions
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
        return current_streak, 0
    elif last_activity == yesterday:
        current_streak += 1
        xp_earned = 10 + (current_streak * 2)
    else:
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
            "video_poster": lesson.get("video_poster"),
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
        "video_url": lesson.get("video_url"),
        "video_poster": lesson.get("video_poster"),
        "video_description": lesson.get("video_description_ru"),
        "video_description_en": lesson.get("video_description_en"),
        "video_description_kk": lesson.get("video_description_kk"),
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

    streak, streak_xp = await update_streak(db, user["id"], progress)
    xp_earned += streak_xp

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
async def submit_quiz(lesson_id: str, request: Request):
    """Submit quiz answers and get results"""
    db = get_database()
    user = await get_current_user(request, db)
    progress = await get_or_create_progress(db, user["id"])

    if lesson_id not in QUIZZES_DATA:
        raise HTTPException(status_code=404, detail="Quiz not found")

    body = await request.json()
    answers = body.get("answers", [])

    quiz = QUIZZES_DATA[lesson_id]
    questions = quiz["questions"]

    if len(answers) != len(questions):
        raise HTTPException(status_code=400, detail="Invalid number of answers")

    correct = 0
    for i, q in enumerate(questions):
        if answers[i] == q["correct"]:
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

    streak, streak_xp = await update_streak(db, user["id"], progress)
    xp_earned += streak_xp

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

    current_xp = progress.get("xp", 0)
    current_level = progress.get("level", 1)

    next_level_xp = None
    for level in LEVELS:
        if level["level"] > current_level:
            next_level_xp = level["min_xp"]
            break

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
