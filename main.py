import myParser
import os
import random

global pc
global reg
global mem
global config
global narrow
global std
global narrow

def add(rs, rt, rd):
    global reg
    global pc
    pc += 4
    ins = "add $%d, $%d, $%d\n" % (rd, rs, rt)
    if rd != 0:
        reg[rd] = (reg[rs] + reg[rt]) & (4294967296 - 1)
    return ins


def sub(rs, rt, rd):
    global reg
    global pc
    pc += 4
    ins = "sub $%d, $%d, $%d\n" % (rd, rs, rt)
    if rd != 0:
        reg[rd] = (reg[rs] - reg[rt]) & (2147483648 - 1)
    return ins


def ori(rs, rt):
    global reg
    global pc
    pc += 4
    if config['bound']:
        imm = random.randint(65530, 65535)
    else:
        imm = random.randint(0, 65535)
    ins = "ori $%d, $%d, 0x%x\n" % (rt, rs, imm)  # require 0-ext, 0x0000_xxxx
    if rt != 0:
        reg[rt] = reg[rs] | (imm & (65536 - 1))
    return ins


def lw(rs, rt):
    global reg
    global mem
    global pc
    pc += 4
    imm = random.randint(0, 0x0000_2fff)
    imm = imm - imm % 4
    imm = imm - reg[rs]
    if imm > 32767 or imm < -32768 or imm + reg[rs] > 0x0000_2fff or imm + reg[rs] < 0:
        ins = ""
    else:
        ins = "lw $%d, %d($%d)\n" % (rt, imm, rs)
        reg[rt] = mem[reg[rs] + imm]

    return ins


def sw(rs, rt):
    global reg
    global mem
    global pc
    pc += 4
    imm = random.randint(0, 0x0000_2fff)
    imm = imm - imm % 4
    imm = imm - reg[rs]
    if imm > 32767 or imm < -32768 or imm + reg[rs] > 0x0000_2fff or imm + reg[rs] < 0:
        ins = ""
    else:
        ins = "sw $%d, %d($%d)\n" % (rt, imm, rs)
        mem[reg[rs] + imm] = reg[rt]

    return ins


def beq(rs, rt, rd):
    global reg
    global pc
    pc = pc - 4  # same as jal
    ins = "beq $%d, $%d, label%d\n" % (rs, rt, config['label_num'])
    config['label_num'] += 1
    opcode = random.randint(0, 5)
    if reg[rs] != reg[rt]:
        db = nop()
    elif opcode == 0 and rd != rt and rd != rt:
        db = add(rs, rt, rd)
    elif opcode == 1 and rd != rt and rd != rt:
        db = sub(rs, rt, rd)
    elif opcode == 2 and rd != rt and rd != rt:
        db = ori(rs, rd)
    elif opcode == 3 and rd != rt and rd != rt:
        db = lui(rd)
    elif opcode == 4 and (config['mixed'] or config['suit'] == 2) and rd != rt and rd != rt:
        db = lw(rs, rd)
        if db == "":
            db = nop()
    elif opcode == 5 and (config['mixed'] or config['suit'] == 2):
        db = sw(rs, rt)
        if db == "":
            db = nop()
    else:
        db = nop()
    ins = ins + db
    return ins


def lui(rt):
    global reg
    global pc
    pc += 4
    if config['bound']:
        imm = random.randint(65530, 65535)
    else:
        imm = random.randint(0, 65535)
    ins = "lui $%d, 0x%x\n" % (rt, imm)
    if rt != 0:
        reg[rt] = imm << 16
    return ins


