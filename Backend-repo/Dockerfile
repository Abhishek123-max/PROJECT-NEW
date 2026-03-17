FROM node:18-alpine

WORKDIR /app

COPY Hotel-Management-ui/package*.json ./
RUN npm install

COPY Hotel-Management-ui/ .

EXPOSE 4000

CMD ["node", "index.js"]
