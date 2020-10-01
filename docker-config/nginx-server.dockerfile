FROM nginx:alpine

# copy docker config
COPY docker-config/nginx.conf /etc/nginx/conf.d/default.conf
