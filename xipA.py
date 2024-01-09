import os
import struct
import sys
from datetime import datetime

import lab4 


def log_warn(mes: str):
    print(f'{datetime.now()} [WARN] : {mes}')


def log_err(mes: str):
    print(f'{datetime.now()} [ERROR] : {mes}')


def generate_out_file_name(filename: str):
    if '.' in filename:
        return ".".join(filename.split('.')[0:len(filename.split('.')) - 1]) + '.xip'
    return filename + '.xip'


CODE_1 = 0x01
CODE_2 = 0x02 # RLE
CODE_3 = 0x04
CODE_4 = 0x08


def parse_codes(codes: int):
    return codes & CODE_4, codes & CODE_3, codes & CODE_2, codes & CODE_1


SIGNATURE_NAME = 0x1111
SIGNATURE_ALLOWED_VERSION = (1, 0)
SIGNATURE_UNPACK_STR = 'hBBBQ'
SIGNATURE_SIZE = 16


def getCodes(signature):
    return signature[3]


def generate_signature(version: tuple = (1, 0), codes: int = 0, data_size: int = 0):
    name = SIGNATURE_NAME
    res_size = SIGNATURE_SIZE + data_size
    codes = CODE_2
    return struct.pack(SIGNATURE_UNPACK_STR, name, version[0], version[1], codes, res_size)


def unpack_signature(signature):
    return struct.unpack(SIGNATURE_UNPACK_STR, signature)


def check_signature(signature):
    check = unpack_signature(signature)
    if check[0] != SIGNATURE_NAME or (check[1], check[2]) != SIGNATURE_ALLOWED_VERSION:
        return False
    return True


def create_out_file(name: str):
    try:
        if os.path.exists(name):
            log_warn(f'name {name} exist')
    finally:
        pass

    file = open(name, "wb+")
    return file


def check_path_to_zip(path: str):
    try:
        if not os.path.exists(path):
            log_warn(f'zip path {path} not exist')
            return False
    except:
        return False

    return True


def get_file_str(file_from, code):
    data = b''

    with open(file_from, 'rb') as file_r:
        data = file_r.read()
    
    if code == CODE_2:
        return lab4.RLEencode(data)
    else:
        return data
    

def zip_loop(file_path, code):
    data = dict()

    for root, dirs, files in os.walk(file_path):
        print(f'encoding dir \'{root}\'')
        data[root] = []
        for file in files:
            buf = get_file_str(os.path.join(root, file), code)
            data[root] += [{file: buf}]
            print(f'+\tfile \'{file}\' was encoded')

    return data


def parse_len(it):
    value, buf = '', next(it)
    while chr(buf[1]) != ';':
        if chr(buf[1]) == "}":
            return None, None
        value += str(buf[1] - 48)
        buf = next(it)

    value = int(value)

    for i in range(value + 1):
        next(it)

    return value, buf[0] + 1


def parse_file(it, d):
    filename_len, last = parse_len(it)
    if not filename_len and not last:
        return None, None
    
    filename = d[last:last + filename_len]

    data_len, last = parse_len(it)
    if not data_len and not last:
        return None, None
    
    data = d[last:last + data_len]

    return {filename.decode(): data}, chr(d[data_len + last])


def parse_dir_name(it, d):
    dir_len, last = parse_len(it)
    dir_name = d[last:last + dir_len]

    return dir_name.decode()


def read_dir(d):
    it = iter(enumerate(d))
    data = dict()
    buf = ''

    try:
        while 1:
            cur_dir = parse_dir_name(it, d)
            data[cur_dir] = []
            while buf != '}':
                file, buf = parse_file(it, d)
                if not file and not buf:
                    break
                data[cur_dir].append(file)
            buf = ''
    except StopIteration:
        return data



def decodeCodes(s, codes):
    if codes & CODE_2:
        return lab4.RLEdecode(s)
    else:
        return s


def unzip_loop(data, file_path, signature):
    for root, files in data.items():
        work = os.path.join(file_path, root)

        try:
            os.mkdir(work)
        except:
            pass

        for file in files:
            work_file = os.path.join(work, list(file.keys())[0])
            file_data = decodeCodes(list(file.values())[0], getCodes(signature))

            with open(work_file, 'wb+', encoding=None) as open_file:
                open_file.write(file_data)


def fill_file_tittle(pair):
    tittle = b''

    file = list(pair.items())[0][0]
    value = list(pair.items())[0][1]

    tittle += str(len(file)).encode() + b';'
    tittle += file.encode() + b';'
    tittle += str(len(value)).encode() + b';'
    tittle += value

    return tittle


def fill_files_tittles(data):
    tittle = b''

    pre_last_index = len(data) - 1
    for i in range(pre_last_index):
        pair = data[i]
        tittle += fill_file_tittle(pair)
        tittle += b'|'
    pair = data[pre_last_index]
    tittle += fill_file_tittle(pair)

    return tittle


def write_from_dict(data):
    new_data = b''

    for dirs in data.keys():
        new_data += str(len(dirs)).encode() + b';'
        new_data += dirs.encode() + b'{'

        if len(data[dirs]):
            new_data += fill_files_tittles(data[dirs])

        new_data += b'}'

    return new_data


def zip_item(filepath, code: int=0):
    fd = create_out_file(OUT_FILE_NAME)
    data = write_from_dict(zip_loop(filepath, code))
    fd.write(generate_signature(data_size=sys.getsizeof(data)))
    fd.write(data)
    fd.close()


def unzip_item(filepath):
    with open(filepath, 'rb') as file:
        signature = file.read(SIGNATURE_SIZE)
        if check_signature(signature):
            signature = unpack_signature(signature)
            data = read_dir(file.read())
            unzip_loop(data, os.path.join('.', 'unzip'), signature)


def main():
    zip_item(PATH_TO_ZIP, CODE_2)
    print(f'object \'{PATH_TO_ZIP}\' encoded')
    unzip_item(OUT_FILE_NAME)
    print(f'object \'{PATH_TO_ZIP} decoded')


PATH_TO_ZIP = "toZip"   # Название файла для архивации
OUT_FILE_NAME = generate_out_file_name(PATH_TO_ZIP)
main()
