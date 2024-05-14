FROM python:3.10-alpine

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN apk add --no-cache openssh

WORKDIR /app

COPY . .

CMD ["python", "botoslav.py"]
