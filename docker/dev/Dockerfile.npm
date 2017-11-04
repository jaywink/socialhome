FROM node

RUN mkdir /code

WORKDIR /code
COPY . .

RUN npm install
RUN node_modules/.bin/bower --allow-root install
RUN node_modules/.bin/grunt dev

RUN cp docker/dev/docker-entrypoint.sh.npm ./docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["watch"]
