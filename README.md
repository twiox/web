## Web-App Twio X Member-Area ##
This project is meant to provide a scaled version of the current web-page at https://twio-x.de/mitglieder.
### 1. Set Up ###

#### Option 1: local setup ####

Requirements:
- Conda

To run a version of the webapp on your local machine, run:\
`git clone https://github.com/twiox/web`

change into the project directory. Using conda you can now create an environment with all the requirements by typing: 

`conda env create -f django.yml &&
conda activate django`

create a file **twio_web/secrets.py** (use the secrets_example.py as template)
update the following lines

EMAIL_USE_TLS = True\
EMAIL_HOST ="smtp.gmail.com"\
EMAIL_HOST_USER="your_email@gmail.com"\
EMAIL_HOST_PASSWORD="your_pw"

We currently use a mysql database. To use a sqlite database in the local setup (for testing purposes),
replace in the **twio_web/settings.py** the 

DATABASES = {...} parameter with:

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

go back to the base-directory. To initiate the models run\
`python3 manage.py makemigrations`\
`python3 manage.py migrate`

to access the site and the admin-panel, you should create a super-user:\
`python3 manage.py createsuperuser`

To run the server:\
`python3 manage.py runserver`

#### Option 2: Docker ####

Requirements: docker and docker-compose are installed.

Run `docker-compose up` to build and start the python server.

### 2. Use the current version ###

Now open your browser and navigate to:\
**localhost:8000**\
you can log in with your superuser credentials

At first, make yourself a chairman
http://127.0.0.1:8000/vorstand/liste/neu

Then explore what you can do :)

