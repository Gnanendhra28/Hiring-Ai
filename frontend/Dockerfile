FROM node:20-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install

FROM base AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL=https://ai-interview-api-30597175496.asia-south1.run.app
ARG NEXT_PUBLIC_FIREBASE_PROJECT_ID=hiring-ai-4ae76
ARG NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=hiring-ai-4ae76.firebaseapp.com
ARG NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=hiring-ai-4ae76.firebasestorage.app
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_FIREBASE_PROJECT_ID=$NEXT_PUBLIC_FIREBASE_PROJECT_ID
ENV NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=$NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
ENV NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=$NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=8080
ENV HOSTNAME="0.0.0.0"
ENV NEXT_PUBLIC_API_URL=https://ai-interview-api-30597175496.asia-south1.run.app

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 8080

CMD ["node", "server.js"]

