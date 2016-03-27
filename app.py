from flask import Flask, request, render_template, url_for, redirect, flash, session, g, send_file, abort
from flask.ext.login import LoginManager
from flask.ext.login import login_user , logout_user , current_user , login_required
from werkzeug import generate_password_hash, check_password_hash
from flask.ext.seasurf import SeaSurf #for csrf protection
from flask_mail import Mail, Message
from flask import copy_current_request_context #for async mail
from threading import Thread
import os
import pytz
import datetime
import shutil
import requests as req
app = Flask(__name__)

app.config.from_object('config')

from models import User, Student, Teacher, Category, Post, Document, Comment, Discussion, Assignment
from models import db

db.init_app(app)
csrf = SeaSurf(app)
mail=Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_request
def before_request():
    g.user = current_user

# The categories and teachers in each view is created for populating the
# navbar dropdowns
@app.route('/')
def index():
	teachers = Teacher.query.all()
	return render_template("index.html",page="home", teachers = teachers)

@app.route('/about')
def aboutus():
	teachers = Teacher.query.all()
	return render_template("aboutus.html",page="about", teachers = teachers)

@app.route('/contact')
def contactus():
	teachers = Teacher.query.all()
	return render_template("contactus.html",page="contact", teachers = teachers)


@app.route('/posts')
@login_required
def posts():
    """ The main page. If there is a GET argument called 'category', only posts of
    that category is given to the template. Else, all posts, ordered by id (and there by date)
    is given"""

    categories = Category.query.all()
    teachers = Teacher.query.all()
    category_id = request.args.get('category_id')
    if category_id:
        posts = Post.query.filter_by(category_id=category_id).order_by(Post.id.desc()).all()
        bycategory = True
        categoryname = Category.query.get(category_id).name
        return render_template('posts.html',page="home", posts = posts,utc_to_local=utc_to_local,
    bycategory = bycategory, category_id = category_id, categories=categories,
    categoryname=categoryname, teachers=teachers)

    else:
        posts = Post.query.order_by(Post.id.desc()).all()
        bycategory = False
        return render_template('posts.html',page="posts", posts = posts,utc_to_local=utc_to_local,
    bycategory = bycategory, categories=categories,teachers=teachers)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if g.user is not None and g.user.is_authenticated():
            return redirect(url_for('posts'))
        return render_template('login.html',page="login")

    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            if not user.verified:
                return render_template('pendingverification.html')
            if check_password_hash(user.pwdhash, password):
                user.authenticated = True
                db.session.commit()
                login_user(user)
                return redirect(url_for('posts'))
            flash('Username or Password is invalid' , 'warning')
            return render_template("login.html",page="login")
        else:
            flash('Username or Password is invalid' , 'warning')
            return render_template("login.html",page="login")

@app.route('/logout')
@login_required
def logout():
    g.user.authenticated = False
    db.session.commit()
    logout_user()
    flash('Logged out successfully.' , 'success')
    return redirect(url_for('login'))

@app.route('/admin/verify',methods=['GET','POST'])
@login_required
def admin_verify():
    if g.user.is_admin:
        if request.method == 'POST':
            app.logger.info(request.form)
            formtype = request.form['formtype']
            user_id = request.form['userid']
            user = User.query.get(int(user_id))
            if formtype == 'approve':
                user.verified = True
                db.session.add(user)
            elif formtype == 'reject':
                if user.verified == False:
                    db.session.delete(user)
            db.session.commit()
            return redirect(url_for('admin_verify'))

        categories = Category.query.all()
        teachers = Teacher.query.all()
        unverifiedusers = User.query.filter_by(verified=False).order_by(User.id.desc()).all()
        return render_template('admin-verify.html', unverifiedusers = unverifiedusers, categories=categories, teachers=teachers, page="admin" )

