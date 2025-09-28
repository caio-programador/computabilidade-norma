import re
from typing import Dict, Tuple, List, Any


PADRAO_ROTULO = re.compile(r'^\s*([0-9]+)\s*:\s*(.+)$', re.IGNORECASE)   # Representa o rótulo, que é um numero seguido de :
PADRAO_COMENTARIO = re.compile(r'#.*$')                                         # para ignorar os comentários

"""
Converte o nome do registrador 'a','b'... para o índice 0,1,...
"""
def nome_para_indice_registrador(nome: str) -> int:
    """Converte 'a'..'z' -> 0..25, valida nome."""
    if not isinstance(nome, str):
        raise ValueError("Nome de registrador deve ser string.")
    s = nome.strip().lower()
    if len(s) != 1 or not ('a' <= s <= 'z'):
        raise ValueError(f"Nome de registrador inválido: '{nome}'")
    return ord(s) - ord('a')


"""
    Analisa uma única string de instrução (sem rótulo).
    Essa função irá verificar se a instrução escrita na linha se adequa em alguma das intruções aceitas.
    Caso sim, retorna uma tupla com a respectiva isntrução, registradores e rótulos.
"""
def analisar_instrucao_linha(texto_instr: str) -> Tuple:
    t = PADRAO_COMENTARIO.sub('', texto_instr).strip()
    if t == '':
        return ('vazio',)

    # Identifica a MACRO correspondente. Macros: IGUAL a b c | MAIOR a b c d | MENOR a b c
    m = re.match(r'^(IGUAL)\s+([a-z])\s+([a-z])\s+([a-z])$', t, re.IGNORECASE)
    if m:
        return ('macro_igual', m.group(2).lower(), m.group(3).lower(), m.group(4).lower())

    m = re.match(r'^(MAIOR)\s+([a-z])\s+([a-z])\s+([a-z])\s+([a-z])$', t, re.IGNORECASE)
    if m:
        return ('macro_maior', m.group(2).lower(), m.group(3).lower(), m.group(4).lower(), m.group(5).lower())

    m = re.match(r'^(MENOR)\s+([a-z])\s+([a-z])\s+([a-z])$', t, re.IGNORECASE)
    if m:
        return ('macro_menor', m.group(2).lower(), m.group(3).lower(), m.group(4).lower())

    # instruções primitivas
    # se zero_x então vá_para A senão vá_para B
    m = re.match(r'^se\s+zero[_\s]?([a-z])\s+.*?([0-9]+)\s+.*?([0-9]+)$', t, re.IGNORECASE)
    if m:
        return ('se_zero', m.group(1).lower(), int(m.group(2)), int(m.group(3)))

    # faça add_x vá_para N
    m = re.match(r'^(?:fa(c|ç)a\s+)?(?:add|adicionar)[_\s]?([a-z])\s+.*?([0-9]+)$', t, re.IGNORECASE)
    if m:
        return ('adicionar', m.group(2).lower(), int(m.group(3)))

    # faça sub_x vá_para N
    m = re.match(r'^(?:fa(c|ç)a\s+)?(?:sub|subtrair)[_\s]?([a-z])\s+.*?([0-9]+)$', t, re.IGNORECASE)
    if m:
        return ('subtrair', m.group(2).lower(), int(m.group(3)))

    # se a linha não corresponder a nenhum  dos padrões da linguagem, gera um erro
    raise ValueError(f"Instrução inválida ou não reconhecida: '{texto_instr}'")

"""
    Esta função coordena a análise linha por linha. Ela lê todo o  programa, separa-o em linhas e, para cada linha, 
    chama analisar_instrucao_linha. O resultado é um dicionário que mapeia cada rótulo do seu programa para sua 
    representação estruturada.
"""
def analisar_texto_programa(texto: str) -> Dict[int, Tuple]:
    linhas = texto.splitlines()
    programa = {}
    for raw in linhas:
        linha = raw.strip()
        if linha == '' or linha.startswith('#'):
            continue
        m = PADRAO_ROTULO.match(linha)
        if not m:
            raise ValueError(f"Linha com formato errado (esperado 'rotulo: instr'): '{linha}'")
        rotulo = int(m.group(1))
        instr = m.group(2).strip()
        analisado = analisar_instrucao_linha(instr)     # Chama função para analisar a linha
        programa[rotulo] = analisado
    return programa


"""
É uma das funções principais. Ela executa o programa expandido instrução por instrução, simulando o comportamento 
da máquina Norma.
"""
def rodar_norma(programa: Dict[int, Dict], rotulo_inicial: int, regs: List[int], max_passos=100000) -> Tuple[
    List[Tuple[int, Tuple[int, ...]]], str]:
    traco = []              # Serve para armazenar o histórico de execução (trace) do programa.
    pc = rotulo_inicial     # Program counter (para indicar qual instrução deve ser executada)
    passos = 0
    erro = ''
    rotulos_validos = set(programa.keys())

    # Executa as instrções até o final do programa
    while True:
        if passos > max_passos:     # Se o programa fizer mais de 100 mil passos, provavelmente é infinito
            erro = "Máximo de passos excedido (loop provável)."
            break
        if pc not in programa:      # se o pc apontar para um rotulo que não existe, acaba o programa
            break

        instr = programa[pc]                # pega a instrução atual
        traco.append((pc, tuple(regs)))     # adicona o estado atual e os valores dos registradores
        t = instr.get('tipo')               # t armazena o tipo da instrução

        # se_zero: Checa o valor de um registrador. Se for zero, atualiza o pc para o rótulo de destino entao. Caso contrário, atualiza para o rótulo senao
        if t == 'se_zero':
            reg = instr['reg']
            if not (0 <= reg < len(regs)):
                erro = f"Referência a registrador inválido {reg} em label {pc}"
                break
            ent = instr['entao']
            sen = instr['senao']
            destino = ent if regs[reg] == 0 else sen
            if destino not in rotulos_validos:
                traco.append((destino, tuple(regs)))
                break
            pc = destino

        # adicionar: Incrementa o registrador e atualiza o pc para o rótulo de destino ir_para
        elif t == 'adicionar':
            reg = instr['reg']
            if not (0 <= reg < len(regs)):
                erro = f"Referência a registrador inválido {reg} em label {pc}"
                break
            regs[reg] += 1
            destino = instr['ir_para']
            if destino not in rotulos_validos:
                traco.append((destino, tuple(regs)))
                break
            pc = destino

        # subtrair: decrementa o registrador e atualiza o pc para o rótulo de destino ir_para
        elif t == 'subtrair':
            reg = instr['reg']
            if not (0 <= reg < len(regs)):
                erro = f"Referência a registrador inválido {reg} em label {pc}"
                break
            if regs[reg] > 0:
                regs[reg] -= 1
            destino = instr['ir_para']
            if destino not in rotulos_validos:
                traco.append((destino, tuple(regs)))
                break
            pc = destino

        # ir_para: Apenas atualiza o pc para o rótulo de destino
        elif t == 'ir_para':
            destino = instr['ir_para']
            if destino not in rotulos_validos:
                traco.append((destino, tuple(regs)))
                break
            pc = destino

        # instruções desconhecidas
        else:
            erro = f"Instrução desconhecida no label {pc}: {instr}"
            break

        passos += 1

    return traco, erro