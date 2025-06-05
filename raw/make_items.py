import sys

import zstandard


def main(filepath: str):
    filepath_base = filepath.rsplit('.', 1)[0]
    with zstandard.open(filepath, 'r') as f, \
        open(filepath_base+'_not_supported.txt', 'w') as fskip, \
        open(filepath_base+'_items.txt', 'w') as fitems:
        for line in f:
            line = line.strip()
            if len(line) == 0:
                continue
            if line.count('/') == 2:
                line += '/'
            split = line.split('/', 3)
            if len(split) < 3:
                print(line)
                continue
            if split[2] not in (
                'rfa.org',
                'www.rfa.org',
                'benarnews.org',
                'www.benarnews.org',
                'wainao.me',
                'www.wainao.me'
            ):
                fskip.write(line+'\n')
            else:
                fitems.write('article:{}:{}\n'.format(split[2].split('.')[-2], split[3]))

if __name__ == '__main__':
    for filepath in sys.argv[1:]:
        main(filepath)