@app.route('/admin/comments',methods=['GET','POST'])
@login_required
def admin_comments():
    if g.user.is_admin:
        if request.method == 'POST':
            app.logger.info(request.form)
            formtype = request.form['formtype']
            comment_id = request.form['commentid']
            comment = Comment.query.get(int(comment_id))
            if formtype == 'unflag':
                comment.flagged = False
                db.session.add(comment)
            elif formtype == 'delete':
                db.session.delete(comment)

            db.session.commit()
            return redirect(url_for('admin_comments'))

        categories = Category.query.all()
        teachers = Teacher.query.all()
        flaggedcomments = Comment.query.filter_by(flagged=True).order_by(Comment.id.desc()).all()
        return render_template('admin-comments.html', flaggedcomments = flaggedcomments, categories=categories, teachers=teachers, page="admin" )


@app.route('/admin/discussions',methods=['GET','POST'])
@login_required
def admin_discussions():
    if g.user.is_admin:
        if request.method == 'POST':
            app.logger.info(request.form)
            formtype = request.form['formtype']
            discussion_id = request.form['discussionid']
            discussion = Discussion.query.get(int(discussion_id))
            if formtype == 'unflag':
                discussion.flagged = False
                db.session.add(discussion)
            elif formtype == 'delete':
                for comment in discussion.comments.all():
                    db.session.delete(comment)
                db.session.delete(discussion)

            db.session.commit()
            return redirect(url_for('admin_discussions'))

        categories = Category.query.all()
        teachers = Teacher.query.all()
        flaggeddiscussions = Discussion.query.filter_by(flagged=True).order_by(Discussion.id.desc()).all()
        return render_template('admin-discussions.html', flaggeddiscussions = flaggeddiscussions, categories=categories, teachers=teachers, page="admin" )



@app.route('/admin/teachers',methods=['GET','POST'])
@login_required
def admin_teachers():
    if g.user.is_admin:
        if request.method == 'POST':
            app.logger.info(request.form)
            formtype = request.form['formtype']
            if formtype == 'makeadmin':
                userid = request.form['userid']
                user = User.query.get(int(userid))
                if user.user_role == 'teacher':
                    user.is_admin = True
                    db.session.add(user)
                    db.session.commit()


 
            return redirect(url_for('admin_teachers'))

        categories = Category.query.all()
        teachers = Teacher.query.all()
        return render_template('admin-teachers.html', categories=categories, teachers=teachers, page="admin" )

@app.route('/admin/students')
@login_required
def admin_students():
    if g.user.is_admin:
        categories = Category.query.all()
        teachers = Teacher.query.all()
        students = Student.query.all()
        return render_template('admin-students.html', students = students, categories=categories, teachers=teachers, page="admin" )



@app.route('/user/edit',methods=['GET','POST'])
@login_required
def edituser():
    categories = Category.query.all()
    teachers = Teacher.query.all()

    error = False
    if request.method == 'GET':
        return render_template('edituser.html',page="edituser", categories=categories,teachers=teachers)

    elif request.method == 'POST':
        app.logger.info(repr(request.form))
        edittype = request.form['edittype']
        if edittype == 'changepassword':
            oldpassword = request.form['old-password']
            newpassword = request.form['new-password']
            passwordconfirm = request.form['password-confirm']
            if newpassword != passwordconfirm:
                error = True
                flash("Passwords don't match",'warning')

            if not check_password_hash(g.user.pwdhash, oldpassword):
                error = True
                flash("Current Password is invalid",'warning')
            if error:
                return render_template('edituser.html',page="edituser",categories=categories,teachers=teachers)
            else:
                g.user.pwdhash = generate_password_hash(newpassword)
                db.session.commit()
                flash("Password changed succesfully.",'success')
                return render_template('edituser.html',page="edituser",categories=categories,teachers=teachers)

        elif edittype == 'userdetails':
            usrname = request.form['name']
            mobno = request.form['mobilenumber']
            password = request.form['password']
            if len(mobno) != 10 or not mobno.isdigit():
                error = True
                flash("Mobile number is invalid",'warning')
            if not check_password_hash(g.user.pwdhash, password):
                error = True
                flash("Password is invalid",'warning')
            if error:
                return render_template('edituser.html',page="edituser",categories=categories,teachers=teachers)
            else:
                g.user.name = usrname
                g.user.mobilenumber = mobno
                db.session.commit()
                flash("Details changed succesfully.",'success')
                return render_template('edituser.html',page="edituser",categories=categories,teachers=teachers)


