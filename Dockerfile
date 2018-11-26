FROM node:carbon


WORKDIR /code/
COPY package.json /code/
COPY bower.json /code/
COPY lib/* /code/lib/
COPY .git/ /code/.git/

RUN yarn global add bower
RUN yarn install --pure-lockfile && bower install --allow-root

WORKDIR /code/lib

RUN yarn install --pure-lockfile
RUN GIT_DIR=/tmp bower install --allow-root

WORKDIR /code/
CMD ["./node_modules/.bin/ember", "s"]
