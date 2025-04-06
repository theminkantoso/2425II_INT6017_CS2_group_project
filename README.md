# FastAPI Service Template

## Requirements

- Python 3.10+
- MySQL 5.7+
- [Poetry](https://python-poetry.org/)

## Installation

### Set up virtual environment
```shell
python -m venv venv
source ./venv/bin/activate
(If you are using Windows, use `venv\Scripts\activate`)
```


### Install dependencies

```shell
poetry config virtualenvs.in-project true
poetry install
poetry shell
```

### System as is scripts
```shell
python scripts/system_as_is.py
```
Remember to install tesseract before running the script.

### Setup database

Create a database

```shell
mysql -u root -p
mysql> CREATE DATABASE fastapi_template_development;
mysql> exit
```

In `.env` file (create one if it doesn't exist), add database uri

```
SQLALCHEMY_DATABASE_URI=mysql+aiomysql://root:123456@127.0.0.1/fastapi_template_development
```

Then upgrade database

```shell
alembic upgrade head
```

### Install `pre-commit` hooks

- Install `pre-commit`: https://pre-commit.com/ (should be installed globally)
- Install `pre-commit` hooks:

  ```shell
  make install-git-hooks
  ```

## Running

Inside the virtual environment, run

```shell
make run
```

### Run tests

Inside the virtual environment, run

```shell
make test
```
