## Web-App Twio X Member-Area ##
This project is meant to provide a scaled version of the current web-page at https://twio-x.com/mitglieder.
### 1. Set Up ###
To run a version of the webapp on your local machine, run:\
`git clone https://github.com/MerlinSzymanski/twio_web`

change into the project directory. Using conda you can now create an environment with all the requirements by typing: 

`conda env create -f django.yml &&\
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

### 2. Run the current version ###
To run the server:\
`python3 manage.py runserver`

Now open your browser and navigate to:\
**localhost:8000/members**\
you can log in with your superuser credentials

To add members, sessions and events, you need at first to create some Trainingsgroups and Spots (This will be available at a later point from the main page too) . So navigate to \
**localhost:8000/admin/**\
There you should add:
- Group "T" (necessary if you want to add a trainer)
- One more Trainingsgroup if needed
- A spot (necessary if you want to create sessions from the main-page)

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
