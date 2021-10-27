# Importing required modules
try:
    from flask import Flask, render_template, flash, redirect, url_for, session, request, send_file, Response, make_response
    from flask_mysqldb import MySQL
    import os
    import csv
    import secrets
    import io
    from fpdf import FPDF

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


@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        if request.form.get("upload"):
            return redirect('/upload')
        elif request.form.get("download"):
            return redirect('/download')
    return render_template('index.html')


# To upload the csv files
@app.route("/upload", methods=["POST", "GET"])
def upload():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM csv_file ORDER By emp_id ASC")
    post = cur.fetchall()

    if request.method == "POST":
        if 'csv_file' not in request.files:
            flash("There is no file")
            return redirect('/')
        csv_file = save_file(request.files['csv_file'])
        # print(csv_file)
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
        flash('Files uploaded Successfully!')
        return redirect('/')
    return render_template('upload.html', post=post)


@app.route('/download', methods=["POST", "GET"])
def download():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM csv_file ORDER By emp_id ASC")
    post = cur.fetchall()
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

        elif request.form.get("pdf_report"):
            pdf = FPDF()
            pdf.add_page()
            page_width = pdf.w - 2 * pdf.l_margin
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Employee Report', align='C')
            pdf.ln(10)
            pdf.set_font('Courier', '', 12)
            col_width = page_width / 5
            pdf.ln(1)
            th = pdf.font_size

            for row in post:
                pdf.cell(col_width, th, str(row['emp_id']), border=1)
                pdf.cell(col_width, th, row['first_name'], border=1)
                pdf.cell(col_width, th, row['last_name'], border=1)
                pdf.cell(col_width, th, row['designation'], border=1)
                pdf.cell(col_width, th, str(row['salary']), border=1)
                pdf.ln(th)

            pdf.ln(10)
            pdf.set_font('Times', '', 10.0)
            pdf.cell(page_width, 0.0, '----- End of Report -----', align='C')
            cur.close()
            return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf',
                            headers={'Content-Disposition': 'attachment;filename=employee_report.pdf'})
    return render_template('download.html')


if __name__ == "__main__":
    app.run(debug=True)