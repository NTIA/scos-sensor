FROM nginx:1.17-alpine

RUN mkdir -p /var/www/scos-sensor/static
COPY --chown=nginx:nginx ./src/static/ /var/www/scos-sensor/static/
COPY --chown=root:root ./nginx/conf.template /etc/nginx/nginx.conf.template
