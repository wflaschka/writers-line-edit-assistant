import textwrap
import argparse
from picotui.widgets import *
from picotui.menu import *
from picotui.context import Context

from utility.text_splitter import TextSplitter

####################################################################################
## ARGUMENTS
####################################################################################
parser = argparse.ArgumentParser(prog='WB story editor assistant')
parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1 alpha')
parser.add_argument('-f', '--filename', help="Path and filename of .md file", type=str, default="test-file.md")
args = parser.parse_args()

####################################################################################
## Get our text or article to split
####################################################################################
# print(f"args.filename: `{args.filename}`")
# args.filename = 'utility/text_splitter_test.md'
ts = TextSplitter(filename=args.filename)
ts.shuffle() # Mix up lines


####################################################################################
## Settings
####################################################################################
window_width = 80
window_height = 13
window_inset = 5
sentence_index = 0
filename_output = args.filename.replace('utility/', '').replace('.md', '-OUTPUT.md')
wrapper = textwrap.TextWrapper(initial_indent='', width=(window_width-10), subsequent_indent='')

####################################################################################
## App
####################################################################################
d = None

def screen_redraw(s, allow_cursor=False):
    s.attr_color(C_WHITE, C_BLUE)
    s.cls()
    s.attr_reset()
    d.redraw()

def change_displayed_sentence(direction='forward'):
    global sentence_index # Tut tut, bad form

    sentence_index += 1 if direction == 'forward' else -1

    ## Behavior: roll over to front of stack if at end, and vice versa
    if sentence_index < 0:
        sentence_index = len(ts.df) - 1
    if sentence_index >= len(ts.df):
        sentence_index = 0

    ## Handle if next/prior sentences in stack are one or more NEWLINES
    ## ...rolling over to front of stack again, etc.
    direction_add = 1 if direction == 'forward' else -1
    tmptext = ts.df.text.iloc[sentence_index]
    while tmptext == "NEWLINE":
        sentence_index = sentence_index + direction_add

        if sentence_index >= len(ts.df):
            sentence_index = 0

        if sentence_index < 0:
            sentence_index = len(ts.df) - 1

        tmptext = ts.df.text.iloc[sentence_index]

    text = wrapper.wrap(tmptext) # returns list

    # Update sentence display widget
    w = get_widget_by_tag(tag="sentence")
    w.set(text)

    ## Reset 'replace' input
    w = get_widget_by_tag(tag="replace")
    w.set('')
    w.adjust_cursor_eol()

    ## Focus 'replace' input
    d.change_focus(w)

    ## Reset 'search' input
    w = get_widget_by_tag(tag="search")
    w.set('')
    w.adjust_cursor_eol()

    ## Focus 'search' input
    d.change_focus(w)

    ## Update % of file position:
    update_progress()

    screen_redraw(Screen)
    Screen.set_screen_redraw(screen_redraw)

def get_widget_by_tag(tag=None):
    for w in d.childs:
        if isinstance(w, EditableWidget):
            if w.tag == tag:
                return w

def sentence_replace():
    global ts

    w = get_widget_by_tag(tag="search")
    str_search = w.get()
    w = get_widget_by_tag(tag="replace")
    str_replace = w.get()

    if str_search == '' or str_replace == '':
        return

    sentence_old = ts.df.text.iloc[sentence_index]
    sentence_new = sentence_old.replace(str_search, str_replace)

    ts.df['text'].iat[sentence_index] = sentence_new

    return

def save_file():
    file = open(filename_output,"w") 
    file.write( ts.dump_text() ) 
    file.close() 

    return

def update_progress():
    prog = ((sentence_index + 1) / len(ts.df)) * 100
    str_progress = f"Position: {prog:5.2f}%"
    pos_x = window_width - window_inset - len(str_progress)
    d.add(pos_x, 2, WLabel(str_progress))

def main_loop():
    global sentence_index

    while 1:
        key = d.get_input()

        if isinstance(key, list):
            # Mouse click... not working right now?
            x, y = key
            d.add((window_inset * 2), 3, f"Mouse click: x:{x}, y:{y}")

        if key == KEY_ENTER:
            """
                ENTER = default key to "save changes" and "advance to next sentence"
            """

            sentence_replace()
            save_file()

            change_displayed_sentence(direction='forward')

        elif key == KEY_RIGHT:
            """
                Move to next sentence in stack
            """
            change_displayed_sentence(direction='forward')

        elif key == KEY_LEFT:
            """
                Move to prior sentence in stack
            """
            change_displayed_sentence(direction='backward')

        else:
            """
                Everything else gets sent to the dialog for handling
            """
            res = d.handle_input(key)
            if res is not None and res is not True:
                return res

with Context():

    Screen.attr_color(C_WHITE, C_BLUE)
    Screen.cls()
    Screen.attr_reset()
    d = Dialog(window_inset, window_inset, window_width, window_height)

    ##########################################
    ## App title
    d.add(window_inset, 2, WLabel(">> WRITER'S COPY EDITOR <<"))

    ##########################################
    ## Get first line to edit, skipping errant newlines, and wrap it
    tmptext = ts.df.text.iloc[sentence_index]
    while tmptext == "NEWLINE":
        sentence_index = sentence_index + 1
        tmptext = ts.df.text.iloc[sentence_index]
    text = wrapper.wrap(tmptext) # returns list

    ##########################################
    ## Display our first line in a multi-line text box with wrapping
    w = WMultiEntry((window_width-10), 5, text)
    w.tag = "sentence"
    d.add(window_inset, 5, w)

    ##########################################
    ## Input prompt handling -- search and replace inputs
    width_prompt = 10
    width_input = int(round((window_width - (2 * window_inset) - (2 * width_prompt))/2, 0))

    d.add(window_inset, window_height - 2, "  Search:")
    w = WTextEntry(width_input, "teh")
    w.tag = "search"
    d.add(window_inset + width_prompt, window_height - 2, w)

    d.add(window_inset + width_prompt + width_input, window_height - 2, " Replace:")
    w = WTextEntry(width_input, "the")
    w.tag = "replace"
    d.add(window_inset + width_prompt + width_input + width_prompt, window_height - 2, w)

    screen_redraw(Screen)
    Screen.set_screen_redraw(screen_redraw)

    ##########################################
    ## Keep the loop going
    res = main_loop()

####################################################################################
## Output results
####################################################################################
print("\n    DONE!   \n")


##########################################
## Fancy debugging output:

# from pprint import pprint
# print()
# print("Result:", res)
# data = {}
# for w in d.childs:
#     if isinstance(w, EditableWidget):
#         val = w.get()
#         if val is not None:
#             data[w.tag] = val
# pprint(data)
# print()
# print()
# print()
# print(ts.df.text)
