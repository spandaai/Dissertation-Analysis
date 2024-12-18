#!/bin/bash

# Create the config.js file
echo "window.env = {" > /usr/share/nginx/html/config.js


# Dynamically populate environment variables starting with REACT_APP_
for var in $(printenv | grep REACT_APP_ | cut -d= -f1); do
   value=$(printenv "$var") # Get the actual value of the variable
   echo "  \"$var\": \"$value\"," >> /usr/share/nginx/html/config.js
done


# Close the JavaScript object
echo "};" >> /usr/share/nginx/html/config.js


# Start NGINX
nginx -g "daemon off;"