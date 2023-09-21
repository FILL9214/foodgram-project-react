
# Продуктовый помощник Foodgram - дипломный проект студента 58 когорты Истомина Ф.В.

После запуска проекта, он будет доступен по адресу http://127.0.0.1 (если развернут на локальной машине в докере)
Как запустить и посмотреть в действии описано ниже.

## Описание проекта Foodgram

«Продуктовый помощник»: приложение, на котором пользователи публикуют рецепты кулинарных изделий, подписываться на публикации других авторов и добавлять рецепты в свое избранное.
Сервис «Список покупок» позволит пользователю создавать список продуктов, которые нужно купить для приготовления выбранных блюд согласно рецепта/ов.

## Запуск проекта
### Заполнить в настройках репозитория секреты .env, необходимы для работы postgres в docker

```python
POSTGRES_DB=db_name # Задаем имя для БД.
POSTGRES_USER=username # Задаем пользователя для БД.
POSTGRES_PASSWORD=password # Задаем пароль для БД.
DB_HOST=db
DB_PORT=5432
```

### Далее в папке infra выполняем команду:

```bash
docker-compose up -d --build
```


### Для доступа к контейнеру backend и сборки финальной части выполняем следующие команды:

```bash
docker-compose exec backend python manage.py makemigrations
```

```bash
docker-compose exec backend python manage.py migrate --noinput
```

```bash
docker-compose exec backend python manage.py createsuperuser
```

```bash
docker-compose exec backend python manage.py collectstatic --no-input
```

### Дополнительно нужно наполнить DB ингредиентами и тэгами:

```bash
docker-compose exec backend python manage.py load_tags
```

```bash
docker-compose exec backend python manage.py load_ingrs
```

### Документация к API доступна после запуска

```url
http://127.0.0.1/api/docs/
```

Автор: Филипп Истомин
