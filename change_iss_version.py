import re

from src.version import __version__

ISS_FILE = 'installer.iss'

with open(ISS_FILE, encoding='utf-8') as f:
    iss = f.read()

iss = re.sub(
    r'(#define\s+MyAppVersion\s+)".*?"',
    r'\1"{}"'.format(__version__),
    iss,
)

with open(ISS_FILE, 'w', encoding='utf-8') as f:
    f.write(iss)
