"""
Ponto de entrada do sistema. Rode a partir da pasta do projeto:
    python main.py
"""

import sys

from PySide6.QtWidgets import QApplication

from scripts.src.interface.janela_principal import JanelaPrincipal

# visual simples: verde de máscara de solda como cor de destaque
ESTILO = """
QWidget { font-size: 10pt; }
QGroupBox { font-weight: bold; margin-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 6px; padding: 0 3px; }
QLabel#tituloVisualizador { font-weight: bold; padding: 2px 0; }
QLabel#areaImagem { border: 1px solid #a9b6b0; background: #eef2f0; color: #5d6a64; }
QLabel#textoSecundario { color: #5d6a64; }
QPushButton#botaoPrincipal { background: #1e6b52; color: white; padding: 6px 14px; border-radius: 3px; }
QPushButton#botaoPrincipal:disabled { background: #a9b6b0; }
"""


def main():
    aplicativo = QApplication(sys.argv)
    aplicativo.setStyleSheet(ESTILO)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(aplicativo.exec())


if __name__ == "__main__":
    main()
