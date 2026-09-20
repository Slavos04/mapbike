FROM nginx:alpine

# Kopiowanie przygotowanego interaktywnego frontendu do serwera Nginx
COPY public /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
