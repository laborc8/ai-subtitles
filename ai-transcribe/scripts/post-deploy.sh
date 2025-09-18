#!/bin/bash
cd /var/www/vhosts/kopilot.at/whisper.kopilot.at/flaskapp
mkdir -p logs

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

pkill -f "flask run" || true

nohup venv/bin/python3 app.py > logs/flask.log 2>&1 &

# not working via script > manual run :: sudo sytemctl restart apache2
#echo "Restarting Apache..." >> logs/deploy.log
#sudo systemctl restart apache2 >> logs/deploy.log 2>&1

