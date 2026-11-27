"""
Versão inicial do processamento: compara a placa testada com a referência.
Responsável: Francisco (diferença, limiarização e morfologia)

Etapas:
1. Registro: alinha a testada sobre a referência (registro.py, do Danilo)
2. Pré-processamento: tons de cinza + suavização
3. Comparação: diferença absoluta + limiarização
4. Análise: abertura morfológica + componentes conexos
5. Classificação: ainda não implementada (todas as regiões ficam "não classificado")

O formato do dicionário devolvido está descrito no README (contrato entre as telas).
"""

import time

import cv2
import numpy as np

from . import registro

# valores iniciais dos parâmetros (a tela Etapas permite mudar)
LIMIAR_PADRAO = 40
TAMANHO_KERNEL_PADRAO = 3
AREA_MINIMA_PADRAO = 20


def para_cinza(imagem):
    if imagem.ndim == 2:
        return imagem
    return cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)


def alinhar_placas(imagem_referencia, imagem_teste):
    """Parte cara e que não depende dos parâmetros: dá para guardar e reaproveitar
    quando o usuário só muda o limiar, o kernel ou a área mínima."""
    inicio = time.perf_counter()
    alinhada, area_valida, homografia = registro.alinhar(imagem_referencia, imagem_teste)
    return {
        "alinhada": alinhada,
        "area_valida": area_valida,
        "angulo": registro.angulo_estimado(homografia),
        "tempo_segundos": time.perf_counter() - inicio,
    }


def executar(imagem_referencia, imagem_teste, alinhamento=None,
             limiar=LIMIAR_PADRAO,
             tamanho_kernel=TAMANHO_KERNEL_PADRAO,
             area_minima=AREA_MINIMA_PADRAO):
    inicio = time.perf_counter()

    # 1. Registro (se já veio pronto, reaproveita)
    if alinhamento is None:
        alinhamento = alinhar_placas(imagem_referencia, imagem_teste)
    alinhada = alinhamento["alinhada"]

    # 2. Pré-processamento
    cinza_referencia = para_cinza(imagem_referencia)
    cinza_teste = para_cinza(alinhada)
    suave_referencia = cv2.GaussianBlur(cinza_referencia, (5, 5), 0)
    suave_teste = cv2.GaussianBlur(cinza_teste, (5, 5), 0)

    # 3. Comparação
    diferenca = cv2.absdiff(suave_referencia, suave_teste)
    _, mascara = cv2.threshold(diferenca, limiar, 255, cv2.THRESH_BINARY)

    # ignora as bordas que ficaram vazias depois do alinhamento
    # (a erosão afasta um pouco da borda, onde a interpolação deixa resíduos)
    area_valida = cv2.erode(alinhamento["area_valida"], np.ones((15, 15), np.uint8))
    mascara = cv2.bitwise_and(mascara, area_valida)

    # 4. Análise: abertura remove pontinhos soltos de ruído
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (tamanho_kernel, tamanho_kernel))
    mascara_limpa = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)

    quantidade, _, estatisticas, centroides = cv2.connectedComponentsWithStats(mascara_limpa)
    regioes = []
    for indice in range(1, quantidade):  # o índice 0 é o fundo
        x, y, largura, altura, area = estatisticas[indice]
        if area < area_minima:
            continue
        regioes.append({
            "id": len(regioes) + 1,
            "x": int(x), "y": int(y),
            "largura": int(largura), "altura": int(altura),
            "area": int(area),
            "centro": (float(centroides[indice][0]), float(centroides[indice][1])),
            "tipo": "não classificado",  # 5. classificação: etapa futura
        })

    return {
        "imagem_teste": alinhada,
        "etapas": [
            ("Referência em cinza", cinza_referencia),
            ("Placa testada alinhada", alinhada),
            ("Diferença absoluta", diferenca),
            ("Máscara após limiar", mascara),
            ("Máscara após abertura", mascara_limpa),
        ],
        "regioes": regioes,
        "parametros": {"limiar": limiar, "tamanho_kernel": tamanho_kernel, "area_minima": area_minima},
        "angulo_estimado": alinhamento["angulo"],
        # tempo total da inspeção, contando o alinhamento (mesmo se foi reaproveitado)
        "tempo_segundos": time.perf_counter() - inicio + alinhamento["tempo_segundos"],
    }
