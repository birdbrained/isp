
""" Download all files from a selected google drive in csv format then convert to a json format. The script
    can repeat this process upon user request.

    Requires access to the main google drive folder (or credentials from a developer who
    has access). The ID for the main google folder is stored in TRANSLATION_FOLDER_ID.

    Steps:
    1. Obtain client_secret.json file:
       a. Go to https://console.developers.google.com/
       b. Create a project for ISP
       c. Under the credentials tab, click Create Credentials --> OAuth client ID, select "Other"
          as application type and click "Create"
       d. Find the newly created credentials under "OAuth 2.0 client IDs" and download as json
       e. Rename json file to "client_secret.json"
    2. In the scripts directory, create a 'credentials' folder and add the client_secret.json file
    3. Run the script.
       a. If the OAuth login complains about not being able to find the redirect uri, rerun the script
          with the --noauth_local_webserver argument.  It will open a new workflow that will give you a
          token you can copy and paste into your terminal window.
    4. Move the content of the generated files as described in the README.md file.

    The first time you run this script, you may get a message saying that you need to authorize specific APIs for use
    with this project. The message will provide instructions needed to complete this process; wait several minutes
    and then try running again.

    Modifies: https://developers.google.com/drive/v3/web/quickstart/python """

import httplib2
import os
import sys

import consent_form_json, format_translations

from apiclient import discovery
from oauth2client import file, client, tools

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at isp/scripts/credentials/credentials.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'credentials/client_secret.json'
APPLICATION_NAME = 'International Situations Project'

# Main google directory that contain all translation folders
TRANSLATION_FOLDER_ID = '0B441UYO1vv_CVjRrc25SZjRhazA'

# Downloaded csv files with each site's consent form
files_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'consent_forms')



def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials')
    credential_path = os.path.join(credential_dir, 'credentials.json')
    store = file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def display_languages(service):
    # List of languages with their IDs
    LANGUAGE_LIST = {}
    print 'List of available languages:\n----------------------------'
    data = service.files().list(q="'" + TRANSLATION_FOLDER_ID + "'" + " in parents").execute()
    for f in data['files']:
        if f['mimeType'].endswith('.folder'):
            LANGUAGE_LIST[f['name']] = f['id']

    # store the generated IDs to match against user input.
    language_id = {}
    for i, item in enumerate(sorted(LANGUAGE_LIST)):
        print  str(i+1) + ' ' + item
        language_id[i+1] = item

    response = raw_input('--> Select language from the list: ')
    user_choice = language_id[int(response)]
    print 'User selected '+user_choice+ ' language'
    if user_choice not in LANGUAGE_LIST:
        print '\nInvalid selection'
        sys.exit(1)

    else:
        return LANGUAGE_LIST[user_choice]


def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    selection = display_languages(service)

    while True:
        # get and download files
        data = service.files().list(q="'" + selection + "'" + " in parents").execute()
        download_translation_file(data['files'], service)
        response = raw_input('--> Add new language? (y/n) ')
        if response == 'y':
            selection = display_languages(service)
            continue
        elif response == 'n':
            print 'Exit..'
            sys.exit(1)

def download_consent_files(files, service):
    count = len(files)
    for i, f in enumerate(files):
        file_id = f['id']
        request = service.files().export_media(fileId=file_id, mimeType='text/csv').execute()
        fn = '%s.csv' % ('consent_forms/' + f['name'].replace(' ', '_'))
        if request:
            with open(fn, 'wb') as csvfile:
                csvfile.write(request)
                print 'Download {i} of {c} consent forms translation'.format(i=i+1, c=count)


def download_translation_file(files, service):
    for f in files:
        file_id= f['id']
        file_type= f['mimeType']
        file_name= f['name']
        if file_type.endswith('.spreadsheet'):
            request = service.files().export_media(fileId=file_id, mimeType='text/csv').execute()
            fn = '%s.csv' % (file_name.replace(' ', '_'))
            if request:
                with open(fn, 'wb') as csvfile:
                    print 'Downloading file: {f}'.format(f=fn)
                    csvfile.write(request)
            print 'Converting language translation from .csv to .json format'
            format_translations.main(fn)
        if file_type.endswith('.folder'):
            data = service.files().list(q="'" + file_id + "'" + " in parents").execute()
            download_consent_files(data['files'], service)
    print 'Converting all consent forms at {f}'.format(f=os.path.join(os.path.dirname(os.path.realpath(__file__)), "consent_forms"))
    consent_form_json.main()



if __name__ == '__main__':
    main()
