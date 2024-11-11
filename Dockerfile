FROM python:3-alpine3.20

WORKDIR /blind-reader

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["streamlit","run","app.py"]