@app.route('/register',methods=['GET','POST'])
def register():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('posts'))

    error = False
    if request.method == 'GET':
        return render_template('register.html',page="register")

    elif request.method == 'POST':
        app.logger.info(repr(request.form))
        name = request.form['name']
        email = request.form['email']
        mobilenumber = request.form['mobilenumber']

        password = request.form['password']
        passwordconfirm = request.form['password-confirm']
        user_role = request.form['user_role']

        user = User.query.filter_by(email=email).first()
        if user:

            error = True
            flash('Email already registered','warning')

        if password != passwordconfirm:
            error = True
            flash("Passwords don't match",'warning')
        if len(mobilenumber) != 10 or not mobilenumber.isdigit():
            error = True
            flash("Mobile number is invalid",'warning')

        #app.logger.info("Error = ", str(error))
        if error:
            return render_template('register.html',page="register",retry=True, oldform = request.form)
        else:
            if user_role == 'teacher':
                newuser = Teacher(name,email,password,mobilenumber,user_role)
            elif user_role == 'student':
                newuser = Student(name,email,password,mobilenumber,user_role)

            newuser.authenticated = True
            db.session.add(newuser)
            db.session.commit()
            return render_template('pendingverification.html')

@app.route('/posts/<post_id>',methods = ['GET', 'POST'])
@login_required
def viewpost(post_id):
    """Route for individual posts, identified by post_id. The POST request
    is handled for removing posts. Upon receiving the delete request, the logged in user
    is checked with the post owner, and the files are removed one by one."""
    post = Post.query.get(int(post_id))
    if not post:
        flash('No such post found.', 'warning')
        return redirect(url_for('posts'))
    categories = Category.query.all()
    teachers = Teacher.query.all()
    if request.method == 'GET':
        return render_template('post.html', post=post, categories=categories,
               utc_to_local=utc_to_local,teachers=teachers)

    if request.method == 'POST':
        app.logger.info(repr(request.form))
        formtype = request.form['formtype']
        if formtype == 'delpost':
            if post.user_id == g.user.id:
                files = post.documents.all()
                for f in files:
                    if f.filetype == 'image':
                        os.remove(os.path.join(app.config['IMAGE_FOLDER'], f.filename))
                    elif f.filetype == 'doc':
                        os.remove(os.path.join(app.config['DOC_FOLDER'], f.filename))
                    db.session.delete(f)
                db.session.delete(post)
                db.session.commit()
                flash('Post removed','success')
                return redirect(url_for('posts'))
        elif formtype == 'addcomment':
            text = request.form['commenttext']
            newcomment = Comment(text,g.user.id,'post', post.id)
            db.session.add(newcomment)
            db.session.commit()

        elif formtype == 'delcomment':
            commentid = request.form['commentid']
            comment = Comment.query.get(int(commentid))
            if comment and comment.user.id == g.user.id:
                db.session.delete(comment)
                db.session.commit()
        elif formtype == 'flagcomment':
            commentid = request.form['commentid']
            comment = Comment.query.get(int(commentid))
            if comment and g.user.user_role == 'teacher':
                comment.flagged = True
                db.session.add(comment)
                db.session.commit()

        return redirect(url_for('viewpost',post_id=post.id))


