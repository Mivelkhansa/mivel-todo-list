FROM python:3.13.3

LABEL "maintainer"="mivelkhansa6@gmail.com"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#CMD ["python","app.py"]

# use this for prod
CMD ["gunicorn","app:app","--workers","9","--bind","0.0.0.0:5000"]
