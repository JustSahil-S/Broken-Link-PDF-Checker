# Broken Link Checker for PDFs

This project is a web-based application built with Django that scans PDFs for broken, stale or invalid hyperlinks. It's designed to help users quickly identify and address link issues within PDF documents. The app provides a user-friendly interface where you can upload your PDFs, analyze them, and view a detailed report of any broken links found. This program was initially created for a non-profit organization called Parents Helping Parents but can be used for any site where PDFs are published. 

## Description
### Web Interface 
The application has a web-interface that logs all the hyperlinks that have been found by the program.
Each link logged includes the following details:
* URL of the hyperlink
* Final URL redirect 
* Linked text displayed in the PDF
* HTTP response code
* Timestamp of the last check by the system

Links flagged by the system as broken will automatically be put in a the broken category. Users can manually double check these links and fix the PDFs. If the links are falsely flagged, they can be moved into the ignore or dismiss category which either stops that link from being checked again or only flags the link if its status changes. 

### Checking Frequency
By default, all PDFs will be checked by the program at 7:00 am every day and initially when run. This can be altered in the settings tab of the application, where users can change the start time and periodicity of the checks. 

### Email Client
Beyond the web interface, this program has the capability to email a spreadsheet of the updated list whenever the system finds a new broken link. The email client sender and recipients can be configured in the settings tab and smtp account credentials can be configured in the advanced settings. The spreadsheet can also be manually downloaded through the web interface. 

### User Management
During the installation, the program will prompt for the creation of a superuser/admin account. This user has the ability to add new users to the website through the interface. Non privileged users can perform all the tasks but cannot add or remove other users.

## Getting Started
To initialize the application, you must initialize the SQLite database. 
```
python manage.py makemigrations
```
```
python manage.py migrate
```
Running the web application:
```
python manage.py runserver
```
Creating initial superuser/admin account:
```
python manage.py createsuperuser
```

### Docker based installation (Recommended)
Dockerfile and docker_run.sh script simplify installation process.  Check these files for inline comments with example of commands to use for building docker image and running containerized application.

## Feature Roadmap

### PDF preview (https://github.com/JustSahil-S/Broken-Link-PDF-Checker/issues/26)
Open PDF preview when user clicks on a pdf link or pdf file path

### Link resolution management (https://github.com/JustSahil-S/Broken-Link-PDF-Checker/issues/33)
Assign broken links to user for fixing and track progress
