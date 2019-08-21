import ass
import re
# Use https://github.com/chireiden/python-ass


class DanMu:
    # Create Danmu by Ass event
    def createByAss(self, evt, play_res_x, play_res_y):
        # Text
        self.text = evt.text[evt.text.find('}')+1:]

        # Time
        self.start = evt.start.total_seconds()
        self.end = evt.end.total_seconds()
         
        # Style
        cind = evt.text.find('\c&')
        if cind != -1:
            self.color = self.color_format(evt.text[cind: cind+10])
        else:
            # Default
            self.color = '#FFFFFF'
            #self.color = (255, 255, 255, 0.6)
        self.fontname = 'Microsoft YaHei UI'
        self.fontsize = 20

        # Relative Position

        if evt.style == 'R2L':
            pos = re.findall(r"([-]?[0-9]{1,}[.]?[0-9]*)", evt.text)[0:4]
            self.startX = float(pos[0]) / play_res_x
            self.startY = float(pos[1]) / play_res_y
            self.endX = float(pos[2]) / play_res_x
            self.endY = float(pos[3]) / play_res_y
            self.type = 1

        elif evt.style == 'Fix':
            pos = re.findall(r"([-]?[0-9]{1,}[.]?[0-9]*)", evt.text)[0:2]
            self.startX = float(pos[0]) / play_res_x
            # TOP or BOTTOM
            if float(pos[1]) < play_res_y * 0.5:
                self.startY = float(pos[1]) / play_res_y
                self.type = 2
            else:
                self.startY = (float(pos[1]) + self.fontsize) / play_res_y
                self.type = 3
            self.endX = self.startX
            self.endY = self.startY

        else:
            print('Fount Undefined Style %s' % evt.style)
            assert(False)
        
        return self

    @staticmethod
    def color_format(hexd):
        hexd = hexd.lstrip('\c&H')
        bb = hexd[0:2]
        gg = hexd[2:4]
        rr = hexd[4:6]
        return '#' + rr + gg + bb
        #return (int(rr, 16), int(gg, 16), int(bb, 16), 0.6)


def readAss(fname):
    assert str(fname).endswith('.ass')

    with open(fname, 'r') as f:
        doc = ass.parse(f)

    dml = []
    for evt in doc.events:
        dm = DanMu()
        dm.createByAss(evt, doc.play_res_x, doc.play_res_y)
        dml.append(dm)

    return doc.styles, dml


readAss('dm.ass')