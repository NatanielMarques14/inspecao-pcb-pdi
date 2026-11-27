"""
Tela "Etapas": mostra a imagem de cada etapa do processamento e os parâmetros ajustáveis.
Responsável: Francisco

Serve para entender por que uma região foi apontada (ex.: um alarme que na
verdade é reflexo de luz) e para calibrar a sensibilidade da inspeção.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ..processamento import pipeline

from .componentes import VisualizadorImagem


class AbaEtapas(QWidget):
    # avisa a janela principal que os parâmetros mudaram (para reprocessar)
    parametros_alterados = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.etapas = []  # lista de (nome, imagem) vinda do pipeline

        # --- Parâmetros ---
        self.campo_limiar = QSpinBox()
        self.campo_limiar.setRange(0, 255)
        self.campo_limiar.setValue(pipeline.LIMIAR_PADRAO)
        self.campo_limiar.setToolTip("Diferença mínima de intensidade para um pixel contar como alterado.")

        self.campo_kernel = QSpinBox()
        self.campo_kernel.setRange(1, 21)
        self.campo_kernel.setSingleStep(2)  # tamanho ímpar: 1, 3, 5...
        self.campo_kernel.setValue(pipeline.TAMANHO_KERNEL_PADRAO)
        self.campo_kernel.setToolTip("Tamanho do elemento estruturante da abertura morfológica.")

        self.campo_area_minima = QSpinBox()
        self.campo_area_minima.setRange(0, 10000)
        self.campo_area_minima.setSuffix(" px")
        self.campo_area_minima.setValue(pipeline.AREA_MINIMA_PADRAO)
        self.campo_area_minima.setToolTip("Regiões menores que isso são descartadas.")

        self.botao_aplicar = QPushButton("Aplicar e reprocessar")
        self.botao_aplicar.setObjectName("botaoPrincipal")
        self.botao_aplicar.setEnabled(False)
        self.botao_aplicar.clicked.connect(self.parametros_alterados.emit)

        grupo_parametros = QGroupBox("Parâmetros")
        formulario = QFormLayout(grupo_parametros)
        formulario.addRow("Limiar da diferença:", self.campo_limiar)
        formulario.addRow("Tamanho do kernel:", self.campo_kernel)
        formulario.addRow("Área mínima da região:", self.campo_area_minima)
        formulario.addRow(self.botao_aplicar)

        # --- Lista de etapas ---
        self.lista_etapas = QListWidget()
        self.lista_etapas.currentRowChanged.connect(self.mostrar_etapa)

        coluna = QVBoxLayout()
        coluna.addWidget(QLabel("Etapas do processamento"))
        coluna.addWidget(self.lista_etapas, 1)
        coluna.addWidget(grupo_parametros)
        painel_esquerdo = QWidget()
        painel_esquerdo.setLayout(coluna)
        painel_esquerdo.setMaximumWidth(320)

        # --- Imagem da etapa escolhida ---
        self.visualizador = VisualizadorImagem("Etapa selecionada")
        self.visualizador.limpar("Rode uma inspeção para ver as etapas")

        layout = QHBoxLayout(self)
        layout.addWidget(painel_esquerdo)
        layout.addWidget(self.visualizador, 1)

    def parametros(self):
        """Valores atuais, no formato que pipeline.executar recebe."""
        tamanho_kernel = self.campo_kernel.value()
        if tamanho_kernel % 2 == 0:  # garante ímpar se alguém digitar um número par
            tamanho_kernel += 1
        return {
            "limiar": self.campo_limiar.value(),
            "tamanho_kernel": tamanho_kernel,
            "area_minima": self.campo_area_minima.value(),
        }

    def mostrar_etapas(self, resultado):
        """Recebe o resultado do pipeline e preenche a lista."""
        linha_anterior = max(self.lista_etapas.currentRow(), 0)
        self.etapas = resultado["etapas"]

        self.lista_etapas.blockSignals(True)
        self.lista_etapas.clear()
        for numero, (nome, _) in enumerate(self.etapas, start=1):
            self.lista_etapas.addItem(f"{numero}. {nome}")
        self.lista_etapas.blockSignals(False)

        # continua na mesma etapa quando o usuário só mudou um parâmetro
        self.lista_etapas.setCurrentRow(min(linha_anterior, len(self.etapas) - 1))
        self.mostrar_etapa(self.lista_etapas.currentRow())
        self.botao_aplicar.setEnabled(True)

    def mostrar_etapa(self, linha):
        if 0 <= linha < len(self.etapas):
            nome, imagem = self.etapas[linha]
            self.visualizador.definir_titulo(nome)
            self.visualizador.mostrar(imagem)
