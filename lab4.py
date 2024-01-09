import struct

def RLEencode(s: bytes) -> bytes:
    res = b''
    l = 0
    s += b'\0'

    for i in range(len(s)):
        if i + 1 < len(s) and (l == 255 or s[i] != s[i + 1]):
            res += struct.pack('c', l.to_bytes()) + struct.pack('c', s[i].to_bytes())
            l = 0
        else:
            l += 1
    
    return res


def RLEdecode(s: bytes) -> bytes:
    res = b''

    for i in range(0, len(s), 2):
        c = int.from_bytes(struct.unpack('c', s[i].to_bytes())[0]) + 1
        for j in range(c):
            res += struct.unpack('c', s[i+1].to_bytes())[0]
    
    return res


if __name__ == "__main__":
    encode = b''
    decode = b''

    with open('./test.jpg', 'rb') as file:
        encode = (RLEencode(file.read()))
    
    with open('./zip.jpg', 'wb+') as file:
        file.write(encode)

    with open('./unzip.jpg', 'wb+') as file:
        file.write(RLEdecode(encode))

