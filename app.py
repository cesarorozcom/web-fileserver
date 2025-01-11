from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_bootstrap import Bootstrap
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from pathlib import Path
import configparser
import io

config = configparser.ConfigParser()
config.read(Path.joinpath(Path(__file__).parent, 'app.ini'))

print(config.sections())

web_config = config['webapp']
aws_config = config['aws_prd']

print(aws_config)

app = Flask(__name__)
app.config['SECRET_KEY'] = web_config['secret_key']
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max file size
Bootstrap(app)

# Assume Role
sts_client = boto3.client('sts')

assumed_role_object = sts_client.assume_role(
    RoleArn=aws_config['role_arn'],
    RoleSessionName='AssumeRoleSession1')

credentials = assumed_role_object['Credentials']


# AWS S3 Configuration
S3_BUCKET = aws_config['bucket_name']
S3_REGION = aws_config['region']

s3 = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken'],
)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        prefix = request.form['prefix']
        file = request.files['file']

        if file and allowed_file(file.filename):
            try:
                s3.upload_fileobj(
                    file,
                    S3_BUCKET,
                    f"{prefix}/{file.filename}",
                    
                )
                flash('El Archivo ha sido cargado correctamente!', 'success')
            except (NoCredentialsError, PartialCredentialsError):
                flash('Credentials not available', 'danger')
            except Exception as e:
                flash(str(e), 'danger')
        else:
            flash('Tamaño o tipo de archivo no permitido', 'danger')

        return redirect(url_for('index'))
    # List files in S3 bucket
    files = list_files()
    return render_template('index.html', files=files)

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Download a file from the S3 bucket."""
    try:
        file_obj = s3.get_object(Bucket=S3_BUCKET, Key=filename)
        return send_file(
            io.BytesIO(file_obj['Body'].read()),
            download_name=filename,
            as_attachment=True
        )
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('index'))
    
def list_files():
    """List files in the S3 bucket."""
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET)
        if 'Contents' in response:
            return [file['Key'] for file in response['Contents']]
        else:
            return []
    except Exception as e:
        flash(str(e), 'danger')
        return []

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True)