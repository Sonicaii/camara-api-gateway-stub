FROM node:22

RUN npm install -g @stoplight/prism-cli@4

ENTRYPOINT [ "prism" ]