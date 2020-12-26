from __future__ import print_function

import io
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
from googleapiclient.http import MediaIoBaseDownload

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = 'True'

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly',
          'https://www.googleapis.com/auth/classroom.coursework.me',
          'https://www.googleapis.com/auth/classroom.coursework.me.readonly',
          'https://www.googleapis.com/auth/classroom.coursework.students',
          'https://www.googleapis.com/auth/classroom.coursework.students.readonly',
          'https://www.googleapis.com/auth/classroom.profile.emails',
          'https://www.googleapis.com/auth/classroom.profile.photos',
          'https://www.googleapis.com/auth/classroom.rosters',
          'https://www.googleapis.com/auth/classroom.rosters.readonly',
          'https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive.readonly']


def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    classroom_service = build('classroom', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Call the Classroom API
    students = classroom_service.courses().students().list(courseId="248897306948").execute()
    id_number = {i['userId']: i['profile']['name']['givenName'] for i in students['students']}
    work = classroom_service.courses().courseWork().list(courseId="248897306948").execute()
    work_name = [i['title'] for i in work['courseWork']]
    print(f"Existed Work:\n{work_name}")
    ex_sel = input("Select Work: ")
    selected_work_id = None
    for coursework in work['courseWork']:
        if coursework['title'] == ex_sel:
            selected_work_id = coursework['id']
            print(f"Commencing {coursework['title']}")
            selected_work_name = coursework['title']
    submission = classroom_service.courses().courseWork().studentSubmissions().list(courseId="248897306948",
                                                                                    courseWorkId=selected_work_id).execute()
    for submitted in submission['studentSubmissions']:
        if submitted['assignmentSubmission'] != {}:
            filename = id_number[submitted['userId']] + f"_{submitted['assignmentSubmission']['attachments'][0]['driveFile']['title']}"
            file_id = submitted['assignmentSubmission']['attachments'][0]['driveFile']['id']
            print(f"Downloading {filename}\n{submitted['assignmentSubmission']['attachments'][0]['driveFile']['thumbnailUrl']}")
            drive_download(drive_service, filename, file_id, selected_work_name)
        else:
            print(f"{id_number[submitted['userId']]} Not Submitted")


# Drive API
def drive_download(service, file_name, file_id, destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    file_path = os.path.join(destination_folder, file_name)
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(file_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))


if __name__ == '__main__':
    main()
