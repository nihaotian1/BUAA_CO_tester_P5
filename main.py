import myParser
import os
import random

global reg
global mem
global config
global narrow
global std
global narrow

def add(rs, rt, rd):
    global reg
    ins = "add $%d, $%d, $%d\n" % (rd, rs, rt)
    if rd != 0:
        reg[rd] = (reg[rs] + reg[rt]) & (4294967296 - 1)
    return ins


def sub(rs, rt, rd):
    global reg
    ins = "sub $%d, $%d, $%d\n" % (rd, rs, rt)
    if rd != 0:
        reg[rd] = (reg[rs] - reg[rt]) & (2147483648 - 1)
    return ins


def ori(rs, rt):
    if config['bound']:
        imm = random.randint(65530, 65535)
    else:
        imm = random.randint(0, 65535)
    imm = imm - imm % 4
    ins = "ori $%d, $%d, 0x%x\n" % (rt, rs, imm)  # require 0-ext, 0x0000_xxxx
    if rt != 0:
        reg[rt] = reg[rs] | (imm & (65536 - 1))
    return ins


def lw(rs, rt):
    imm = random.randint(0, 12287)
    imm = imm - imm % 4
    imm = imm - reg[rs]
    if imm > 32767 or imm < -32768 or imm + reg[rs] > 0x0000_2fff or imm + reg[rs] < 0:
        ins = ""
    else:
        ins = "lw $%d, %d($%d)\n" % (rt, imm, rs)
        reg[rt] = mem[reg[rs] + imm]

    return ins


def sw(rs, rt):
    imm = random.randint(0, 12287)
    imm = imm - imm % 4
    imm = imm - reg[rs]
    if imm > 32767 or imm < -32768 or imm + reg[rs] > 0x0000_2fff or imm + reg[rs] < 0:
        ins = ""
    else:
        ins = "sw $%d, %d($%d)\n" % (rt, imm, rs)
        mem[reg[rs] + imm] = reg[rt]

    return ins


def beq(rs, rt):
    ins = "beq $%d, $%d, label%d\nnop\n" % (rs, rt, config['label_num'])
    config['label_num'] += 1
    return ins


def lui(rt):
    if config['bound']:
        imm = random.randint(65530, 65535)
    else:
        imm = random.randint(0, 65535)
    ins = "lui $%d, 0x%x\n" % (rt, imm)
    if rt != 0:
        reg[rt] = imm << 16
    return ins


def jal():
    ins = "jal jump%d\nnop\n" % config['jump_num']
    config['jump_num'] += 1
    return ins


def jr():
    global reg
    global std
    list = []
    for i in range(narrow + 1):
        if 0x3000 <= reg[trans(std, i)] <= 0x3000 + 4 * config['test_size'] and reg[trans(std, i)] % 4 == 0:
            list.append(i)

    if len(list) == 0:
        return ""
    else:
        index = random.randint(0, len(list) - 1)
        rs = list[index]
        ins = "jr $%d\nnop\n" % rs
        return ins


def nop():
    return "nop\n"


def random_insert_list(list1=[], list2=[]):
    for i in list2:
        list1.insert(random.randint(0, len(list1)), i)


def trans(std, ranid):
    if ranid == narrow:
        return 31
    else:
        return std + ranid


def addInstr(rs, rt, rd):
    if config['mixed']:
        opcode = random.randint(0, 9)
        if opcode == 0:
            return add(rs, rt, rd)
        if opcode == 1:
            return sub(rs, rt, rd)
        if opcode == 2:
            return ori(rs, rt)
        if opcode == 3:
            return lw(rs, rt)
        if opcode == 4:
            return sw(rs, rt)
        if opcode == 5:
            return beq(rs, rt)
        if opcode == 6:
            return lui(rt)
        if opcode == 7:
            return jal()
        if opcode == 8:
            return jr()
        if opcode == 9:
            return nop()
    else:
        if config['suit'] == 1:
            opcode = random.randint(0, 3)
            if opcode == 0:
                return add(rs, rt, rd)
            if opcode == 1:
                return sub(rs, rt, rd)
            if opcode == 2:
                return ori(rs, rt)
            if opcode == 3:
                return lui(rt)
        elif config['suit'] == 2:
            opcode = random.randint(0, 5)
            if opcode == 0:
                return add(rs, rt, rd)
            if opcode == 1:
                return sub(rs, rt, rd)
            if opcode == 2:
                return ori(rs, rt)
            if opcode == 3:
                return lui(rt)
            if opcode == 4:
                return lw(rs, rt)
            if opcode == 5:
                return sw(rs, rt)


def run():
    global config
    global mem
    global reg
    global std
    global narrow
    config = myParser.prepare_parser()
    print(config)
    config['label_num'] = 0
    config['jump_num'] = 0
    narrow = config['narrow']

    print("---------------------------------------------------------------------------------------------"
          "-----------------------------------------------------------")
    print("The config of TestSuit:")
    print(config)
    print("---------------------------------------------------------------------------------------------"
          "-----------------------------------------------------------")
    
    init_asm = []
    # use reg to track 32 register
    reg = {}
    mem = {}
    reg[0] = 0

    for i in range(12278):
        mem[i] = 0
    if config['init']:
        for i in range(32):
            hi = random.randint(0, 65536)
            lo = random.randint(0, 65536)
            init_asm.append("lui $%d, 0x%x\n" % (i, hi))
            init_asm.append("ori $%d, $%d, 0x%x\n" % (i, i, lo))
            if i != 0:
                reg[i] = (hi << 16) | lo
            # print("%x, %x, %x" % (reg[i], hi, lo))
    else:
        for i in range(32):
            reg[i] = 0

    # if not config['init']:  # if didn't random init, follow MARS initial settings
    #     reg[28] = 0x0000_1800
    #     reg[29] = 0x0000_2ffc

    # print(reg)
    # print(mem)
    std = 0
    file_name = 'code.asm'
    with open(file_name, "w") as file:
        buffer = []
        labels = []
        print(config['bound'])
        for j in range(config['test_size']):
            if j % 50 == 0:
                std = random.randint(0, 30-narrow)
            rs = trans(std, random.randint(0, narrow))
            rt = trans(std, random.randint(0, narrow))
            rd = trans(std, random.randint(0, narrow))
            print(rs, rt, rd)
            buffer.append(addInstr(rs, rt, rd))

        for i in range(config['label_num']):
            labels.append("label%d:\n" % i)
        for i in range(config['jump_num']):
            labels.append("jump%d:\n" % i)

        print(buffer)
        print(labels)
        random.shuffle(labels)
        random_insert_list(buffer, labels)

        # do init
        if len(init_asm) != 0:
            for j in init_asm:
                file.write(j)

        for j in buffer:
            file.write(j)


if __name__ == '__main__':
    run()
    