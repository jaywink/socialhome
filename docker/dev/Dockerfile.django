FROM python:3.6

RUN mkdir /code
WORKDIR /code
COPY . .

# Ensure pip and setuptools are up to date as well
RUN pip install -U pip setuptools pip-tools

# Development environment
RUN pip-sync dev-requirements.txt

## # We need Node for Javascript. Install it and then grab the latest version
## RUN apt-get install -y npm
## RUN npm cache clean -f
## RUN npm install -g n
## RUN n stable

RUN cp .env.example .env

# This file needs to be outside the /code dir as it's mounted  durin development
RUN cp docker/dev/docker-entrypoint.sh.django ./docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["runserver"]
