from MySQLdb import connections
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL, MySQLdb
import datetime
import hashlib
import re

app = Flask(__name__)

# Connection MySQL
app.config['MYSQL_HOST'] = 'bopzzm3wvllhte5nnepy-mysql.services.clever-cloud.com'
app.config['MYSQL_USER'] = 'u1abqfyilh7e5mat'
app.config['MYSQL_PASSWORD'] = 'lcnX1iCTWu3kMSoTZtgg'
app.config['MYSQL_DB'] = 'bopzzm3wvllhte5nnepy'

mysql = MySQL(app)

app.secret_key = 'mysecretkey'

@app.route('/')
def home():
    if 'name' in session:
        id = session['id'] 
        return redirect(url_for('sessiones', id = id))
    else:
        return render_template('home.html')

@app.route('/register')
def registrer():
    if 'name' in session:
        id = session['id'] 
        return redirect(url_for('sessiones', id = id))
    else:
        return render_template('register.html')

@app.route('/login')
def login():
    if 'name' in session:
        id = session['id'] 
        return redirect(url_for('sessiones', id = id))
    else:
        return render_template('login.html')

@app.route('/profile/<string:id>')
def profile(id):
    if 'name' in session:
        if session['id'] == int(id): 
            cursor = mysql.connection.cursor()
            cursor.execute(f'SELECT * FROM usuarios WHERE id = {id}')
            datas = cursor.fetchone()

            # Calculo edad
            edad_nacimiento = datas[3]

            hoy = datetime.date.today()
            año = edad_nacimiento.year
            mes = edad_nacimiento.month
            dia = edad_nacimiento.day

            edad = 0
            while edad_nacimiento < hoy:
                edad += 1
                edad_nacimiento = datetime.date(año+edad, mes, dia)

            edad = edad -1

            return render_template('profile.html', datas = datas, edad = edad)
        else:
            return 'error'
    else:
        return redirect('/')

#-------------------------------------------

# Register
@app.route('/register/post', methods = ['GET','POST'])
def registerpost():

    name = request.form['names']
    surnames = request.form['surnames']
    fechanac = request.form['fecha_nacimiento']
    ocupation = request.form['ocupation']
    email = request.form['email']
    password = request.form['password'].encode("utf-8")

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
    datas = cur.fetchone()

    if datas == None:

        passoword_encode = hashlib.sha1(password)
        passoword_encode = passoword_encode.hexdigest()

        if name != '' and email != '' and password != '':
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO usuarios (nombes, apellidos, fechanac, ocupacion, email, clave) VALUES (%s, %s, %s, %s, %s, %s)',(name, surnames, fechanac, ocupation, email, passoword_encode))
            mysql.connection.commit()
            
            session['name'] = name
            session['email'] = email

            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
            datas = cur.fetchone()
            
            session['id'] = datas[0]

            return redirect(url_for('sessiones', id = datas[0]))
        else:
            flash('Rellene todos los campos')
            return redirect('/register')
    else:
        flash('Ingrese un correo valido')
        return redirect('/register')

# Login
@app.route('/login/post', methods = ['GET','POST'])
def loginpost():

    email = request.form['email']
    password = request.form['password'].encode('utf-8')

    # Encode password post
    passoword_encode = hashlib.sha1(password)
    passoword_encod = passoword_encode.hexdigest()

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
    datas = cur.fetchone()

    if email != '' and password != '':
        if datas != None:
            if email == datas[5] and passoword_encod == datas[6]:
                session['name'] = datas[1]
                session['email'] = datas[5]
                session['id'] = datas[0]
                return redirect(url_for('sessiones', id = datas[0]))

            else:
                flash('Contraseña incorrecta')
                return redirect(url_for('login'))
        else:
            flash('Correo o contraseña incorrecto')
            return redirect(url_for('login'))
    else:
        flash('Rellene todos los campos')
        return redirect(url_for('login'))

