import ass
# Use https://github.com/chireiden/python-ass


class DanMu:
    def __init__(self):
        self.posX0 = 0
        self.posX1 = 0
        self.posY0 = 0
        self.posY1 = 0
        self.text = ""
        self.color = (0, 0, 0, 0)
        self.fontsize = 12
        self.fontname = "YaHei"
        self.bold = False

class DanMuList:
    def __init__(self):
        ls = []

    def optimize(self, screen_width, screen_height):
        # Some Best Value
        pass
    


def readAss(fname):
    assert str(fname).endswith('.ass')

    with open(fname, 'r') as f:
        doc = ass.parse(f)

    return doc.styles, doc.events, (doc.play_res_x, doc.play_res_y)


#readAss('dm.ass')