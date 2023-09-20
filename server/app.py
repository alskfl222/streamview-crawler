#!/usr/bin/env python
# coding: utf-8

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/image", StaticFiles(directory="../image"), name="image")

@app.get('/check')
def crawler_health_check():
    return "qwerty"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

