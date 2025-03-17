from flask import Flask, render_template, url_for, redirect, flash, request, jsonify
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, ForeignKey, desc
from flask_login import UserMixin, login_user, current_user, login_required, logout_user, LoginManager
import os


from forms import RegisterForm, UserForm, PredictionForm, ChangeForm
from werkzeug.security import generate_password_hash, check_password_hash

# Initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = "your_key"
app.config['STATIC_FOLDER'] = 'static'
app.config['TEMPLATE_FOLDER'] = 'templates'

# Creating login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(id):
    user = Users.query.get(int(id))
    return user


# Creating DB
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///f1.db"
db.init_app(app)


# User DB
class Users(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    favourite_driver: Mapped[str] = mapped_column(String, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    predictions: Mapped[list['Prediction']] = relationship('Prediction', backref='user')


# Update user position once race is finished
def update_user_positions():
    users = Users.query.order_by(Users.points.desc()).all()
    old_positions = {user.id: user.position for user in users}
    for idx, user in enumerate(users):
        new_position = idx + 1
        old_position = old_positions.get(user.id, new_position)
        user.change = old_position - new_position
        user.position = new_position
    db.session.commit()


# Races DB
class Racers(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[str] = mapped_column(String, nullable=False)
    team: Mapped[str] = mapped_column(String, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    img: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    podiums: Mapped[str] = mapped_column(String, nullable=False)
    max_points: Mapped[int] = mapped_column(Integer, nullable=False)
    bio: Mapped[str] = mapped_column(String, nullable=False)
    results: Mapped[list['Result']] = relationship('Result', backref='driver')
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey('teams.id'))
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    championships: Mapped[int] = mapped_column(Integer, nullable=False)
    driver_predictions: Mapped[list['PredictionResult']] = relationship('PredictionResult', backref='driver_predict')


# Teams DB
class Teams(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    img: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    team_chief: Mapped[str] = mapped_column(String, nullable=False)
    drivers: Mapped[list['Racers']] = relationship('Racers', backref='team_reference')
    color: Mapped[str] = mapped_column(String, nullable=False)
    championships: Mapped[int] = mapped_column(Integer, nullable=False)


# Race DB
class Race(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    race_results: Mapped[list['Result']] = relationship('Result', backref='race')
    winner: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    predictions_user: Mapped[list['Prediction']] = relationship('Prediction', backref='race_predict')


# Result DB
class Result(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[str] = mapped_column(String, nullable=False)
    place: Mapped[int] = mapped_column(Integer, nullable=False)
    race_id: Mapped[int] = mapped_column(Integer, ForeignKey('race.id'))
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey('racers.id'))
    points: Mapped[int] = mapped_column(Integer, nullable=False)


# Prediction DB
class Prediction(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    race_id: Mapped[int] = mapped_column(Integer, ForeignKey('race.id'))
    predictions: Mapped[list['PredictionResult']] = relationship('PredictionResult', backref='prediction')
    total_sum: Mapped[int] = mapped_column(Integer, nullable=False)


# PredictionResult DB
class PredictionResult(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[int] = mapped_column(Integer, ForeignKey('prediction.id'))
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey('racers.id'))
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    @property
    def driver(self):
        return Racers.query.get(self.driver_id)

    @property
    def driver_name(self):
        driver = self.driver
        if driver:
            return f"{driver.name} {driver.surname}"
        return "Unknown Driver"


with app.app_context():
    db.create_all()


# Initialization home page
@app.route('/')
def home():
    results = db.session.execute(db.Select(Racers))
    teams_results = db.session.execute(db.Select(Teams))
    teams = teams_results.scalars().all()
    racers = results.scalars().all()
    return render_template('index.html', current_user=current_user, racers=racers, teams=teams)


# Adding and refreshing result for prediction, racer stats, race stats and user stats
@app.route('/add_result', methods=['POST'])
def add_result():
    racer_id = request.args.get('driver_id')
    race_id = request.args.get('race_id')
    place = int(request.args.get('place'))
    # Validate existence of racer and race
    racer = Racers.query.get(racer_id)
    race = Race.query.get(race_id)
    if not racer:
        return jsonify(result={"failed": "This driver doesn't exist within DB"}), 404
    if not race:
        return jsonify(result={"failed": "This race doesn't exist within DB"}), 404
    # Add new result
    new_result = Result(
        time=request.args.get('time'),
        place=place,
        race_id=race.id,
        driver_id=racer.id,
        points=int(request.args.get('points'))
    )
    db.session.add(new_result)
    # Update racer and team points
    team = Teams.query.filter_by(name=racer.team).first()
    racer.points += int(request.args.get('points'))
    team.points += int(request.args.get('points'))
    # Update race winner if applicable
    if place == 1:
        race.winner = f"{racer.name} {racer.surname}"
    db.session.commit()
    # Update predictions and user points
    predictions = Prediction.query.filter_by(race_id=race.id).all()
    for prediction in predictions:
        user = Users.query.get(prediction.user_id)
        score = 0
        # Calculate score based on correct predictions
        for pre_result in prediction.predictions:
            actual_result = Result.query.filter_by(race_id=race.id, driver_id=pre_result.driver_id).first()
            if actual_result and int(actual_result.place) == int(pre_result.position):
                score += (11 - int(pre_result.position))
        # Update prediction score and user points if there are points to award
        if score > 0:
            prediction.total_sum = str(score)
            user.points = sum(int(each.total_sum) for each in Prediction.query.filter_by(user_id=user.id).all())
    db.session.commit()
    update_user_positions()
    return jsonify(result={"success": "The driver result has been added and user/team points updated!"})

# Register Form
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        user_name = Users.query.filter_by(name=name).first()
        email_name = Users.query.filter_by(email=email).first()
        if user_name is None and email_name is None:
            password = form.password.data
            confirm_password = form.confirm_password.data
            if password == confirm_password:
                hash_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)
                new_user = Users(
                    name=name,
                    email=email,
                    password=hash_password,
                    favourite_driver="None",
                    points=0
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect(url_for('home'))
            else:
                flash("Passwords don't match", "error")
        else:
            flash("Email or name is already exist", "error")

    return render_template('signin.html', form=form, current_user=current_user)


# LogIn Form
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = UserForm()
    if form.validate_on_submit():
        email = form.email.data
        user = Users.query.filter_by(email=email).first()
        if user != None:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect(url_for('home'))
            else:
                flash("Password is incorrect", 'error')
        else:
            flash("Email isn`t correct or doesn't exist", "error")
    return render_template('login.html', form=form, current_user=current_user)


# Logout Process
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# All drivers
@app.route('/driver/<int:id>')
def driver(id):
    racer = Racers.query.get_or_404(id)
    driver_name = racer.name + " " + racer.surname
    return render_template('driver_profile.html', racer=racer, current_user=current_user, driver_name=driver_name)


# Set your favourite drivers
@app.route('/set_driver/<int:driver_id>/<int:user_id>')
def set_driver(driver_id, user_id):
    user = Users.query.get(user_id)
    driver = Racers.query.get(driver_id)
    driver_name = driver.name + " " + driver.surname
    user.favourite_driver = driver_name
    db.session.commit()
    return redirect(url_for('home'))


# User Profile
@app.route('/profile/<int:id>')
def profile(id):
    user = Users.query.get(id)
    return render_template('profile.html', user=user)


# All races
@app.route('/races')
def races():
    results = db.session.execute(db.Select(Race))
    races = results.scalars().all()
    return render_template('races.html', races=races)


# Particular race
@app.route('/races/<int:race_id>')
def race(race_id):
    race = Race.query.get(race_id)
    results_sorted = sorted(race.race_results, key=lambda result: int(result.place))
    return render_template('race_details.html', race=race, results=results_sorted)


# All teams
@app.route('/teams')
def teams():
    results = db.session.execute(db.Select(Teams))
    teams = results.scalars().all()
    return render_template('teams.html', teams=teams)


# Particular team
@app.route('/teams/<int:id>')
def team(id):
    team = Teams.query.get(id)
    return render_template('team_profile.html', team=team)


# Particular driver
@app.route('/drivers')
def drivers():
    results = db.session.execute(db.Select(Racers).order_by(desc(Racers.points)))
    drivers = results.scalars().all()
    return render_template('drivers.html', drivers=drivers)


# Predictions form
@app.route('/predictions', methods=['GET', 'POST'])
@login_required
def predictions():
    form = PredictionForm()
    # Populate race choices - only races without existing predictions
    races = db.session.execute(db.select(Race)).scalars().all()
    form.race.choices = [(race.id, race.name) for race in races
                         if not Prediction.query.filter_by(race_id=race.id, user_id=current_user.id).first()]
    # Populate driver choices for all position fields
    drivers = db.session.execute(db.select(Racers)).scalars().all()
    driver_choices = [(driver.id, f"{driver.name} {driver.surname}") for driver in drivers]
    for i in range(1, 11):
        getattr(form, f'driver_{i}').choices = driver_choices
    if form.validate_on_submit():
        # Create new prediction
        new_prediction = Prediction(user_id=current_user.id, race_id=form.race.data, total_sum=0)
        db.session.add(new_prediction)
        db.session.commit()
        # Create prediction results for all positions
        prediction_results = [
            PredictionResult(
                prediction_id=new_prediction.id,
                driver_id=getattr(form, f'driver_{i}').data,
                position=i
            ) for i in range(1, 11)
        ]
        db.session.add_all(prediction_results)
        db.session.commit()
        flash("Predictions submitted successfully!", "success")
        return redirect(url_for('prediction', id=new_prediction.id))
    return render_template('predictions.html', races=races, drivers=drivers, form=form)

# Choosing particular prediction
@app.route('/prediction/<int:id>')
@login_required
def prediction(id):
    prediction = Prediction.query.get(id)
    prediction_race = prediction.race_id
    finished = False
    race = Race.query.get(prediction_race)
    if race.winner != "":
        finished = True
    # Avoiding possibility that someone can enter to prediction of another user
    if prediction is None or current_user.id != prediction.user_id:
        return redirect(url_for('home'))
    results = prediction.predictions
    return render_template('prediction.html', prediction=prediction, predictionresult=results, status=finished)


# Dashboard of users
@app.route('/dashboard')
def dashboard():
    users = Users.query.order_by(Users.points.desc()).all()
    return render_template('dashboard.html', users=users)


# Change prediction
@app.route('/change_prediction/<int:id>', methods=['GET', 'POST'])
@login_required
def change_prediction(id):
    form = ChangeForm()
    prediction = Prediction.query.get(id)
    prediction_race = prediction.race_id
    race = Race.query.get(prediction_race)
    # If the race was completed, please redirect to profile
    if race.winner != "":
        return redirect(url_for('profile',id=current_user.id))
    else:
        drivers = db.session.execute(db.select(Racers)).scalars().all()
        driver_choices = [(driver.id, f"{driver.name} {driver.surname}") for driver in drivers]
        for i in range(1, 11):
            getattr(form, f'driver_{i}').choices = driver_choices
        # Rendered 10 drivers and their position based on actual prediction in db
        if request.method == 'GET':
            for i in range(1, 11):
                result = PredictionResult.query.filter_by(prediction_id=prediction.id, position=i).first()
                if result:
                    field = getattr(form, f'driver_{i}')
                    field.data = result.driver_id
        if form.validate_on_submit():
            try:
                selected_drivers = []
                for i in range(1, 11):
                    driver_id = getattr(form, f'driver_{i}').data
                    selected_drivers.append(driver_id)
                for position, driver_id in enumerate(selected_drivers, start=1):
                    result = PredictionResult.query.filter_by(prediction_id=prediction.id, position=position).first()
                    result.driver_id = driver_id
                db.session.commit()
                return redirect(url_for('prediction', id=prediction.id))
            except Exception as e:
                db.session.rollback()
                flash(f"Error updating prediction: {str(e)}", "error")
    return render_template('change_prediction.html', form=form, drivers=drivers, prediction=prediction)


if __name__ == "__main__":
    app.run(debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
