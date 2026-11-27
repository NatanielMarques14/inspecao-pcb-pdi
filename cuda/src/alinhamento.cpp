#include "alinhamento.h"
#include <iostream>

using namespace std;
using namespace cv;

Mat alinhar(const Mat& referencia, const Mat& teste, Mat& area_valida) {
    // 1.ORB: acha pontos marcantes e calcula a impressão digital de cada um
    Ptr<ORB> orb = ORB::create(5000);
    vector<KeyPoint> pontos_referencia, pontos_teste;
    Mat descritores_referencia, descritores_teste;
    orb->detectAndCompute(referencia, noArray(), pontos_referencia, descritores_referencia);
    orb->detectAndCompute(teste, noArray(), pontos_teste, descritores_teste);

    // 2.para cada ponto da testada, os 2 mais parecidos na referência
    BFMatcher casador(NORM_HAMMING);
    vector<vector<DMatch>> pares;
    casador.knnMatch(descritores_teste, descritores_referencia, pares, 2);

    // 3. Teste de Lowe: fica só com os pares em que o melhor é bem melhor que o segundo
    vector<Point2f> origem, destino;
    for (size_t i = 0; i < pares.size(); i++) {
        if (pares[i].size() == 2 && pares[i][0].distance < 0.75f * pares[i][1].distance) {
            origem.push_back(pontos_teste[pares[i][0].queryIdx].pt);
            destino.push_back(pontos_referencia[pares[i][0].trainIdx].pt);
        }
    }

    // 4.RANSAC: votação que descarta os pares errados e calcula a homografia
    Mat consistentes;
    Mat homografia = findHomography(origem, destino, RANSAC, 3.0, consistentes);

    // 5.aplica a homografia: deforma a testada até ela encaixar na referência
    Mat alinhada;
    warpPerspective(teste, alinhada, homografia, referencia.size());

    //a mesma deformação numa imagem toda branca mostra onde existe foto de verdade
    Mat branca(teste.size(), CV_8UC1, Scalar(255));
    warpPerspective(branca, area_valida, homografia, referencia.size());

    double angulo = atan2(homografia.at<double>(1, 0), homografia.at<double>(0, 0)) * 180.0 / CV_PI;
    cout << "Pares aprovados no teste de Lowe: " << origem.size() << endl;
    cout << "Pares consistentes (RANSAC):      " << countNonZero(consistentes) << endl;
    cout << "Rotacao corrigida: " << angulo << " graus" << endl;

    return alinhada;
}