import requests
import time
import random

def load_user_agents():
    try:
        with open('user_agents.txt', 'r') as fp:
            return [str(line).strip() for line in fp.readlines()]
    except:
        return []

class HttpRequest(object):
    default_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9"
    }
    user_agents = load_user_agents()

    def __init__(self):
        self.s = None
        self.headers = {
            "User-Agent": self.user_agents[random.randint(0, len(self.user_agents) - 1)] if self.user_agents else \
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36"
        }
        self.headers.update(HttpRequest.default_headers)

    def __del__(self):
        self.close()

    def session(self):
        if not self.s:
            self.s = requests.session()
        return self.s

    def close(self):
        if self.s:
            self.s.close()

    def get(self, url, headers=None):
        retries = 5
        timeout = .1

        h = self.headers.copy()
        if headers:
            h.update(headers)

        for _ in range(retries):
            try:
                r = self.session().get(url, headers=h)
                if r.status_code == 200:
                    try:
                        r.content.decode('UTF-8')
                    except UnicodeDecodeError:
                        r.encoding = 'GB18030'
                    return r.text
                elif r.status_code == 503:
                    self.close()
                elif r.status_code == 404:
                    return None

            except requests.exceptions.RequestException:
                pass

            # Wait 100ms for server response
            time.sleep(timeout)
            timeout *= 2

        return None
