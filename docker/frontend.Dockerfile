FROM node:20-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend .

ENV NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

EXPOSE 3000

CMD ["npm", "run", "dev"]