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
poetry install --directory <path_to_your_project>
poetry shell
```

### System as is scripts
```shell
python ./gateway_service/scripts/system_as_is.py
```
Remember to install tesseract before running the script.

### Setup database

Create a database

```shell
mysql -u root -p
mysql> CREATE DATABASE modern_sa;
mysql> exit
```

In `.env` file (create one if it doesn't exist), add database uri

```
SQLALCHEMY_DATABASE_URI=mysql+aiomysql://root:123456@127.0.0.1/modern_sa
```

Then upgrade database

```shell
cd gateway_service
alembic upgrade head
```

### Install `pre-commit` hooks

- Install `pre-commit`: https://pre-commit.com/ (should be installed globally)

## Running

Running with docker-compose

```shell
docker-compose up --build -d
```

### Environment variables
- Create a `.env` file in each service directory (if it doesn't exist) and add the following variables:
```env
SQLALCHEMY_DATABASE_URI
RABBITMQ_CONNECTION
RABBITMQ_QUEUE_GATEWAY_TO_OCR
RABBITMQ_QUEUE_OCR_TO_TRANSLATE
RABBITMQ_QUEUE_TRANSLATE_TO_PDF
REDIS_HOST
REDIS_PORT
REDIS_DB
MYSQL_ROOT_PASSWORD
GCS_BUCKET_NAME
PUSHER_APP_ID
PUSHER_KEY
PUSHER_SECRET
PUSHER_CLUSTER
SENTRY_DSN
```
Also, get the Google Cloud Storage json credential file, name as `credentials.json` and add to the `pdf_service` folder and `gateway_service/gcs-config` folder.
