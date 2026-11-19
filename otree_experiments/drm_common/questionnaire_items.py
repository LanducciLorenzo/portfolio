"""
Visual-verbal cognitive style questionnaire.

IMPORTANT: replace the placeholder items with the items of the questionnaire used in the thesis
(the one based on Paivio's imagery questionnaire), keeping the same order, and set REVERSED
for the items that are reverse-scored. Use the questionnaire only if you are allowed to.
The placeholders below are NOT a validated scale: they only make the experiment run.
"""

SCALE_LABELS = ['1 Strongly disagree', '2 Disagree', '3 Neither', '4 Agree', '5 Strongly agree']

ITEMS = [
    '[Item 1 - replace with the questionnaire item]',
    '[Item 2 - replace with the questionnaire item]',
    '[Item 3 - replace with the questionnaire item]',
    '[Item 4 - replace with the questionnaire item]',
    '[Item 5 - replace with the questionnaire item]',
    '[Item 6 - replace with the questionnaire item]',
    '[Item 7 - replace with the questionnaire item]',
    '[Item 8 - replace with the questionnaire item]',
    '[Item 9 - replace with the questionnaire item]',
    '[Item 10 - replace with the questionnaire item]',
]

# 'visual' items: agreement = more visual style ; 'verbal' items: agreement = more verbal style
ITEM_DIMENSION = ['visual', 'verbal'] * 5

# positions (1-based) of reverse-scored items, if any
REVERSED = []