@app.route('/teachers/<user_id>')
@login_required
def viewuser(user_id):
    user = User.query.get(int(user_id))
    if not user or user.user_role != 'teacher':

        flash('No such teacher found.', 'warning')
        return redirect(url_for('posts'))

    teachers = Teacher.query.all()
    categories = Category.query.all()
    posts = Post.query.filter_by(user_id=user.id).all()
    for i in posts:
        i.type = 'post'
    discussions = Discussion.query.filter_by(user_id=user.id).all()
    for i in discussions:
        i.type = 'discussion'
    assignments = Assignment.query.filter_by(user_id=user.id).all()
    for i in assignments:
        i.type = 'assignment'
    items = posts + discussions + assignments
    items = sorted(items, key=lambda i : i.timestamp, reverse=True)
    return render_template('user.html', items = items, user=user, utc_to_local = utc_to_local,
        teachers=teachers,categories=categories,page="user")

@app.route('/posts/new', methods = ['GET', 'POST'])
@login_required
def newpost():
    """ Creates a new post. The POST request is sent from the client's browser by ajax
    using XMLHttpRequest."""

    if request.method == 'GET':
        categories = Category.query.all()
        teachers = Teacher.query.all()
        return render_template('newpost.html', categories=categories, teachers=teachers,page="newpost" )
    elif request.method == 'POST':
        app.logger.info(repr(request.form))
        title = request.form['title']
        posttext = request.form['posttext']
        category_id = request.form['category']
        newpost = Post(title, posttext, category_id, g.user.id)
        db.session.add(newpost)
        db.session.commit()

        post_id =newpost.id

        if not os.path.isdir(app.config['IMAGE_FOLDER']):
            try:
                os.makedirs(app.config['IMAGE_FOLDER'])
            except:
                app.logger.info("Couldn't create directory")
                return "Couldn't create directory"

        if not os.path.isdir(app.config['DOC_FOLDER']):
            try:
                os.makedirs(app.config['DOC_FOLDER'])
            except:
                app.logger.info("Couldn't create directory")
                return "Couldn't create directory"

        for idx,f in enumerate(request.files.getlist("file")):
            app.logger.info(repr(f.content_type))
            if f.__dict__['filename'] == '':
                continue
            filename = "p%d_%s"%(post_id,f.__dict__['filename'])
            if f.content_type[:5] == 'image':
                filetype = 'image'
                f.save(os.path.join(app.config['IMAGE_FOLDER'], filename))
            else:
                filetype = 'doc'
                f.save(os.path.join(app.config['DOC_FOLDER'], filename))

            newfile = Document(filename, filetype, 'post', post_id,g.user.id)
            db.session.add(newfile)
            db.session.commit()

        students = [student.email for student in Student.query.filter_by(verified=True).all()]
        app.logger.info(students)
        send_email("New post: %s" %newpost.title,
            'TIM',
            students,
            render_template('newpostemail.html',post=newpost)
            )
        studentnumbers = [student.mobilenumber for student in Student.query.filter_by(verified=True).all()]
        app.logger.info(studentnumbers)
        payload = {'user':"<usercredentials>", 'senderID':"TEST SMS", 'state':4,
        'msgtxt':"TIM-New post by %s : %s"%(g.user.name, newpost.title) }
        send_sms(payload, studentnumbers)

        flash('Post created successfully' , 'success')
        return "ok"

