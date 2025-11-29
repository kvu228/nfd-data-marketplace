#!/bin/bash

# compile smart contracts
npx hardhat compile

# remove any left over assets from watermarking
rm -rf src/lsb_watermarking/input/0/*
rm -rf src/lsb_watermarking/output/imgs/*
rm -rf images/*

# empty contents of contracts list
> contracts.json

# remove the current database and create new one from schema
rm -f src/db/demo.db
sqlite3 src/db/demo.db < src/db/schema.sql

# seed the database with test data
sqlite3 src/db/demo.db < src/db/seed.sql

# start a eth node
npx hardhat node &

# replace this process with main app
exec streamlit run src/app.py