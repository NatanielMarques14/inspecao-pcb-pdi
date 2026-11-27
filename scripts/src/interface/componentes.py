"""
Componentes visuais usados por mais de uma tela.
Responsável: Danilo

ATENÇÃO: as outras telas usam ler_imagem, VisualizadorImagem.mostrar e
VisualizadorImagem.limpar. Mudou algum desses nomes? Avise o grupo.
"""

from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


def ler_imagem(caminho):
    """Lê uma imagem do disco. Devolve None se não conseguir abrir.

    O cv2.imread falha com acentos no caminho (ex.: "Área de trabalho"),
    por isso lemos os bytes com o numpy e decodificamos depois.
    """
    caminho = Path(caminho)
    if not caminho.is_file():
        return None
    dados = np.fromfile(str(caminho), dtype=np.uint8)
    return cv2.imdecode(dados, cv2.IMREAD_COLOR) if dados.size else None


def cv_para_pixmap(imagem):
    """Converte uma imagem do OpenCV (colorida BGR ou em cinza) para QPixmap."""
    imagem = np.ascontiguousarray(imagem)
    if imagem.ndim == 2:
        altura, largura = imagem.shape
        qimagem = QImage(imagem.data, largura, altura, largura, QImage.Format_Grayscale8)
    else:
        rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
        altura, largura, _ = rgb.shape
        qimagem = QImage(rgb.data, largura, altura, 3 * largura, QImage.Format_RGB888)
    # copy(): a QImage passa a ter a própria memória (senão some junto com o array)
    return QPixmap.fromImage(qimagem.copy())


class VisualizadorImagem(QWidget):
    """Quadro com um título e uma imagem que se ajusta ao tamanho da janela."""

    def __init__(self, titulo, parent=None):
        super().__init__(parent)
        self.pixmap_original = None

        self.rotulo_titulo = QLabel(titulo)
        self.rotulo_titulo.setObjectName("tituloVisualizador")

        self.rotulo_imagem = QLabel()
        self.rotulo_imagem.setAlignment(Qt.AlignCenter)
        self.rotulo_imagem.setMinimumSize(240, 180)
        self.rotulo_imagem.setWordWrap(True)
        # Ignored: deixa o quadro encolher junto com a janela
        self.rotulo_imagem.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.rotulo_imagem.setObjectName("areaImagem")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.rotulo_titulo)
        layout.addWidget(self.rotulo_imagem, 1)
        self.limpar()

    def definir_titulo(self, titulo):
        self.rotulo_titulo.setText(titulo)

    def mostrar(self, imagem):
        """Exibe uma imagem do OpenCV no quadro."""
        self.pixmap_original = cv_para_pixmap(imagem)
        self._atualizar_escala()

    def limpar(self, mensagem="Nenhuma imagem carregada"):
        self.pixmap_original = None
        self.rotulo_imagem.clear()
        self.rotulo_imagem.setText(mensagem)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._atualizar_escala()

    def _atualizar_escala(self):
        # redimensiona mantendo a proporção da placa
        if self.pixmap_original is None:
            return
        self.rotulo_imagem.setPixmap(self.pixmap_original.scaled(
            self.rotulo_imagem.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