@app.route('/discussions/new', methods = ['GET', 'POST'])
@login_required
def newdiscussion():
    """ Creates a new discussion. The POST request is sent from the client's browser by ajax
    using XMLHttpRequest."""

    if request.method == 'GET':
        categories = Category.query.all()
        teachers = Teacher.query.all()
        return render_template('newdiscussion.html', categories=categories, teachers=teachers,page="newdiscussion")
        
    elif request.method == 'POST':
        app.logger.info(repr(request.form))
        title = request.form['title']
        posttext = request.form['posttext']
        category_id = request.form['category']
        new_discussion = Discussion(title, posttext, category_id, g.user.id)
        db.session.add(new_discussion)
        db.session.commit()

        discussion_id =new_discussion.id

        if not os.path.isdir(app.config['IMAGE_FOLDER']):
            try:
                os.makedirs(app.config['IMAGE_FOLDER'])
            except:
                app.logger.info("Couldn't create directory")
                return "Couldn't create directory"

        if not os.path.isdir(app.config['DOC_FOLDER']):
            try:
                os.makedirs(app.config['DOC_FOLDER'])
            except:
                app.logger.info("Couldn't create directory")
                return "Couldn't create directory"

        for idx,f in enumerate(request.files.getlist("file")):
            app.logger.info(repr(f.content_type))
            if f.__dict__['filename'] == '':
                continue
            filename = "d%d_%s"%(discussion_id,f.__dict__['filename'])
            if f.content_type[:5] == 'image':
                filetype = 'image'
                f.save(os.path.join(app.config['IMAGE_FOLDER'], filename))
            else:
                filetype = 'doc'
                f.save(os.path.join(app.config['DOC_FOLDER'], filename))

            newfile = Document(filename, filetype, 'discussion', discussion_id,g.user.id)
            db.session.add(newfile)
            db.session.commit()

        students = [student.email for student in Student.query.all()]
        app.logger.info(students)
        send_email("New post: %s" %new_discussion.title,
            'TIM',
            students,
            render_template('newdiscussionemail.html',discussion=new_discussion)
            )


        flash('Discussion created successfully' , 'success')
        return "ok"
        


@app.route('/discussions', methods = ['GET', 'POST'])
@login_required
def discussions():
    categories = Category.query.all()
    teachers = Teacher.query.all()
    category_id = request.args.get('category_id')
    if category_id:
        discussions = Discussion.query.filter_by(category_id=category_id).order_by(Discussion.id.desc()).all()
        bycategory = True
        categoryname = Category.query.get(category_id).name
        return render_template('discussions.html',page="discussions", discussions = discussions,utc_to_local=utc_to_local,
    bycategory = bycategory, category_id = category_id, categories=categories,
    categoryname=categoryname, teachers=teachers)

    else:
        discussions = Discussion.query.order_by(Discussion.id.desc()).all()
        bycategory = False
        return render_template('discussions.html',page="discussions", discussions = discussions,utc_to_local=utc_to_local,
    bycategory = bycategory, categories=categories,teachers=teachers)


@app.route('/discussions/<discussion_id>',methods = ['GET', 'POST'])
@login_required
def viewdiscussion(discussion_id):
    """Route for individual discussions, identified by discussion_id. The POST request
    is handled for removing discussion. Upon receiving the delete request, the logged in user
    is checked with the discussion owner, and the files are removed one by one."""
    discussion = Discussion.query.get(int(discussion_id))
    if not discussion:
        flash('No such discussion found.', 'warning')
        return redirect(url_for('discussions'))
    categories = Category.query.all()
    teachers = Teacher.query.all()
    if request.method == 'GET':
        return render_template('discussion.html', post=discussion, categories=categories,
               utc_to_local=utc_to_local,teachers=teachers, page="discussions")

    if request.method == 'POST':
        app.logger.info(repr(request.form))
        formtype = request.form['formtype']
        if formtype == 'deldiscussion':
            if discussion.user_id == g.user.id:
                files = discussion.documents.all()
                for f in files:
                    if f.filetype == 'image':
                        os.remove(os.path.join(app.config['IMAGE_FOLDER'], f.filename))
                    elif f.filetype == 'doc':
                        os.remove(os.path.join(app.config['DOC_FOLDER'], f.filename))
                    db.session.delete(f)
                db.session.delete(discussion)
                db.session.commit()
                flash('Discussion removed','success')
                return redirect(url_for('discussions'))

        elif formtype == 'addcomment':
            text = request.form['commenttext']
            newcomment = Comment(text,g.user.id,'discussion', discussion.id)
            db.session.add(newcomment)
            db.session.commit()

        elif formtype == 'delcomment':
            commentid = request.form['commentid']
            comment = Comment.query.get(int(commentid))
            if comment and comment.user.id == g.user.id:
                db.session.delete(comment)
                db.session.commit()
        elif formtype == 'flagcomment':
            commentid = request.form['commentid']
            comment = Comment.query.get(int(commentid))
            if comment and g.user.user_role == 'teacher':
                comment.flagged = True
                db.session.add(comment)
                db.session.commit()

        elif formtype == 'flagdiscussion':
            discussion.flagged = True
            db.session.add(discussion) 
            db.session.commit()
       

        return redirect(url_for('viewdiscussion',discussion_id=discussion.id))

