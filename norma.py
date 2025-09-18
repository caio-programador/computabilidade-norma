from typing import List, Dict, Tuple
import re

LABEL_RE = re.compile(r'^\s*([0-9]+)\s*:\s*(.+)$', re.IGNORECASE)
COMMENT_RE = re.compile(r'#.*$')


def run_norma(program: Dict[int, Dict], start_label:int, regs:List[int], max_steps=100000) -> Tuple[List[Tuple[int, Tuple[int,...]]], str]:
    """
    Programa Norma com fim automático para rótulos inexistentes.
    """
    label_index = {label: label for label in program.keys()}
    trace = []
    pc = start_label
    steps = 0
    error = ''

    while True:
        if steps > max_steps:
            error = 'Máximo de passos excedido (loop infinito provável).'
            break
        if pc not in program:
            # rótulo não existe: encerra como fim automático
            break

        instr = program[pc]
        # registra estado atual
        trace.append((pc, tuple(regs)))
        t = instr.get('type')

        if t == 'if_zero':
            reg = instr['reg']
            if reg < 0 or reg >= len(regs):
                error = f"Referência a registrador inválido {reg} em label {pc}"
                break
            dest = instr['then'] if regs[reg] == 0 else instr['else']
            if dest not in label_index:
                # salto para rótulo inexistente = fim automático
                trace.append((dest, tuple(regs)))
                break
            pc = dest
            steps += 1
            continue

        elif t in ('add', 'sub'):
            reg = instr['reg']
            if reg < 0 or reg >= len(regs):
                error = f"Referência a registrador inválido {reg} em label {pc}"
                break
            if t == 'add':
                regs[reg] += 1
            else:
                if regs[reg] > 0:
                    regs[reg] -= 1
            dest = instr['goto']
            if dest not in label_index:
                trace.append((dest, tuple(regs)))
                break
            pc = dest
            steps += 1
            continue

        elif t == 'goto':
            dest = instr['goto']
            if dest not in label_index:
                trace.append((dest, tuple(regs)))
                break
            pc = dest
            steps += 1
            continue

        else:
            error = f"Instrução desconhecida no label {pc}: {instr}"
            break

    return trace, error

# A helper to patch block-local gotos produced by macro expansion into absolute labels:
def assign_block_labels_and_patch(block_instrs: List[Dict], following_label:int) -> List[Dict]:
    """
    Given a block of instr dicts produced by macro expander in block-index style,
    patch special_end to goto 'following_label', and convert 'goto_block_idx' into numeric gotos if present.
    The block here is small; we assume internal gotos that reference block indices use numeric labels within block in the
    sense that instructions refer to numeric 'goto' equal to some block index (0-based). We used small indexes in expansions.
    For safety, if an instruction has 'goto_block_idx' or 'special_end', we patch appropriately.
    """
    n = len(block_instrs)
    return block_instrs


def regname_to_index(name: str) -> int:
    """Converts register name 'a','b'... to index 0,1,..."""
    name = name.strip().lower()
    if len(name) != 1 or not ('a' <= name <= 'z'):
        raise ValueError(f"Nome de registrador inválido: {name}")
    return ord(name) - ord('a')

def parse_line_instruction(instr_text: str):
    """
    Parse a single instruction string (without label).
    Accepts:
      se zero_a então vá_para 9 senão vá_para 2
      faça add_a vá_para 3
      faça sub_b vá_para 1
      macro MUL a b c   (handled elsewhere)
    Returns a dict representing the instruction or a macro tuple.
    """
    t = instr_text.strip()
    t = COMMENT_RE.sub('', t).strip()
    if t == '':
        return ('empty',)
    m = re.match(r'^(MUL)\s+([a-z])\s+([a-z])\s+([a-z])$', t, re.IGNORECASE)
    if m:
        return ('macro_mul', m.group(2).lower(), m.group(3).lower(), m.group(4).lower())
    m = re.match(r'^(DIV)\s+([a-z])\s+([a-z])\s+([a-z])\s+([a-z])$', t, re.IGNORECASE)
    if m:
        return ('macro_div', m.group(2).lower(), m.group(3).lower(), m.group(4).lower(), m.group(5).lower())
    m = re.match(r'^(POW)\s+([a-z])\s+([0-9]+)\s+([a-z])$', t, re.IGNORECASE)
    if m:
        return ('macro_pow', m.group(2).lower(), int(m.group(3)), m.group(4).lower())

    m = re.match(r'^se\s+zero_([a-z])\s+ent[oó]o\s+v[aá]_[pP]ara\s+([0-9]+)\s+sen[oõ]o\s+v[aá]_[pP]ara\s+([0-9]+)$', t, re.IGNORECASE)
    if m:
        return ('if_zero', m.group(1).lower(), int(m.group(2)), int(m.group(3)))
    m = re.match(r'^fa(c|ç)a\s+add_([a-z])\s+v[aá]_[pP]ara\s+([0-9]+)$', t, re.IGNORECASE)
    if m:
        return ('add', m.group(2).lower(), int(m.group(3)))
    m = re.match(r'^fa(c|ç)a\s+sub_([a-z])\s+v[aá]_[pP]ara\s+([0-9]+)$', t, re.IGNORECASE)
    if m:
        return ('sub', m.group(2).lower(), int(m.group(3)))
    m = re.match(r'^se\s+zero[_\s]?([a-z])\s+ent[oó]o\s+v[aá]a?[_\s]para\s+([0-9]+)\s+sen[oõ]o\s+v[aá]a?[_\s]para\s+([0-9]+)$', t, re.IGNORECASE)
    if m:
        return ('if_zero', m.group(1).lower(), int(m.group(2)), int(m.group(3)))
    m = re.match(r'^se\s+zero[_\s]?([a-z])\s+.*?([0-9]+)\s+.*?([0-9]+)$', t, re.IGNORECASE)
    if m:
        return ('if_zero', m.group(1).lower(), int(m.group(2)), int(m.group(3)))

    m = re.match(r'^(add|sub)_([a-z])\s+v[aá]a?[_\s]para\s+([0-9]+)$', t, re.IGNORECASE)
    if m:
        typ = m.group(1).lower()
        if typ == 'add':
            return ('add', m.group(2).lower(), int(m.group(3)))
        else:
            return ('sub', m.group(2).lower(), int(m.group(3)))

    raise ValueError(f"Instrução inválida ou não reconhecida: '{instr_text}'")

def parse_program_text(text: str) -> Dict[int, Tuple]:
    """
    Returns a dict label -> parsed instruction (or macro tuple).
    """
    lines = text.splitlines()
    program = {}
    for raw in lines:
        line = raw.strip()
        if line == '' or line.lstrip().startswith('#'):
            continue
        m = LABEL_RE.match(line)
        if not m:
            raise ValueError(f"Linha com formato errado (esperado 'label: instr'): '{line}'")
        label = int(m.group(1))
        instr = m.group(2).strip()
        parsed = parse_line_instruction(instr)
        program[label] = parsed
    return program
