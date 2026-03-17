FROM nginx:alpine

COPY Hotel-Management-ui/out /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
