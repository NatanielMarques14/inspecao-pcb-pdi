"""
Tela "Referências": cadastro das placas de referência (placas sem defeito).
Responsável: Bruno (dados e pré-processamento)

As imagens são copiadas para dados/referencias/ e a lista fica em
dados/referencias/referencias.json, no formato:
    [{"nome": "Placa 07", "arquivo": "placa_07.jpg"}, ...]

O botão "Importar do dataset" cadastra de uma vez as 10 placas da pasta
PCB_USED do PKU-Market-PCB (01.JPG vira "Placa 01", e assim por diante).
"""

import json
import re
import shutil
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from .componentes import VisualizadorImagem, ler_imagem

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PASTA_REFERENCIAS = RAIZ_PROJETO / "dados" / "referencias"
ARQUIVO_LISTA = PASTA_REFERENCIAS / "referencias.json"
EXTENSOES = {".jpg", ".jpeg", ".png", ".bmp"}


def nome_para_arquivo(nome):
    """'Placa 07 (azul)' -> 'placa_07_azul'"""
    return re.sub(r"[^a-z0-9]+", "_", nome.lower()).strip("_") or "referencia"


class AbaReferencias(QWidget):
    # envia a lista atualizada para a tela Inspeção (passando pela janela principal)
    referencias_atualizadas = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.referencias = []
        self.caminho_nova_imagem = None

        # --- Lista das cadastradas ---
        self.lista = QListWidget()
        self.lista.currentRowChanged.connect(self.mostrar_referencia)
        self.botao_remover = QPushButton("Remover selecionada")
        self.botao_remover.clicked.connect(self.remover)
        botao_importar = QPushButton("Importar do dataset (PCB_USED)...")
        botao_importar.clicked.connect(self.importar_pasta)

        # --- Cadastro de uma placa ---
        self.campo_nome = QLineEdit()
        self.campo_nome.setPlaceholderText("Ex.: Placa 13")
        self.rotulo_arquivo = QLabel("Nenhuma imagem escolhida")
        botao_escolher = QPushButton("Escolher imagem...")
        botao_escolher.clicked.connect(self.escolher_imagem)
        botao_cadastrar = QPushButton("Cadastrar referência")
        botao_cadastrar.setObjectName("botaoPrincipal")
        botao_cadastrar.clicked.connect(self.cadastrar)

        grupo_cadastro = QGroupBox("Nova referência")
        formulario = QFormLayout(grupo_cadastro)
        dica = QLabel("Use a foto de uma placa aprovada, sem defeitos.")
        dica.setObjectName("textoSecundario")
        dica.setWordWrap(True)
        formulario.addRow(dica)
        formulario.addRow("Nome:", self.campo_nome)
        formulario.addRow("Imagem:", self.rotulo_arquivo)
        formulario.addRow(botao_escolher)
        formulario.addRow(botao_cadastrar)

        coluna = QVBoxLayout()
        coluna.addWidget(QLabel("Placas cadastradas"))
        coluna.addWidget(self.lista, 1)
        coluna.addWidget(self.botao_remover)
        coluna.addWidget(botao_importar)
        coluna.addWidget(grupo_cadastro)
        painel_esquerdo = QWidget()
        painel_esquerdo.setLayout(coluna)
        painel_esquerdo.setMaximumWidth(360)

        self.visualizador = VisualizadorImagem("Pré-visualização")

        layout = QHBoxLayout(self)
        layout.addWidget(painel_esquerdo)
        layout.addWidget(self.visualizador, 1)

    # ---------- leitura e gravação da lista ----------

    def carregar(self):
        """Lê o JSON e avisa as outras telas. Chamado pela janela principal ao abrir."""
        if ARQUIVO_LISTA.exists():
            with open(ARQUIVO_LISTA, encoding="utf-8") as arquivo:
                self.referencias = json.load(arquivo)
        self._atualizar_lista()

    def _salvar(self):
        PASTA_REFERENCIAS.mkdir(parents=True, exist_ok=True)
        with open(ARQUIVO_LISTA, "w", encoding="utf-8") as arquivo:
            json.dump(self.referencias, arquivo, ensure_ascii=False, indent=2)

    def _atualizar_lista(self):
        self.lista.clear()
        for referencia in self.referencias:
            self.lista.addItem(referencia["nome"])
        # as outras telas recebem o caminho completo de cada imagem
        self.referencias_atualizadas.emit([
            {"nome": r["nome"], "caminho": str(PASTA_REFERENCIAS / r["arquivo"])}
            for r in self.referencias
        ])

    def _adicionar(self, nome, caminho_origem):
        """Copia a imagem para dentro do projeto e acrescenta na lista."""
        PASTA_REFERENCIAS.mkdir(parents=True, exist_ok=True)
        nome_arquivo = nome_para_arquivo(nome) + caminho_origem.suffix.lower()
        shutil.copy(caminho_origem, PASTA_REFERENCIAS / nome_arquivo)
        self.referencias.append({"nome": nome, "arquivo": nome_arquivo})

    def _existe(self, nome):
        return any(r["nome"] == nome for r in self.referencias)

    # ---------- ações dos botões ----------

    def mostrar_referencia(self, linha):
        if not 0 <= linha < len(self.referencias):
            self.visualizador.limpar()
            return
        imagem = ler_imagem(PASTA_REFERENCIAS / self.referencias[linha]["arquivo"])
        if imagem is None:
            self.visualizador.limpar("Arquivo da referência não encontrado")
        else:
            self.visualizador.mostrar(imagem)

    def escolher_imagem(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Imagem da placa de referência", "", "Imagens (*.jpg *.jpeg *.JPG *.png *.bmp)")
        if caminho and ler_imagem(caminho) is not None:
            self.caminho_nova_imagem = Path(caminho)
            self.rotulo_arquivo.setText(self.caminho_nova_imagem.name)
            self.visualizador.mostrar(ler_imagem(caminho))

    def cadastrar(self):
        nome = self.campo_nome.text().strip()
        if not nome or self.caminho_nova_imagem is None:
            QMessageBox.warning(self, "Cadastro", "Informe um nome e escolha a imagem da placa.")
            return
        if self._existe(nome):
            QMessageBox.warning(self, "Cadastro", f"Já existe uma referência chamada '{nome}'.")
            return

        self._adicionar(nome, self.caminho_nova_imagem)
        self._salvar()
        self._atualizar_lista()
        self.campo_nome.clear()
        self.rotulo_arquivo.setText("Nenhuma imagem escolhida")
        self.caminho_nova_imagem = None

    def importar_pasta(self):
        """Cadastra todas as imagens de uma pasta (ex.: PCB_DATASET/PCB_USED)."""
        pasta = QFileDialog.getExistingDirectory(self, "Escolha a pasta PCB_USED do dataset")
        if not pasta:
            return
        imagens = sorted(p for p in Path(pasta).iterdir() if p.suffix.lower() in EXTENSOES)
        novas = 0
        for caminho in imagens:
            nome = f"Placa {caminho.stem}"
            if not self._existe(nome):
                self._adicionar(nome, caminho)
                novas += 1
        self._salvar()
        self._atualizar_lista()
        QMessageBox.information(self, "Importar", f"{novas} referência(s) importada(s) de:\n{pasta}")

    def remover(self):
        linha = self.lista.currentRow()
        if linha < 0:
            return
        nome = self.referencias[linha]["nome"]
        if QMessageBox.question(self, "Remover", f"Remover a referência '{nome}'?") == QMessageBox.Yes:
            # tira só da lista; a imagem continua na pasta, por segurança
            self.referencias.pop(linha)
            self._salvar()
            self._atualizar_lista()
