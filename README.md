# Социальная сеть Yatube
Реализованный функционал:
- авторизация
- персональные ленты
- комментарии
- подписка на авторов
- пагинация
- кэширование
- тесты

## Используемые технологии
- Python 3.7
- Django 2.2
- SQLite

## Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/enjoywg/yatube_final
```
```
cd yatube_final
```

Cоздать и активировать виртуальное окружение:
```
python3 -m venv venv
```
```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```

Выполнить миграции:
```
python3 manage.py migrate
```

Запустить проект:
```
python3 manage.py runserver
```
