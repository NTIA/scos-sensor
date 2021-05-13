from authentication.auth import get_uid_from_dn


def test_get_uid_from_dn_comma():
    assert "12345671111111" == get_uid_from_dn(
        "UID=12345671111111,CN=JUSTIN HAZE,OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US"
    )
    assert "12345671111111" == get_uid_from_dn(
        "CN=JUSTIN HAZE,OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US,UID=12345671111111"
    )
    assert "1234567" == get_uid_from_dn(
        "UID=1234567,CN=JUSTIN HAZE,OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US"
    )
    assert "1234567" == get_uid_from_dn(
        "CN=JUSTIN HAZE,OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US,UID=1234567"
    )


def test_get_uid_from_dn_plus():
    assert "12345671111111" == get_uid_from_dn(
        "UID=12345671111111+CN=JUSTIN HAZE,OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US"
    )
    assert "12345671111111" == get_uid_from_dn(
        "CN=JUSTIN HAZE+UID=12345671111111,OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US"
    )
    assert "12345671111111" == get_uid_from_dn(
        "OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US,UID=12345671111111+CN=JUSTIN HAZE"
    )
    assert "12345671111111" == get_uid_from_dn(
        "OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US,CN=JUSTIN HAZE+UID=12345671111111"
    )
    assert "1234567" == get_uid_from_dn(
        "UID=1234567+CN=JUSTIN HAZE,OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US"
    )
    assert "1234567" == get_uid_from_dn(
        "CN=JUSTIN HAZE+UID=1234567,OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US"
    )
    assert "1234567" == get_uid_from_dn(
        "OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US,UID=1234567+CN=JUSTIN HAZE"
    )
    assert "1234567" == get_uid_from_dn(
        "OU=National Telecommunication and Information Administration,OU=Department of Commerce,O=U.S. Government,C=US,CN=JUSTIN HAZE+UID=1234567"
    )
