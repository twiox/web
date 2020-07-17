## Web-App Twio X Member-Area ##
This project is meant to provide a scaled version of the current web-page at https://twio-x.com/mitglieder.
### 1. Set Up ###

#### Option 1: local setup ####
To run a version of the webapp on your local machine, run:\
`git clone https://github.com/MerlinSzymanski/twio_web`

change into the project directory. Using conda you can now create an environment with all the requirements by typing: 

`conda env create -f django.yml &&
conda activate django`
 
 open **twio_web/settings.py**
 at the very bottom include:
 
EMAIL_USE_TLS = True\
EMAIL_HOST ="smtp.gmail.com"\
EMAIL_HOST_USER="your_email@gmail.com"\
EMAIL_HOST_PASSWORD="your_pw"

go back to the base-directory. To create a sqlite3-database and to initiate the models within it, run\
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
**localhost:8000/members**\
you can log in with your superuser credentials

At first, make yourself a chairman
http://127.0.0.1:8000/chairman/#nav

Then Add a Group
http://127.0.0.1:8000/members/group/#nav

Then Add Members
http://127.0.0.1:8000/register/#nav

Add Trainers
http://127.0.0.1:8000/trainer/#nav

Then Add Sessions
http://127.0.0.1:8000/members/sessions/new/#nav

### 3. Change Things ###
To change/create pages make sure to think of the 3 things below:
1. The **url** to your page is mentioned in the /twio_web/urls.py file or forwarded from there to another urls.py file
2. There is a corresponding **view** in an imported views.py module the url points to
3. There is a **template** specified in the view which is send as a respond to the request to the browser

The css-file is in\
**/members/static/**

The html templates can be found in:\
**/members/templates/members/*.html** and\
**/user_handling/templates/user_handling/*.html**

the corresponding views are in:\
**/members/views.py**\
**user_handling/views.py**

the urls leading to the views can be found in:\
**/twio_web/urls.py** and\
**/members/urls.py**
