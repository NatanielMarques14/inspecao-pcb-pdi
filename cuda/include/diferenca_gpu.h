#pragma once

// diferença absoluta + limiar na GPU: mesma entrada e mesma saída da versão da CPU
void diferenca_limiar_gpu(const unsigned char* referencia, const unsigned char* teste,
                          unsigned char* mascara, int largura, int altura, int limiar);