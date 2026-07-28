# SPDX-FileCopyrightText: 2022-present Didier Malenfant
#
# SPDX-License-Identifier: MIT


class Url:
    """Utility class to handle git URLs."""

    def __init__(self, url: str):
        """Init from a Url string."""

        self.as_string = url

        if self.as_string.endswith('.git'):
            self.as_string = self.as_string[:-4]

        if self.as_string.startswith('http://'):
            self.as_string = self.as_string[7:]
        elif self.as_string.startswith('https://'):
            self.as_string = self.as_string[8:]

        # -- Let's make sure there is a .com,.net,etc.. before the first slash in the path.
        # -- Github usernames cannot have dots in them so testing like this should be ok.
        first_dot_index = self.as_string.find('.')
        first_slash_index = self.as_string.find('/')

        if first_dot_index < 0 or first_dot_index > first_slash_index:
            # -- We assume a url with no server is one from Github.
            if not self.as_string.startswith('/'):
                self.as_string = '/' + self.as_string

            self.as_string = 'github.com' + self.as_string

        url_components = self.as_string.split('/')
        if len(url_components) != 3:
            raise SyntaxError('Malformed git URL \'' + url + '\'.')

        self.server = url_components[0]
        self.username = url_components[1]
        self.repo_name = url_components[2]

    def __eq__(self, other: 'Url'):
        return self.as_string == other.as_string

    def __hash__(self):
        return hash(self.as_string)
