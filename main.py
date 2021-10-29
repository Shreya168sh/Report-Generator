# Importing required modules
try:
    from flask import Flask, render_template, redirect, request, Response
    from flask_mysqldb import MySQL
    import os
    import csv
    import secrets
    import io
    from fpdf import FPDF
    import pandas as pd
    import numpy as np
    from matplotlib import pyplot as plt

except ModuleNotFoundError as e:
    print("Some required modules not found!")

app = Flask(__name__)

# Config MySQL
mysql = MySQL(app)
app.secret_key = "secret"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root123"
app.config["MYSQL_DB"] = "mycsv"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


# Defining path to save the files
def save_file(file):
    file_path = os.path.join(app.root_path, 'static/file', file.filename)
    file.save(file_path)
    return file.filename


@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        if request.form.get("upload"):
            return redirect('/upload')
        elif request.form.get("download"):
            return redirect('/download')
    return render_template('index.html')


# To upload the csv files into database
@app.route("/upload", methods=["POST", "GET"])
def upload():
    # Connecting to MySQl database and fetching all the fields from database
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM csv_file ORDER By emp_id ASC")
    post = cur.fetchall()

    if request.method == "POST":
        csv_file = save_file(request.files['csv_file'])
        csv_data = csv.DictReader(open('static/file/'+csv_file))
        data = [row for row in csv_data]

        # storing values into variables from csv file
        for data in data:
            emp_id = data['emp_id']
            first_name = data['first_name']
            last_name = data['last_name']
            designation = data['designation']
            salary = data['salary']

            # Inserting the values into database
            cur.execute("INSERT INTO csv_file"
                        "(emp_id, first_name, last_name, designation, salary)VALUES(%s, %s, %s, %s, %s)",
                        (emp_id, first_name, last_name, designation, salary))
            cur.commit()
            cur.close()

        print('Files uploaded Successfully!')
        return redirect('/')
    return render_template('upload.html', post=post)


# to download the collated file/report
@app.route('/download', methods=["POST", "GET"])
def download():
    con = mysql.connection
    cur = con.cursor()
    cur.execute("SELECT * FROM csv_file ORDER By emp_id ASC")
    post = cur.fetchall()
    # Execute when user wants to download csv file
    if request.method == "POST":
        if request.form.get("csv_report"):
            output = io.StringIO()
            writer = csv.writer(output)

            line = ['emp_id', 'first_name', 'last_name', 'designation', 'salary']
            writer.writerow(line)

            for row in post:
                line = [str(row['emp_id']) + ',' + row['first_name'] + ',' + row['last_name'] + ',' + row['designation'] + ',' + str(row['salary'])]
                writer.writerow(line)
                output.seek(0)
                cur.close()

            return Response(output, mimetype="text/csv",
                            headers={"Content-Disposition": "attachment;filename=Report.csv"})

        # Execute when user wants to download csv file
        elif request.form.get("pdf_report"):
            #  calling function which generates the plots
            bar_chart()
            #  calling function which generates the plots
            pdf = FPDF()
            pdf.add_page()
            pdf.ln(5)
            # The full page width is stored in pdf.w and the full height in pdf.h
            # Subtract from pdf.w both left and right margins
            page_width = pdf.w - 2 * pdf.l_margin
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Employee Report', align='C')
            pdf.ln(10)
            pdf.set_font('Times', 'B', 12)
            width = page_width / 5
            pdf.ln(1)
            header_height = 14
            height = pdf.font_size

            pdf.cell(width, header_height, 'Emp Id', border=1, align='C')
            pdf.cell(width, header_height, 'First Name', border=1, align='C')
            pdf.cell(width, header_height, 'Last Name', border=1, align='C')
            pdf.cell(width, header_height, 'Designation', border=1, align='C')
            pdf.cell(width, header_height, 'Salary', border=1, align='C')
            pdf.ln(header_height)

            pdf.set_font('Times', '', 12)
            for row in post:
                pdf.cell(width, height, str(row['emp_id']), border=1, align='C')
                pdf.cell(width, height, row['first_name'], border=1, align='C')
                pdf.cell(width, height, row['last_name'], border=1, align='C')
                pdf.cell(width, height, row['designation'], border=1, align='C')
                pdf.cell(width, height, str(row['salary']), border=1, align='C')
                pdf.ln(height)

            # Adding page for charts
            pdf.add_page()
            pdf.ln(5)
            page_width = pdf.w - 2 * pdf.l_margin

            # to display fig1
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Visualization of Designation w.r.t. Salary', align='C')
            pdf.ln(4)
            pdf.image('fig1.png', w=200, h=100)
            pdf.ln(2)

            # to display fig2
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Visualization of Designation', align='C')
            pdf.ln(4)
            pdf.image('fig2.png', w=200, h=100)

            cur.close()
            return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf',
                            headers={'Content-Disposition': 'attachment;filename=employee_report.pdf'})
    return render_template('download.html')


# To generate plots from data
@app.route("/bar_chart")
def bar_chart():
    con = mysql.connection
    df = pd.read_sql("SELECT designation, salary FROM csv_file", con=con)

    # for fig1 - Designation vs Salary
    plt.bar(df['designation'], df['salary'])
    plt.xticks(rotation=90)
    plt.subplots_adjust(bottom=0.50)
    plt.savefig('fig1.png')

    # for fig2 - Designation
    df['designation'].value_counts().plot.bar()
    plt.savefig('fig2.png')


if __name__ == "__main__":
    app.run()
