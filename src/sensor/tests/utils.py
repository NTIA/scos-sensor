from rest_framework import status


HTTPS_KWARG = {'wsgi.url_scheme': 'https'}


def validate_response(response, expected_code=None):
    actual_code = response.status_code

    if expected_code is None:
        assert status.is_success(actual_code)
    else:
        assert actual_code == expected_code, response.data

    if actual_code not in (status.HTTP_204_NO_CONTENT,):
        rjson = response.json()
        return rjson
