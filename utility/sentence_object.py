"""

Data object containing one sentence

"""

class SentenceObj:

    def __init__(self):
        self.inquote = False
        self.index = 0
        self.block_index = 0
        self.rawtext = None
        self.text = None
        self.is_newline = False

    def __str__(self):
        # return self.text
        return f"SentenceObj ({self.index:5}:{self.block_index:2}): `{self.text}`"