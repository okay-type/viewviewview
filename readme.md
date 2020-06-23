# Robofont Tool



Warning, this is a mess and built for my workflow and zero consideration for yours. 



self-guided tour:

on the left is a big multiline view

on the bottom is the text input
    - there is a control string input in front, it's a little buggy and i rarely use it
    - there is a barely functional metrics editor if you hover, i had big plans for this but rarely edit metrics like this so... (instead I use https://github.com/okay-type/GlyphviewMetricsHUD-robofontExt)

on the right is the control panel
    - it annoyingly changes color on mouse enter because i got bored
    - at the very bottom is a checkbox to autohide the menu 
    - there are five sections of tools, which need more explanation on their own

Fonts
This is a list of open ufos
    - drag to reorder (sometimes you need the widest at the top)
    - the checkbox toggles visibility (careful if the top font is hidden)
    - the crossing arrows reverses the sort order
    - the ghost button makes a hidden rFont that is an interpolation of the above/below ufos. it's fucking amazing if you keep the number of glyphs on display kind of short 
    - the ghost font has a slider to set the interpolation value and an X to close the rFont
    - i'd like to add the ability do drag-drop ufos into the list and toggle their openness --- having a ufo open with noUI is much lighter and could let us preview / interpolate, but also a button to open a font as a font info sheet only, or the whole glyphview)

View Options
Mostly self explanatory buttons and sliders
    - Max (lines) is very useful to keep the tool from getting bogged down
    - There are some logic conflicts between the "show as" and "separate" buttons... sorry

Manipulate Text
"Useful" shortcuts to manipulate the input text or selected characters
    - I have a typo in the label
    - These buttons are kind of broken and need to be updated
    - The small-caps button assumes a '.sc' suffix

Word-o-matic
This is my quick, stripped down rewrite of Nina's tool

Glyphs in Context
This builds text strings based on the current or selected glyphs
    - uses a data file described below that needs work
    - the 'automatic' button is dangerous



to install:

set multiviewer.py as a startup script


there are two data folders:

dictionaries - this is from word-o-mat and is used by the language selection ... you can add your own like I did with redwings.txt or hoefler.txt

contexts - used by "glyphs in context". This is the oldest part of the dumb tool, similar to the hoefler test strings if you've seen those. A very messy collection of control strings for each character. For letters, I tried to get real words with initial, middle, double, and final positions. The extended latin samples are iffy (I made up more than a few), but better than HHŁHH. There are also very brief, very sloppy strings for symbols and punctuation. Reworking this feature is very high on my to-do list, esp. after hoefler helped me see the validity of this approach. 



the 'trigger' files are keyboard shortcuts:

⌘ + ⬇︎ word-o-matic
⌘ + ⬆︎ tries to go back in the input text history (useful if you're mindlessly hitting the word-o button and go past something good)
⌘ + ➡︎ next preset input text
⌘ + ⬅︎ previous preset input text
⌘ + ⌥ + ⇧ + ⬇︎ glyphs in context
