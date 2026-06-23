# Stage 1: Install dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Stage 2: Build
FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build
RUN npm prune --production

# Stage 3: Production
FROM node:20-alpine AS production
WORKDIR /app

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 sveltekit

COPY --from=build --chown=sveltekit:nodejs /app/build ./build
COPY --from=build --chown=sveltekit:nodejs /app/node_modules ./node_modules
COPY --from=build --chown=sveltekit:nodejs /app/package.json ./
COPY --from=build --chown=sveltekit:nodejs /app/otel.mjs ./otel.mjs

USER sveltekit

ENV NODE_ENV=production
ENV PORT=3000
ENV HOST=0.0.0.0

EXPOSE 3000

# otel.mjs를 앱보다 먼저 로드해 OpenTelemetry 자동계측을 활성화한다.
# OTEL_EXPORTER_OTLP_ENDPOINT 가 없으면 otel.mjs는 no-op이므로 비계측 환경에서도 안전.
CMD ["node", "--import", "./otel.mjs", "build"]
