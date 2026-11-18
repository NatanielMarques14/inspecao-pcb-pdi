"""
Janela principal: junta as quatro telas e faz a comunicação entre elas.

Fluxo (ver docs/fluxograma.svg):
  Referências --(lista de placas)--> Inspeção
  Inspeção --(referência, testada)--> janela --> pipeline --> Etapas e Resultados
  Inspeção --("referência não encontrada")--> abre a tela Referências
  Etapas --(parâmetros mudaram)--> janela --> reprocessa sem alinhar de novo
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTabWidget

from ..processamento import pipeline

from .aba_etapas import AbaEtapas
from .aba_inspecao import AbaInspecao
from .aba_referencias import AbaReferencias
from .aba_resultados import AbaResultados

EQUIPE = [
    "Breno Fernandes Barbosa de Sousa",
    "Bruno Nascimento Brasilino de Freitas",
    "Danilo Bezerra Vieira",
    "Francisco Vinicius Castro Silveira",
    "Nataniel Marques Viana Neto",
]


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inspeção de PCB")
        self.resize(1280, 800)

        # guarda o último par e o alinhamento, para reprocessar rápido
        self.ultimo_par = None
        self.ultimo_alinhamento = None

        # --- Telas ---
        self.aba_inspecao = AbaInspecao()
        self.aba_etapas = AbaEtapas()
        self.aba_resultados = AbaResultados()
        self.aba_referencias = AbaReferencias()

        self.abas = QTabWidget()
        self.abas.addTab(self.aba_inspecao, "Inspeção")
        self.abas.addTab(self.aba_etapas, "Etapas")
        self.abas.addTab(self.aba_resultados, "Resultados")
        self.abas.addTab(self.aba_referencias, "Referências")
        self.setCentralWidget(self.abas)

        self._criar_menu()
        self.statusBar().showMessage("Pronto")

        # --- Ligações entre as telas ---
        self.aba_inspecao.inspecao_solicitada.connect(self.inspecionar)
        self.aba_inspecao.cadastro_solicitado.connect(
            lambda: self.abas.setCurrentWidget(self.aba_referencias))
        self.aba_etapas.parametros_alterados.connect(self.reprocessar)
        self.aba_referencias.referencias_atualizadas.connect(self.aba_inspecao.atualizar_referencias)

        # por último, para a tela Inspeção já receber a lista de referências
        self.aba_referencias.carregar()

    def _criar_menu(self):
        menu_arquivo = self.menuBar().addMenu("Arquivo")
        acao_sair = QAction("Sair", self)
        acao_sair.triggered.connect(self.close)
        menu_arquivo.addAction(acao_sair)

        menu_ajuda = self.menuBar().addMenu("Ajuda")
        acao_sobre = QAction("Sobre", self)
        acao_sobre.triggered.connect(self.mostrar_sobre)
        menu_ajuda.addAction(acao_sobre)

    def mostrar_sobre(self):
        QMessageBox.about(self, "Sobre", (
            "Detecção e Caracterização Automática de Defeitos em Placas de "
            "Circuito Impresso por Processamento Digital de Imagens\n\n"
            "Processamento Digital de Imagens — UFC, 2026.2\n\n"
            "Equipe:\n" + "\n".join(EQUIPE)))

    # ---------- orquestração ----------

    def inspecionar(self, imagem_referencia, imagem_teste):
        self.ultimo_par = (imagem_referencia, imagem_teste)
        self.ultimo_alinhamento = None  # par novo: precisa alinhar de novo
        if self._rodar_pipeline():
            self.abas.setCurrentWidget(self.aba_resultados)

    def reprocessar(self):
        if self.ultimo_par is not None:
            self._rodar_pipeline()

    def _rodar_pipeline(self):
        imagem_referencia, imagem_teste = self.ultimo_par
        self.statusBar().showMessage("Processando...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            if self.ultimo_alinhamento is None:
                self.ultimo_alinhamento = pipeline.alinhar_placas(imagem_referencia, imagem_teste)
            resultado = pipeline.executar(imagem_referencia, imagem_teste,
                                          alinhamento=self.ultimo_alinhamento,
                                          **self.aba_etapas.parametros())
        except Exception as erro:  # no protótipo, mostrar o erro ajuda a depurar
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Erro no processamento", str(erro))
            self.aba_inspecao.mostrar_situacao("Erro no processamento.")
            return False
        QApplication.restoreOverrideCursor()

        self.aba_etapas.mostrar_etapas(resultado)
        self.aba_resultados.mostrar_resultados(resultado)

        quantidade = len(resultado["regioes"])
        mensagem = (f"{quantidade} região(ões) candidata(s) encontrada(s) "
                    f"em {resultado['tempo_segundos'] * 1000:.0f} ms")
        self.aba_inspecao.mostrar_situacao(mensagem)
        self.statusBar().showMessage(mensagem)
        return True
