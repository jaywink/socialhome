# We use the official Python images. This may need to get locked in, or back to Ubuntu at some point
FROM python:3

RUN apt-get update
RUN apt-get install -y lib32z1-dev lib32z1 libpq-dev
RUN pip install --no-cache-dir -U pip setuptools

RUN mkdir /code
WORKDIR /code
COPY . .

RUN mv docker/django/docker-entrypoint.sh .

# Ensure pip and setuptools are up to date as well
# We need a slightly older setuptools due to a bug in pip-tools
RUN pip install -U pip setuptools==30.4 pip-tools

# Development environment
RUN pip-sync dev-requirements.txt

# We need Node for Javascript. Install it and then grab the latest version
RUN apt-get install -y npm
RUN npm cache clean -f
RUN npm install -g n
RUN n stable

RUN npm install
RUN npm install -g bower
RUN bower --allow-root install
RUN npm -g install grunt
RUN grunt dev

# We need to use --allow-root inside our docker container
#RUN node_modules/.bin/bower --allow-root install
#RUN node_modules/.bin/grunt build
RUN npm run dev

EXPOSE 8000

RUN mv env.docker env.local
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["dev"]
