## YaTube Social Network / Blog Platform educational project

Welcome to my Python 3.7 / Django 2.2.19 educational project. It's a social network with all required functionality, including subscriptions. It's got 30 custom tests to check everything's is working as planned.

This product features:

- SQL request optimization using Django ORM's _select_related_ directive
- Subscriptions to other user's posts
- 30 custom tests using Django TestCase: forms, models, urls and views and site functionality
- Custom server errors templates
- Pagination and caching

### Installation, testing and launching

```
git clone git@github.com:holohup/yatube_subscriptions_en.git && cd yatube_subscriptions_en && ./install_yatube.sh
```

#### Virtual environment activation

In order to proceed, we need to activate our virtual environment once again if it is not active:

```
source venv/bin/activate && cd yatube
```

#### Pre-launch tests

The tests are located in _yatube/posts/tests_ folder. They're implemented using Django TestCase library. To run the tests, make sure you're in your virtual environment and enter a command:

```
python manage.py test
```

#### And away we go!

```
python manage.py runserver
```

The website will be accessible by the address http://127.0.0.1:8000/ .
The django web server can be stopped by pressing **Ctrl+C**.

If you want to check out the admin panel, be sure to create a superuser before starting the server:
```
python manage.py createsuperuser
```

Then launch the server and enter your creditials at http://127.0.0.1:8000/admin/

#### Fixtures

For testing purposes and for your convenience a set of prepopulated data is available to be uploaded to the database. It also comes with an admin account **tester/tester**. To load the data, make sure you're in the project virtual environment in the _yatube_ folder and execute the following command:

```
python manage.py loaddata fixtures.json
```

### Final notes
- This version is supplied with Django Debug Toolbar installed to check the database queries effeciency. It is turned off by setting DEBUG = False in the _settings.py_ file.
- The project doesn't include an e-mail server. All the e-mails (needed for registration, password restoration/reset, etc) are saved as files in _yatube/sent_emails_ folder.

