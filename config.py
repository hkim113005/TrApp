# SQLAlchemy Database
SQLALCHEMY_DATABASE_URI = "sqlite:///../data/TrApp.db"
SECRET_KEY = "ACS-TSU@2023.VerYvERySeCreT"

# Mail Stuff
MAIL_SERVER = "smtp.gmail.com"
MAIL_DEFAULT_SENDER = "TSU TrApp"
MAIL_USERNAME = "acstsutesting@gmail.com" # Change to tsu@acs.sch.ae after testing finished
MAIL_PASSWORD = "xbuqjxaljpqpenoz" # App Password - https://myaccount.google.com/u/apppasswords
MAIL_PORT = 587
MAIL_USE_SSL = False # Port 465
MAIL_USE_TLS = True # Port 587

# File Uploads
UPLOAD_FOLDER = "data/user_uploads"
MAX_CONTENT_LENGTH = 16 * 1000 * 1000 # 16 MB