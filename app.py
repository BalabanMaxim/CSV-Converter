from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import pandas as pd
import openpyxl
import json
import zipfile
import shutil


app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
TEMPLATES_FILE = 'templates.json'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
STORAGE_FOLDER = 'storage'
app.config['STORAGE_FOLDER'] = STORAGE_FOLDER

def allowed_file(filename):
    return '.' in filename and (filename.rsplit('.', 1)[1].lower() == 'zip' or filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)

def move_file(source_path, destination_folder):
    destination_path = os.path.join(destination_folder, os.path.basename(source_path))
    shutil.move(source_path, destination_path)

def load_templates():
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, 'r') as json_file:
            return json.load(json_file)
    return {}

def save_templates(templates_data):
    with open(TEMPLATES_FILE, 'w') as json_file:
        json.dump(templates_data, json_file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Verplaats alle bestanden uit de upload-map naar de storage-map
    for existing_file in os.listdir(app.config['UPLOAD_FOLDER']):
        file_to_move = os.path.join(app.config['UPLOAD_FOLDER'], existing_file)
        new_file_path = os.path.join(STORAGE_FOLDER, existing_file)
        shutil.move(file_to_move, new_file_path)

    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        if file.filename.endswith('.zip'):
            extract_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted')
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)

            os.remove(file_path)

            for root, dirs, files in os.walk(extract_folder):
                for file in files:
                    if file.lower().endswith('.csv'):
                        csv_path = os.path.join(root, file)
                        excel_filename = os.path.splitext(file)[0] + '.xlsx'
                        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
                        df = pd.read_csv(csv_path)
                        df.to_excel(excel_path, index=False)

            shutil.rmtree(extract_folder)

            csv_files = get_csv_files()

            return render_template('zip_upload.html', csv_files=csv_files)

        if filename.endswith('.csv'):
            excel_filename = os.path.splitext(filename)[0] + '.xlsx'
            excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
            df = pd.read_csv(file_path)
            df.to_excel(excel_path, index=False)

            os.remove(file_path)

        return redirect(url_for('choose_action', filename=excel_filename))
    return "Ongeldig bestandstype"

@app.route('/choose_action/<filename>')
def choose_action(filename):
    return render_template('choose_action.html', filename=filename)

@app.route('/csv_upload')
def csv_upload():
    return render_template('csv_upload.html')

@app.route('/zip_upload')
def zip_upload():
    csv_files = get_csv_files()
       

    return render_template('zip_upload.html', csv_files=csv_files)

def get_csv_files():
    csv_files = []

    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            if file.lower().endswith(".csv") or file.lower().endswith(".xlsx"):
                csv_files.append(file)

    return csv_files

@app.route('/select_csv', methods=['GET'])
def select_csv():
    csv_filename = request.args.get('csv_file')

    if csv_filename:
        return render_template('choose_action.html', filename=csv_filename)
    else:
        return "No CSV file selected."

@app.route('/new_template/<filename>')
def new_template(filename):
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active
    column_names = sheet[1]

    return render_template('new_template.html', filename=filename, column_names=column_names)

@app.route('/edit_template/<filename>')
def edit_template(filename):
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active
    column_names = sheet[1]

    return render_template('edit_template.html', filename=filename, column_names=column_names)

@app.route('/save_template/<filename>', methods=['POST'])
def save_template(filename):
    template_name = request.form.get('template_name')

    templates_data = load_templates()

    if filename not in templates_data:
        templates_data[filename] = {}

    templates_data[filename]['template_name'] = template_name

    selected_columns_kolom1 = [col_name.replace('kolom1_', '') for col_name in request.form.keys() if col_name.startswith('kolom1_')]
    selected_columns_kolom2 = [col_name.replace('kolom2_', '') for col_name in request.form.keys() if col_name.startswith('kolom2_')]
    selected_columns_kolom3 = [col_name.replace('kolom3_', '') for col_name in request.form.keys() if col_name.startswith('kolom3_')]
    selected_columns_kolom4 = [col_name.replace('kolom4_', '') for col_name in request.form.keys() if col_name.startswith('kolom4_')]
    selected_columns_kolom5 = [col_name.replace('kolom5_', '') for col_name in request.form.keys() if col_name.startswith('kolom5_')]

    df = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    all_columns = df.columns.tolist()

    templates_data[filename]['kolom1'] = selected_columns_kolom1
    templates_data[filename]['kolom2'] = selected_columns_kolom2
    templates_data[filename]['kolom3'] = selected_columns_kolom3
    templates_data[filename]['kolom4'] = selected_columns_kolom4
    templates_data[filename]['kolom5'] = selected_columns_kolom5
    templates_data[filename]['kolom6'] = all_columns

    eerst_tij_verwijderen = "yes" if 'optie1' in request.form else "no"
    templates_data[filename]['optie1'] = eerst_tij_verwijderen

    save_templates(templates_data)

    # Move the source file to the storage folder
    source_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    move_file(source_path, app.config['STORAGE_FOLDER'])

    return render_template('index.html', filename=filename)

@app.route('/use_template/<filename>')
def use_template(filename):
    templates_data = load_templates()
    template_names = list(templates_data.keys())

    return render_template('use_template.html', template_names=template_names, filename=filename)

@app.route('/view_template/<template_name>')
def view_template(template_name):
    templates_data = load_templates()

    if template_name not in templates_data:
        return f"There is no template for this file."

    excel_filename = template_name 
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)

    if not os.path.exists(excel_path):
        return f"There is no template for this file."

    df = pd.read_excel(excel_path)

    column_names_kolom1 = templates_data[template_name].get('kolom1', [])
    column_names_kolom2 = templates_data[template_name].get('kolom2', [])
    column_names_kolom3 = templates_data[template_name].get('kolom3', [])
    column_names_kolom4 = templates_data[template_name].get('kolom4', [])
    column_names_kolom5 = templates_data[template_name].get('kolom5', [])
    column_names_kolom6 = templates_data[template_name].get('kolom6', [])
    
    df['Customer Name'] = df[column_names_kolom1].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)
    df['Customer ID'] = df[column_names_kolom2].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)
    df['Product SKU'] = df[column_names_kolom3].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)
    df['Product Name'] = df[column_names_kolom4].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)
    df['Licenses'] = df[column_names_kolom5].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)

    df = df.drop(columns=column_names_kolom1+column_names_kolom2+column_names_kolom3+column_names_kolom4+column_names_kolom5+column_names_kolom6)

    if templates_data[template_name].get('optie1', 'no') == 'yes':
        df = df.iloc[1:]

    table_html = df.to_html(index=False)

    output_folder = 'output'
    os.makedirs(output_folder, exist_ok=True)
    output_file_path = os.path.join(output_folder, f'{template_name}_output.xlsx')
    df.to_excel(output_file_path, index=False)

    return render_template('view_template.html', template_name=template_name, table_html=table_html, output_file=output_file_path)


@app.route('/download/<filename>')
def download_output(filename):
    return send_file(filename, as_attachment=True)


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['STORAGE_FOLDER']):
        os.makedirs(app.config['STORAGE_FOLDER'])

    app.run(debug=True)
