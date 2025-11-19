FROM node:20-alpine

WORKDIR /app/apps/frontend

COPY apps/frontend/package.json ./
COPY apps/frontend/package-lock.json ./
RUN npm install || true

COPY apps/frontend .

CMD ["npm", "run", "dev"]
