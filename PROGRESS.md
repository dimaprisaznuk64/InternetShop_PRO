# Internet Shop PRO — Progress

> Точка збереження проєкту. Як продовжити: прочитай цей файл, потім `git log --oneline` та `git status`. Завжди оновлюй цей файл і комить після кожного завершеного блоку.

## Останнє оновлення

- Дата: 2026-08-24 (post-release hygiene)
- Стан: **v1.0.1 + security-hygiene фікси + автоматизований release-check.**
  0. НОВЕ: `release-check.ps1` + `RELEASE_CHECKLIST.md` — стандарт релізу за алгоритмом
      власника проєкту: forbidden files → secret scan → branch → версії → pytest/vitest/
      tsc/lint/build → docker compose config (dev+prod). Вердикт GREEN/RED.
      Запуск: `powershell -ExecutionPolicy Bypass -File release-check.ps1 [-SkipTests]`.
      Повний прогін на поточному стані: GREEN (1087 backend, frontend 4кроки, compose ок).
      PS5.1-ньюанс: скрипт мусить бути UTF-8 з BOM; нативні команди під Continue-EAP.
  1. `.env.docker` прибраний з git (залишений локально); замість нього в репо
      `.env.docker.example` — шаблон з плейсхолдерами. .gitignore: `!.env.docker`
      → `!.env.docker.example`. README Quick Start: `cp .env.docker.example .env.docker`.
  2. deploy.yml: `git pull origin main` → `master` (default branch); notify.yml
      "Branch: main" → "master". Тригери й так покривали master.
  НЮАНС для майбутніх прогонів: infra-тести читають PROJECT_ROOT/.env.docker,
  якого більше немає в git — перед повним suite-ом У DOCKER скопіюй локальний
  `.env.docker` у /repo (`docker cp`). На хості все працює як було.
- Рішення по відкладеному (v1.1.0): Redis-based token blacklist + rate limiter; simulated email.
- **Як продовжити:** проєкт опублікований: github.com/dimaprisaznuk64/InternetShop_PRO.
  Далі v1.1.0 (blacklist/rate limiter/email) за бажанням.
- Робоча папка: `C:\Users\DIMAS\Desktop\Programming\PythonPRO\InternetShop_PRO`

### Реліз v1.0.1 — фінальна перевірка (того ж дня)

1. Production compose (DEBUG=false): postgres/redis/backend/celery-worker/celery-beat/frontend
    (= nginx 1.27, статика + api-proxy) — ВСІ healthy. Пофікшено IPv4 healthcheck фронта
    (busybox wget резолвить localhost у ::1, а nginx слухає лише 0.0.0.0 → wget 127.0.0.1).
2. Повний suite У DOCKER/production-подібному середовищі:
    - backend **1087 passed** у прод-образі (git archive → /repo, щоб infra-тести бачили
      compose/nginx/env файли; env прогону: DEBUG=true ALLOWED_HOSTS='*' WEBHOOK_SECRET='');
    - frontend **82 passed** у node:22-alpine контейнері;
    - дубль на хості: backend 1087, frontend 82, tsc + oxlint чисто.
3. E2E smoke проти живого прод-стеку (backend/scripts/smoke_e2e.py): register → login → me →
    duplicate-register 409 → catalog → product detail → ILIKE search → admin login → promo
    create (з tz-aware expires_at) → promo apply → cart add (повний контракт) → checkout з
    промо → payment create → webhook БЕЗ підпису 400 fail-closed → webhook з HMAC 200 →
    order status=paid → webhook з поганим підписом 400 → review create → reviews list
    (модерація by design) → notifications [welcome, order_created, order_paid] → logout 204 →
    reuse refresh-токена після logout відхилено (400). РЕЗУЛЬТАТ: ALL STEPS PASSED.
Знайдено й пофікшено під час фіналу:
- promo.py модель: created_at БЕЗ явного sa.DateTime(timezone=True) → SQLAlchemy виводив
  naive тип → asyncpg DataError на живому PG (SQLite приховував!). Тепер усі datetime-колонки
  всіх моделей мають явний timezone=True (авто-перевірка grep).
