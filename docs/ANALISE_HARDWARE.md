# LLM local — análise do hardware (09/11/2026)

## Máquina (medido)
| Item | Valor | Impacto |
|---|---|---|
| CPU | Intel Core i5-1135G7 (4 núcleos / 8 threads, AVX-512) | O llama.cpp roda bem na CPU; o AVX-512 ajuda |
| RAM | 16 GB (1 pente de 3200 MHz, **canal único**), ~2,8 GB livres no momento da medição | Limita o tamanho do modelo; o canal único reduz a velocidade (a geração depende da largura de banda da memória) |
| GPU | Intel Iris Xe integrada (sem placa de vídeo dedicada) | Usa a RAM do sistema; o backend Vulkan do llama.cpp pode ajudar um pouco, mas não muda o tamanho que cabe |
| Disco C: | 33,6 GB livres de 237,5 GB | Cabem 2 ou 3 modelos GGUF médios; o modelo completo não cabe |
| SO | Windows 11 Pro 64 bits; Python 3.13 | O llama.cpp tem binário pronto para Windows |

## O que roda localmente (estimativa, quantização Q4_K_M)
| Tamanho do modelo | Arquivo | RAM necessária | Velocidade esperada | Veredito |
|---|---|---|---|---|
| 7–8B | ~5 GB | ~6–7 GB | ~5–8 tokens/s | **Recomendado** para uso diário |
| 14B | ~9 GB | ~10–11 GB | ~2–4 tokens/s | Usável, lento; exige fechar navegador e outros apps |
| 32B | ~19 GB | >16 GB | — | Não cabe |
| DeepSeek completo (V3/R1 671B e sucessores) | centenas de GB | — | — | Impossível localmente |

As velocidades são estimativas, não foram medidas. Rodar um benchmark (`llama-bench`) depois de instalar.
"DeepSeek 4.2": a existência e o nome exato **não foram verificados**. Pesquisar antes de escolher.
As versões DeepSeek que cabem aqui são as "distill" (por exemplo, R1-Distill-Qwen 7B/14B) em GGUF.

## Ponto do usuário: alternar entre local e Google Colab
Ideia: o mesmo fluxo pode rodar **no PC** (modelos pequenos, offline) ou **no Google Colab**, que tem GPU
gratuita T4 com ~15 GB de VRAM (modelos 14B rápidos; 32B Q4 só parcialmente).
Esboço a discutir:
- No PC: o `llama-server` (llama.cpp) expõe uma API compatível com OpenAI em `localhost`.
- No Colab: um notebook roda o mesmo `llama-server` com GPU e expõe a API por um túnel
  (ngrok ou cloudflared).
- O cliente (script ou chat) só troca a URL base: local ou Colab. Um único arquivo de configuração decide.
- Limites do Colab gratuito: sessão de ~12 h no máximo, desconexão por inatividade, GPU nem sempre
  disponível; o modelo precisa ser baixado de novo a cada sessão (ou guardado no Google Drive).

## Pendente (conversar antes)
- Escolha do modelo (inclusive variantes "sem filtro" da comunidade): decisão do usuário.
- Instalação do llama.cpp + o primeiro modelo 7–8B, e um benchmark real.
- Notebook do Colab + túnel + chave de configuração local/Colab.
