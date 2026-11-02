FROM node:24-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --no-audit --no-fund
COPY . .
# Web v podadresáři za reverse proxy (např. /rodokmen/martin); prázdné = web v kořeni domény.
ARG BASE_PATH=
RUN npm run build && if [ -n "$BASE_PATH" ]; then node scripts/podcesta.mjs "$BASE_PATH"; fi

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
