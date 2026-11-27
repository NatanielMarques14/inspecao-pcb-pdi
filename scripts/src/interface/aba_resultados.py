"""
Tela "Resultados": placa com os defeitos destacados, resumo, tabela das regiões,
exportação em CSV e espaço reservado para as métricas de avaliação.
"""

import csv

import cv2
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from .componentes import VisualizadorImagem

COLUNAS = ["ID", "Tipo", "X", "Y", "Largura", "Altura", "Área (px)"]
CHAVES = ["id", "tipo", "x", "y", "largura", "altura", "area"]

# cores em BGR (padrão do OpenCV)
COR_REGIAO = (0, 0, 230)          # vermelho
COR_SELECIONADA = (0, 200, 255)   # amarelo


def desenhar_regioes(imagem, regioes, id_selecionado=None):
    """Desenha um retângulo e o número de cada região numa cópia da imagem."""
    desenho = cv2.cvtColor(imagem, cv2.COLOR_GRAY2BGR) if imagem.ndim == 2 else imagem.copy()

    # espessura proporcional ao tamanho, senão some nas fotos grandes do dataset
    espessura = max(2, desenho.shape[1] // 500)
    margem = 3 * espessura
    for regiao in regioes:
        cor = COR_SELECIONADA if regiao["id"] == id_selecionado else COR_REGIAO
        x, y = regiao["x"], regiao["y"]
        x2, y2 = x + regiao["largura"], y + regiao["altura"]
        cv2.rectangle(desenho, (x - margem, y - margem), (x2 + margem, y2 + margem), cor, espessura)
        cv2.putText(desenho, str(regiao["id"]), (x, max(y - 2 * margem, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4 * espessura, cor, espessura)
    return desenho


class AbaResultados(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resultado = None

        # --- Placa com os defeitos ---
        self.visualizador = VisualizadorImagem("Defeitos destacados")
        self.visualizador.limpar("Rode uma inspeção para ver os resultados")

        # --- Resumo ---
        self.rotulo_quantidade = QLabel("—")
        self.rotulo_area_total = QLabel("—")
        self.rotulo_angulo = QLabel("—")
        self.rotulo_tempo = QLabel("—")
        grupo_resumo = QGroupBox("Resumo")
        resumo = QFormLayout(grupo_resumo)
        resumo.addRow("Regiões encontradas:", self.rotulo_quantidade)
        resumo.addRow("Área total:", self.rotulo_area_total)
        resumo.addRow("Rotação corrigida:", self.rotulo_angulo)
        resumo.addRow("Tempo de processamento:", self.rotulo_tempo)

        # --- Métricas: preenchidas quando a avaliação com as anotações XML existir ---
        grupo_metricas = QGroupBox("Métricas contra as anotações")
        metricas = QFormLayout(grupo_metricas)
        self.rotulos_metricas = {}
        for nome in ["Precisão", "Revocação", "F1", "Falsos positivos"]:
            self.rotulos_metricas[nome] = QLabel("—")
            metricas.addRow(f"{nome}:", self.rotulos_metricas[nome])
        aviso = QLabel("Disponível quando a avaliação for implementada.")
        aviso.setObjectName("textoSecundario")
        metricas.addRow(aviso)

        # --- Tabela de regiões ---
        self.tabela = QTableWidget(0, len(COLUNAS))
        self.tabela.setHorizontalHeaderLabels(COLUNAS)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.itemSelectionChanged.connect(self.destacar_selecionada)

        self.botao_exportar = QPushButton("Exportar tabela em CSV...")
        self.botao_exportar.setEnabled(False)
        self.botao_exportar.clicked.connect(self.exportar_csv)

        coluna = QVBoxLayout()
        coluna.addWidget(grupo_resumo)
        coluna.addWidget(grupo_metricas)
        coluna.addWidget(QLabel("Regiões candidatas a defeito (clique para destacar)"))
        coluna.addWidget(self.tabela, 1)
        coluna.addWidget(self.botao_exportar)
        painel_direito = QWidget()
        painel_direito.setLayout(coluna)
        painel_direito.setMaximumWidth(580)

        layout = QHBoxLayout(self)
        layout.addWidget(self.visualizador, 1)
        layout.addWidget(painel_direito)

    def mostrar_resultados(self, resultado):
        """Recebe o resultado do pipeline e atualiza imagem, resumo e tabela."""
        self.resultado = resultado
        regioes = resultado["regioes"]

        self.rotulo_quantidade.setText(str(len(regioes)))
        self.rotulo_area_total.setText(f"{sum(r['area'] for r in regioes)} px")
        angulo = resultado.get("angulo_estimado")
        self.rotulo_angulo.setText("—" if angulo is None else f"{angulo:.1f}°")
        self.rotulo_tempo.setText(f"{resultado['tempo_segundos'] * 1000:.0f} ms")

        self.tabela.setRowCount(len(regioes))
        for linha, regiao in enumerate(regioes):
            for coluna, chave in enumerate(CHAVES):
                self.tabela.setItem(linha, coluna, QTableWidgetItem(str(regiao[chave])))

        self.botao_exportar.setEnabled(bool(regioes))
        self.visualizador.mostrar(desenhar_regioes(resultado["imagem_teste"], regioes))

    def destacar_selecionada(self):
        # pinta de amarelo a região clicada na tabela
        if self.resultado is None:
            return
        linhas = self.tabela.selectionModel().selectedRows()
        id_selecionado = int(self.tabela.item(linhas[0].row(), 0).text()) if linhas else None
        self.visualizador.mostrar(
            desenhar_regioes(self.resultado["imagem_teste"], self.resultado["regioes"], id_selecionado))

    def exportar_csv(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Exportar regiões", "regioes.csv", "CSV (*.csv)")
        if not caminho:
            return
        with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.writer(arquivo)
            escritor.writerow(COLUNAS)
            for regiao in self.resultado["regioes"]:
                escritor.writerow([regiao[chave] for chave in CHAVES])
        QMessageBox.information(self, "Exportar", f"Tabela salva em:\n{caminho}")
