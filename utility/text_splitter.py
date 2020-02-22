"""
Custom text splitter, February 17, 2020

(Self note: ideas lifted from much more detailed work in `/wb_writing/core/class_corpus.py`.)
"""

import re
# import logging
import os.path
import pandas as pd

from .sentence_object import SentenceObj

class TextSplitter:

    # TODO: handle DOT_WORDS = 'Dr. Mr. Mrs. Ms. dr. mr. mrs. ms.'.split(' ')

    def __init__(self, filename='text_splitter_test.txt'):
        # logging.basicConfig(filename='testing.log', level=logging.INFO)
        self.filename = filename

        self.allblocks = []
        self.df = pd.DataFrame()

        self.load_file()
        self.clean_rawtext()
        self.split_text()
        self.make_df()

    def make_df(self):
        newDict = {}
        newDict['index'] = []
        newDict['block_index'] = []
        newDict['inquote'] = []
        newDict['rawtext'] = []
        newDict['text'] = []
        newDict['is_newline'] = []
        newDict['sentence_object'] = []

        for block in self.allblocks:
            newDict['index'].append(block.index)
            newDict['block_index'].append(block.block_index)
            newDict['inquote'].append(block.inquote)
            newDict['rawtext'].append(block.rawtext)
            newDict['text'].append(block.text)
            newDict['is_newline'].append(block.is_newline)
            newDict['sentence_object'].append(block)

        self.df = pd.DataFrame.from_dict(newDict)
        self.df.set_index(['index', 'block_index'], inplace=True)


    def shuffle(self):
        """
            Randomize the order of the lines
        """
        self.df = self.df.sample(frac=1).copy()


    def load_file(self):
        if not os.path.isfile(self.filename):
            raise Exception(f"File `{self.filename}` doesn't exist.")

        with open(self.filename, "r") as f:
            self.rawtext = f.read()

    def clean_rawtext(self):
        # Sort-of-curly-quotes handling
        self.rawtext = self.rawtext.replace('“', '"').replace('”', '"')
        self.rawtext = self.rawtext.replace("’", "'").replace("’", "'")


    def split_text(self):

        """
            First, define our within-the-block splitter
            Splitter test string:
            "A quoted sentence." Sentences that end in different *marks*! "Are you okay?" "Are you **okay?"** "Are you *okay?"* "Are you **okay?**" "Are you *okay?*" What do you think? This is a boring one. Here's another boring one. "One of two quoted sentences. Two of two quoted sentences." "A sentence with ellipses..." "A sentence with someone saying, 'Hi there, how are you?'" If you need this: do that. If we see something; our eyes are working.
        """
        splitter = r"[^\!\.\?]+[\!\.\?]{1,4}\*{0,2}_?'?\"?\*{0,2}_?\s?|\n"
        compiled = re.compile(splitter, re.MULTILINE)

        """
            Then we split into paragraphs/blocks
        """
        blocks = self.rawtext.split("\n")

        """
            Build `self.allblocks` stack out of blocks>sentences
        """
        index = 0
        inquote = False
        for block in blocks:
            block_index = 0

            if '' == block:
                ## This is an empty line / newline:
                sent = SentenceObj()
                sent.index = index
                sent.block_index = block_index
                sent.rawtext = "NEWLINE"
                sent.text = "NEWLINE"
                sent.is_newline = True
                sent.inquote = inquote
                self.allblocks.append(sent)

                index = index + 1
                continue

            ## If we're here, it's not a newline, so split the sentences:
            for match in compiled.finditer(block):
                ## For each sentence...
                sent = SentenceObj()
                sent.index = index
                sent.block_index = block_index
                sent.rawtext = match[0]
                sent.text = match[0]

                ## Are we in a quote?
                if '"' in sent.text:
                    if '"' == sent.text.strip()[0]:
                        inquote = True
                sent.inquote = inquote
                if '"' in sent.text:
                    if '"' == sent.text.strip()[-1]:
                        inquote = False

                self.allblocks.append(sent)

                # Update our indexes for next sentence in block
                index = index + 1
                block_index = block_index + 1

            ## At the end of each paragraph, we add a newline
            sent = SentenceObj()
            sent.index = index
            sent.block_index = 0
            sent.rawtext = "NEWLINE"
            sent.text = "NEWLINE"
            sent.is_newline = True
            sent.inquote = inquote
            self.allblocks.append(sent)

            index = index + 1

    def dump_text(self):
        output = ''

        for idx,block in self.df.sort_index(axis=0, ascending=True, inplace=False, sort_remaining=True).iterrows():

            if block.is_newline:
                output = output + "\n"
            else:
                output = output + block.text

        return output

    def dump_original_text(self):
        output = ''

        for idx,block in self.df.sort_index(axis=0, ascending=True, inplace=False, sort_remaining=True).iterrows():

            if block.is_newline:
                output = output + "\n"
            else:
                output = output + block.rawtext

        return output


if __name__ == "__main__":
    ## Debugging and sanity check

    print()
    print("##########################################")
    print("##")
    print("## Testing `TextSplitter()")
    print("##")
    print("##########################################")
    print()

    # from sentence_object import SentenceObj

    ts = TextSplitter()
    [print(t) for t in ts.allblocks]

    print()
    print()

    print(ts.dump_text())

    print()
    print()

    print(ts.df.head())
