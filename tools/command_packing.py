"""Bounded private command packing: short pairs and 2-KiB long references."""


def pack(data):
    n = len(data)
    matches, positions = [], {}
    for at in range(n):
        best = distance = near = 0
        key = data[at:at+2]
        for previous in reversed(positions.get(key, [])):
            delta = at-previous
            if delta > 2048:
                break
            length = 2
            while length < 18 and at+length < n and data[previous+length] == data[at+length]:
                length += 1
            if length > best:
                best, distance = length, delta
            if delta <= 128 and not near:
                near = delta
        matches.append((best,distance,near))
        positions.setdefault(key,[]).append(at)
    costs = [[0]*8 for _ in range(n+1)]
    choices = [[None]*8 for _ in range(n)]
    for at in range(n-1,-1,-1):
        length,distance,near = matches[at]
        for slot in range(8):
            following = (slot+1)%8
            options = [(1+costs[at+1][following],-1,0)]
            if near:
                options.append((1+costs[at+2][following],-2,near))
            options.extend((2+costs[at+k][following],-k,distance)
                           for k in range(3,length+1))
            cost,negative,distance = min(options)
            costs[at][slot] = cost+(slot==0)
            choices[at][slot] = (-negative,distance)
    result = bytearray()
    at = 0
    while at < n:
        flags = len(result)
        result.append(0)
        for bit in range(8):
            if at == n:
                break
            length,distance = choices[at][bit]
            if length == 1:
                result[flags] |= 1<<bit
                result.append(data[at])
            elif length == 2:
                result.append(distance-1)
            else:
                distance -= 1
                result.extend((0x80|(distance&127), (distance>>7)|((length-3)<<4)))
            at += length
    return bytes(result)


def unpack(data, size):
    result = bytearray()
    at = 0
    while len(result) < size:
        if at >= len(data):
            raise ValueError('missing flags')
        flags = data[at]
        at += 1
        for bit in range(8):
            if len(result) == size:
                if flags >> bit:
                    raise ValueError('nonzero unused flags')
                break
            if at >= len(data):
                raise ValueError('truncated token')
            byte = data[at]
            at += 1
            if flags & (1<<bit):
                result.append(byte)
                continue
            count,distance = 2,byte+1
            if byte & 128:
                if at == len(data):
                    raise ValueError('truncated long token')
                second = data[at]
                at += 1
                count,distance = (second>>4)+3,((second&15)<<7)+(byte&127)+1
            if distance > len(result) or len(result)+count > size:
                raise ValueError('invalid backreference')
            for _ in range(count):
                result.append(result[-distance])
    if at != len(data):
        raise ValueError('trailing tokens')
    return bytes(result)
