python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd yatube
python manage.py migrate
python manage.py runserver
