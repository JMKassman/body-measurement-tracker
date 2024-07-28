FROM python:3.10

LABEL org.opencontainers.image.source https://github.com/JMKassman/body-measurement-tracker

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
COPY ./templates /code/templates
COPY ./images /code/images

EXPOSE 8080

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*", "app.main:app"]