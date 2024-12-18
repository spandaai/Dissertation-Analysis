# Build stage
FROM node:20.11.0 as build


# Set working directory
WORKDIR /app


# Copy package files
COPY package*.json ./


# Install dependencies
RUN npm install


# Copy project files
COPY . .
RUN apt-get update && apt-get install -y bash




# Build the app
RUN npm run build


# Production stage
FROM nginx:alpine


# Install bash for config.sh
RUN apk add --no-cache bash


# Set working directory
WORKDIR /usr/share/nginx/html


# Copy built assets from build stage
COPY --from=build /app/dist .


# Copy config.sh and ensure it is executable
COPY config.js /usr/share/nginx/html/config.js


# Add custom nginx config
RUN printf 'server {\n\
   listen 4000;\n\
   location / {\n\
       root /usr/share/nginx/html;\n\
       index index.html index.htm;\n\
       try_files $uri $uri/ /index.html;\n\
   }\n\
}' > /etc/nginx/conf.d/default.conf


# Expose port 4000
EXPOSE 4000


# Run config.sh at startup
CMD ["nginx", "-g", "daemon off;"]
