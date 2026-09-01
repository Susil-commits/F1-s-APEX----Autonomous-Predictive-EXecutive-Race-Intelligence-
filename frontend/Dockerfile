# Stage 1: Build React Vite App
FROM node:20-slim AS builder
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install --prefer-offline --no-audit

COPY . ./
ENV NODE_OPTIONS="--max-old-space-size=2048"
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
