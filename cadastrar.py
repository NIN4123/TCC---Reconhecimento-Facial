# cadastrar.py - cadastra uma pessoa nova capturando o rosto pela webcam
# Uso: python cadastrar.py

import sys

import cv2
import face_recognition

import banco
from config import CAMERA_INDEX, AMOSTRAS_CADASTRO


def janela_aberta(nome):
    """True enquanto a janela existir. Se o usuário fechar no X, devolve False
    (dependendo da versão do OpenCV, fechar a janela gera erro ou valor < 1)."""
    try:
        return cv2.getWindowProperty(nome, cv2.WND_PROP_VISIBLE) >= 1
    except cv2.error:
        return False


def main():
    if len(sys.argv) >= 3:   # chamado pelo iniciar.pyw (sem terminal)
        nome, perfil = sys.argv[1].strip(), sys.argv[2].strip() or "aluno"
    else:
        nome = input("Nome completo: ").strip()
        perfil = input("Perfil (aluno/professor/funcionario/visitante) [aluno]: ").strip() or "aluno"
    if not nome:
        print("O nome é obrigatório.")
        return False

    camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        print("Não foi possível abrir a câmera.")
        return False

    encodings = []
    print("Olhe para a câmera. ESPACO captura uma foto, Q cancela.")
    print("Dica: varie um pouco o ângulo da cabeça entre as capturas.")

    while len(encodings) < AMOSTRAS_CADASTRO:
        ok, frame = camera.read()
        if not ok:
            break

        # Detecção na imagem reduzida (só para o preview ficar fluido)
        pequeno = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_pequeno = cv2.cvtColor(pequeno, cv2.COLOR_BGR2RGB)
        for (topo, direita, base, esquerda) in face_recognition.face_locations(rgb_pequeno):
            cv2.rectangle(frame, (esquerda * 2, topo * 2), (direita * 2, base * 2), (0, 255, 0), 2)

        # Obs.: o OpenCV não desenha acentos no texto da janela
        cv2.putText(frame, f"Amostras: {len(encodings)}/{AMOSTRAS_CADASTRO}  |  ESPACO = capturar  |  Q = sair",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow("Cadastro", frame)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord("q") or not janela_aberta("Cadastro"):
            break
        if tecla == 32:  # barra de espaço
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locais = face_recognition.face_locations(rgb)
            if len(locais) != 1:
                print(f"Foram encontrados {len(locais)} rostos. É preciso exatamente 1.")
                continue
            encodings.append(face_recognition.face_encodings(rgb, locais)[0])
            print(f"Amostra {len(encodings)}/{AMOSTRAS_CADASTRO} capturada.")

    camera.release()
    cv2.destroyAllWindows()

    if len(encodings) < AMOSTRAS_CADASTRO:
        print("Cadastro cancelado. Nada foi salvo.")
        return False

    usuario_id = banco.criar_usuario(nome, perfil)
    for vetor in encodings:
        banco.salvar_encoding(usuario_id, vetor)
    print(f"{nome} cadastrado(a) com sucesso (id {usuario_id}).")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
