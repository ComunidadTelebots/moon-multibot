"""Small fail-closed authentication primitives shared by the web dashboard."""

import hmac


def dashboard_password_matches(configured_password, supplied_password, jwt_secret):
    """Only authenticate when both server-side secrets are actually configured."""
    if not isinstance(configured_password, str) or not configured_password:
        return False
    if not isinstance(jwt_secret, str) or not jwt_secret:
        return False
    if not isinstance(supplied_password, str):
        return False
    return hmac.compare_digest(configured_password, supplied_password)
