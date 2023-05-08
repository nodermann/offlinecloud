import requests


SERVER_UNIQUE_TEST_DIR_NAME = 'api_test_directory_619af1a8bf3d8e50718027eb9b41f6cb'


def test_server_ping():
    print('should return status 200')


def before():
    pass
    # make sure the SERVER_UNIQUE_TEST_DIR_NAME on the server does not exist before the each test
    # should return 400 and path not found


def after():
    pass
    # remove the SERVER_UNIQUE_TEST_DIR_NAME after each test
    # should return 400 and path not found


def test_api_dir_list():
    print('should return a list of files and directories')
    before()
    # upload a directory to the server
    # compare file paths
    after()


def test_api_upload_download_file():
    print('should compare two files uploaded and downloaded, the files should match')
    before()
    # upload file to the server
    # download file from the server
    # compare two files (bytes)
    after()


def test_api_upload_download_dir():
    print('should compare two dirs uploaded and downloaded, the files in the directories should match')
    before()
    # upload directory to the server
    # download directory from the server
    # compare two directories (each file)
    after()


def test_api_create_empty_file():
    print('should create an empty file')
    before()
    pass
    # create an empty file
    # make sure that the file has been created
    after()


def test_api_create_empty_dir():
    print('should create an empty directory')
    before()
    pass
    # create an empty directory
    # make sure that the directory has been created
    after()


def test_api_file_move():
    print('should move a file')
    before()
    pass
    # upload a file to the server
    # move the file
    # make sure the previous path does not exist
    # make sure the new path exist
    after()


def test_api_dir_move():
    print('should move a directory')
    before()
    pass
    # upload a directory to the server
    # move the directory
    # make sure the previous path does not exist
    # make sure the new path exist
    after()


def test_api_file_copy():
    print('should copy a file')
    before()
    pass
    # upload a file to the server
    # make sure the both directories exist
    after()


def test_api_dir_copy():
    print('should copy a directory')
    before()
    pass
    # make sure the both directories exist
    after()


def test_api_remove_file():
    print('should remove a file')
    before()
    pass
    # upload a file to the server
    # make sure the file exists
    # remove the file on the server
    # make sure that the file does not exist
    after()


def test_api_remove_dir():
    print('should remove a directory')
    before()
    pass
    after()


if __name__ == '__main__':
    test_server_ping()
    test_api_dir_list()
    test_api_upload_download_file()
    test_api_upload_download_dir()

    test_api_create_empty_file()
    test_api_create_empty_dir()

    test_api_file_move()
    test_api_dir_move()

    test_api_file_copy()
    test_api_dir_copy()
