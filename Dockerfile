FROM python:3.8

RUN mkdir /t_m_bot
COPY . /t_m_bot
WORKDIR /t_m_bot

RUN pip install --upgrade pip
COPY requirements.txt t_m_notifications_bot/requirements.txt
RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["main.py"]