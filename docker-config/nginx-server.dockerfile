FROM nginx:alpine

COPY docker-config/nginx.conf /etc/nginx/conf.d/default.conf
