<p align="center">
  <img src="project/static/images/logo.png" alt="ИАРА" width="120"/>
</p>

<h1 align="center">ИАРА</h1>

<p align="center">
  <b>Изпълнителна агенция по рибарство и аквакултури</b><br/>
  <i>Платформа за управление на кораби, разрешителни, инспекции и проследимост на улова</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white"/>&nbsp;&nbsp;<img src="https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white"/>&nbsp;&nbsp;<img src="https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white"/>&nbsp;&nbsp;<img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=000"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white"/>&nbsp;&nbsp;<img src="https://img.shields.io/badge/Kivy-EE4C2C?style=flat&logo=python&logoColor=white"/>&nbsp;&nbsp;<img src="https://img.shields.io/badge/MySQL-4479A1?style=flat&logo=mysql&logoColor=white"/>&nbsp;&nbsp;<img src="https://img.shields.io/badge/SQLAlchemy-1B5E20?style=flat&logo=python&logoColor=white"/>
</p>

<br/>

---

## Структура на проекта

```bash
project/
├── app.py              # Flask уеб приложение
├── templates/          # HTML шаблони
├── static/             # Статични файлове
│   ├── css/            # Стилове
│   ├── js/             # Скриптове
│   └── images/         # Изображения и лога
├── routes/             # API и уеб маршрути
├── models/             # SQLAlchemy база данни модели
├── database/           # Конфигурация на връзката с БД
├── requirements.txt    # Зависимости за бекенда
└── .env                # Локални променливи на средата

project-mobile/
├── app.py              # Kivy мобилно приложение
├── assets/             # Ресурси за мобилния интерфейс
└── requirements.txt    # Зависимости за мобилното приложение
```

---

## Ръководство за стартиране

### 1. Конфигурация

> Създайте файл с име `.env` в директорията `project/` и попълнете вашите данни за връзка с базата данни:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=test_db
DB_USER=test_user
DB_PASSWORD=test_password
SECRET_KEY=your-secret-key-here
```

### 2. Разгръщане на приложенията

#### 2.1. Уеб сървър (Flask)
Изпълнете следните команди в терминала, за да стартирате уеб сървър:

```bash
cd project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py runserver
```

#### 2.2. Мобилно приложение (Kivy)
Изпълнете следните команди, за да стартирате мобилно приложението:

```bash
cd project-mobile
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

---

<p align="center">
  <img src="project/static/images/logo.png" width="35"/>
  <br/>
  <b>ИАРА</b> &copy; 2026
</p>