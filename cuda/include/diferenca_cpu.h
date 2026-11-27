#pragma once

//diferença absoluta + limiar, pixel por pixel na cpu.
//mascara[i] = 255 se a diferença for maior que o limiar, 0 caso contrário
void diferenca_limiar_cpu(const unsigned char* referencia, const unsigned char* teste, unsigned char* mascara, int largura, int altura, int limiar);