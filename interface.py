import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Dict, Tuple
from norma import analisar_texto_programa, rodar_norma, nome_para_indice_registrador
from macro import ExpansorMacro


"""
Classe que representa a interface gráfica do usuário (GUI) do compilador. Feita usando a biblioteca tKinter
"""
class AppNorma:

    """
       Construtor da classe. Ele cria todos os elementos da interface (janelas, botões, caixas de texto) e define
       suas propriedades e posições
    """
    def __init__(self, root):
        self.root = root
        root.title("Simulador Máquina Norma")
        frm = tk.Frame(root)
        frm.pack(padx=8, pady=8, fill=tk.BOTH, expand=True)

        topo = tk.Frame(frm)
        topo.pack(fill=tk.X)

        tk.Label(topo, text="Número de registradores (N):").pack(side=tk.LEFT)
        self.entrada_N = tk.Entry(topo, width=4)
        self.entrada_N.insert(0, "2")
        self.entrada_N.pack(side=tk.LEFT, padx=4)

        tk.Label(topo, text="Valores iniciais (vírgula):").pack(side=tk.LEFT, padx=(10, 0))
        self.entrada_init = tk.Entry(topo, width=20)
        self.entrada_init.insert(0, "3,0")
        self.entrada_init.pack(side=tk.LEFT, padx=4)

        btn_carregar = tk.Button(topo, text="Carregar arquivo", command=self.carregar_arquivo)
        btn_carregar.pack(side=tk.RIGHT, padx=2)
        btn_rodar = tk.Button(topo, text="Rodar", command=self.rodar_programa)
        btn_rodar.pack(side=tk.RIGHT, padx=2)

        btn_ajuda = tk.Button(topo, text="❓ Ajuda", command=self.abrir_ajuda, bg="#eaf2f8", relief="groove")
        btn_ajuda.pack(side=tk.RIGHT, padx=2)

        corpo = tk.PanedWindow(frm, orient=tk.HORIZONTAL)
        corpo.pack(fill=tk.BOTH, expand=True, pady=8)

        frame_esquerda = tk.Frame(corpo)
        corpo.add(frame_esquerda, stretch="always")

        tk.Label(frame_esquerda, text="Programa (monolítico rotulado):").pack(anchor='w')
        self.texto_programa = scrolledtext.ScrolledText(frame_esquerda, width=60, height=25)
        self.texto_programa.pack(fill=tk.BOTH, expand=True)
        exemplo = """1: se zero_a então vá_para 9 senão vá_para 2 
2: faça sub_a vá_para 3 
3: faça add_b vá_para 1
"""
        self.texto_programa.insert(tk.END, exemplo)

        frame_direita = tk.Frame(corpo)
        corpo.add(frame_direita)

        tk.Label(frame_direita, text="Saída (computação completa):").pack(anchor='w')
        self.texto_saida = scrolledtext.ScrolledText(frame_direita, width=50, height=25)
        self.texto_saida.pack(fill=tk.BOTH, expand=True)


    """
    Função para criar as abas de ajuda
    """
    def abrir_ajuda(self):
        janela_ajuda = tk.Toplevel(self.root)
        janela_ajuda.title("❓ Ajuda / Dúvidas")
        janela_ajuda.geometry("850x450")
        janela_ajuda.configure(bg="#f0f4f7")

        style = ttk.Style()
        style.configure("TNotebook", tabposition="nw")
        style.configure("TNotebook.Tab", padding=[10, 5], font=("Arial", 10, "bold"))

        notebook = ttk.Notebook(janela_ajuda)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Função auxiliar para criar abas
        def criar_aba(titulo, conteudo):
            frame = tk.Frame(notebook, bg="white")
            notebook.add(frame, text=titulo)

            lbl_titulo = tk.Label(frame, text=titulo, font=("Arial", 14, "bold"), fg="#2c3e50", bg="white")
            lbl_titulo.pack(anchor="w", pady=(10, 5), padx=10)

            texto = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 11), bg="#fafafa", fg="#2c3e50")
            texto.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

            texto.insert(tk.END, conteudo)
            texto.config(state=tk.DISABLED)

        # Conteúdo que aparece na aba de ajuda
        conteudo1 = (
            "Como Usar o Compilador da Máquina Norma\n\n"

            "1. Configuração Inicial\n"
            "   • Defina o número de registradores (N)\n"
            "   • Informe os valores iniciais separados por vírgula\n"
            "   • Exemplo: 3,5,0 para 3 registradores com valores a=3, b=5, c=0\n\n"

            "2. Programação\n"
            "   • Escreva o programa no campo esquerdo\n"
            "   • Formato: rótulo: instrução\n"
            "   • Use instruções primitivas ou macros\n"
            "   • Exemplo: 1: se_zero_a então vá_para 5 senão vá_para 2\n\n"

            "3. Execução\n"
            "   • Clique em 'Rodar' para iniciar a simulação\n"
            "   • Acompanhe a computação passo a passo\n"
            "   • Verifique o estado final dos registradores\n\n"

            "4. Resultados\n"
            "   • Analise a saída completa no campo direito\n"
            "   • Cada linha mostra (rótulo atual, estado dos registradores)\n"
            "   • Identifique possíveis erros ou loops infinitos\n\n"

            "DICA: Você pode carregar programas salvos em arquivos .txt"
        )

        conteudo2 = (
            "Instruções Primitivas da Máquina Norma\n\n"

            "se_zero_X então vá_para L1 senão vá_para L2\n"
            "   • Funcionalidade: Testa se o registrador X é zero\n"
            "   • Comportamento: Se X = 0, salta para o rótulo L1; caso contrário, salta para L2\n"
            "   • Exemplo: 1: se_zero_a então vá_para 5 senão vá_para 2\n\n"

            "faça add_X vá_para L\n"
            "   • Funcionalidade: Incrementa o registrador X\n"
            "   • Comportamento: Adiciona 1 ao valor de X e salta para o rótulo L\n"
            "   • Exemplo: 2: faça add_b vá_para 3\n\n"

            "faça sub_X vá_para L\n"
            "   • Funcionalidade: Decrementa o registrador X\n"
            "   • Comportamento: Subtrai 1 de X (se X > 0) e salta para o rótulo L\n"
            "   • Exemplo: 3: faça sub_c vá_para 4\n\n"

            "OBS: Substitua X pelo registrador (a, b, c, ...) e L pelo rótulo desejado (1, 2, 3...)."
        )

        conteudo3 = (
            "Macros Disponíveis\n\n"

            "IGUAL a b c\n"
            "   • Número de registradores: 3 (a, b, c)\n"
            "   • Pré-condição: c deve iniciar com valor 0\n"
            "   • Sintaxe: 1: IGUAL a b c\n"
            "   • Funcionalidade: Se a == b, armazena 1 em c, senão 0\n\n"

            "MAIOR a b c d\n"
            "   • Número de registradores: 4 (a, b, c, d)\n"
            "   • Pré-condição: c e d devem iniciar com valor 0\n"
            "   • Sintaxe: 1: MAIOR a b c d\n"
            "   • Funcionalidade: Armazena o maior valor entre a e b em d\n\n"

            "MENOR a b c\n"
            "   • Número de registradores: 3 (a, b, c)\n"
            "   • Pré-condição: c deve iniciar com valor 0\n"
            "   • Sintaxe: 1: MENOR a b c\n"
            "   • Funcionalidade: Armazena o menor valor entre a e b em c\n\n"

            "OBS: As macros são traduzidas internamente em instruções primitivas."
        )

        criar_aba("Como usar", conteudo1)
        criar_aba("Primitivas", conteudo2)
        criar_aba("Macros", conteudo3)


    """
        Lida com a abertura e a leitura de arquivos de programa.
    """
    def carregar_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[('Arquivos de texto', '*.txt'), ('Todos os arquivos', '*.*')])
        if not caminho:
            return
        with open(caminho, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        self.texto_programa.delete('1.0', tk.END)
        self.texto_programa.insert('1.0', conteudo)

    """
    Converte código alto nível (com macros) em código que a máquina norma entende
    """
    def montar_programa_expandido(self, analisado: Dict[int, Tuple], N: int) -> Dict[int, Dict]:
        expansor = ExpansorMacro(base_rotulo_inicio=100000)     # Rótulo inicial que a macro irá aparecer
        programa_expandido = {}
        rotulos_orig = sorted(analisado.keys())

        for idx, rotulo in enumerate(rotulos_orig):
            no = analisado[rotulo]

            if no[0] != 'vazio' and not no[0].startswith('macro_'):
                tipo = no[0]
                if tipo == 'se_zero':
                    programa_expandido[rotulo] = {
                        'tipo': 'se_zero',
                        'reg': nome_para_indice_registrador(no[1]),
                        'entao': no[2],
                        'senao': no[3]
                    }
                elif tipo == 'adicionar':
                    programa_expandido[rotulo] = {
                        'tipo': 'adicionar',
                        'reg': nome_para_indice_registrador(no[1]),
                        'ir_para': no[2]
                    }
                elif tipo == 'subtrair':
                    programa_expandido[rotulo] = {
                        'tipo': 'subtrair',
                        'reg': nome_para_indice_registrador(no[1]),
                        'ir_para': no[2]
                    }
                else:
                    raise ValueError(f"Tipo pós-análise desconhecido: {no}")

            elif no[0].startswith('macro_'):
                bloco = expansor.expandir_macro(no, N)
                rotulos_bloco = [rotulo] + [expansor.novo_rotulo() for _ in range(len(bloco) - 1)]
                rotulo_seguinte = rotulos_orig[idx + 1] if (idx + 1) < len(rotulos_orig) else None
                r_rotulo_retorno = rotulo_seguinte if rotulo_seguinte is not None else (rotulo + 1)

                for i, instr_rel in enumerate(bloco):
                    instr = instr_rel.copy()

                    if instr.get('tipo') == 'se_zero':
                        ent_idx = instr.pop('entao_idx', None)
                        sen_idx = instr.pop('senao_idx', None)

                        def conv_index(v):
                            if v == 'ret' or v is None:
                                return r_rotulo_retorno
                            if v == 'error_div0':
                                return 99999998
                            if isinstance(v, int):
                                if 0 <= v < len(rotulos_bloco):
                                    return rotulos_bloco[v]
                                else:
                                    return r_rotulo_retorno
                            raise ValueError("índice desconhecido em se_zero: " + str(v))

                        instr['entao'] = conv_index(ent_idx)
                        instr['senao'] = conv_index(sen_idx)
                        instr['tipo'] = 'se_zero'

                    elif instr.get('tipo') in ('adicionar', 'subtrair'):
                        if 'ir_idx' in instr:
                            ir = instr.pop('ir_idx')
                            if isinstance(ir, int):
                                instr['ir_para'] = rotulos_bloco[ir] if 0 <= ir < len(
                                    rotulos_bloco) else r_rotulo_retorno
                            elif ir == 'ret' or ir is None:
                                instr['ir_para'] = r_rotulo_retorno
                            else:
                                instr['ir_para'] = r_rotulo_retorno
                        else:
                            instr['ir_para'] = instr.get('ir_para', r_rotulo_retorno)
                        instr['tipo'] = instr_rel['tipo']

                    elif instr.get('tipo') == 'ir_idx':
                        ir = instr.pop('ir_idx')
                        if isinstance(ir, int) and 0 <= ir < len(rotulos_bloco):
                            instr = {'tipo': 'ir_para', 'ir_para': rotulos_bloco[ir]}
                        else:
                            instr = {'tipo': 'ir_para', 'ir_para': r_rotulo_retorno}

                    elif instr.get('tipo') == 'ret':
                        instr = {'tipo': 'ir_para', 'ir_para': r_rotulo_retorno}

                    programa_expandido[rotulos_bloco[i]] = instr

        return programa_expandido

    """
    Coordena todo o processo: leitura --> compilação --> execução --> exibição
    """
    def rodar_programa(self):
        # Leitura e validação dos valores de entrada
        try:
            N = int(self.entrada_N.get().strip())
            if N <= 0:
                raise ValueError("N deve ser positivo")
        except Exception as e:
            messagebox.showerror("Erro", f"Valor de N inválido: {e}")
            return

        str_init = self.entrada_init.get().strip()
        try:
            vals_init = [int(x.strip()) for x in str_init.split(',') if x.strip() != '']
        except:
            messagebox.showerror("Erro", "Valores iniciais inválidos")
            return

        if len(vals_init) < N:
            vals_init += [0] * (N - len(vals_init))
        elif len(vals_init) > N:
            vals_init = vals_init[:N]

        # Chama analisar_texto_programa para converter o código digitado em um dicionário.
        src = self.texto_programa.get('1.0', tk.END)
        try:
            analisado = analisar_texto_programa(src)
        except Exception as e:
            messagebox.showerror("Erro na análise", str(e))
            return

        # Expande todas as macros no programa.
        try:
            programa_expandido = self.montar_programa_expandido(analisado, N)
        except Exception as e:
            messagebox.showerror("Erro ao expandir macros", str(e))
            return

        if not programa_expandido:
            messagebox.showinfo("Execução", "Programa vazio.")
            return

        # Chama rodar_norma para simular a execução do programa já expandido.
        rotulo_inicial = min(programa_expandido.keys())
        regs = list(vals_init)
        historico_execucao, erro = rodar_norma(programa_expandido, rotulo_inicial, regs, max_passos=100000)

        # Formata o historico_execucao de execução para exibição e, se houver um erro, mostra uma mensagem de aviso.
        self.texto_saida.delete('1.0', tk.END)
        for passo in historico_execucao:
            lbl, estado = passo
            self.texto_saida.insert(tk.END, f"({lbl}, ({', '.join(str(x) for x in estado)}))\n")

        if erro:
            self.texto_saida.insert(tk.END, f"\nERRO: {erro}\n")
            messagebox.showwarning("Execução", "Execução terminou com erro (veja saída).")
        else:
            if historico_execucao:
                ultimo_lbl, ultimos_regs = historico_execucao[-1]
                self.texto_saida.insert(tk.END,
                                        f"\nFinal: ({ultimo_lbl}, ({', '.join(str(x) for x in ultimos_regs)}))\n")
            messagebox.showinfo("Execução", "Execução finalizada (veja saída).")
