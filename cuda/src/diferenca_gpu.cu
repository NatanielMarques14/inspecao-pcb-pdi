#include "diferenca_gpu.h"
#include <cuda_runtime.h>
#include <cstdlib>

// o kernel: o quê CADA thread executa
__global__ void kernel_diferenca_limiar(const unsigned char* referencia, const unsigned char* teste,
                                        unsigned char* mascara, int largura, int altura, int limiar) {
    // 1. cada thread descobre qual é o seu pixel
    int coluna = blockIdx.x * blockDim.x + threadIdx.x;
    int linha  = blockIdx.y * blockDim.y + threadIdx.y;

    // 2. threads que caíram fora da imagem não fazem nada
    if (coluna >= largura || linha >= altura)
        return;

    // 3. o mesmo miolo da versão da CPU, para um único pixel
    int i = linha * largura + coluna;
    int diferenca = abs((int)referencia[i] - (int)teste[i]);

    if (diferenca > limiar)
        mascara[i] = 255;
    else
        mascara[i] = 0;
}

//a função que roda na CPU e comanda a GPU
void diferenca_limiar_gpu(const unsigned char* referencia, const unsigned char* teste,
                          unsigned char* mascara, int largura, int altura, int limiar) {
    size_t bytes = (size_t)largura * altura * sizeof(unsigned char);

    // 1. reserva espaço na memória da GPU (d_ = device, a GPU)
    unsigned char *d_referencia, *d_teste, *d_mascara;
    cudaMalloc(&d_referencia, bytes);
    cudaMalloc(&d_teste, bytes);
    cudaMalloc(&d_mascara, bytes);

    // 2. copia as duas imagens da RAM para a GPU
    cudaMemcpy(d_referencia, referencia, bytes, cudaMemcpyHostToDevice);
    cudaMemcpy(d_teste, teste, bytes, cudaMemcpyHostToDevice);

    // 3. organiza as threads: blocos de 16 x 16 e quantos blocos cobrem a imagem
    dim3 threads(16, 16);
    dim3 blocos((largura + 15) / 16, (altura + 15) / 16);

    // 4. lança o kernel e espera todas as threads terminarem
    kernel_diferenca_limiar<<<blocos, threads>>>(d_referencia, d_teste, d_mascara, largura, altura, limiar);
    cudaDeviceSynchronize();

    // 5. copia a máscara de volta para a RAM
    cudaMemcpy(mascara, d_mascara, bytes, cudaMemcpyDeviceToHost);

    // 6. libera a memória da GPU
    cudaFree(d_referencia);
    cudaFree(d_teste);
    cudaFree(d_mascara);
}