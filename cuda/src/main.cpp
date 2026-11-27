#include <opencv2/opencv.hpp>
#include <iostream>
#include "alinhamento.h"
#include "diferenca_cpu.h"
#include "diferenca_gpu.h"

using namespace std;
using namespace cv;

int main(int argc, char** argv) {
    // argv[1]: placa de referência   argv[2]: placa testada
    Mat referencia = imread(argv[1]);
    Mat teste = imread(argv[2]);

    cout << "Referencia: " << referencia.cols << " x " << referencia.rows << endl;
    cout << "Testada:    " << teste.cols << " x " << teste.rows << endl;

    // converte para tons de cinza (um número de 0 a 255 por pixel)
    Mat cinza_referencia, cinza_teste;
    cvtColor(referencia, cinza_referencia, COLOR_BGR2GRAY);
    cvtColor(teste, cinza_teste, COLOR_BGR2GRAY);
    
    // alinha a testada com a referência, devolvendo a área válida da testada
    Mat area_valida;
    Mat alinhada = alinhar(cinza_referencia, cinza_teste, area_valida);
    
    // salva os resultados em disco
    imwrite("../resultados/cuda/1_cinza_referencia.png", cinza_referencia);
    imwrite("../resultados/cuda/2_alinhada.png", alinhada);
    imwrite("../resultados/cuda/2_area_valida.png", area_valida);

    // sobreposição para conferir o alinhamento: referência em vermelho, testada em ciano
    // antes: a testada sem alinhar, recortada no tamanho da referência
    Mat sem_alinhar = cinza_teste(Rect(0, 0, cinza_referencia.cols, cinza_referencia.rows));
    Mat canais_antes[3] = {sem_alinhar, sem_alinhar, cinza_referencia};   // B, G, R
    Mat sobreposicao_antes;
    merge(canais_antes, 3, sobreposicao_antes);
    imwrite("../resultados/cuda/2_sobreposicao_antes.png", sobreposicao_antes);

    // depois: a testada alinhada
    Mat canais_depois[3] = {alinhada, alinhada, cinza_referencia};
    Mat sobreposicao_depois;
    merge(canais_depois, 3, sobreposicao_depois);
    imwrite("../resultados/cuda/2_sobreposicao_depois.png", sobreposicao_depois);

    //diferença + limiar na cpu

    int limiar = 20;
    if (argc > 3) limiar = atoi(argv[3]);

    // suavização: reduz o ruído da câmera antes de comparar
    Mat suave_referencia, suave_teste;
    GaussianBlur(cinza_referencia, suave_referencia, Size(3, 3), 0);
    GaussianBlur(alinhada, suave_teste, Size(3, 3), 0);

    // máscara do mesmo tamanho, 1 canal de 8 bits (CV_8UC1)
    Mat mascara_cpu(suave_referencia.rows, suave_referencia.cols, CV_8UC1);

    diferenca_limiar_cpu(suave_referencia.data, suave_teste.data, mascara_cpu.data,
                         suave_referencia.cols, suave_referencia.rows, limiar);

    // ignora as bordas sem foto (área válida da etapa 2)
    bitwise_and(mascara_cpu, area_valida, mascara_cpu);

    cout << "Pixels marcados (CPU): " << countNonZero(mascara_cpu) << endl;
    imwrite("../resultados/cuda/3_mascara_cpu.png", mascara_cpu);

    
    // a mesma conta na GPU
    Mat mascara_gpu(suave_referencia.rows, suave_referencia.cols, CV_8UC1);

    diferenca_limiar_gpu(suave_referencia.data, suave_teste.data, mascara_gpu.data,
                         suave_referencia.cols, suave_referencia.rows, limiar);

    bitwise_and(mascara_gpu, area_valida, mascara_gpu);

    cout << "Pixels marcados (GPU): " << countNonZero(mascara_gpu) << endl;
    imwrite("../resultados/cuda/4_mascara_gpu.png", mascara_gpu);

    // conferência: quantos pixels a CPU e a GPU calcularam diferente
    int pixels_diferentes = countNonZero(mascara_cpu != mascara_gpu);
    cout << "Pixels diferentes entre CPU e GPU: " << pixels_diferentes << endl;


    Mat diferenca;
    absdiff(suave_referencia, suave_teste, diferenca);

    double menor, maior;
    minMaxLoc(diferenca, &menor, &maior);
    cout << "Maior diferenca na imagem: " << maior << " (limiar usado: " << limiar << ")" << endl;

    // só para visualizar: estica os valores para ocupar de 0 a 255
    Mat diferenca_visual;
    normalize(diferenca, diferenca_visual, 0, 255, NORM_MINMAX);
    imwrite("../resultados/cuda/3_diferenca.png", diferenca_visual);




    return 0;
}