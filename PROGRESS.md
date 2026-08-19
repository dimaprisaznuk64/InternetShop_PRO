# Internet Shop PRO — Progress

> Точка збереження проєкту. Як продовжити: прочитай цей файл, потім `git log --oneline` та `git status`. Завжди оновлюй цей файл і комить після кожного завершеного блоку.

## Останнє оновлення

- Дата: 2026-08-19
- Стан: **Урок 58 завершений**. OWASP basics:
  58: OWASP tests — CSRF (Bearer ≠ cookie → неможливий), IDOR (orders, reviews, payments, cart, notifications, profile — жоден юзер не бачить/не змінює чужі ресурси), broken access control (admin endpoints захищені, user не може створювати promo/ Categories/видаляти products), sensitive data exposure (login generic error, no password hash в JSON, no internal leak при duplicate register), input validation (negative/zero/huge quantity, invalid email/password/rating), mass assignment (role не можна задати при реєстрації чи оновленні профілю). 32 new tests.
  **316 backend тестів** + **82 frontend тестів**. Build ~338 KB gzip ~103 KB.
- **Як продовжити (наступного разу):** прочитай цей файл → `git log --oneline` →
  **Урок 59 — Rate limiting**: login, registration, API, sensitive endpoints.
- Робоча папка: `C:\Users\DIMAS\Desktop\Programming\PythonPRO\InternetShop_PRO`
- PostgreSQL: user=postgres, password=dmytro53239, host=localhost:5432, db=internetshop

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
- [ ] Урок 59 — Rate limiting: login, registration, API, sensitive endpoints
- [ ] Урок 60 — Secure configuration: secrets, environment, CORS, headers, production settings

### 🐳 Блок 13. Docker

- [ ] Урок 61 — Docker basics: image, container, Dockerfile
- [ ] Урок 62 — Docker Compose: FastAPI + PostgreSQL + Redis + Frontend
- [ ] Урок 63 — Volumes & networks: database persistence, networking, service communication
- [ ] Урок 64 — Production Docker: multi-stage builds, non-root user, оптимізація image

### 🚀 Блок 14. Deploy

- [ ] Урок 65 — Server: VPS, Linux, SSH, firewall
- [ ] Урок 66 — Deploy backend: FastAPI у production
- [ ] Урок 67 — Deploy frontend: frontend → production
- [ ] Урок 68 — Domain + HTTPS: domain, DNS, SSL, reverse proxy
- [ ] Урок 69 — Nginx: Internet → Nginx → Frontend / API
- [ ] Урок 70 — Production PostgreSQL / Redis: нормальна конфігурація prod-середовища

### 🏁 Блок 15. Фінал

- [ ] Урок 71 — Production audit: security, database, API, frontend, Docker, logs
- [ ] Урок 72 — Performance: SQL queries, indexes, N+1, caching, response time
- [ ] Урок 73 — Logging & monitoring: structured logs, errors, health checks, monitoring
- [ ] Урок 74 — CI/CD: GitHub Actions (git push → Tests → Lint → Build → Deploy)
- [ ] Урок 75 — Final GitHub: README, screenshots, architecture diagram, installation, API documentation, .env.example
- [ ] Урок 76 — Фінальний реліз InternetShop_PRO v1.0: повністю готовий production-проєкт

## Поточний блок (наступний крок)

- ✅ **Урок 58 — OWASP basics**: CSRF, IDOR, broken access control, sensitive data, input validation, mass assignment.

## Конвенції проєкту

- Python 3.12+, FastAPI, SQLAlchemy async, PostgreSQL, Redis, Docker
- Шаблони: routers / services / repositories / schemas
- Урок → перевірка → наступний урок (без стрибків)
- Усі коміти змістовні, історія чиста
