FROM node:22-alpine AS dependencies
WORKDIR /workspace
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci

FROM dependencies AS development
COPY apps/web apps/web
EXPOSE 5173
CMD ["npm", "run", "dev", "--workspace", "@weather/web", "--", "--host", "0.0.0.0"]

FROM dependencies AS build
COPY apps/web apps/web
RUN npm run build --workspace @weather/web

FROM nginx:1.27-alpine AS production
COPY --from=build /workspace/apps/web/dist /usr/share/nginx/html
EXPOSE 80

