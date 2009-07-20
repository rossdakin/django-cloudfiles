import re

USERNAME_SETTINGS_ATTR = 'CLOUDFILES_USERNAME'
API_KEY_SETTINGS_ATTR = 'CLOUDFILES_API_KEY'
CONTAINER_SETTINGS_ATTR = 'CLOUDFILES_CONTAINER'
LOCAL_FILES_ROOT_SETTINGS_ATTR = 'MEDIA_ROOT'

URL_SEPERATOR = '/'
IGNORE_PATTERNS_FLAGS = (
    # editor
    (r'[#~]$',),
    # OS
    (r'\.DS_Store$',),
    (r'\bethumbs\.db$',),
    (r'\bThumbs\.db$',),
    # repo
    (r'\.git$',),
    (r'\.gitignore$',),
    (r'\.svn\b',),
    (r'\.svn-base$',),
)
IGNORE_REGEXS = [re.compile(*tup) for tup in IGNORE_PATTERNS_FLAGS]

def is_ignored_path(path, regexs=IGNORE_REGEXS):
    for regex in regexs:
        if regex.search(path):
            return True
    return False
