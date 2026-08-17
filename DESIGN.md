# Internet Shop PRO — Дизайн-документ

> Повний дизайн проєкту. Дата створення: 2026-08-17. Урок 1.

---

## 1. Опис проєкту

Повноцінний інтернет-магазин з:
- Каталогом товарів, категоріями, фільтрами, пошуком
- Кошиком, замовленнями, оплатою
- Користувацьким кабінетом (профіль, замовлення, обране)
- Адмін-панеллю (управління товарами, користувачами, замовленнями, статистика)
- Фронтендом (React або Jinja2)

---

## 2. Ролі

| Роль | Опис |
|---|---|
| **Guest** | Неавторизований користувач. Бачить каталог, товари, ціни. Не може купувати. |
| **User** | Зареєстрований користувач. Каталог + кошик + замовлення + профіль + обране + відгуки. |
| **Manager** | User + управління замовленнями (статус, пошук), перегляд статистики. |
| **Admin** | Повний доступ: CRUD товарів/категорій, управління користувачами, статистика, промокоди. |

---

## 3. Функціонал

### 3.1. Каталог (для всіх)
- Перегляд категорій та підкатегорій (дерево)
- Перегляд товарів (список з пагінацією)
- Сторінка товару (фото, опис, ціна, наявність, варіанти)
- Пошук за назвою, описом, SKU
- Фільтри: категорія, ціна, наявність, бренд, атрибути
- Сортування: за ціною, датою, рейтингом

### 3.2. Реєстрація / Авторизація
- Реєстрація: email, username, password (хешований)
- Вхід: email + password → JWT (access + refresh token)
- Вихід
- Профіль: перегляд, редагування, зміна пароля

### 3.3. Кошик (User)
- Додавання товару (з урахуванням варіанту)
- Зміна кількості
- Видалення товару з кошика
- Очищення кошика
- Розрахунок: subtotal, знижки, доставка, total

### 3.4. Замовлення (User)
- Checkout: кошик → оформлення → замовлення
- Вибір адреси доставки
- Вибір методу доставки
- Історія замовлень користувача
- Деталі замовлення

### 3.5. Оплата (User)
- Вибір способу оплати
- Оплата через провайдера (Stripe / Fondy / LiqPay)
- Webhook від провайдера → оновлення статусу замовлення

### 3.6. Обране (User)
- Додати / видалити з обраного
- Список обраних товарів

### 3.7. Відгуки (User)
- Залишити відгук (оцінка 1-5 + текст)
- Перегляд відгуків на товарі
- Можна залишити тільки після покупки

### 3.8. Промокоди (Admin створює, User використовує)
- Типи: percentage, fixed discount
- Обмеження: термін дії, кількість використань, мінімальна сума
- Застосування при checkout

### 3.9. Доставка (User + Admin)
- Адреси доставки (зберігати в профілі)
- Методи доставки: Нова Пошта, Укрпошта, самовивіз
- Вартість доставки

### 3.10. Адмін-панель
- Dashboard: статистика (замовлення, виторг, користувачі, популярні товари)
- Управління товарами: create, update, delete, stock
- Управління категоріями: create, update, delete
- Управління користувачами: список, пошук, блокування, зміна ролі
- Управління замовленнями: список, фільтри, зміна статусу, деталі
- Управління промокодами

---

## 4. Архітектура

```
InternetShop_PRO/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings (pydantic-settings, .env)
│   │   ├── database.py          # AsyncSession, engine
│   │   │
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── category.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   ├── payment.py
│   │   │   ├── review.py
│   │   │   ├── favorite.py
│   │   │   └── promo.py
│   │   │
│   │   ├── schemas/             # Pydantic schemas (request/response)
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── category.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   ├── payment.py
│   │   │   ├── review.py
│   │   │   ├── favorite.py
│   │   │   └── promo.py
│   │   │
│   │   ├── routers/             # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── products.py
│   │   │   ├── categories.py
│   │   │   ├── cart.py
│   │   │   ├── orders.py
│   │   │   ├── payments.py
│   │   │   ├── reviews.py
│   │   │   ├── favorites.py
│   │   │   ├── promos.py
│   │   │   └── admin.py
│   │   │
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── product_service.py
│   │   │   ├── category_service.py
│   │   │   ├── cart_service.py
│   │   │   ├── order_service.py
│   │   │   ├── payment_service.py
│   │   │   └── ...
│   │   │
│   │   ├── repositories/        # DB queries (CRUD)
│   │   │   ├── __init__.py
│   │   │   ├── user_repo.py
│   │   │   ├── product_repo.py
│   │   │   └── ...
│   │   │
│   │   ├── utils/               # Хелпери
│   │   │   ├── security.py      # JWT, password hashing
│   │   │   ├── dependencies.py  # get_db, get_current_user
│   │   │   └── exceptions.py
│   │   │
│   │   └── migrations/          # Alembic
│   │
│   ├── tests/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                    # React або Jinja2 (URok 41+)
├── docker-compose.yml
├── Dockerfile
├── .gitignore
└── PROGRESS.md
```

