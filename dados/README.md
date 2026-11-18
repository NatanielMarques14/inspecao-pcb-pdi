# Dados

O dataset usado é o **PKU-Market-PCB** (Universidade de Pequim), disponível em https://robotics.pkusz.edu.cn/resources/dataset/.

Ele **não é versionado** neste repositório por causa do tamanho. Baixe e extraia em `dados/PCB_DATASET/` (pasta ignorada pelo git). As placas de referência cadastradas pela aba "Referências" ficam em `dados/referencias/`, também fora do versionamento.

# Estrutura do dataset

```text
PCB_DATASET/
├── Annotations/                  # Gabarito das coordenadas dos defeitos (.xml)
│   ├── Missing_hole/
│   ├── Mouse_bite/
│   ├── Open_circuit/
│   ├── Short/
│   ├── Spur/
│   └── Spurious_copper/
│
├── images/                        # Imagens das placas com defeitos, separadas por tipo
│   ├── Missing_hole/
│   ├── Mouse_bite/
│   ├── Open_circuit/
│   ├── Short/
│   ├── Spur/                      # Ex.: 07_spur_03.jpg = terceira imagem da placa 7 com defeito Spur
│   └── Spurious_copper/
│
├── PCB_USED/                      # Placas de referência (10 imagens)
│
├── rotation/                      # Imagens rotacionadas para testar o alinhamento
│   ├── Missing_hole_rotation/
│   ├── Mouse_bite_rotation/
│   ├── Open_circuit_rotation/
│   ├── Short_rotation/
│   ├── Spur_rotation/
│   ├── Spurious_copper_rotation/
│   ├── Missing_hole_angles.txt    # Ângulos específicos de cada rotação
│   ├── Mouse_bite_angles.txt
│   ├── Open_circuit_angles.txt
│   ├── Short_angles.txt
│   ├── Spur_angles.txt
│   └── Spurious_copper_angles.txt
│
└── rotate.py                      # Script para rotacionar as imagens
```



Observação em images: Cada erro tem cerca de 115 imagens, placas 01 e 04 com 20 imagens cada, placa 10 com 5, Placas 05, 06, 07, 08, 09, 11, 12 com 10 imagens cada, em Short, a placa 06 tem 11 imagens de erros. Somando os seis tipos de erros ficamos com 693 imagens de placas erradas. A distribuição uniforme da quantidade de placas não foi informada pelos autores. Os defeitos foram inseridos digitalmente nas fotos das placas boas. Cada imagem tem um único tipo de defeito, mas normalmente vários exemplares dele espalhados pela placa.

Observação em rotation: Na vida real as imagens geralmente não são perfeitamente alinhadas com a referência, rotation/ testa se o sistema acha os defeitos mesmo quando a placa não está na posição certa, que é a situação real. Os .txt's servem como um gabarito para saber se o sistema achou o ângulo de alinhamento certo.