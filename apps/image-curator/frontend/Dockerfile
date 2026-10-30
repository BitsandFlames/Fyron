FROM node:22-alpine

WORKDIR /app

LABEL org.opencontainers.image.licenses="CC-BY-NC-4.0"
COPY LICENSE NOTICE ./

COPY package*.json ./
RUN npm ci

COPY index.html vite.config.js tailwind.config.js postcss.config.js ./
COPY src ./src
COPY public ./public

EXPOSE 5174

CMD ["npm", "run", "dev"]
