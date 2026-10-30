FROM node:22-alpine

WORKDIR /app

LABEL org.opencontainers.image.licenses="CC-BY-NC-4.0"
COPY LICENSE NOTICE ./

RUN apk add --no-cache openssl

COPY package*.json ./
RUN npm ci --omit=dev

COPY prisma ./prisma
RUN npx prisma generate

COPY src ./src

EXPOSE 4000

CMD ["npm", "run", "start:migrate"]
