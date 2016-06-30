# TIM

TIM Isn't Moodle (TIM) is an online engagement platform for students and teachers.


## Current features

* User registrations for Student and Teacher
* User login, and viewing posts
* Add post for Teachers
* Attach images and files with posts
* View and download attachments
* Filter posts by category and teacher who posted them  

 The prepopulated categories are the subjects in  Calicut University's Sixth Semester  
Computer Science and Engineering (2009) scheme syllabus.  
 Example users Teacher1 and Teacher2 with Teacher privilage and Student1 and Student2  
with Student privilage are also added.  

## Usage

1. Set configuration as required in ```config.py``` and change the sms user credentials in app.py

1. Then run ```createdb.py``` to initialise the database and to populate it with sample data  
	```
	python createdb.py  
	```
2. Then run ```app.py``` to launch the app  
	```
	python app.py  
	```  
 This starts the development web server listening at port 8008

3. Visit ```localhost:8008``` or ```127.0.0.1:8008``` in the browser to use the app.


4. See ```createdb.py``` for login details of sample accounts 


