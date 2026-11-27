#include "diferenca_cpu.h"
#include <cstdlib>

void diferenca_limiar_cpu(const unsigned char* referencia, const unsigned char* teste,
                          unsigned char* mascara, int largura, int altura, int limiar) {
    // percorre a imagem inteira, um pixel de cada vez
    for (int linha = 0; linha < altura; linha++) {
        for (int coluna = 0; coluna < largura; coluna++) {
            int i = linha * largura + coluna;   // posição do pixel na fila

            int diferenca = abs((int)referencia[i] - (int)teste[i]);

            if (diferenca > limiar)
                mascara[i] = 255;   // mudou: candidato a defeito
            else
                mascara[i] = 0;     // igual
        }
    }
}