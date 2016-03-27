from app import app
from models import db
db.init_app(app)

with app.app_context():
    db.drop_all()
    db.create_all()
    db.session.commit()

#add sample entries
from app import Teacher, Category, Student
with app.app_context():
    t1 = Teacher("Teacher1","teacher1@example.com","password","1234567890","teacher")
    t1.is_admin = True
    t1.verified = True
    db.session.add(t1)
    t2 = Teacher("Teacher2","teacher2@example.com","password","0987654321","teacher")
    db.session.add(t2)
    s1 = Student("Shafeeq K","shafeeq94@gmail.com","password","1234567890","student")
    db.session.add(s1)
    s2 = Student("Ashwin Jayakumar","ashwinjkm94@gmail.com","password","1234567890","student")
    db.session.add(s2)
    s3 = Student("Hanzal Salim","hanzalsalim94@gmail.com","password","1234567890","student")
    db.session.add(s3)
    s4 = Student("Bharadhwaj CN","bharadhwaj10@gmail.com","password","1234567890","student")
    db.session.add(s4)
    c = Category("General")
    db.session.add(c)
    c1 = Category("Embedded Systems")
    db.session.add(c1)
    c2 = Category("Compiler Design")
    db.session.add(c2)
    c3 = Category("Computer Networks")
    db.session.add(c3)
    c4 = Category("Database Management Systems")
    db.session.add(c4)
    c5 = Category("Computer Graphics")
    db.session.add(c5)
    c6 = Category("Information Security")
    db.session.add(c6)
    c7 = Category("Systems Lab")
    db.session.add(c7)
    c8 = Category("Mini Project")
    db.session.add(c8)
    db.session.commit()



