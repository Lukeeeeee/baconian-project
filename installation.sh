#!/usr/bin/env bash
pip install pip==9.0.1
pip install -e .
npm install -g pyright
pyright --stat