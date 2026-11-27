"""
Tela "Inspeção": o usuário abre a placa testada, o sistema identifica a
referência, mostra as duas lado a lado e inicia a inspeção.
Responsável: Danilo (é também onde o registro/alinhamento entra no fluxo)
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from src.processamento import registro

from .componentes import VisualizadorImagem, ler_imagem

FILTRO_IMAGENS = "Imagens (*.jpg *.jpeg *.JPG *.png *.bmp *.tif *.tiff)"
OPCAO_AUTOMATICA = "Identificar automaticamente"


class AbaInspecao(QWidget):
    # pede à janela principal para rodar a inspeção: (referência, testada)
    inspecao_solicitada = Signal(object, object)
    # pede à janela principal para abrir a tela de cadastro
    cadastro_solicitado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.imagem_teste = None
        self.imagem_referencia = None
        self.referencias = []          # lista vinda da tela Referências
        self.pontos_referencias = {}   # cache: caminho -> pontos ORB (calcula uma vez só)

        # --- Placa testada ---
        self.rotulo_arquivo = QLabel("Nenhum arquivo")
        botao_abrir = QPushButton("Abrir placa testada...")
        botao_abrir.clicked.connect(self.abrir_teste)
        grupo_teste = QGroupBox("1. Placa testada")
        linha_teste = QHBoxLayout(grupo_teste)
        linha_teste.addWidget(self.rotulo_arquivo, 1)
        linha_teste.addWidget(botao_abrir)

        # --- Referência ---
        self.combo_referencia = QComboBox()
        self.combo_referencia.addItem(OPCAO_AUTOMATICA)
        self.combo_referencia.currentIndexChanged.connect(self.escolher_referencia)
        self.rotulo_identificacao = QLabel("")
        self.rotulo_identificacao.setWordWrap(True)
        self.botao_cadastrar = QPushButton("Cadastrar referência")
        self.botao_cadastrar.clicked.connect(self.cadastro_solicitado.emit)
        self.botao_cadastrar.hide()

        grupo_referencia = QGroupBox("2. Placa de referência")
        coluna_referencia = QVBoxLayout(grupo_referencia)
        coluna_referencia.addWidget(self.combo_referencia)
        linha_aviso = QHBoxLayout()
        linha_aviso.addWidget(self.rotulo_identificacao, 1)
        linha_aviso.addWidget(self.botao_cadastrar)
        coluna_referencia.addLayout(linha_aviso)

        # --- Imagens lado a lado ---
        self.visualizador_referencia = VisualizadorImagem("Referência")
        self.visualizador_teste = VisualizadorImagem("Placa testada")
        imagens = QHBoxLayout()
        imagens.addWidget(self.visualizador_referencia)
        imagens.addWidget(self.visualizador_teste)

        # --- Ação ---
        self.botao_inspecionar = QPushButton("Inspecionar placa")
        self.botao_inspecionar.setObjectName("botaoPrincipal")
        self.botao_inspecionar.setEnabled(False)
        self.botao_inspecionar.clicked.connect(self.inspecionar)
        self.rotulo_situacao = QLabel("Abra a foto da placa que será inspecionada.")
        linha_acao = QHBoxLayout()
        linha_acao.addWidget(self.botao_inspecionar)
        linha_acao.addWidget(self.rotulo_situacao, 1)

        topo = QHBoxLayout()
        topo.addWidget(grupo_teste, 1)
        topo.addWidget(grupo_referencia, 1)

        layout = QVBoxLayout(self)
        layout.addLayout(topo)
        layout.addLayout(imagens, 1)
        layout.addLayout(linha_acao)

    # ---------- placa testada ----------

    def abrir_teste(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Abrir placa testada", "", FILTRO_IMAGENS)
        if not caminho:
            return
        imagem = ler_imagem(caminho)
        if imagem is None:
            QMessageBox.warning(self, "Imagem inválida", f"Não foi possível abrir:\n{caminho}")
            return
        self.carregar_teste(imagem, Path(caminho).name)

    def carregar_teste(self, imagem, nome_arquivo):
        self.imagem_teste = imagem
        self.rotulo_arquivo.setText(nome_arquivo)
        self.visualizador_teste.mostrar(imagem)
        self.escolher_referencia()

    # ---------- referência ----------

    def escolher_referencia(self, *_):
        """Automático: procura a referência pela imagem. Manual: usa a escolhida."""
        if self.combo_referencia.currentIndex() <= 0:
            self.identificar()
        else:
            referencia = self.referencias[self.combo_referencia.currentIndex() - 1]
            self._definir_referencia(ler_imagem(referencia["caminho"]),
                                     f"Referência escolhida manualmente: {referencia['nome']}.")

    def identificar(self):
        if self.imagem_teste is None:
            return
        if not self.referencias:
            self._referencia_nao_encontrada("Nenhuma referência cadastrada.")
            return

        self.rotulo_identificacao.setText("Identificando a placa...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            candidatas = [{"nome": r["nome"], "pontos": self._pontos_da_referencia(r)} for r in self.referencias]
            indice, pontuacoes = registro.identificar_referencia(self.imagem_teste, candidatas)
        finally:
            QApplication.restoreOverrideCursor()

        if indice is None:
            melhor = max(pontuacoes) if pontuacoes else 0
            self._referencia_nao_encontrada(
                f"Referência não encontrada (melhor correspondência: {melhor} pontos; "
                f"mínimo: {registro.MINIMO_CORRESPONDENCIAS}).")
            return

        referencia = self.referencias[indice]
        self._definir_referencia(
            ler_imagem(referencia["caminho"]),
            f"Placa identificada: {referencia['nome']} ({pontuacoes[indice]} pontos em comum).")

    def _pontos_da_referencia(self, referencia):
        # calcula os pontos de cada referência só na primeira vez
        caminho = referencia["caminho"]
        if caminho not in self.pontos_referencias:
            self.pontos_referencias[caminho] = registro.calcular_pontos(ler_imagem(caminho))
        return self.pontos_referencias[caminho]

    def _definir_referencia(self, imagem, mensagem):
        self.imagem_referencia = imagem
        self.rotulo_identificacao.setStyleSheet("")
        self.rotulo_identificacao.setText(mensagem)
        self.botao_cadastrar.hide()
        self.visualizador_referencia.mostrar(imagem)
        self._atualizar_botao()

    def _referencia_nao_encontrada(self, mensagem):
        self.imagem_referencia = None
        self.rotulo_identificacao.setStyleSheet("color: #b3261e; font-weight: bold;")
        self.rotulo_identificacao.setText(mensagem)
        self.botao_cadastrar.show()
        self.visualizador_referencia.limpar("Referência não encontrada")
        self._atualizar_botao()

    def _atualizar_botao(self):
        pronto = self.imagem_referencia is not None and self.imagem_teste is not None
        self.botao_inspecionar.setEnabled(pronto)
        if pronto:
            self.mostrar_situacao("Pronto para inspecionar.")

    # ---------- chamados pela janela principal ----------

    def atualizar_referencias(self, referencias):
        """Recebe a lista de referências cadastradas: [{"nome", "caminho"}, ...]."""
        self.referencias = referencias
        caminhos = {r["caminho"] for r in referencias}
        self.pontos_referencias = {c: p for c, p in self.pontos_referencias.items() if c in caminhos}

        self.combo_referencia.blockSignals(True)
        self.combo_referencia.clear()
        self.combo_referencia.addItem(OPCAO_AUTOMATICA)
        for referencia in referencias:
            self.combo_referencia.addItem(referencia["nome"])
        self.combo_referencia.blockSignals(False)

        # se havia uma placa esperando referência, tenta de novo
        if self.imagem_teste is not None and self.imagem_referencia is None:
            self.identificar()

    def mostrar_situacao(self, texto):
        self.rotulo_situacao.setText(texto)

    def inspecionar(self):
        self.mostrar_situacao("Processando...")
        self.inspecao_solicitada.emit(self.imagem_referencia, self.imagem_teste)
