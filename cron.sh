crontab -l | { cat; echo "0 * * * * python3 ./santiment_test/main.py"; } | crontab -