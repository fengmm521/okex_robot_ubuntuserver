#!/bin/sh


export PATH=/usr/bin/:/usr/local/bin:/bin:

if [[ -f rsa_1024_priv.pem ]]; then
    #statements
    rm rsa_1024_priv.pem
    rm rsa_1024_pub.pem
fi

openssl genrsa -out rsa_1024_priv.pem 1024

cat rsa_1024_priv.pem

openssl rsa -pubout -in rsa_1024_priv.pem -out rsa_1024_pub.pem

cat rsa_1024_pub.pem