@app.route('/assignments', methods = ['GET', 'POST'])
@login_required
def assignments():
    categories = Category.query.all()
    teachers = Teacher.query.all()
    category_id = request.args.get('category_id')
    if category_id:
        assignments = Assignment.query.filter_by(category_id=category_id).order_by(Assignment.id.desc()).all()
        bycategory = True
        categoryname = Category.query.get(category_id).name
        return render_template('assignments.html',page="assignments", assignments = assignments,utc_to_local=utc_to_local,
    bycategory = bycategory, category_id = category_id, categories=categories,
    categoryname=categoryname, teachers=teachers)

    else:
        assignments = Assignment.query.order_by(Assignment.id.desc()).all()
        bycategory = False
        return render_template('assignments.html',page="assignments", assignments = assignments,utc_to_local=utc_to_local,
    bycategory = bycategory, categories=categories,teachers=teachers)

@app.route('/assignments/new', methods = ['GET', 'POST'])
@login_required
def newassignment():
    """ Creates a new Assignment."""

    if request.method == 'GET':
        categories = Category.query.all()
        teachers = Teacher.query.all()
        return render_template('newassignment.html', categories=categories, teachers=teachers,page="newdiscussion")
        
    elif request.method == 'POST':
        app.logger.info(repr(request.form))
        title = request.form['title']
        posttext = request.form['posttext']
        category_id = request.form['category']
        duedate = request.form['duedate']

        new_assignment= Assignment(title, posttext, duedate, category_id, g.user.id)
        db.session.add(new_assignment)
        db.session.commit()

        assignment_id =new_assignment.id

        if not os.path.isdir(app.config['IMAGE_FOLDER']):
            try:
                os.makedirs(app.config['IMAGE_FOLDER'])
            except:
                app.logger.info("Couldn't create directory")
                return "Couldn't create directory"

        if not os.path.isdir(app.config['DOC_FOLDER']):
            try:
                os.makedirs(app.config['DOC_FOLDER'])
            except:
                app.logger.info("Couldn't create directory")
                return "Couldn't create directory"

        for idx,f in enumerate(request.files.getlist("file")):
            app.logger.info(repr(f.content_type))
            if f.__dict__['filename'] == '':
                continue
            filename = "a%d_%s"%(assignment_id,f.__dict__['filename'])
            if f.content_type[:5] == 'image':
                filetype = 'image'
                f.save(os.path.join(app.config['IMAGE_FOLDER'], filename))
            else:
                filetype = 'doc'
                f.save(os.path.join(app.config['DOC_FOLDER'], filename))

            newfile = Document(filename, filetype, 'assignment', assignment_id,g.user.id)
            db.session.add(newfile)
            db.session.commit()

        students = [student.email for student in Student.query.all()]
        app.logger.info(students)
        send_email("New post: %s" %new_assignment.title,
            'TIM',
            students,
            render_template('newassignmentemail.html',assignment=new_assignment)
            )


        flash('Assignment created successfully' , 'success')
        return "ok"
        

