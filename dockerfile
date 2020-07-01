FROM python:3.7
RUN mkdir /yad2bot
COPY . /yad2bot
WORKDIR /yad2bot
RUN pip install pipenv
RUN pipenv install
CMD pipenv run python bot/bot.py