#!/bin/bash

# Start the Flask web server
python3 mvs.py &

# Start the Telegram bot
python3 -m mvs &

# Keep the script running
wait -n
