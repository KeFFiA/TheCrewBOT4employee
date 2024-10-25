FROM python:3.12

WORKDIR /usr/src/app/bots

COPY requirements.txt requirements.txt

RUN pip install --upgrade setuptools
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod 755 .

COPY . .

#CMD ["/bin/bash", "-c", "python BOT.py"]