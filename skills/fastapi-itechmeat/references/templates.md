# Templates

Jinja2 HTML templates in FastAPI.

## Install

```bash
pip install jinja2
```

## Basic Setup

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Home", "items": ["a", "b", "c"]}
    )
```

## Project Structure

```
project/
├── main.py
├── templates/
│   ├── base.html
│   └── index.html
└── static/
    └── styles.css
```

## Template File (templates/index.html)

```html
<!DOCTYPE html>
<html>
  <head>
    <title>{{ title }}</title>
    <link href="{{ url_for('static', path='styles.css') }}" rel="stylesheet" />
  </head>
  <body>
    <h1>{{ title }}</h1>
    <ul>
      {% for item in items %}
      <li>{{ item }}</li>
      {% endfor %}
    </ul>
  </body>
</html>
```

## url_for in Templates

```html
<!-- Static files -->
<link href="{{ url_for('static', path='css/style.css') }}" rel="stylesheet" />
<img src="{{ url_for('static', path='images/logo.png') }}" />

<!-- Route links -->
<a href="{{ url_for('read_item', item_id=1) }}">Item 1</a>
```

## Static Files Setup

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

## Template Inheritance

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
  <head>
    <title>{% block title %}{% endblock %} - My Site</title>
  </head>
  <body>
    <nav>...</nav>
    {% block content %}{% endblock %}
  </body>
</html>

<!-- templates/page.html -->
{% extends "base.html" %} {% block title %}Page Title{% endblock %} {% block content %}
<h1>Page Content</h1>
{% endblock %}
```

## Passing Data

```python
@app.get("/users/{user_id}", response_class=HTMLResponse)
def user_page(request: Request, user_id: int):
    user = get_user(user_id)
    return templates.TemplateResponse(
        request=request,
        name="user.html",
        context={
            "user": user,
            "is_admin": user.role == "admin"
        }
    )
```

## Request Object Required

Template requires `request` in context for `url_for()` to work:

```python
# Correct
return templates.TemplateResponse(
    request=request,  # Required
    name="page.html",
    context={"data": data}
)
```

## Custom Response Headers

```python
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={},
        headers={"X-Custom": "value"}
    )
```

## Jinja2 Features

```html
<!-- Conditionals -->
{% if user.is_admin %}
<span>Admin</span>
{% endif %}

<!-- Loops -->
{% for item in items %}
<li>{{ item.name }}</li>
{% endfor %}

<!-- Filters -->
{{ name|title }} {{ date|strftime('%Y-%m-%d') }}

<!-- Include -->
{% include "partials/header.html" %}
```
