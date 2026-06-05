from src.utils.config import Config

SESSION_URL = f'{Config.SPOTIDL_BASE}/session'
METADATA_URL = f'{Config.SPOTIDL_BASE}/metadata'
TRACKS_URL = f'{Config.SPOTIDL_BASE}/tracks'
DOWNLOAD_URL = f'{Config.SPOTIDL_BASE}/download'


def api_headers(bearer: str | None = None) -> dict:
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'origin': Config.SPOTIDL_SITE,
        'referer': f'{Config.SPOTIDL_SITE}/',
        'user-agent': Config.USER_AGENT,
    }
    if bearer:
        headers['authorization'] = f'Bearer {bearer}'
    return headers