# Session user
@app.route('/session/<string:id>')
def sessiones(id):
    if 'name' in session:
        if session['id'] == int(id):  

            # Filter 
            if 'date' in session:
                cur = mysql.connection.cursor()
                cur.execute(f"SELECT * FROM eventos WHERE (fecha = '{session['date']}' OR hora = '{session['time']}' OR lugar = '{session['lugar']}' ) AND idusuario = '{id}' ")
                datas = cur.fetchall()

                if len(session['date']) != 0:
                    if datas != ():
                        message = 'Eventos registrados el '+'"'+ session['date'] + '"'
                    else:
                        message = 'No se encontraron eventos registrados el '+'"'+ session['date'] + '"'
                        
                elif len(session['time']) != 0:
                    if datas != ():
                        message = 'Eventos registrados a las '+'"'+ session['time'] + '"'
                    else:
                        message = 'No se encontraron eventos a las '+'"'+ session['time'] + '"'

                elif len(session['desc']) != 0:

                    cur = mysql.connection.cursor()
                    cur.execute(f"SELECT * FROM eventos WHERE (descripcion LIKE '%{session['desc']}%') AND idusuario = '{id}' ")
                    datas = cur.fetchall()
                    
                    if datas != ():
                        message = 'Conicidencias con '+'"'+ session['desc'] + '"'
                    else:
                        message = 'No se encontraron coincidencias con '+'"'+ session['desc'] + '"'

                elif len(session['lugar']) != 0:
                    if datas != ():
                        message = 'Eventos en el lugar '+'"'+ session['lugar'] + '"'
                    else:
                        message = 'No se encontraron eventos en el lugar '+'"'+ session['lugar'] + '"'
                else:
                    message = 'No se ingreso un dato en el filtro'

                return render_template('session.html', datas = datas, id = id, message = message)
            
            # Proxim events 
            else:    
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM eventos WHERE fecha_hora > NOW() AND idusuario = %s order by fecha_hora asc', ( id,))
                user = cur.fetchall()

                if user != ():
                    message = 'Eventos proximos'
                else:
                    message = 'No hay eventos proximos disponibles'

                return render_template('session.html', datas = user, id = id, message = message)
        else:
            return 'error'
    else:
        return redirect('/')

# Clear filter
@app.route('/clear_filter')
def clearfilter():
    session.pop('date', None)
    session.pop('time', None)
    session.pop('desc', None)
    session.pop('lugar', None)

    return redirect(url_for('sessiones', id = session['id']))

# Add event
@app.route('/add_event/<id>', methods = ['GET','POST'])
def text(id):
    if 'name' in session:
        if session['id'] == int(id):

            date = request.form['date']
            time = request.form['time']
            descripcion = request.form['event']
            lugar = request.form['lugar']

            if date != '' and time != '' and lugar != '' and lugar != '':

                datetime = str(date) + ' ' + str(time)

                cursor = mysql.connection.cursor()
                cursor.execute('INSERT INTO eventos (idusuario, fecha, hora, fecha_hora, descripcion, lugar) VALUES (%s, %s, %s, %s, %s, %s)',(id, date, time, datetime, descripcion, lugar))
                mysql.connection.commit()

                return redirect(url_for('sessiones', id = id))
            else:
                flash('Rellene todos los campos')
                return redirect(url_for('sessiones', id = id))
        else:
            return 'error'
    else:
        return redirect('/')

# Remove event
@app.route('/remove_event/<id>/<id_event>', methods = ['GET','POST'])
def remove(id, id_event):
    if 'name' in session:
        if session['id'] == int(id):
            cursor = mysql.connection.cursor()
            cursor.execute('DELETE FROM eventos WHERE idevento = %s AND idusuario = %s',(id_event, id,))
            mysql.connection.commit()
            
            flash('Evento eliminado')
            return redirect(url_for('sessiones', id = id))
        else:
            return 'error'
    else:
        return redirect('/')

# Edit event
@app.route('/edit_event/<id>/<id_event>', methods = ['GET','POST'])
def edit(id, id_event):
    if 'name' in session:
        if session['id'] == int(id):

            cursor = mysql.connection.cursor()
            cursor.execute(f"SELECT * FROM eventos WHERE idevento = '{id_event}' and idusuario = '{id}' ")
            datas = cursor.fetchone()

            if datas != None:

                if request.method == 'POST':
                    date = request.form['date']
                    time = request.form['time']
                    descripcion = request.form['event']
                    lugar = request.form['lugar']

                    if date != '' and time != '' and lugar != '' and lugar != '':

                        datetime = str(date) + ' ' + str(time)

                        cursor = mysql.connection.cursor()
                        cursor.execute(f"UPDATE eventos SET fecha = '{date}', hora = '{time}', fecha_hora = '{datetime}', descripcion = '{descripcion}', lugar = '{lugar}' WHERE idevento = {id_event} ")
                        mysql.connection.commit()

                        return redirect(url_for('sessiones', id = id))
                    else:
                        flash('Rellene todos los campos')
                        return redirect(url_for('sessiones', id = id))
                else:
                    cursor = mysql.connection.cursor()
                    cursor.execute(f"SELECT * FROM eventos WHERE idevento = {id_event} ")
                    datas = cursor.fetchone()

                    return render_template('edit_event.html', id = id, id_event = id_event, datas = datas)

            else:
                return 'error'
        else:
            return 'error'
    else:
        return redirect('/')

# Filter
@app.route('/search_event/<int:id>', methods = ['POST'])
def search(id):
    if 'name' in session:
        if session['id'] == int(id):  
            date = request.form['date']
            time = request.form['time']
            descripcion = request.form['descripcion']
            lugar = request.form['lugar']

            session['date'] = date
            session['time'] = time
            session['desc'] = descripcion
            session['lugar'] = lugar

            return redirect(url_for('sessiones', id = id))
        else:
            return 'error'
    else:
        return redirect('/')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host = "0.0.0.0", port = 3000, debug = True)