def jal(rs, rt, rd):
    global reg
    global pc
    reg[31] = pc + 8
    pc = pc - 4  # two ins + 8, it should to sum up +4
    ins = "jal jump%d\n" % config['jump_num']
    config['jump_num'] += 1
    opcode = random.randint(0, 5)
    if opcode == 0 and rd != 31:
        db = add(rs, rt, rd)
    elif opcode == 1 and rd != 31:
        db = sub(rs, rt, rd)
    elif opcode == 2 and rt != 31:
        db = ori(rs, rt)
    elif opcode == 3 and rt != 31:
        db = lui(rt)
    elif opcode == 4 and (config['mixed'] or config['suit'] == 2) and rt != 31 and rs != 31:  # untrack reg[31] = pc
        db = lw(rs, rt)
        if db == "":
            db = nop()
    elif opcode == 5 and (config['mixed'] or config['suit'] == 2) and rs != 31:
        db = sw(rs, rt)
        if db == "":
            db = nop()
    else:
        db = nop()
    ins = ins + db
    return ins


def jr(rs, rt, rd):
    global reg
    global std
    global pc
    pc += 4
    ins = "jr $31\n"
    opcode = random.randint(0, 5)
    if opcode == 0:
        db = add(rs, rt, rd)
    elif opcode == 1:
        db = sub(rs, rt, rd)
    elif opcode == 2:
        db = ori(rs, rt)
    elif opcode == 3:
        db = lui(rt)
    elif opcode == 4 and (config['mixed'] or config['suit'] == 2) and rs != 31:
        db = lw(rs, rd)
        if db == "":
            db = nop()
    elif opcode == 5 and (config['mixed'] or config['suit'] == 2) and rs != 31:
        db = sw(rs, rt)
        if db == "":
            db = nop()
    else:
        db = nop()
    ins = ins + db
    return ins


def nop():
    global pc
    pc += 4
    return "nop\n"


def random_insert_list(list1=[], list2=[]):
    for i in list2:
        list1.insert(random.randint(0, len(list1)), i)


def trans(std, ranid):
    if ranid == narrow:
        return 31
    else:
        return std + ranid


def addInstr(rs, rt, rd, op):
    if op == 2:
        return jal(rs, rt, rd)
    elif op == 3:
        return beq(rs, rt, rd)
    elif op == 1:
        if config['suit'] == 1:
            opcode = random.randint(0, 4)
            if opcode == 0:
                return add(rs, rt, rd)
            if opcode == 1:
                return sub(rs, rt, rd)
            if opcode == 2:
                return ori(rs, rt)
            if opcode == 3:
                return lui(rt)
            if opcode == 4:
                return nop()
        elif config['suit'] == 2:
            opcode = random.randint(0, 6)
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
            if opcode == 6:
                return nop()


def run():
    global config
    global mem
    global reg
    global std
    global narrow
    global pc
    pc = 0x3000_0000
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
        jump = []
        print(config['bound'])
        # generate basic Instr
        for j in range(config['test_size']):
            if j % 50 == 0:
                std = random.randint(0, 30-narrow)
            rs = trans(std, random.randint(0, narrow))
            rt = trans(std, random.randint(0, narrow))
            rd = trans(std, random.randint(0, narrow))
            print(rs, rt, rd)
            op = random.randint(0, 5)
            if op == 2 and config['mixed']:
                buffer.append(addInstr(rs, rt, rd, 2))
                jrstr = jr(rs, rt, rd)
                jrstr = ("jump%d:\n" % (config['jump_num'] - 1)) + jrstr
                jump.append(jrstr)
            elif op == 3 and config['mixed']:
                beqstr = addInstr(rs, rt, rd, 3)
                label1 = "label%d:\n" % (config['label_num'] - 1)
                beq1str = addInstr(rs, rt, rd, 3)
                beqstr = beqstr + ("label%d:\n" % (config['label_num'] - 1))
                beq1str = label1 + beq1str
                buffer.append(beqstr)
                jump.append(beq1str)
            else:
                buffer.append(addInstr(rs, rt, rd, 1))

        # do init
        if len(init_asm) != 0:
            for j in init_asm:
                file.write(j)

        if config['mixed']:
            for i in buffer:
                file.write(i)
            file.write("beq $0, $0, end\nnop\n")
            for i in jump:
                file.write(i)
            file.write("end:\n")
        else:
            for i in buffer:
                file.write(i)


if __name__ == '__main__':
    run()
    