NVCC = nvcc
ARCH = -arch=sm_120
OPENCV = $(shell pkg-config --cflags --libs opencv4)
FONTES = src/main.cpp src/alinhamento.cpp src/diferenca_cpu.cpp src/diferenca_gpu.cu

inspecao: $(FONTES)
	$(NVCC) $(ARCH) -Iinclude $(FONTES) -o inspecao $(OPENCV)

clean:
	rm -f inspecao