#!/bin/bash
cd /home/zar/ghost-agent

/home/zar/ghost-agent/venv/bin/python3 core/aggregator.py

if [ "$1" == "full" ]; then
    /home/zar/ghost-agent/venv/bin/python3 core/reflector.py
    # Jalankan pembaruan profil identitas setelah refleksi selesai
    /home/zar/ghost-agent/venv/bin/python3 core/identity_engine.py
fi
