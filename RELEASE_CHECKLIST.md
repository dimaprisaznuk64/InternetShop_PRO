# 🚀 GitHub Release Checklist

> Стандартний чекліст перед кожним пушем/релізом.
> Автоматична версія: `.\release-check.ps1` (див. нижче, що вона покриває).

## 1. Git-гігієна

- [ ] `git status --short` — серед файлів немає `.env`, `.env.docker`, `.venv`, `node_modules`, `*.db`
- [ ] `.gitignore` актуальний; дозволені тільки шаблони: `!.env.example`, `!.env.docker.example`
- [ ] Скан секретів: `git grep -n -I -E "password=|secret|api_key|token|PRIVATE KEY"` — результати переглянуто вручну (слово `secret` у коді — це ок; значення — ні)

## 2. Гілка і версія

- [ ] `git branch --show-current` → `master` (усі workflows використовують master)
- [ ] Версія однакова скрізь: `backend/app/main.py`, `frontend/package.json`, README бейдж

## 3. QA (все зелене ДО коміту)

- [ ] Backend: `cd backend && .\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider`
- [ ] Frontend: `npm test -- --run`, `npx tsc -b`, `npm run lint`, `npm run build`
- [ ] Compose: `docker compose config` (+ prod-варіант з `--env-file .env.docker`)
- [ ] Релізний пуш: DEBUG=false стек, усі healthchecks healthy, `/health`, E2E smoke

## 4. Коміт

```bash
git add .
git status            # подивитись, що саме потрапило
git commit -m "<тип>: <суть>"   # feat / fix / docs / refactor / test / chore
git show --stat --oneline HEAD
git status            # working tree clean
```

## 5. Push + tag

```bash
git push origin master
git tag vX.X.X
git push origin vX.X.X
```

Якщо тег треба пересунути (до пуша тегу!):

```bash
git tag -d vX.X.X
git tag vX.X.X
# якщо старий тег уже на GitHub:
git push origin :refs/tags/vX.X.X && git push origin vX.X.X
```

## 6. Верифікація ПІСЛЯ пуша

```bash
git fetch origin --tags
git rev-parse HEAD origin/master vX.X.X   # усі три SHA однакові
git ls-remote --tags origin vX.X.X        # тег існує на GitHub
git status --short                         # порожньо
```

Плюс очима на GitHub: README, PROGRESS.md, структуру папок, workflows,
відсутність `.env*` / сміття.

---

## ⚙️ Автоматизація

```powershell
.\release-check.ps1              # повна перевірка: git + secrets + версії + тести + build + compose
.\release-check.ps1 -SkipTests   # швидкий прогін без тестів/build
```

Скрипт виводить `🟢 READY FOR GITHUB` або список того, що треба полагодити.
Рішення про реліз все одно за людиною: скрипт ловить механіку, але змісти
комітів і «чи той код я комічy» — перевіряєш сам.
