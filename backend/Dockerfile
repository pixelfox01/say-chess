FROM python:latest

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD [ "waitress-serve", "--host", "0.0.0.0", "--call", "say_chess:create_app" ]
