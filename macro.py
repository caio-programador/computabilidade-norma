from typing import List, Dict, Tuple, Any
from norma import nome_para_indice_registrador


"""
Classe usada para a tradução das macros para a linguagem da Máquina Norma
"""
class ExpansorMacro:
    def __init__(self, base_rotulo_inicio=100000):
        self.proximo_rotulo = base_rotulo_inicio - 1

    """ 
    Gera rótulos únicos e de alta numeração (100001, 100002, etc.) para as instruções que são criadas durante 
    a expansão das macros. Isso evita dar conflito com os rótulos do programa principal
    """
    def novo_rotulo(self) -> int:
        self.proximo_rotulo += 1
        return self.proximo_rotulo

    """
    Expande uma macro para uma lista de instruções primitivas que a máquina norma conhece.
    """
    def expandir_macro(self, no: Tuple, num_regs: int) -> List[Dict[str, Any]]:
        tipo = no[0]
        if tipo == 'macro_igual':
            _, a, b, c = no
            ra = nome_para_indice_registrador(a)
            rb = nome_para_indice_registrador(b)
            rc = nome_para_indice_registrador(c)
            return self.expandir_igual(ra, rb, rc, num_regs)

        if tipo == 'macro_maior':
            _, a, b, c, d = no
            ra = nome_para_indice_registrador(a)
            rb = nome_para_indice_registrador(b)
            rc = nome_para_indice_registrador(c)
            rd = nome_para_indice_registrador(d)
            return self.expandir_maior(ra, rb, rc, rd, num_regs)

        if tipo == 'macro_menor':
            _, a, b, c = no
            ra = nome_para_indice_registrador(a)
            rb = nome_para_indice_registrador(b)
            rc = nome_para_indice_registrador(c)
            return self.expandir_menor(ra, rb, rc, num_regs)

        raise ValueError("Macro desconhecida: " + str(tipo))

    def expandir_maior(self, r_a: int, r_b: int, r_c: int, r_d: int, num_regs: int) -> List[Dict[str, Any]]:
        """
        MACRO MAIOR:
        Encontra o maior valor entre os registradores a e b.
        Armazena o valor máximo no registrador d.
        Usa o registrador c como auxiliar para contagem e restauração


        Requisitos:
        - Número mínimo de registradores: 4 (a, b, c, d)
        - Os registradores c e d devem ser zerados antes do uso
        - Use o comando (MAIOR a b c d) para chamar ela na interface


        Lógica de implementação:
        1. Zera os registradores auxiliares c e d
        2. Decrementa ambos a e b simultaneamente enquanto ambos forem > 0
        3. Conta em c quantas vezes ambos foram decrementados
        4. Quando um chega a zero, o maior valor é c + o valor restante do outro
        5. Restaura os valores originais de a e b usando o contador c
        6. Armazena o maior valor final em d


        Macro escrita:
        0: se zero_c então vá_para 3 senão vá_para 1
        1: faça sub_c vá_para 0
        2: se zero_d então vá_para 4 senão vá_para 3
        3: faça sub_d vá_para 2
        4: se zero_a então vá_para 9 senão vá_para 5
        5: se zero_b então vá_para 12 senão vá_para 6
        6: faça sub_a vá_para 7
        7: faça sub_b vá_para 8
        8: faça add_c vá para 4
        9: se zero_b vá_para 15 senão vá_para 10
        10: faça sub_b vá_para 11
        11: faça add_d vá_para 9
        12: se zero_a então vá_para 15 senão vá_para 13
        13: faça sub_a vá_para 14
        14: faça add_d vá_para 12
        15: se zero_c então vá_para 18 senão vá_para 16
        16: faça sub_c vá_para 17
        17: faça add_d vá_para 15
        18: # fim
        """

        instrs = []
        instrs.append({'tipo': 'se_zero', 'reg': r_c, 'entao_idx': 2, 'senao_idx': 1})  # OBS: Como é uma lista, começa no label 0
        instrs.append({'tipo': 'subtrair', 'reg': r_c, 'ir_idx': 0})

        instrs.append({'tipo': 'se_zero', 'reg': r_d, 'entao_idx': 4, 'senao_idx': 3})
        instrs.append({'tipo': 'subtrair', 'reg': r_d, 'ir_idx': 2})

        instrs.append({'tipo': 'se_zero', 'reg': r_a, 'entao_idx': 9, 'senao_idx': 5})
        instrs.append({'tipo': 'se_zero', 'reg': r_b, 'entao_idx': 12, 'senao_idx': 6})

        instrs.append({'tipo': 'subtrair', 'reg': r_a, 'ir_idx': 7})
        instrs.append({'tipo': 'subtrair', 'reg': r_b, 'ir_idx': 8})
        instrs.append({'tipo': 'adicionar', 'reg': r_c, 'ir_idx': 4})

        instrs.append({'tipo': 'se_zero', 'reg': r_b, 'entao_idx': 15, 'senao_idx': 10})
        instrs.append({'tipo': 'subtrair', 'reg': r_b, 'ir_idx': 11})
        instrs.append({'tipo': 'adicionar', 'reg': r_d, 'ir_idx': 9})

        instrs.append({'tipo': 'se_zero', 'reg': r_a, 'entao_idx': 15, 'senao_idx': 13})
        instrs.append({'tipo': 'subtrair', 'reg': r_a, 'ir_idx': 14})
        instrs.append({'tipo': 'adicionar', 'reg': r_d, 'ir_idx': 12})

        instrs.append({'tipo': 'se_zero', 'reg': r_c, 'entao_idx': 18, 'senao_idx': 16})
        instrs.append({'tipo': 'subtrair', 'reg': r_c, 'ir_idx': 17})
        instrs.append({'tipo': 'adicionar', 'reg': r_d, 'ir_idx': 15})

        instrs.append({'tipo': 'ret'})    # O ret é uma instrução especial, equivale a um "ir_para" o rótulo seguinte do programa principal.
        return instrs

    def expandir_menor(self, r_a: int, r_b: int, r_c: int, num_regs: int) -> List[Dict[str, Any]]:
        """
        MACRO MENOR:
        Encontra o menor valor entre os registradores a e b.
        Armazena o valor mínimo no registrador c.


        Requisitos:
        - Número mínimo de registradores: 3 (a, b, c)
        - O registrador c deve ser zerado antes do uso
        - Use o comando (MENOR a b c) para chamar ela na interface


        Lógica de implementação:
        1. Zera o registrador c (se necessário)
        2. Decrementa ambos a e b simultaneamente enquanto ambos forem > 0
        3. O valor em c representa quantas vezes ambos puderam ser decrementados
        4. Quando um dos registradores chega a zero, c contém o menor valor


        Macro escrita:
        0: se zero_c então vá_para 3 senão vá_para 1
        1: faça sub_c vá_para 0
        2: se zero_a então vá_para 7 senão vá_para 3
        3: se zero_b então vá_para 7 senão vá_para 4
        4: faça sub_a vá_para 5
        5: faça sub_b vá_para 6
        6: faça add_c vá para 2
        7: # fim
        """
        instrs = []
        instrs.append({'tipo': 'se_zero', 'reg': r_c, 'entao_idx': 2, 'senao_idx': 1})
        instrs.append({'tipo': 'subtrair', 'reg': r_c, 'ir_idx': 0})

        instrs.append({'tipo': 'se_zero', 'reg': r_a, 'entao_idx': 7, 'senao_idx': 3})
        instrs.append({'tipo': 'se_zero', 'reg': r_b, 'entao_idx': 7, 'senao_idx': 4})

        instrs.append({'tipo': 'subtrair', 'reg': r_a, 'ir_idx': 5})
        instrs.append({'tipo': 'subtrair', 'reg': r_b, 'ir_idx': 6})
        instrs.append({'tipo': 'adicionar', 'reg': r_c, 'ir_idx': 2})

        instrs.append({'tipo': 'ret'})
        return instrs

    def expandir_igual(self, r_a: int, r_b: int, r_c: int, num_regs: int) -> List[Dict[str, Any]]:
        """
        MACRO IGUAL:
        Compara se os valores nos registradores a e b são iguais.
        Se a == b: armazena 1 no registrador c
        Se a ≠ b: armazena 0 no registrador c


        Requisitos:
        - Número mínimo de registradores: 3 (a, b, c)
        - O registrador c deve ser zerado antes do uso
        - Use o comando (IGUAL a b c) para chamar ela na interface


        Lógica de implementação:
        1. Zera o registrador c (se necessário)
        2. Decrementa ambos a e b simultaneamente enquanto ambos forem > 0
        3. Se ambos chegarem a zero ao mesmo tempo --> valores eram iguais (c = 1)
        4. Se um chegar a zero antes do outro --> valores eram diferentes (c = 0)


        Macro escrita:
        1: se zero_c então vá_para 3 senão vá_para 2
        2: faca sub_c vá_para 1
        3: se zero_a vá_para 7 senão vá_para 4
        4: se zero_b vá_para 9 senão vá_para 5
        5: faca sub_a vá_para 6
        6: faca sub_b vá_para 3
        7: se zero_b vá_para 8 senão vá_para 9
        8: faca add_c vá_para 9
        9: # fim
        """
        instrs = []
        instrs.append({'tipo': 'se_zero', 'reg': r_c, 'entao_idx': 2, 'senao_idx': 1})
        instrs.append({'tipo': 'subtrair', 'reg': r_c, 'ir_idx': 0})

        instrs.append({'tipo': 'se_zero', 'reg': r_a, 'entao_idx': 6, 'senao_idx': 3})
        instrs.append({'tipo': 'se_zero', 'reg': r_b, 'entao_idx': 8, 'senao_idx': 4})
        instrs.append({'tipo': 'subtrair', 'reg': r_a, 'ir_idx': 5})
        instrs.append({'tipo': 'subtrair', 'reg': r_b, 'ir_idx': 2})

        instrs.append({'tipo': 'se_zero', 'reg': r_b, 'entao_idx': 7, 'senao_idx': 8})
        instrs.append({'tipo': 'adicionar', 'reg': r_c, 'ir_idx': 8})

        instrs.append({'tipo': 'ret'})
        return instrs

