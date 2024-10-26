FROM node:16

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
EXPOSE 8080

CMD ["node", "service_discovery.js"]  # Ensure this points to the correct entry file
