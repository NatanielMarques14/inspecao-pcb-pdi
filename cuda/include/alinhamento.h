#pragma once
#include <opencv2/opencv.hpp>

// alinhamento das placas, devolve a testada alinhada e preenche area_valida (255 onde há foto e 0 nas bordas vazias)
cv::Mat alinhar(const cv::Mat& referencia, const cv::Mat& teste, cv::Mat& area_valida);