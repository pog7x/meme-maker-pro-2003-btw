FROM python:3.10.6

VOLUME /meme_maker_pro_2003_btw

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 3228

RUN mkdir static/shared

CMD [ "python", "manage.py", "runserver", "0.0.0.0:3228" ]