- frontend/Dockerfile healthcheck → http://127.0.0.1/ (IPv4).
- README: blacklist чесно названий in-process (Redis-backed → v1.1.0).
Інструменти: scripts/smoke_e2e.py — відтворюваний smoke (env: WEBHOOK_SECRET, ADMIN_EMAIL,
ADMIN_PASSWORD); rate limiter на register — реальний захист, між прогонами чекати ~1 хв.

## Roadmap (76 уроків)

### 🟢 Блок 1. Архітектура та старт

- [x] Урок 1 — Проєктування Internet Shop: вимоги, функціонал, ролі, архітектура, API, БД, frontend/backend, структура проєкту
- [x] Урок 2 — Створення проєкту: Git, .venv, структура, .env, .gitignore, requirements.txt, базова конфігурація
- [x] Урок 3 — FastAPI foundation: routers, dependencies, configuration, Swagger/OpenAPI, health endpoint
- [x] Урок 4 — PostgreSQL + SQLAlchemy: async engine, AsyncSession, models, база даних
- [x] Урок 5 — Alembic: migrations, revision, upgrade/downgrade, автоматичне визначення змін моделей

### 🟡 Блок 2. Користувачі та авторизація

- [x] Урок 6 — User model: користувач, email, username, password, timestamps
- [x] Урок 7 — Registration: Pydantic schemas, валідація, хешування пароля
- [x] Урок 8 — Login: authentication, JWT, access token, refresh token
- [x] Урок 9 — Roles & permissions: user / manager / admin, RBAC, permissions, захист endpoint'ів
- [x] Урок 10 — Profile: отримання профілю, редагування, зміна пароля, видалення акаунта

### 🟠 Блок 3. Каталог

- [x] Урок 11 — Categories: категорії, підкатегорії, зв'язки
- [x] Урок 12 — Products: товар, ціна, SKU, stock, description, статус
- [x] Урок 13 — Product images: завантаження, зберігання, URL, основне фото, додаткові фото
- [x] Урок 14 — Product variants: варіанти товару (напр. iPhone Black 128GB / White 256GB)
- [x] Урок 15 — Search: пошук, ILIKE, full-text search, пошук за SKU
- [x] Урок 16 — Filters: category, price, stock, brand, attributes
- [x] Урок 17 — Sorting & pagination: pagination, sorting, limit/offset, cursor pagination

### 🔵 Блок 4. Кошик

- [x] Урок 18 — Cart model: cart, cart_items
- [x] Урок 19 — Add to cart: додавання, кількість, перевірка stock
- [x] Урок 20 — Update / remove: зміна кількості, видалення, очищення
- [x] Урок 21 — Cart calculations: subtotal, discount, delivery, total
- [x] Урок 22 — Race conditions: конкуренція на залишках (Stock=1, два покупці) — транзакції/locking

### 🟣 Блок 5. Orders

- [x] Урок 23 — Order architecture: orders, order_items
- [x] Урок 24 — Checkout: Cart → Checkout → Order
- [x] Урок 25 — Order statuses: pending, paid, processing, shipped, completed, cancelled
- [x] Урок 26 — Order history: користувач бачить свої замовлення
- [x] Урок 27 — Admin orders: перегляд, зміна статусу, пошук, робота з клієнтом

### 🔴 Блок 6. Оплата

- [x] Урок 28 — Payment architecture: payment flow, payment status, idempotency
- [x] Урок 29 — Payment provider: підключення реального payment API
- [x] Урок 30 — Webhooks: Payment Provider → Webhook → FastAPI → Order = PAID
- [x] Урок 31 — Безпека платежів: signature verification, webhook secret, повторний webhook, idempotency, fraud protection basics

### 🟤 Блок 7. Обране, відгуки та промокоди

- [x] Урок 32 — Favorites: додати, видалити, список
- [x] Урок 33 — Reviews: оцінка, текст, перевірка покупки, moderation
- [x] Урок 34 — Promo codes: WELCOME10/SALE20, percentage, fixed discount, expiration, usage limits
- [x] Урок 35 — Delivery: адреси, доставка, delivery methods, shipping cost

### ⚫ Блок 8. Admin Panel

