from flask import Flask, render_template, request
from pymysql import connections
import os
import random
import boto3
import argparse

app = Flask(__name__)

# ----- ENVIRONMENT CONFIGS -----
DBHOST = os.environ.get("DBHOST", "localhost")
DBUSER = os.environ.get("DBUSER", "root")
DBPWD = os.environ.get("DBPWD", "password")
DATABASE = os.environ.get("DATABASE", "employees")
DBPORT = int(os.environ.get("DBPORT", 3306))
COLOR_FROM_ENV = os.environ.get('APP_COLOR', 'lime')
GROUP_NAME = os.environ.get("GROUP_NAME", "Code Ninjas")
SLOGAN = os.environ.get("SLOGAN", "Deploy or Die")
S3_BUCKET = os.environ.get("S3_BUCKET")
BACKGROUND_IMAGE = os.environ.get("BACKGROUND_IMAGE", "background.jpg")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

# ----- COLOR SETUP -----
color_codes = {
    "red": "#e74c3c",
    "green": "#16a085",
    "blue": "#89CFF0",
    "blue2": "#30336b",
    "pink": "#f4c2c2",
    "darkblue": "#130f40",
    "lime": "#C1FF9C",
}
SUPPORTED_COLORS = ",".join(color_codes.keys())
COLOR = random.choice(list(color_codes.keys()))

# ----- DOWNLOAD IMAGE FROM S3 -----
def download_background_image():
    try:
        if not os.path.exists("static"):
            os.makedirs("static")

        s3 = boto3.client("s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

        s3.download_file(S3_BUCKET, BACKGROUND_IMAGE, f"static/{BACKGROUND_IMAGE}")
        print(f"✅ Background image downloaded from S3: {BACKGROUND_IMAGE}")
    except Exception as e:
        print(f"❌ Error downloading image from S3: {e}")

download_background_image()

# ----- DB CONNECTION -----
db_conn = connections.Connection(
    host=DBHOST,
    port=DBPORT,
    user=DBUSER,
    password=DBPWD,
    db=DATABASE
)

# ----- ROUTES -----
@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("addemp.html", color=color_codes[COLOR], group=GROUP_NAME, slogan=SLOGAN, image=BACKGROUND_IMAGE)

@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template("about.html", color=color_codes[COLOR], group=GROUP_NAME, slogan=SLOGAN, image=BACKGROUND_IMAGE)

@app.route("/addemp", methods=["POST"])
def AddEmp():
    emp_id = request.form["emp_id"]
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    primary_skill = request.form["primary_skill"]
    location = request.form["location"]

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    try:
        cursor.execute(insert_sql, (emp_id, first_name, last_name, primary_skill, location))
        db_conn.commit()
        emp_name = first_name + " " + last_name
    finally:
        cursor.close()

    return render_template("addempoutput.html", name=emp_name, color=color_codes[COLOR], group=GROUP_NAME, slogan=SLOGAN, image=BACKGROUND_IMAGE)

@app.route("/getemp", methods=["GET", "POST"])
def GetEmp():
    return render_template("getemp.html", color=color_codes[COLOR], group=GROUP_NAME, slogan=SLOGAN, image=BACKGROUND_IMAGE)

@app.route("/fetchdata", methods=["POST"])
def FetchData():
    emp_id = request.form["emp_id"]
    output = {}
    select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location FROM employee WHERE emp_id=%s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (emp_id,))
        result = cursor.fetchone()

        output["emp_id"] = result[0]
        output["first_name"] = result[1]
        output["last_name"] = result[2]
        output["primary_skills"] = result[3]
        output["location"] = result[4]

    except Exception as e:
        print(e)
    finally:
        cursor.close()

    return render_template("getempoutput.html",
        id=output["emp_id"],
        fname=output["first_name"],
        lname=output["last_name"],
        interest=output["primary_skills"],
        location=output["location"],
        color=color_codes[COLOR],
        group=GROUP_NAME,
        slogan=SLOGAN,
        image=BACKGROUND_IMAGE
    )

# ----- RUN -----
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--color", required=False)
    args = parser.parse_args()

    if args.color:
        COLOR = args.color
    elif COLOR_FROM_ENV:
        COLOR = COLOR_FROM_ENV

    if COLOR not in color_codes:
        print(f"❌ Invalid color '{COLOR}', expected one of: {SUPPORTED_COLORS}")
        exit(1)

    app.run(host="0.0.0.0", port=81, debug=True)
