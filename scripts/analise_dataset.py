"""
Análise inicial do dataset PKU-Market-PCB.

Organização esperada (como vem no download):
    PCB_DATASET/
    ├── PCB_USED/               placas de referência, sem defeito (01.JPG, 04.JPG, ...)
    ├── images/<Tipo>/          imagens com defeito (ex.: 07_short_03.jpg)
    ├── Annotations/<Tipo>/     um XML por imagem, com as caixas dos defeitos
    └── rotation/
        ├── <Tipo>_rotation/    as mesmas imagens, giradas
        └── <Tipo>_angles.txt   ângulo usado em cada imagem girada

O nome de cada imagem segue o padrão PLACA_tipo_NUMERO.jpg:
o número da placa liga a imagem à sua referência em PCB_USED.

Uso (a partir da pasta do projeto):
    python scripts/analise_dataset.py dados/PCB_DATASET
"""

import argparse
import csv
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # só salva os gráficos em arquivo, sem abrir janela
import matplotlib.pyplot as plt

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".bmp"}
COR = "#1e6b52"


def listar_imagens(pasta):
    if not pasta.exists():
        return []
    return sorted(p for p in pasta.iterdir() if p.suffix.lower() in EXTENSOES_IMAGEM)


def numero_placa(nome_arquivo):
    """'07_short_03.jpg' -> '07'"""
    return nome_arquivo.split("_")[0]


def ler_referencias(raiz):
    """Placas de referência em PCB_USED. Devolve {'01': caminho, ...}."""
    return {p.stem: p for p in listar_imagens(raiz / "PCB_USED")}


def ler_imagens_defeito(raiz):
    """Imagens com defeito, agrupadas pela pasta do tipo. Devolve {tipo: [caminhos]}."""
    pasta = raiz / "images"
    return {tipo.name: listar_imagens(tipo) for tipo in sorted(pasta.iterdir()) if tipo.is_dir()}


def ler_anotacoes(raiz):
    """Lê todos os XML. Devolve uma lista com um item por defeito anotado."""
    defeitos = []
    for arquivo in sorted((raiz / "Annotations").rglob("*.xml")):
        xml = ET.parse(arquivo).getroot()
        tamanho = xml.find("size")
        largura_img = int(tamanho.findtext("width"))
        altura_img = int(tamanho.findtext("height"))

        for objeto in xml.iter("object"):
            caixa = objeto.find("bndbox")
            xmin, ymin = int(caixa.findtext("xmin")), int(caixa.findtext("ymin"))
            xmax, ymax = int(caixa.findtext("xmax")), int(caixa.findtext("ymax"))
            defeitos.append({
                "arquivo": arquivo.stem,
                "placa": numero_placa(arquivo.stem),
                "pasta_tipo": arquivo.parent.name,
                "tipo": objeto.findtext("name").strip().lower(),
                "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax,
                "largura": xmax - xmin,
                "altura": ymax - ymin,
                "largura_imagem": largura_img,
                "altura_imagem": altura_img,
            })
    return defeitos


def ler_angulos(raiz):
    """Lê os <Tipo>_angles.txt da pasta rotation. Devolve {tipo: [ângulos]}."""
    angulos = {}
    for arquivo in sorted((raiz / "rotation").glob("*_angles.txt")):
        valores = []
        for linha in arquivo.read_text().splitlines():
            partes = linha.split()
            if len(partes) == 2:  # "08_missing_hole_03   -9"
                valores.append(int(partes[1]))
        angulos[arquivo.stem.replace("_angles", "")] = valores
    return angulos


def resumo(valores):
    return f"menor {min(valores)}   mediana {statistics.median(valores):g}   maior {max(valores)}"


def titulo(texto):
    print(f"\n== {texto} ==")