@app.route('/assignments/<assignment_id>',methods = ['GET', 'POST'])
@login_required
def viewassignment(assignment_id):
    
    assignment = Assignment.query.get(int(assignment_id))
    if not assignment:
        flash('No such assignment found.', 'warning')
        return redirect(url_for('assignments'))
    categories = Category.query.all()
    teachers = Teacher.query.all()
    if request.method == 'GET':
        return render_template('assignment.html', assignment=assignment, categories=categories,
               utc_to_local=utc_to_local,teachers=teachers, page="assignments",
               now=datetime.datetime.utcnow())

    if request.method == 'POST':
        app.logger.info(repr(request.form))
        formtype = request.form['formtype']
        if formtype == 'delassignment':
            if assignment.user_id == g.user.id:
                files = assignment.documents.all()
                for f in files:
                    if f.filetype == 'image':
                        os.remove(os.path.join(app.config['IMAGE_FOLDER'], f.filename))
                    elif f.filetype == 'doc':
                        os.remove(os.path.join(app.config['DOC_FOLDER'], f.filename))
                    db.session.delete(f)
                db.session.delete(assignment)
                db.session.commit()
                flash('Assignment removed','success')
                return redirect(url_for('assignments'))
        if formtype == 'adddocument':
            if not os.path.isdir(app.config['ASSIGNMENT_FOLDER']+'/'+str(assignment.id)):
                try:
                    os.makedirs(app.config['ASSIGNMENT_FOLDER']+'/'+str(assignment.id))
                except:
                    app.logger.info("Couldn't create directory")
                    return "Couldn't create directory"
            app.logger.info(request.files.getlist("file"))
            f = request.files.getlist("file")[0]
            filename = g.user.name +'-'+ f.__dict__['filename']
            f.save(os.path.join(app.config['ASSIGNMENT_FOLDER']+'/'+str(assignment.id), filename))
            prev = g.user.documents.filter_by(assignment_id=assignment.id).first()
            if prev:
                os.remove(os.path.join(app.config['ASSIGNMENT_FOLDER']+'/'+str(assignment.id), prev.filename))
                db.session.delete(prev)
                db.session.commit()

            newfile = Document(filename,'assignmentsubmission','assignment',assignment.id,g.user.id)
            db.session.add(newfile)
            db.session.commit()

            if os.path.exists(app.config['ASSIGNMENT_FOLDER']+'/'+str(assignment.id)+'/all.zip'):
                os.remove(app.config['ASSIGNMENT_FOLDER']+'/'+str(assignment.id)+'/all.zip')
            shutil.make_archive(app.config['ASSIGNMENT_FOLDER']+str(assignment.id)+'all',
                'zip',app.config['ASSIGNMENT_FOLDER']+'/'+str(assignment.id))
            shutil.move(app.config['ASSIGNMENT_FOLDER']+str(assignment.id)+'all.zip',app.config['ASSIGNMENT_FOLDER']+'/'+str(assignment.id)+'/all.zip')


        return redirect(url_for('viewassignment',assignment_id=assignment.id))


@app.route('/test/<template>')
def test(template):
    """ Route for quickly testing templates under development"""
    return render_template(template+'.html')


def utc_to_local(utc_dt):
    """Used for converting time stored as UTC to Asia/Kolkata timezone and
    display it in preferred formats. Depends on pytz"""

    local_tz = pytz.timezone('Asia/Kolkata')
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)


def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target = f, args = args, kwargs = kwargs)
        thr.start()
    return wrapper

@async
def send_sms(payload, numbers):
    for i in numbers:
        payload['receipientno'] = i
        # r = req.get("http://localhost:5050", params = payload)
        r = req.get("http://api.mVaayoo.com/mvaayooapi/MessageCompose", params = payload)


@async
def send_async_email(subject,sender,recipients,text_body):
    with app.app_context():
        with mail.connect() as conn:
            for i in recipients:
                msg = Message(subject, sender = sender, recipients = [i])
                msg.html = text_body

                conn.send(msg)
        app.logger.info('Sent email')

def send_email(subject, sender, recipients, text_body):
    send_async_email(subject,sender,recipients,text_body)

@app.route('/test', methods=['GET'])
def testpost():
    app.logger.info(request)
    return "ok"
if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8008)
