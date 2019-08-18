import ass
# Use https://github.com/chireiden/python-ass

def readAss(fname):
    assert str(fname).endswith('.ass')

    with open(fname, 'r') as f:
        doc = ass.parse(f)

    return doc.styles, doc.events, (doc.play_res_x, doc.play_res_y)


#readAss('dm.ass')