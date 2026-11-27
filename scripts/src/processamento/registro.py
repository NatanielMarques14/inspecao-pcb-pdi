"""
Identificação da placa e registro (alinhamento) entre a placa testada e a referência.
Responsável: Danilo

As duas tarefas usam a mesma ideia:
1. achar pontos característicos (ORB) nas duas imagens;
2. casar os pontos parecidos;
3. com RANSAC, ficar só com os casamentos que concordam com uma mesma
   transformação geométrica (homografia).

- Identificar: a referência com mais casamentos consistentes é a placa certa.
- Alinhar: a homografia encontrada leva a placa testada para cima da referência.

Para ficar rápido, os pontos são calculados numa versão reduzida da imagem e a
transformação é ajustada para o tamanho real. A identificação só precisa saber
"qual placa é", então usa uma versão bem pequena; o alinhamento precisa de
precisão de pixel, então usa uma versão maior e mais pontos.
"""

import cv2
import numpy as np

# identificação: rápida, só precisa reconhecer a placa
TAMANHO_IDENTIFICACAO = 1000    # lado maior da imagem reduzida, em pixels
PONTOS_IDENTIFICACAO = 3000     # quantidade de pontos ORB
MINIMO_CORRESPONDENCIAS = 40    # abaixo disso: "referência não encontrada"

# alinhamento: mais lento, mas com precisão de pixel
# (com 1000 px, sobravam erros de 1-2 px nas bordas das trilhas, que viravam falsos defeitos)
TAMANHO_ALINHAMENTO = 2000
PONTOS_ALINHAMENTO = 5000
LIMIAR_RANSAC = 3.0             # erro máximo (px) para um par contar como consistente


def calcular_pontos(imagem, tamanho=TAMANHO_IDENTIFICACAO, quantidade=PONTOS_IDENTIFICACAO):
    """Calcula os pontos ORB de uma imagem.

    Devolve um dicionário com os pontos, os descritores e a escala usada,
    para poder ser guardado e reaproveitado (as referências são calculadas uma vez só).
    """
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY) if imagem.ndim == 3 else imagem
    escala = tamanho / max(cinza.shape[:2])
    if escala < 1:
        cinza = cv2.resize(cinza, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)
    else:
        escala = 1.0

    orb = cv2.ORB_create(nfeatures=quantidade)
    pontos, descritores = orb.detectAndCompute(cinza, None)
    return {"pontos": pontos, "descritores": descritores, "escala": escala}


def estimar_homografia(pontos_teste, pontos_referencia):
    """Casa os pontos e estima a homografia (testada -> referência), já no tamanho real.

    Devolve (homografia, quantidade de casamentos consistentes).
    """
    if pontos_teste["descritores"] is None or pontos_referencia["descritores"] is None:
        return None, 0

    # Hamming é a distância certa para descritores binários como o ORB
    casador = cv2.BFMatcher(cv2.NORM_HAMMING)
    pares = casador.knnMatch(pontos_teste["descritores"], pontos_referencia["descritores"], k=2)

    # teste de Lowe: só aceita o casamento se ele for bem melhor que o segundo colocado
    bons = [m for m, n in (p for p in pares if len(p) == 2) if m.distance < 0.75 * n.distance]
    if len(bons) < 4:  # a homografia precisa de pelo menos 4 pares
        return None, len(bons)

    origem = np.float32([pontos_teste["pontos"][m.queryIdx].pt for m in bons])
    destino = np.float32([pontos_referencia["pontos"][m.trainIdx].pt for m in bons])

    # coordenadas da imagem reduzida -> coordenadas da imagem real
    origem /= pontos_teste["escala"]
    destino /= pontos_referencia["escala"]

    homografia, inliers = cv2.findHomography(origem, destino, cv2.RANSAC, LIMIAR_RANSAC)
    if homografia is None:
        return None, 0
    return homografia, int(inliers.sum())


def identificar_referencia(imagem_teste, referencias):
    """Procura qual referência cadastrada corresponde à placa testada.

    `referencias` é uma lista de dicionários com pelo menos "nome" e "pontos"
    (o resultado de calcular_pontos). Devolve (indice ou None, pontuações),
    onde pontuações é a quantidade de casamentos consistentes com cada referência.
    """
    pontos_teste = calcular_pontos(imagem_teste)
    pontuacoes = [estimar_homografia(pontos_teste, ref["pontos"])[1] for ref in referencias]

    if not pontuacoes or max(pontuacoes) < MINIMO_CORRESPONDENCIAS:
        return None, pontuacoes
    return int(np.argmax(pontuacoes)), pontuacoes


def alinhar(imagem_referencia, imagem_teste):
    """Deforma a placa testada até ela ficar sobre a referência.

    Devolve (testada alinhada, máscara da área válida, homografia).
    A máscara marca com 255 a parte da imagem alinhada que veio de fato da foto;
    o resto (bordas que ficaram vazias depois de girar) não deve ser comparado.
    """
    pontos_teste = calcular_pontos(imagem_teste, TAMANHO_ALINHAMENTO, PONTOS_ALINHAMENTO)
    pontos_referencia = calcular_pontos(imagem_referencia, TAMANHO_ALINHAMENTO, PONTOS_ALINHAMENTO)
    homografia, _ = estimar_homografia(pontos_teste, pontos_referencia)
    altura, largura = imagem_referencia.shape[:2]

    if homografia is None:
        # sem alinhamento possível: só deixa do mesmo tamanho para não quebrar o resto
        alinhada = cv2.resize(imagem_teste, (largura, altura))
        return alinhada, np.full((altura, largura), 255, np.uint8), None

    alinhada = cv2.warpPerspective(imagem_teste, homografia, (largura, altura))
    area_valida = cv2.warpPerspective(
        np.full(imagem_teste.shape[:2], 255, np.uint8), homografia, (largura, altura)
    )
    return alinhada, area_valida, homografia


def angulo_estimado(homografia):
    """Ângulo de rotação (em graus) contido na homografia. Útil para conferir com os
    arquivos *_angles.txt do dataset."""
    if homografia is None:
        return None
    return float(np.degrees(np.arctan2(homografia[1, 0], homografia[0, 0])))