def main():
    parser = argparse.ArgumentParser(description="Análise inicial do PKU-Market-PCB")
    parser.add_argument("pasta", type=Path, help="pasta PCB_DATASET")
    parser.add_argument("--saida", type=Path, default=Path("resultados/analise_dataset"))
    argumentos = parser.parse_args()

    raiz = argumentos.pasta
    for necessaria in ["PCB_USED", "images", "Annotations"]:
        if not (raiz / necessaria).is_dir():
            sys.exit(f"Pasta '{necessaria}' não encontrada em {raiz}. Confira o caminho do dataset.")

    referencias = ler_referencias(raiz)
    imagens = ler_imagens_defeito(raiz)
    defeitos = ler_anotacoes(raiz)
    angulos = ler_angulos(raiz) if (raiz / "rotation").is_dir() else {}

    todas_imagens = [img for lista in imagens.values() for img in lista]
    placas = sorted(referencias)

    # 1. Visão geral
    titulo("Visão geral")
    print(f"  Placas de referência (PCB_USED): {len(referencias)}  -> {', '.join(placas)}")
    print(f"  Imagens com defeito (images):     {len(todas_imagens)}")
    print(f"  Tipos de defeito:                  {len(imagens)}")
    print(f"  Defeitos anotados (XML):           {len(defeitos)}")
    if angulos:
        total_giradas = sum(len(listar_imagens(p)) for p in (raiz / "rotation").iterdir() if p.is_dir())
        print(f"  Imagens giradas (rotation):        {total_giradas}")

    # 2. Conferência: toda imagem tem anotação e toda placa tem referência?
    titulo("Conferência dos pares")
    nomes_imagens = {img.stem for img in todas_imagens}
    nomes_xml = {d["arquivo"] for d in defeitos}
    sem_xml = sorted(nomes_imagens - nomes_xml)
    sem_referencia = sorted({numero_placa(n) for n in nomes_imagens} - set(referencias))
    print(f"  Imagens sem XML:              {len(sem_xml)} {sem_xml[:5] if sem_xml else ''}")
    print(f"  Placas sem imagem de referência: {sem_referencia if sem_referencia else 'nenhuma'}")

    # 3. Imagens por tipo e por placa
    titulo("Imagens com defeito por tipo e por placa")
    contagem = {tipo: Counter(numero_placa(img.name) for img in lista) for tipo, lista in imagens.items()}
    cabecalho = f"  {'Tipo':<18}" + "".join(f"{p:>5}" for p in placas) + f"{'Total':>7}"
    print(cabecalho)
    for tipo, por_placa in contagem.items():
        linha = "".join(f"{por_placa.get(p, 0):>5}" for p in placas)
        print(f"  {tipo:<18}{linha}{sum(por_placa.values()):>7}")
    total_placa = Counter(numero_placa(img.name) for img in todas_imagens)
    print(f"  {'Total':<18}" + "".join(f"{total_placa.get(p, 0):>5}" for p in placas) + f"{len(todas_imagens):>7}")

    # 4. Defeitos anotados por tipo
    titulo("Defeitos anotados por tipo")
    por_tipo = Counter(d["tipo"] for d in defeitos)
    for tipo, quantidade in por_tipo.most_common():
        print(f"  {tipo:<18} {quantidade:>5}  ({100 * quantidade / len(defeitos):.1f}%)")

    # 5. Quantos defeitos cada imagem tem
    titulo("Defeitos por imagem")
    por_imagem = Counter(d["arquivo"] for d in defeitos)
    print(f"  {resumo(list(por_imagem.values()))}")
    tipos_por_imagem = defaultdict(set)
    for d in defeitos:
        tipos_por_imagem[d["arquivo"]].add(d["tipo"])
    mistas = sum(1 for t in tipos_por_imagem.values() if len(t) > 1)
    print(f"  Imagens com mais de um tipo de defeito: {mistas}")

    # 6. Resolução das imagens (vem do XML)
    titulo("Resoluções mais comuns (largura x altura)")
    # cada imagem conta uma vez, mesmo tendo vários defeitos
    resolucao_por_imagem = {d["arquivo"]: (d["largura_imagem"], d["altura_imagem"]) for d in defeitos}
    resolucoes = Counter(resolucao_por_imagem.values())
    for (largura, altura), quantidade in resolucoes.most_common(5):
        print(f"  {largura} x {altura}: {quantidade} imagens")

    # 7. Tamanho das caixas: ajuda a escolher a área mínima no pipeline
    titulo("Tamanho das caixas anotadas por tipo (área em px²)")
    for tipo in sorted(por_tipo):
        areas = [d["largura"] * d["altura"] for d in defeitos if d["tipo"] == tipo]
        print(f"  {tipo:<18} {resumo(areas)}")
    todas_areas = [d["largura"] * d["altura"] for d in defeitos]
    print(f"  {'todos':<18} {resumo(todas_areas)}")

    # 8. Ângulos das imagens giradas
    if angulos:
        titulo("Ângulos de rotação (graus)")
        for tipo, valores in angulos.items():
            print(f"  {tipo:<18} {len(valores):>4} imagens   {resumo(valores)}")

    # 9. Salva tabelas e gráficos para o relatório
    saida = argumentos.saida
    saida.mkdir(parents=True, exist_ok=True)

    with open(saida / "defeitos.csv", "w", newline="", encoding="utf-8") as arquivo:
        colunas = ["arquivo", "placa", "tipo", "xmin", "ymin", "xmax", "ymax", "largura", "altura"]
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(defeitos)

    with open(saida / "imagens_por_tipo_e_placa.csv", "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["tipo"] + placas + ["total"])
        for tipo, por_placa in contagem.items():
            escritor.writerow([tipo] + [por_placa.get(p, 0) for p in placas] + [sum(por_placa.values())])

    tipos, quantidades = zip(*por_tipo.most_common())
    plt.figure(figsize=(8, 4))
    plt.bar(tipos, quantidades, color=COR)
    plt.title("Defeitos anotados por tipo")
    plt.ylabel("Quantidade de defeitos")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(saida / "defeitos_por_tipo.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.bar(placas, [total_placa.get(p, 0) for p in placas], color=COR)
    plt.title("Imagens com defeito por placa")
    plt.xlabel("Placa")
    plt.ylabel("Quantidade de imagens")
    plt.tight_layout()
    plt.savefig(saida / "imagens_por_placa.png", dpi=150)
    plt.close()

    print(f"\nArquivos salvos em: {saida}/")


if __name__ == "__main__":
    main()
