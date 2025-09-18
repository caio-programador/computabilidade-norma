from tkinter import filedialog, messagebox, scrolledtext
import tkinter as tk

from macro import MacroExpander
from norma import parse_program_text, regname_to_index, run_norma

class NormaApp:
    def __init__(self, root):
        self.root = root
        root.title("Simulador Máquina Norma - Tkinter")
        frm = tk.Frame(root)
        frm.pack(padx=8, pady=8, fill=tk.BOTH, expand=True)

        top = tk.Frame(frm)
        top.pack(fill=tk.X)

        tk.Label(top, text="Número de registradores (N):").pack(side=tk.LEFT)
        self.entry_N = tk.Entry(top, width=4)
        self.entry_N.insert(0, "2")
        self.entry_N.pack(side=tk.LEFT, padx=4)

        tk.Label(top, text="Valores iniciais (vírgula):").pack(side=tk.LEFT, padx=(10,0))
        self.entry_init = tk.Entry(top, width=20)
        self.entry_init.insert(0, "3,0")
        self.entry_init.pack(side=tk.LEFT, padx=4)

        btn_load = tk.Button(top, text="Load file", command=self.load_file)
        btn_load.pack(side=tk.RIGHT, padx=2)
        btn_run = tk.Button(top, text="Run", command=self.run_program)
        btn_run.pack(side=tk.RIGHT, padx=2)

        body = tk.PanedWindow(frm, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, pady=8)

        left_frame = tk.Frame(body)
        body.add(left_frame, stretch="always")

        tk.Label(left_frame, text="Programa (monolítico rotulado):").pack(anchor='w')
        self.program_text = scrolledtext.ScrolledText(left_frame, width=60, height=25)
        self.program_text.pack(fill=tk.BOTH, expand=True)
        # example program
        sample = """1: se zero_a então vá_para 9 senão vá_para 2
2: faça sub_a vá_para 3
3: faça add_b vá_para 1
"""
        self.program_text.insert(tk.END, sample)

        right_frame = tk.Frame(body)
        body.add(right_frame)

        tk.Label(right_frame, text="Saída (computação completa):").pack(anchor='w')
        self.output_text = scrolledtext.ScrolledText(right_frame, width=50, height=25)
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[('Text files','*.txt'),('All files','*.*')])
        if not path:
            return
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.program_text.delete('1.0', tk.END)
        self.program_text.insert('1.0', content)

    def run_program(self):
        try:
            N = int(self.entry_N.get().strip())
            if N <= 0:
                raise ValueError("N deve ser positivo")
        except Exception as e:
            messagebox.showerror("Erro", f"Valor de N inválido: {e}")
            return
        init_str = self.entry_init.get().strip()
        try:
            init_vals = [int(x.strip()) for x in init_str.split(',') if x.strip()!='']
        except:
            messagebox.showerror("Erro", "Valores iniciais inválidos")
            return
        # pad with zeros if needed
        if len(init_vals) < N:
            init_vals += [0]*(N - len(init_vals))
        elif len(init_vals) > N:
            messagebox.showwarning("Aviso", "Mais valores iniciais que N; extras serão ignorados")
            init_vals = init_vals[:N]

        src = self.program_text.get('1.0', tk.END)
        try:
            parsed = parse_program_text(src)
        except Exception as e:
            messagebox.showerror("Erro no parse", str(e))
            return

        # Expand macros with simplistic strategy: when macro encountered, replace with small block and assign new unique labels
        expander = MacroExpander(base_label_start=100000)
        expanded_program = {}
        # Keep ordering by original label insertion; when macro expands into K instructions, first uses original label, others get fresh ones
        for label in sorted(parsed.keys()):
            node = parsed[label]
            if node[0].startswith('macro_'):
                # expand block
                try:
                    block = expander.expand_macro(node, N)
                except Exception as e:
                    messagebox.showerror("Erro na macro", str(e))
                    return
                # assign labels
                labels = [label] + [expander.fresh_label() for _ in range(len(block)-1)]
                # Patch special_end -> map to "no-op" (i.e., end of macro returns to next label after this: we will take next program label or None)
                # To compute following_label: find next label in parsed after original label
                all_labels = sorted(parsed.keys())
                idx = all_labels.index(label)
                following_label = all_labels[idx+1] if idx+1 < len(all_labels) else None
                for i, instr in enumerate(block):
                    instr_copy = instr.copy()
                    # if instr has 'special_end', convert to goto following_label else if following_label None, it ends (no goto)
                    if instr_copy.get('special_end', False):
                        if following_label is not None:
                            instr_copy.pop('special_end', None)
                            instr_copy['type'] = 'goto'
                            instr_copy['goto'] = following_label
                        else:
                            # no following label: leave as a no-op that falls off end => we will not include an instruction that jumps
                            instr_copy.pop('special_end', None)
                            instr_copy['type'] = 'goto'
                            instr_copy['goto'] = 99999999  # a very big label -> will be treated as program end
                    # Convert any internal goto numeric indices (like 0,1,2 referencing block positions) into labels in 'labels' list:
                    # if 'goto' exists and refers to a small integer <= len(block)-1, map to labels[that index].
                    if 'goto' in instr_copy and isinstance(instr_copy['goto'], int):
                        target = instr_copy['goto']
                        if 0 <= target < len(labels):
                            instr_copy['goto'] = labels[target]
                        else:
                            # leave as-is (could be external label like 2 etc.)
                            pass
                    # also patch 'then'/'else' if they are small integers (from our macro templates)
                    if 'then' in instr_copy and isinstance(instr_copy['then'], int):
                        t = instr_copy['then']
                        if 0 <= t < len(labels):
                            instr_copy['then'] = labels[t]
                    if 'else' in instr_copy and isinstance(instr_copy['else'], int):
                        e = instr_copy['else']
                        if 0 <= e < len(labels):
                            instr_copy['else'] = labels[e]
                    # if it's a 'goto_block_idx' we patched earlier, ignore
                    # Save to expanded_program
                    expanded_program[labels[i]] = instr_copy
            else:
                # normal instr -> convert to concrete form
                if node[0] == 'if_zero':
                    expanded_program[label] = {'type':'if_zero', 'reg': regname_to_index(node[1]), 'then':node[2], 'else':node[3]}
                elif node[0] == 'add':
                    expanded_program[label] = {'type':'add', 'reg': regname_to_index(node[1]), 'goto':node[2]}
                elif node[0] == 'sub':
                    expanded_program[label] = {'type':'sub', 'reg': regname_to_index(node[1]), 'goto':node[2]}
                else:
                    messagebox.showerror("Erro", f"Tipo pós-parse desconhecido: {node}")
                    return

        # Now run VM starting at the smallest label present
        start_label = min(expanded_program.keys())
        regs = list(init_vals)
        # run
        trace, error = run_norma(expanded_program, start_label, regs, max_steps=50000)
        # Render output
        self.output_text.delete('1.0', tk.END)
        for step in trace:
            lbl, regs_state = step
            regs_str = ', '.join(str(x) for x in regs_state)
            self.output_text.insert(tk.END, f"({lbl}, ({regs_str}))\n")
        if error:
            self.output_text.insert(tk.END, f"\nERRO: {error}\n")
        else:
            # also print final state (if last label not shown)
            if trace:
                last_lbl, last_regs = trace[-1]
                self.output_text.insert(tk.END, f"\nFinal: ({last_lbl}, ({', '.join(str(x) for x in last_regs)}))\n")
        # also pop message when finished
        if error:
            messagebox.showwarning("Execução", "Execução terminou com erro (veja saída).")
        else:
            messagebox.showinfo("Execução", "Execução finalizada (veja saída).")
