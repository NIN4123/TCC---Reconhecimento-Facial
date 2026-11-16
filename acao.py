# acao.py - o que acontece quando o acesso é liberado ou negado.
# É o único arquivo que precisaria mudar para ligar uma fechadura de verdade (Arduino etc.).

import os
import time
import webbrowser
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config

PASTA = os.path.dirname(os.path.abspath(__file__))
AREA_RESTRITA = os.path.join(PASTA, "area_restrita")

# Configurações opcionais (podem ser colocadas no config.py; se não existirem, valem estes padrões)
ACAO_AO_LIBERAR = getattr(config, "ACAO_AO_LIBERAR", "pasta")   # "pasta", "painel" ou "nenhuma"
SEGUNDOS_STATUS = getattr(config, "SEGUNDOS_STATUS", 4)         # quanto tempo o cadeado fica aberto/vermelho
INTERVALO_ABRIR = getattr(config, "INTERVALO_ABRIR", 30)        # evita abrir a pasta várias vezes seguidas
SOM_ATIVO = getattr(config, "SOM_ATIVO", True)

# Cores em BGR (formato do OpenCV)
COR_FAIXA = {"trancado": (110, 110, 110), "aberto": (60, 150, 40), "negado": (40, 40, 200)}
TEXTO_FAIXA = {"trancado": "Aguardando...", "aberto": "ACESSO LIBERADO", "negado": "ACESSO NEGADO"}

_estado = {"tipo": "trancado", "nome": "", "desde": 0.0}
_ultima_abertura = 0.0
_fontes = {}


def preparar():
    """Cria a pasta da área restrita (com um documento de exemplo) se ainda não existir."""
    if ACAO_AO_LIBERAR == "pasta" and not os.path.isdir(AREA_RESTRITA):
        os.makedirs(AREA_RESTRITA)
        with open(os.path.join(AREA_RESTRITA, "Documento_confidencial.txt"), "w", encoding="utf-8") as f:
            f.write("ÁREA RESTRITA\n\n"
                    "Se você está lendo este arquivo, o reconhecimento facial liberou o seu acesso.\n")


def _som(tipo):
    if not SOM_ATIVO:
        return
    try:
        import winsound  # só existe no Windows
        alias = "SystemAsterisk" if tipo == "liberado" else "SystemHand"
        winsound.PlaySound(alias, winsound.SND_ALIAS | winsound.SND_ASYNC)  # ASYNC: não trava o vídeo
    except Exception:
        pass


def _abrir_conteudo():
    """Nível 2: 'desbloqueia' algo de verdade no computador."""
    try:
        if ACAO_AO_LIBERAR == "pasta":
            os.startfile(AREA_RESTRITA)
        elif ACAO_AO_LIBERAR == "painel":
            webbrowser.open(Path(PASTA, "painel", "painel.html").as_uri())
    except Exception as erro:
        print(f"[AVISO] Não foi possível abrir o conteúdo restrito: {erro}")


def liberar(nome):
    global _ultima_abertura
    _estado.update(tipo="aberto", nome=nome, desde=time.time())
    print(f"[PORTA ABERTA] Bem-vindo(a), {nome}!")
    _som("liberado")
    agora = time.time()
    if ACAO_AO_LIBERAR != "nenhuma" and agora - _ultima_abertura >= INTERVALO_ABRIR:
        _ultima_abertura = agora
        _abrir_conteudo()


def negar():
    _estado.update(tipo="negado", nome="", desde=time.time())
    print("[ACESSO NEGADO] Rosto não reconhecido.")
    _som("negado")


def estado_atual():
    """Depois de alguns segundos, o cadeado volta a ficar trancado."""
    if _estado["tipo"] != "trancado" and time.time() - _estado["desde"] > SEGUNDOS_STATUS:
        _estado.update(tipo="trancado", nome="")
    return _estado["tipo"]


def _fonte(tamanho):
    if tamanho not in _fontes:
        candidatas = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        for caminho in candidatas:
            if os.path.exists(caminho):
                _fontes[tamanho] = ImageFont.truetype(caminho, tamanho)
                break
        else:
            _fontes[tamanho] = ImageFont.load_default()
    return _fontes[tamanho]


def _cadeado(frame, cx, cy, k, aberto):
    """Desenha um cadeado branco com formas simples. k = escala (1.0 = ~40 px de altura)."""
    branco = (255, 255, 255)
    fundo = COR_FAIXA[estado_atual()]
    espessura = max(2, int(3 * k))
    raio = int(9 * k)
    corpo_topo = cy
    elevacao = int(8 * k) if aberto else 0
    centro_arco = (cx, cy - int(6 * k) - elevacao)

    cv2.ellipse(frame, centro_arco, (raio, raio), 0, 180, 360, branco, espessura, cv2.LINE_AA)
    cv2.line(frame, (cx - raio, centro_arco[1]), (cx - raio, corpo_topo), branco, espessura, cv2.LINE_AA)
    if not aberto:  # cadeado fechado tem as duas hastes; aberto tem a direita solta
        cv2.line(frame, (cx + raio, centro_arco[1]), (cx + raio, corpo_topo), branco, espessura, cv2.LINE_AA)

    cv2.rectangle(frame, (cx - int(14 * k), corpo_topo), (cx + int(14 * k), cy + int(22 * k)), branco, cv2.FILLED)
    cv2.circle(frame, (cx, cy + int(10 * k)), max(2, int(3 * k)), fundo, cv2.FILLED, cv2.LINE_AA)
    cv2.line(frame, (cx, cy + int(10 * k)), (cx, cy + int(17 * k)), fundo, max(1, int(2 * k)), cv2.LINE_AA)


def desenhar(frame, rotulos=()):
    """Desenha a faixa de status com o cadeado e os nomes sobre os rostos.
    rotulos = lista de (texto, (x, y)). Usa Pillow para o texto, então aceita acentos."""
    tipo = estado_atual()
    largura = frame.shape[1]
    cv2.rectangle(frame, (0, 0), (largura, 64), COR_FAIXA[tipo], cv2.FILLED)
    _cadeado(frame, 36, 26, 1.0, aberto=(tipo == "aberto"))

    itens = [(TEXTO_FAIXA[tipo], (76, 8 if _estado["nome"] else 18), 24)]
    if _estado["nome"] and tipo == "aberto":
        itens.append((_estado["nome"], (76, 36), 20))
    itens += [(texto, pos, 16) for texto, pos in rotulos]

    imagem = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    pincel = ImageDraw.Draw(imagem)
    for texto, pos, tamanho in itens:
        pincel.text(pos, texto, font=_fonte(tamanho), fill=(255, 255, 255))
    frame[:] = cv2.cvtColor(np.array(imagem), cv2.COLOR_RGB2BGR)
