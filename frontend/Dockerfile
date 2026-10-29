# Plain-English description: Dockerfile for containerizing the Next.js frontend application.

FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY frontend/package.json ./
RUN npm install

# Copy frontend application code
COPY frontend/ ./

# Build Next.js production bundle
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]

