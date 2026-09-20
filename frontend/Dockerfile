FROM nginx:alpine

# Kopiowanie przygotowanego interaktywnego frontendu i konfiguracji Nginx
COPY public /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
