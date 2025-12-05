#!/bin/bash
cd backend
rm -rf .env
cat .env.example >> .env
virtualenv venv
source venv/Scripts/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
cd ../ui
rm -rf .env
cat .env.example >> .env
npm install
npm run dev