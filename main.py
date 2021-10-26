# Importing required modules
try:
    from flask import Flask, render_template, flash, redirect, url_for, session, request, current_app, send_file, Response
    from flask_mysqldb import MySQL
    import os
    import csv
    import secrets
    import io

except ModuleNotFoundError as e:
    print("Some required modules not found!")

app = Flask(__name__)
app.secret_key = "secret"

# Config MySQL
mysql = MySQL(app)
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root123"
app.config["MYSQL_DB"] = "mycsv"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


def save_file(file):
    file_path = os.path.join(app.root_path, 'static/file', file.filename)
    file.save(file_path)
    return file.filename


# To upload the csv files
@app.route("/", methods=["POST","GET"])
def upload():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM csv_file ORDER By emp_id ASC")
    post = cur.fetchall()

    if request.method == "POST":
        csv_file = save_file(request.files['csv_file'])
        print(csv_file)
        csv_data = csv.DictReader(open('static/file/'+csv_file))
        data = [row for row in csv_data]
        for data in data:
            emp_id = data['emp_id']
            first_name = data['first_name']
            last_name = data['last_name']
            designation = data['designation']
            salary = data['salary']

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO csv_file"
                        "(emp_id, first_name, last_name, designation, salary)VALUES(%s, %s, %s, %s, %s)",
                        (emp_id, first_name, last_name, designation, salary))
            mysql.connection.commit()
            cur.close()

        return redirect('/')
    return render_template('index.html', post=post)


# To download the report in csv format
@app.route('/')
def download():
    return render_template('index.html')


@app.route('/download/csv_file')
def download_report():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM csv_file ORDER By emp_id ASC")
    post = cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    line = ['emp_id', 'first_name', 'last_name', 'designation', 'salary']
    writer.writerow(line)

    for row in post:
        line = [str(row['emp_id']) + ',' + row['first_name'] + ',' + row['last_name'] + ',' + row['designation'] + ',' + str(row['salary'])]
        writer.writerow(line)
    output.seek(0)
    cur.close()
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=Report.csv"})


if __name__ == "__main__":
    app.run(debug=True)