- [x] Урок 36 — Admin architecture: окрема система для admin / manager
- [x] Урок 37 — Product management: create, update, delete, stock, images
- [x] Урок 38 — User management: список, пошук, блокування, ролі
- [x] Урок 39 — Order management: список, фільтри, статуси, деталі
- [x] Урок 40 — Statistics: sales, revenue, orders, users, popular products

### 🌐 Блок 9. Frontend

- [x] Урок 41 — Frontend architecture: структура, routing, API client, environment
- [x] Урок 42 — Catalog UI: categories, products, search, filters
- [x] Урок 43 — Product page: photos, variants, price, stock, add to cart
- [x] Урок 44 — Authentication UI: registration, login, logout, tokens
- [x] Урок 45 — Cart UI: cart, quantity, total, checkout
- [x] Урок 46 — Orders UI: order creation, order history, order details
- [x] Урок 47 — Profile UI: user information, addresses, password
- [x] Урок 48 — Admin frontend: dashboard, products, users, orders, statistics

### ⚡ Блок 10. Redis та background tasks

- [x] Урок 49 — Redis: cache, connection, TTL
- [x] Урок 50 — Caching: кешуємо categories, popular products, catalog queries
- [x] Урок 51 — Background tasks: email, notifications, cleanup, asynchronous jobs
- [x] Урок 52 — Celery / task queue (якщо потрібно для production-рівня)

### 🧪 Блок 11. Testing

- [x] Урок 53 — Pytest: структура тестів, fixtures, test database
- [x] Урок 54 — API tests: registration, login, products, cart, orders
- [x] Урок 55 — Business logic tests: discounts, stock, checkout, payments
- [x] Урок 56 — Integration tests: API → Service → Repository → PostgreSQL

### 🔐 Блок 12. Security

- [x] Урок 57 — Security audit: перевіряємо весь проєкт
- [x] Урок 58 — OWASP basics: SQL injection, XSS, CSRF, IDOR, broken access control
- [x] Урок 59 — Rate limiting: login, registration, API, sensitive endpoints
- [x] Урок 60 — Secure configuration: secrets, environment, CORS, headers, production settings

### 🐳 Блок 13. Docker

- [x] Урок 61 — Docker basics: image, container, Dockerfile
- [x] Урок 62 — Docker Compose: FastAPI + PostgreSQL + Redis + Frontend
- [x] Урок 63 — Volumes & networks: database persistence, networking, service communication
- [x] Урок 64 — Production Docker: multi-stage builds, non-root user, оптимізація image

### 🚀 Блок 14. Deploy

- [x] Урок 65 — Server: VPS, Linux, SSH, firewall
- [x] Урок 66 — Deploy backend: FastAPI у production
- [x] Урок 67 — Deploy frontend: frontend → production
- [x] Урок 68 — Domain + HTTPS: domain, DNS, SSL, reverse proxy
- [x] Урок 69 — Nginx: Internet → Nginx → Frontend / API
- [x] Урок 70 — Production PostgreSQL / Redis: нормальна конфігурація prod-середовища

### 🏁 Блок 15. Фінал

- [x] Урок 71 — Production audit: security, database, API, frontend, Docker, logs
- [x] Урок 72 — Performance: SQL queries, indexes, N+1, caching, response time
- [x] Урок 73 — Logging & monitoring: structured logs, errors, health checks, monitoring
- [x] Урок 74 — CI/CD: GitHub Actions (git push → Tests → Lint → Build → Deploy)
- [x] Урок 75 — Final GitHub: README, architecture diagram, installation, API docs, .env.example, скріншоти, повний ручний QA-прогін
- [x] Урок 76 — Фінальний реліз InternetShop_PRO v1.0: повністю готовий production-проєкт

## Поточний блок (наступний крок)

- ✅ **Уроки 1–76 завершені. v1.0.0.**
- ➡️ **Залишилось тільки:** створити репо на GitHub і запушити (власнор, команди в PROGRESS).

## Конвенції проєкту

- Python 3.12+, FastAPI, SQLAlchemy async, PostgreSQL, Redis, Docker
- Шаблони: routers / services / repositories / schemas
- Урок → перевірка → наступний урок (без стрибків)
- Усі коміти змістовні, історія чиста
