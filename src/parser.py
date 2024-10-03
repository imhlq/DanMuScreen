import ass
from danmu import DanMu

def read_ass(filename):
    if filename.endswith('.ass'):
        with open(filename, 'r', encoding='utf-8-sig') as f:
            doc = ass.parse(f)

        danmu_list = [
            DanMu.create_by_ass(evt, doc.play_res_x, doc.play_res_y)
            for evt in doc.events
        ]

        return doc.styles, danmu_list
    elif filename.endswith('.xml'):
        raise NotImplementedError('Conversion from XML to ASS is not implemented.')
    else:
        raise ValueError(f'Unsupported file format: {filename}')
