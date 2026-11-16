# reconhecer.py - módulo principal: identifica rostos em tempo real e libera ou nega acesso
# Uso: python reconhecer.py   (tecle Q ou feche a janela para sair)

import sys
import time

import cv2
import numpy as np
import face_recognition

import acao
import banco
import config
from config import CAMERA_INDEX, TOLERANCIA, ESCALA

# Segundos sem aparecer para a pessoa ser considerada "saiu". Quando volta, conta como nova entrada.
SEGUNDOS_AUSENCIA = getattr(config, "SEGUNDOS_AUSENCIA", 3)
# De quanto em quanto tempo relê o banco. Assim, bloquear, excluir ou cadastrar pelo painel
# vale na hora, sem precisar reiniciar o reconhecimento.
SEGUNDOS_RECARREGAR = getattr(config, "SEGUNDOS_RECARREGAR", 5)

ultima_vez_visto = {}  # chave (id do usuário ou "desconhecido") -> horário em que apareceu pela última vez


def janela_aberta(nome):
    """True enquanto a janela existir. Se o usuário fechar no X, devolve False
    (dependendo da versão do OpenCV, fechar a janela gera erro ou valor < 1)."""
    try:
        return cv2.getWindowProperty(nome, cv2.WND_PROP_VISIBLE) >= 1
    except cv2.error:
        return False


def entrou(chave):
    """True só quando a pessoa ENTRA na imagem (ou volta depois de sumir por alguns segundos).
    Evita registrar e abrir a porta dezenas de vezes enquanto ela fica parada na frente da câmera."""
    agora = time.time()
    nova_entrada = agora - ultima_vez_visto.get(chave, 0) > SEGUNDOS_AUSENCIA
    ultima_vez_visto[chave] = agora
    return nova_entrada


def main():
    ids, nomes, vetores = banco.carregar_encodings()
    if not vetores:
        print("[AVISO] Nenhum rosto ativo cadastrado: todos serão tratados como desconhecidos.")

    camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        print("Não foi possível abrir a câmera.")
        return False

    acao.preparar()
    ultimo_reload = time.time()
    fator = int(1 / ESCALA)   # para voltar as coordenadas ao tamanho original
    resultados = []           # último resultado, reaproveitado nos frames pulados
    processar = True          # processa 1 frame sim, 1 não (deixa o vídeo mais fluido)

    while True:
        ok, frame = camera.read()
        if not ok:
            break

        if time.time() - ultimo_reload >= SEGUNDOS_RECARREGAR:
            ultimo_reload = time.time()
            try:
                ids, nomes, vetores = banco.carregar_encodings()
            except Exception as erro:  # mantém a lista anterior se o banco falhar
                print(f"[AVISO] Não foi possível atualizar os rostos: {erro}")

        if processar:
            # 1) Reduz a imagem e converte de BGR (OpenCV) para RGB (face_recognition)
            pequeno = cv2.resize(frame, (0, 0), fx=ESCALA, fy=ESCALA)
            rgb = np.ascontiguousarray(cv2.cvtColor(pequeno, cv2.COLOR_BGR2RGB))

            # 2) Detecta onde estão os rostos e gera o vetor de cada um
            locais = face_recognition.face_locations(rgb)
            encodings = face_recognition.face_encodings(rgb, locais)

            resultados = []
            for local, vetor in zip(locais, encodings):
                # 3) Compara com todos os rostos cadastrados e pega o mais parecido
                if vetores:
                    distancias = face_recognition.face_distance(vetores, vetor)
                    melhor = int(np.argmin(distancias))
                    distancia = float(distancias[melhor])
                else:  # ninguém ativo no banco
                    melhor, distancia = None, None

                # 4) Decide: abaixo da tolerância = reconhecido
                if melhor is not None and distancia <= TOLERANCIA:
                    usuario_id, nome, resultado = ids[melhor], nomes[melhor], "liberado"
                else:
                    usuario_id, nome, resultado = None, "Desconhecido", "negado"

                # 5) Quando a pessoa entra na imagem: registra no banco e executa a ação
                if entrou(usuario_id if usuario_id else "desconhecido"):
                    try:
                        banco.registrar_acesso(usuario_id, resultado, distancia)
                    except Exception as erro:  # banco fora do ar não derruba o reconhecimento
                        print(f"[AVISO] Não foi possível gravar o registro: {erro}")
                    if resultado == "liberado":
                        acao.liberar(nome)
                    else:
                        acao.negar()

                resultados.append((local, nome, resultado))
        processar = not processar

        # 6) Desenha as caixas (verde = liberado, vermelho = negado) e prepara os nomes
        rotulos = []
        for (topo, direita, base, esquerda), nome, resultado in resultados:
            cor = (0, 200, 0) if resultado == "liberado" else (0, 0, 220)
            topo, direita, base, esquerda = (v * fator for v in (topo, direita, base, esquerda))
            cv2.rectangle(frame, (esquerda, topo), (direita, base), cor, 2)
            cv2.rectangle(frame, (esquerda, base - 28), (direita, base), cor, cv2.FILLED)
            rotulos.append((nome, (esquerda + 6, base - 25)))

        # 7) Faixa de status com o cadeado + nomes (aceita acentos)
        acao.desenhar(frame, rotulos)

        cv2.imshow("Controle de Acesso", frame)
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord("q") or not janela_aberta("Controle de Acesso"):
            break

    camera.release()
    cv2.destroyAllWindows()
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
