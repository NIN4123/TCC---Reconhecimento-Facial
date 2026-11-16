# iniciar.pyw - abre uma janela com botões, sem mostrar o terminal (cmd).
# Como usar: dê duplo clique neste arquivo (ou use o atalho descrito na conversa).

import os
import subprocess
import sys
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

# Procura a pasta do projeto: primeiro ao lado deste arquivo, depois em C:\Users\<você>\FaceRecognition.
# Assim o iniciar.pyw pode ficar na área de trabalho sem quebrar.
_AQUI = os.path.dirname(os.path.abspath(__file__))
_CANDIDATAS = [_AQUI, os.path.join(os.path.expanduser("~"), "FaceRecognition")]
PASTA = next((p for p in _CANDIDATAS if os.path.exists(os.path.join(p, "reconhecer.py"))), _AQUI)
LOG = os.path.join(PASTA, "saida.log")  # tudo que antes aparecia no terminal vai para cá

# As bibliotecas estão instaladas no Python 3.11, então usamos o pythonw dele (sem terminal).
PY311 = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python311", "pythonw.exe")
PYTHON = PY311 if os.path.exists(PY311) else sys.executable
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def ultima_linha_do_log(arquivo=None):
    try:
        with open(arquivo or LOG, encoding="utf-8", errors="replace") as f:
            linhas = [l.strip() for l in f if l.strip()]
        return linhas[-1] if linhas else ""
    except OSError:
        return ""


def executar(script, *args, ao_terminar):
    """Roda um script em segundo plano e chama ao_terminar(codigo_de_saida) quando acabar."""
    botoes_estado("disabled")
    log = open(LOG, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [PYTHON, "-u", os.path.join(PASTA, script), *args],
        cwd=PASTA, stdout=log, stderr=log, creationflags=SEM_JANELA,
    )

    def verificar():
        if proc.poll() is None:
            janela.after(300, verificar)
        else:
            log.close()
            botoes_estado("normal")
            ao_terminar(proc.returncode)

    verificar()


def botoes_estado(estado):
    btn_cadastrar.config(state=estado)
    btn_reconhecer.config(state=estado)


painel_proc = None
PAINEL_LOG = os.path.join(PASTA, "painel.log")
sys.path.insert(0, PASTA)
try:
    import config
    PORTA_PAINEL = getattr(config, "PORTA_PAINEL", 5000)
except Exception:
    PORTA_PAINEL = 5000
PAINEL_URL = f"http://127.0.0.1:{PORTA_PAINEL}"


def abrir_painel():
    """Liga o backend (app.py) em segundo plano, sem terminal, e abre o painel no navegador."""
    global painel_proc
    if painel_proc is not None and painel_proc.poll() is None:
        webbrowser.open(PAINEL_URL)
        return
    log = open(PAINEL_LOG, "w", encoding="utf-8")
    painel_proc = subprocess.Popen([PYTHON, "-u", os.path.join(PASTA, "app.py")], cwd=PASTA,
                                   stdout=log, stderr=log, creationflags=SEM_JANELA)
    status.set("Iniciando o painel...")

    def abrir():
        if painel_proc.poll() is not None:
            messagebox.showerror("Painel", "O painel não iniciou.\n\n" + ultima_linha_do_log(PAINEL_LOG))
            status.set("O painel não iniciou.")
        else:
            webbrowser.open(PAINEL_URL)
            status.set("Painel aberto no navegador. Feche esta janela para desligá-lo.")

    janela.after(2000, abrir)


def fechar():
    if painel_proc is not None and painel_proc.poll() is None:
        painel_proc.terminate()
    janela.destroy()


def cadastrar():
    nome = campo_nome.get().strip()
    if not nome:
        messagebox.showwarning("Cadastro", "Digite o nome completo antes de cadastrar.")
        return
    status.set("Cadastro em andamento: olhe para a câmera e aperte ESPAÇO.")

    def fim(codigo):
        if codigo == 0:
            status.set(f"{nome} cadastrado(a) com sucesso.")
            campo_nome.delete(0, tk.END)
        else:
            status.set("Cadastro não concluído.")
            messagebox.showinfo("Cadastro", "Cadastro não concluído.\n\n" + ultima_linha_do_log())

    executar("cadastrar.py", nome, campo_perfil.get(), ao_terminar=fim)


def reconhecer():
    status.set("Reconhecimento ativo. Feche a janela da câmera ou aperte Q para voltar.")

    def fim(codigo):
        status.set("Reconhecimento encerrado.")
        if codigo != 0:
            messagebox.showerror("Reconhecimento", "O reconhecimento não pôde iniciar.\n\n" + ultima_linha_do_log())

    executar("reconhecer.py", ao_terminar=fim)


janela = tk.Tk()
janela.title("Controle de Acesso Facial")
janela.geometry("420x380")
janela.resizable(False, False)

quadro = ttk.Frame(janela, padding=20)
quadro.pack(fill="both", expand=True)

ttk.Label(quadro, text="Controle de Acesso Facial", font=("Segoe UI", 16, "bold")).pack(anchor="w")
ttk.Label(quadro, text="Cadastrar uma pessoa", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(16, 4))

campo_nome = ttk.Entry(quadro, width=45)
campo_nome.pack(anchor="w")
campo_perfil = ttk.Combobox(quadro, values=["aluno", "professor", "funcionario", "visitante"], state="readonly", width=20)
campo_perfil.set("aluno")
campo_perfil.pack(anchor="w", pady=6)

btn_cadastrar = ttk.Button(quadro, text="Cadastrar rosto", command=cadastrar)
btn_cadastrar.pack(anchor="w")

ttk.Separator(quadro).pack(fill="x", pady=14)
btn_reconhecer = ttk.Button(quadro, text="Iniciar reconhecimento", command=reconhecer)
btn_reconhecer.pack(anchor="w")
ttk.Button(quadro, text="Abrir painel administrativo", command=abrir_painel).pack(anchor="w", pady=(10, 0))

status = tk.StringVar(value="Pronto.")
ttk.Label(quadro, textvariable=status, wraplength=380, foreground="#444").pack(anchor="w", pady=(14, 0))

janela.protocol("WM_DELETE_WINDOW", fechar)
janela.mainloop()
