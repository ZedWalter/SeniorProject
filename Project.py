from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
with app.app_context():
    db = SQLAlchemy(app)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    on_bus = db.Column(db.Boolean, nullable=False)
    dob = db.Column(db.Date, nullable=False)
    conditions = db.Column(db.String(500))
    contact_info = db.Column(db.Integer)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'))

    def __repr__(self):
        return '<Student %r>' % self.id

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route = db.Column(db.Integer, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'))
    students = db.relationship('Student')

    def __repr__(self):
        return '<Route %r>' % self.id

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    conditions = db.Column(db.String(500))
    routes = db.relationship('Route')

    def __repr__(self):
        return '<Driver %r>' % self.id


@app.route('/', methods=['GET'])
def display_home():
    return render_template('landing.html')

@app.route('/admin', methods=['GET'])
def display():
    return render_template('admin.html')

##############################################
#USER ROUTES
##############################################


@app.route('/user', methods=['GET'])
def display_user():
    routes = Route.query.order_by(Route.route).all()
    return render_template('user.html', routes=routes)

@app.route('/route/<int:id>', methods=['GET'])
def display_route(id):
    student = Student.query.filter(Student.route_id == id).order_by(Student.first_name).all()
    all_students = Student.query.order_by(Student.first_name).all()
    route_help = student[0]
    current_route = Route.query.get_or_404(id)
    return render_template('route.html', route_help=route_help, students=student, all_students=all_students, current_route=current_route)
    

@app.route('/routeboarding/<int:id>')
def change_boarding_status(id):
    student = Student.query.get_or_404(id)
    if student.on_bus == False:
        student.on_bus = True
    else:
        student.on_bus = False
    db.session.commit()
    return redirect(f'/route/{student.route_id}')

@app.route('/offloadstudents/<int:id>', methods=['POST'])
def offload_all_students(id):
    students = Student.query.filter(Student.route_id == id).order_by(Student.first_name).all()
    for student in students:
        student.on_bus = False
        db.session.commit()
    return redirect(f'/route/{student.route_id}')

@app.route('/overridestudent/<int:id>', methods=['POST'])
def override_student(id):
    edit_student_id = request.form['student']
    student = Student.query.get_or_404(edit_student_id)
    student.route_id = id
    db.session.commit()
    return redirect(f'/route/{student.route_id}')


##############################################
#STUDENT ROUTES
##############################################

@app.route('/students', methods=['GET'])
def display_students():
    student = Student.query.order_by(Student.first_name).all()
    routes = {}
    query = Route.query.all()
    for route in query:
        routes[route.id] = route
    return render_template('students.html', students=student, routes=routes) 

@app.route('/addstudent', methods=['GET','POST'])
def add_student():
    if request.method == 'POST':
        temp_dob = request.form['dob']
        format = '%Y-%m-%d'
        casted_dob = datetime.strptime(temp_dob,format)
        new_student = Student(first_name = request.form['first_name'],
        last_name = request.form['last_name'],
        on_bus = False,
        dob = casted_dob,
        conditions = request.form['conditions'],
        contact_info = request.form['contact_info'],
        route_id = request.form['route_id']
        )
        try:
            db.session.add(new_student)
            db.session.commit()
            return redirect('/students')
        except Exception as e:
            print(e)
            return 'There was an error adding the student'

    else:
        routes = Route.query.order_by(Route.route).all()
        return render_template('addstudent.html', routes=routes)


@app.route('/editstudent/<int:id>', methods=['POST', 'GET'] )
def edit_student(id):
    if request.method == 'POST':
        temp_dob = request.form['dob']
        format = '%Y-%m-%d'
        casted_dob = datetime.strptime(temp_dob,format)
        edit_student = Student.query.get_or_404(id)
        edit_student.first_name = request.form['first_name']
        edit_student.last_name = request.form['last_name']
        edit_student.on_bus = False
        edit_student.dob = casted_dob
        edit_student.conditions = request.form['conditions']
        edit_student.contact_info = request.form['contact_info']
        edit_student.route_id = request.form['route_id']
        try:
            db.session.commit()
            return redirect('/students')
        except:
            return 'There was an error updating your task'
    
    else:
        student = Student.query.get_or_404(id)
        routes = Route.query.order_by(Route.route).all()
        return render_template('editstudent.html', student=student, routes=routes)

@app.route('/removestudent/<int:id>')
def remove_student(id):
    student_to_delete = Student.query.get_or_404(id)

    try:
        db.session.delete(student_to_delete)
        db.session.commit()
        return redirect('/students')
    except:
        return 'There was an error deleting your task'
    
@app.route('/studentexpanded/<int:id>', methods=['GET'])
def display_expanded_student(id):
    student = Student.query.get(id)
    if student is None:
        return render_template('400page.html')
    return render_template('studentexpanded.html', student=student)

##############################################
#ROUTE ROUTES
##############################################

@app.route('/routes', methods=['GET'])
def display_routes():
    route = Route.query.order_by(Route.route).all()
    drivers = {}
    query = Driver.query.all()
    for driver in query:
        drivers[driver.id] = driver
    return render_template('routes.html', routes=route, drivers=drivers)

@app.route('/addroute', methods=['GET', 'POST'])
def add_route():
    if request.method == 'POST':
        new_route = Route(route = request.form['route'],
        driver_id = request.form['driver_id']                  
        )
        try:
            db.session.add(new_route)
            db.session.commit()
            return redirect('/routes')
        except Exception as e:
            print(e)
            return 'There was an error adding the route'
        
    else:
        drivers = Driver.query.order_by(Driver.first_name).all()
        routes = {}
        query = Route.query.all()
        for route in query:
            routes[route.driver_id] = route
        return render_template('addroute.html', drivers=drivers, routes=routes)

@app.route('/editroute/<int:id>', methods=['POST','GET'])
def edit_route(id):
    if request.method == 'POST':
        edit_route = Route.query.get_or_404(id)
        edit_route.route = request.form['route']
        edit_route.driver_id = request.form['driver_id']
        try:
            db.session.commit()
            return redirect('/routes')
        except:
            return 'There was an error adding the student'
    
    else:
        route = Route.query.get_or_404(id)
        drivers = Driver.query.order_by(Driver.first_name).all()
        return render_template('editroute.html', route=route, drivers=drivers)

@app.route('/removeroute/<int:id>')
def remove_route(id):
    route_to_delete = Route.query.get_or_404(id)

    try:
        db.session.delete(route_to_delete)
        db.session.commit()
        return redirect('/routes')
    except:
        return 'There was an error deleting your task'


@app.route('/routesexpanded/<int:id>', methods=['GET'])
def display_expanded_routes(id):
    route = Route.query.get(id)
    if route is None:
        return render_template('400page.html')
    drivers = {}
    query = Driver.query.all()
    for driver in query:
        drivers[driver.id] = driver
    students = Student.query.filter(Student.route_id == id).order_by(Student.first_name).all()
    return render_template('routesexpanded.html', route=route, students=students, drivers=drivers)

##############################################
#DRIVER ROUTES
##############################################

@app.route('/drivers', methods=['GET'])
def display_drivers():
    driver = Driver.query.order_by(Driver.first_name).all()
    routes = {}
    query = Route.query.all()
    for route in query:
        routes[route.driver_id] = route
    return render_template('drivers.html', drivers=driver, routes=routes) 

@app.route('/adddriver', methods=['GET', 'POST'])
def add_driver():
    if request.method == 'POST':
        temp_dob = request.form['dob']
        format = '%Y-%m-%d'
        casted_dob = datetime.strptime(temp_dob,format)
        new_driver = Driver(first_name = request.form['first_name'],
        last_name = request.form['last_name'], 
        dob = casted_dob,
        conditions = request.form['conditions']               
        )
        try:
            db.session.add(new_driver)
            db.session.commit()
            return redirect('/drivers')
        except Exception as e:
            print(e)
            return 'There was an error adding the student'
        
    else:
        return render_template('adddriver.html')

@app.route('/editdriver/<int:id>', methods=['POST','GET'])
def edit_driver(id):
    if request.method == 'POST':
        temp_dob = request.form['dob']
        format = '%Y-%m-%d'
        casted_dob = datetime.strptime(temp_dob,format)
        edit_driver = Driver.query.get_or_404(id)
        edit_driver.first_name = request.form['first_name']
        edit_driver.last_name = request.form['last_name']
        edit_driver.dob = casted_dob
        edit_driver.conditions = request.form['conditions']
        try:
            db.session.commit()
            return redirect('/drivers')
        except:
            return 'There was an error adding the student'
        
    else:
        driver = Driver.query.get_or_404(id)
        return render_template('editdriver.html', driver=driver)


@app.route('/removedriver/<int:id>')
def remove_driver(id):
    driver_to_delete = Driver.query.get_or_404(id)

    try:
        db.session.delete(driver_to_delete)
        db.session.commit()
        return redirect('/drivers')
    except:
        return 'There was an error deleting your task'




if __name__ == "__main__":
    app.run(debug=True)