---

## 5. Моделі бази даних

### User
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| email | str (unique) | Логін |
| username | str (unique) | Ім'я користувача |
| hashed_password | str | Хеш пароля |
| role | enum | user / manager / admin |
| is_active | bool | Активний/заблокований |
| created_at | datetime | Дата реєстрації |
| updated_at | datetime | Останнє оновлення |

### Category
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| name | str | Назва |
| slug | str (unique) | URL-slug |
| parent_id | UUID (FK → Category) | Батьківська категорія (NULL = верхній рівень) |
| image_url | str (nullable) | Зображення |

### Product
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| name | str | Назва |
| slug | str (unique) | URL-slug |
| description | text | Опис |
| price | decimal | Ціна |
| sku | str (unique) | Артикул |
| stock | int | Кількість на складі |
| category_id | UUID (FK → Category) | Категорія |
| brand | str | Бренд |
| is_active | bool | Активний/прихований |
| created_at | datetime | |
| updated_at | datetime | |

### ProductImage
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| product_id | UUID (FK → Product) | Товар |
| url | str | URL зображення |
| is_primary | bool | Основне фото |
| position | int | Порядок |

### ProductVariant
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| product_id | UUID (FK → Product) | Товар |
| name | str | Наприклад "Black 128GB" |
| sku | str (unique) | Артикул варіанту |
| price | decimal | Ціна (може відрізнятись від базової) |
| stock | int | Наявність |
| attributes | JSON | {"color": "black", "storage": "128GB"} |

### Cart
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| user_id | UUID (FK → User) | Власник кошика |
| created_at | datetime | |
| updated_at | datetime | |

### CartItem
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| cart_id | UUID (FK → Cart) | Кошик |
| product_id | UUID (FK → Product) | Товар |
| variant_id | UUID (FK → ProductVariant, nullable) | Варіант |
| quantity | int | Кількість |

### Order
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| user_id | UUID (FK → User) | Покупець |
| status | enum | pending / paid / processing / shipped / completed / cancelled |
| total | decimal | Загальна сума |
| delivery_method | str | Новою Поштою / Укрпоштою / самовивіз |
| delivery_address | str | Адреса |
| promo_code_id | UUID (FK → Promo, nullable) | Застосований промокод |
| notes | text | Коментар |
| created_at | datetime | |
| updated_at | datetime | |

### OrderItem
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| order_id | UUID (FK → Order) | Замовлення |
| product_id | UUID (FK → Product) | Товар |
| variant_id | UUID (FK → ProductVariant, nullable) | Варіант |
| quantity | int | Кількість |
| price | decimal | Ціна на момент покупки |

### Payment
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| order_id | UUID (FK → Order) | Замовлення |
| amount | decimal | Сума |
| method | str | Спосіб оплати |
| status | enum | pending / success / failed / refunded |
| provider_payment_id | str | ID платежу у провайдера |
| created_at | datetime | |

### Review
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| user_id | UUID (FK → User) | Автор |
| product_id | UUID (FK → Product) | Товар |
| rating | int (1-5) | Оцінка |
| text | text | Текст відгуку |
| is_moderated | bool | Пройшов модерацію |
| created_at | datetime | |

### Favorite
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| user_id | UUID (FK → User) | Користувач |
| product_id | UUID (FK → Product) | Товар |
| created_at | datetime | |
| | UNIQUE(user_id, product_id) | |

### PromoCode
| Поле | Тип | Опис |
|---|---|---|
| id | UUID | PK |
| code | str (unique) | Промокод (наприклад WELCOME10) |
| discount_type | enum | percentage / fixed |
| discount_value | decimal | Значення знижки |
| min_order_amount | decimal (nullable) | Мінімальна сума замовлення |
| max_uses | int (nullable) | Максимальна кількість використань |
| used_count | int | Скільки разів використано |
| expires_at | datetime (nullable) | Діє до |
| is_active | bool | Активний |
| created_at | datetime | |

