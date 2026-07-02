import logging
import os
import time

import requests

logger = logging.getLogger(__name__)


# SEC requires a declared User-Agent with contact info; override the sample
# via the EDGAR_USER_AGENT environment variable
headers = {
    'User-Agent': os.environ.get(
        'EDGAR_USER_AGENT',
        'Sample Company Name AdminContact@samplecompanydomain.com')
}

# SEC throttling responses (fair-access guidance: max 10 requests/second)
RETRY_STATUS_CODES = (429, 503)


class GetRequest:
    def __init__(self, url, headers=headers, max_retries=4, backoff_factor=1.0):
        response = None
        for attempt in range(max_retries + 1):
            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'
            if response.status_code in RETRY_STATUS_CODES and attempt < max_retries:
                delay = backoff_factor * (2 ** attempt)
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        delay = max(delay, float(retry_after))
                    except ValueError:
                        pass
                logger.warning(
                    f'{response.status_code} from {url}; '
                    f'retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})')
                time.sleep(delay)
                continue
            break
        if response.status_code != requests.codes.ok:
            raise RequestException('{}: {}'.format(response.status_code, response.text))

        self.response = response


class RequestException(Exception):
    pass
