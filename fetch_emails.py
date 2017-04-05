import httplib2, os, base64, re

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from pprint import PrettyPrinter
from wrangle import update_jsons
from binascii import Error
pp = PrettyPrinter()

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'


def check_local_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    return [credentials, store, credential_path]


def request_live_credentials(store, credential_path):
    flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
    flow.user_agent = APPLICATION_NAME
    if flags:
        credentials = tools.run_flow(flow, store, flags)
    else:  # Needed only for compatibility with Python 2.6
        credentials = tools.run(flow, store)
    print('Storing credentials to ' + credential_path)
    return credentials


def get_credentials():
    credentials, store, credential_path = check_local_credentials()
    if not credentials or credentials.invalid:
        credentials = request_live_credentials(store, credential_path)
    return credentials

def parse_email(message):
    email_content = {}

    email_content["id"] = message.get('id', False)
    meta_dict = {meta["name"].lower(): meta["value"] for meta in message["payload"]["headers"] if meta["name"] in ["Subject", "Date", "From"]}
    email_content["subject"] = meta_dict.get("subject", False)
    email_content["date"] = meta_dict.get("date", False)

    # From format is 'John Doe <johny_appleseed@gmail.com>'
    name = re.findall(re.compile('[a-zA-Z]{1,} [a-zA-Z]{1,}'), meta_dict.get("from", ""))
    email = re.findall(re.compile('<.*>'), meta_dict.get("from", ""))
    email_content["author_name"] = name[0] if name else False
    email_content["author_email"] = email[0].lstrip("<").rstrip(">") if email else False
    email_content["replying_to"] = False
    
    try:
        try:
            try:
                body = message['payload']['parts'][0]['parts'][0]['body']['data']
            except KeyError:
                body = message['payload']['body']['data']
        except KeyError:
            body = message['payload']['parts'][0]['parts'][0]['parts'][0]['body']['data']
    except:
        body = ""
        print("Email "+email_content['id']+": "+email_content['subject']+" message body not found")
    
    missing_padding = len(body) % 4
    if missing_padding != 0:
        body += str(b'='* (4 - missing_padding))

    try:
        email_content['text'] = base64.b64decode(body).decode(errors="ignore")      # Having unicode errors
    except Error:
        email_content['text'] = "Corrupted Data"
        print("Email "+email_content['id']+": "+email_content['subject']+" is corrupted")
    # print(email_content['subject'])
    # print(email_content['text'])
    # print(' ')
    return email_content

def retrieve_emails(service, next_page=None):

    results = service.users().messages().list(userId='me', q="to:carpediem@lists.olin.edu NOT label:email_stored", pageToken=next_page).execute()

    emails = {}
    email_stored = 'Label_1'
    if results['resultSizeEstimate']:
        for result in results['messages']:
            msg_id = result['id']
            message = service.users().messages().get(userId='me', id=msg_id).execute()
            service.users().messages().modify(userId="me", id=msg_id, body={'removeLabelIds': [], 'addLabelIds': [email_stored]}).execute()

            email_content = parse_email(message)

            month = re.findall(re.compile("[A-Z]{1}[a-z]{2} [0-9]{4}"), email_content.get("date", ''))[0]
            
            try:
                emails[month].append(email_content)
            except KeyError:
                emails[month] = [email_content]
        for date, lst_emails in emails.items():
            update_jsons(lst_emails, date)
    else:
        print("No new emails!")

    if results.get('nextPageToken', None):
        retrieve_emails(service, results['nextPageToken'])

def main():
    """Connects to gmail account and pulls out all new emails to the carpe list, then separates them
        by month and sends them in batches to be stored in a JSON"""

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    retrieve_emails(service)
           

if __name__ == '__main__':
    main()