---

## 6. API Endpoints

### Auth
| Метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| POST | /api/auth/register | Реєстрація | Guest |
| POST | /api/auth/login | Вхід (JWT) | Guest |
| POST | /api/auth/refresh | Оновлення access token | User |
| POST | /api/auth/logout | Вихід | User |

### Users
| Метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | /api/users/me | Мій профіль | User |
| PUT | /api/users/me | Оновити профіль | User |
| PUT | /api/users/me/password | Зміна пароля | User |
| DELETE | /api/users/me | Видалити акаунт | User |

### Products
| Метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | /api/products | Список товарів (пошук, фільтри, сортування, пагінація) | Guest |
| GET | /api/products/{slug} | Деталі товару | Guest |
| GET | /api/products/{slug}/reviews | Відгуки товару | Guest |

### Categories
| Метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | /api/categories | Дерево категорій | Guest |
| GET | /api/categories/{slug} | Товари категорії | Guest |

### Cart
| Метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | /api/cart | Мій кошик | User |
| POST | /api/cart/items | Додати товар | User |
| PUT | /api/cart/items/{id} | Змінити кількість | User |
| DELETE | /api/cart/items/{id} | Видалити з кошика | User |
| DELETE | /api/cart | Очистити кошик | User |

### Orders
| Метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| POST | /api/orders/checkout | Оформити замовлення з кошика | User |
| GET | /api/orders | Мої замовлення | User |
| GET | /api/orders/{id} | Деталі замовлення | User |

### Payments
| Метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| POST | /api/payments/{order_id} | Оплатити замовлення | User |
| POST | /api/payments/webhook | Webhook від провайдера | External |

### Favorites
| Метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | /api/favorites | Мої обрані | User |
| POST | /api/favorites/{product_id} | Додати в обране | User |
| DELETE | /api/favorites/{product_id} | Видалити з обраного | User |

### Reviews
| Метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| POST | /api/products/{slug}/reviews | Залишити відгук | User |
| DELETE | /api/reviews/{id} | Видалити відгук | User / Admin |

### Promo Codes
| Метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| POST | /api/promos/apply | Застосувати промокод | User |

### Admin
| Метод | Endpoint | Опис | Доступ |
|---|---|---|---|
| GET | /api/admin/stats | Статистика | Admin |
| GET | /api/admin/users | Всі користувачі | Admin |
| PUT | /api/admin/users/{id} | Змінити роль / заблокувати | Admin |
| GET | /api/admin/orders | Всі замовлення | Manager+ |
| PUT | /api/admin/orders/{id}/status | Змінити статус | Manager+ |
| POST | /api/admin/products | Створити товар | Admin |
| PUT | /api/admin/products/{id} | Оновити товар | Admin |
| DELETE | /api/admin/products/{id} | Видалити товар | Admin |
| POST | /api/admin/categories | Створити категорію | Admin |
| PUT | /api/admin/categories/{id} | Оновити категорію | Admin |
| DELETE | /api/admin/categories/{id} | Видалити категорію | Admin |
| POST | /api/admin/promos | Створити промокод | Admin |
| PUT | /api/admin/promos/{id} | Оновити промокод | Admin |

---

## 7. Стек технологій

| Компонент | Технологія |
|---|---|
| Мова | Python 3.12+ |
| Framework | FastAPI |
| ORM | SQLAlchemy (async) |
| Міграції | Alembic |
| БД | PostgreSQL 16 |
| Кеш | Redis |
| Валідація | Pydantic v2 + pydantic-settings |
| JWT | python-jose |
| Хеш паролів | passlib + bcrypt |
| Тести | pytest + pytest-asyncio + httpx |
| Docker | docker-compose (FastAPI + PostgreSQL + Redis) |
| Frontend | React (URok 41+) або Jinja2 |

---

## 8. Статуси замовлень

```
pending → paid → processing → shipped → completed
                  ↓
              cancelled
```

---

## 9. Статуси платежів

```
pending → success
       → failed
       → refunded
```

---

## 10. Конвенції

- **Структура:** routers → services → repositories → models
- **Schemas:** Request / Response моделі окремо від моделей БД
- **UUID:** всі PK — UUID4
- **Час:** UTC скрізь
- **Логи:** structured logging
- **Коміти:** змістовні, англійською
- **Назви файлів:** snake_case

---

> Документ створено в рамках Уроку 1. Наступний крок: Урок 2 — створення структури проєкту, .venv, .env, requirements.txt, базова конфігурація.
