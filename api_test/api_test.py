import requests
import pytest
import filecmp
import os


SERVER_UNIQUE_TEST_DIR_NAME = 'api_test_directory_619af1a8bf3d8e50718027eb9b41f6cb/'
SERVER_URL = 'http://0.0.0.0:3000'


def test_server_ping():
    print('should return status 200')
    response = requests.get(SERVER_URL + '/api/ping')
    print('status =', response.status_code)


def before():
    # make sure the SERVER_UNIQUE_TEST_DIR_NAME on the server does not exist before the each test
    # should return 400 and path not found
    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 400
    response = requests.post(SERVER_URL + '/api/dir/new', json={'path': '.', 'dirname': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 200


def after():
    # remove the SERVER_UNIQUE_TEST_DIR_NAME after each test
    # should return 400 and path not found
    response = requests.post(SERVER_URL + '/api/dir/remove', json={'path': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 200
    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 400


def test_api_upload_download_file():
    print('should compare two files uploaded and downloaded, the files should match')
    before()
    
    # upload file to the server
    f = open('requirements.txt', 'rb')
    files = {'file': f}
    headers = {'CONTENT-DISPOSITION': f'attachment; filename="{SERVER_UNIQUE_TEST_DIR_NAME}/requiments.txt"'}
    response = requests.post(SERVER_URL + '/api/file/upload', headers=headers, files=files)
    f.close()
    assert response.status_code == 201
    
    # download file from the server
    f = open('requirements2.txt',"wb")
    response = requests.get(SERVER_URL + '/api/file/download', json={'path': os.path.join(SERVER_UNIQUE_TEST_DIR_NAME, 'requiments.txt')})
    f.write(response.content)
    f.close()
    assert response.status_code == 200

    # compare two files (bytes)
    assert filecmp.cmp('requirements.txt', 'requirements2.txt')
    
    after()


def test_api_create_empty_file():
    filename = os.path.join(SERVER_UNIQUE_TEST_DIR_NAME, 'test_empty_file.txt')
    print('should create an empty file')
    before()

    # create an empty file
    response = requests.post(SERVER_URL + '/api/file/new', json={'path': '.', 'filename': filename})
    assert response.status_code == 200
    
    # make sure that the file has been created
    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 200
    response_json = response.json()
    assert filename in response_json['files']
    
    after()


def test_api_create_empty_dir():
    dirname = os.path.join(SERVER_UNIQUE_TEST_DIR_NAME, 'new_test_dir')
    
    print('should create an empty directory')
    before()
    
    # create an empty directory
    response = requests.post(SERVER_URL + '/api/dir/new', json={'path': '.', 'dirname': dirname})
    assert response.status_code == 200
    
    # make sure that the directory has been created
    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 200
    response_json = response.json()
    assert dirname in response_json['files']
    
    after()


def test_api_file_move():
    print('should move a file')
    before()

    # upload a file to the server
    f = open('requirements.txt', 'rb')
    files = {'file': f}
    headers = {'CONTENT-DISPOSITION': f'attachment; filename="{SERVER_UNIQUE_TEST_DIR_NAME}/requiments.txt"'}
    response = requests.post(SERVER_URL + '/api/file/upload', headers=headers, files=files)
    f.close()
    assert response.status_code == 201

    # create new directory
    dist = os.path.join(SERVER_UNIQUE_TEST_DIR_NAME, 'dir_test')
    response = requests.post(SERVER_URL + '/api/dir/new', json={'path': SERVER_UNIQUE_TEST_DIR_NAME, 'dirname': 'dir_test'})
    assert response.status_code == 200
    
    # move the file
    response = requests.post(SERVER_URL + '/api/file/move', json={'src': SERVER_UNIQUE_TEST_DIR_NAME, 'dict': dist})
    assert response.status_code == 200
    
    # make sure the previous path does not exist
    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 200
    response_json = response.json()
    assert 'requiments.txt' not in response_json['files']
    
    # make sure the new path exist
    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': dist})
    assert response.status_code == 200
    response_json = response.json()
    assert 'requiments.txt' in response_json['files']
    
    after()


def test_api_file_copy():
    print('should copy a file')
    before()

    # upload a file to the server
    f = open('requirements.txt', 'rb')
    files = {'file': f}
    headers = {'CONTENT-DISPOSITION': f'attachment; filename="{SERVER_UNIQUE_TEST_DIR_NAME}/requiments.txt"'}
    response = requests.post(SERVER_URL + '/api/file/upload', headers=headers, files=files)
    f.close()
    assert response.status_code == 201

    # create new directory
    dist = os.path.join(SERVER_UNIQUE_TEST_DIR_NAME, 'dir_test')
    response = requests.post(SERVER_URL + '/api/dir/new', json={'path': SERVER_UNIQUE_TEST_DIR_NAME, 'dirname': 'dir_test'})
    assert response.status_code == 200
    
    # copy the file
    response = requests.post(SERVER_URL + '/api/file/copy', json={'src': SERVER_UNIQUE_TEST_DIR_NAME, 'dict': dist})
    assert response.status_code == 200
    
    # make sure the both directories exist
    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 200
    response_json = response.json()
    assert 'requiments.txt' in response_json['files']

    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': dist})
    assert response.status_code == 200
    response_json = response.json()
    assert 'requiments.txt' in response_json['files']
    
    after()


def test_api_dir_copy():
    print('should copy a directory')
    before()

    src = os.path.join(SERVER_UNIQUE_TEST_DIR_NAME, 'dir_test')
    dist = os.path.join(SERVER_UNIQUE_TEST_DIR_NAME, 'dir_test_2')
    response = requests.post(SERVER_URL + '/api/dir/new', json={'path': SERVER_UNIQUE_TEST_DIR_NAME, 'dirname': 'dir_test'})
    assert response.status_code == 200
    response = requests.post(SERVER_URL + '/api/dir/new', json={'path': SERVER_UNIQUE_TEST_DIR_NAME, 'dirname': 'dir_test_2'})
    assert response.status_code == 200 
    
    # make sure the both directories exist
    response = requests.post(SERVER_URL + '/api/dir/copy', json={'src': src, 'dist': dist})
    assert response.status_code == 200

    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': src})
    assert response.status_code == 200
    response_json = response.json()
    assert src in response_json['files']

    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': dist})
    assert response.status_code == 200
    response_json = response.json()
    assert dist in response_json['files']
    
    after()


def test_api_remove_file():
    print('should remove a file')
    before()

    # upload a file to the server
    f = open('requirements.txt', 'rb')
    files = {'file': f}
    headers = {'CONTENT-DISPOSITION': f'attachment; filename="{SERVER_UNIQUE_TEST_DIR_NAME}/requiments.txt"'}
    response = requests.post(SERVER_URL + '/api/file/upload', headers=headers, files=files)
    f.close()
    assert response.status_code == 201
    
    # make sure the file exists
    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 200
    response_json = response.json()
    assert 'requirements.txt' in response_json['files']
    
    # remove the file on the server
    response = requests.post(SERVER_URL + '/api/file/remove', json={'path': os.path.join(SERVER_UNIQUE_TEST_DIR_NAME, 'requiments.txt')})
    assert response.status_code == 200
    
    # make sure that the file does not exist
    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 200
    response_json = response.json()
    assert 'requirements.txt' not in response_json['files']
    
    after()


def test_api_remove_dir():
    print('should remove a directory')
    before()
    
    path = os.path.join(SERVER_UNIQUE_TEST_DIR_NAME, 'dir_test')
    response = requests.post(SERVER_URL + '/api/dir/new', json={'path': SERVER_UNIQUE_TEST_DIR_NAME, 'dirname': 'dir_test'})
    assert response.status_code == 200

    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 200
    response_json = response.json()
    assert 'dir_test' in response_json['files']

    response = requests.post(SERVER_URL + '/api/dir/remove', json={'path': path})
    assert response.status_code == 200

    response = requests.get(SERVER_URL + '/api/dir/list', json={'path': SERVER_UNIQUE_TEST_DIR_NAME})
    assert response.status_code == 200
    response_json = response.json()
    assert 'dir_test' not in response_json['files']
    
    after()


if __name__ == '__main__':
    test_server_ping()
    test_api_upload_download_file()

    test_api_create_empty_file()
    test_api_create_empty_dir()

    test_api_file_move()
    test_api_dir_move()

    test_api_file_copy()
    test_api_dir_copy()
