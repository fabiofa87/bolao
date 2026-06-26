FROM node:24-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.28-alpine
ENV PORT=80
ENV BACKEND_SCHEME=http
ENV BACKEND_URL=backend:8000
ENV FORWARDED_PROTO=http
ENV API_BASE_URL=
ENV ADMIN_URL=
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
