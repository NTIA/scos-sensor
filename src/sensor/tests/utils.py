from rest_framework import status

HTTPS_KWARG = {"wsgi.url_scheme": "https", "secure": True}


def validate_response(response, expected_code=None):
    actual_code = response.status_code

    if expected_code is None:
        assert status.is_success(actual_code)
    else:
        assert actual_code == expected_code, response.data

    if actual_code not in (status.HTTP_204_NO_CONTENT,):
        rjson = response.json()
        return rjson


def get_requests_ssl_dn_header(common_name):
    return {
        "X-Ssl-Client-Dn": f"C=TC,ST=test_state,L=test_locality,O=test_org,OU=test_ou,CN={common_name}",
    }


def get_http_request_ssl_dn_header(common_name):
    return {
        "HTTP_X-SSL-CLIENT-DN": f"C=TC,ST=test_state,L=test_locality,O=test_org,OU=test_ou,CN={common_name}",
    }
