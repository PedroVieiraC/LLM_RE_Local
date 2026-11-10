# LLM_LOCAL

Comando `llm` para conversar no terminal do Windows com o modelo `DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic`, rodando no Google Colab (GPU T4, via túnel) ou localmente na CPU (llama.cpp), com fallback automático e histórico preservado. Só biblioteca padrão do Python 3.13.

## Níveis e riscos
| Nível | Onde roda | Como usa | Risco |
|---|---|---|---|
| N0 | PC (CPU) | `llm` no terminal | nenhum (lento, ~4-7 tokens/s, estimativa) |
| N1 | Colab GPU | chat dentro do notebook, sem túnel | dentro das regras do Colab |
| N2 | Colab GPU | `llm` no terminal via túnel cloudflared + chave | **viola o FAQ do plano gratuito do Colab**; risco seu. Use conta Google secundária, ligue só quando for usar e desconecte o runtime ao terminar |

Não há keep-alive automático nem ocultação de tráfego, de propósito.

## Instalação local (N0)
1. Precisa de ~7 GB livres em disco e RAM livre (o modelo Q4_K_M tem 5,63 GB).
2. Rode: `powershell -ExecutionPolicy Bypass -File scripts\instalar_local.ps1`
   (baixa llama.cpp CPU e o modelo para `%USERPROFILE%\.llm`; pode ser repetido, retoma o download e pula o que já existe).
3. Use `.\llm.cmd` dentro da pasta do projeto, ou adicione a pasta do projeto ao PATH para chamar só `llm`.
4. Teste: `llm status` e depois `llm`.

Config e chave ficam em `%USERPROFILE%\.llm\config.json`, fora do repositório.

## Colab (N1 e N2)
1. Abra `colab/llm_colab.ipynb` no Colab logado na **conta secundária**.
2. Ambiente de execução -> tipo de ambiente -> GPU T4.
3. Execute as células na ordem: 1 (binário CUDA), 2 (modelo Q6_K + servidor, baixa ~7,4 GB a cada sessão), 3 (N1: chat no notebook).
4. Para N2: execute a célula 4, copie a linha `llm colab <url> <chave>` impressa e cole no terminal do Windows. Depois use `llm`.
5. Ao terminar: célula 5 (fecha o túnel), célula 6 (fecha o servidor) e Ambiente de execução -> **Desconectar e excluir ambiente de execução**.

## Comandos
| Comando | O que faz |
|---|---|
| `llm` / `llm chat` | chat (backend `auto`: Colab se configurado e respondendo, senão local) |
| `llm chat --sem-pensar` | desliga o thinking (respostas mais rápidas) |
| `llm chat --local` | força o local nesta sessão |
| `llm status` | backend configurado e se Colab/local respondem |
| `llm colab <url> <chave>` | salva o Colab e testa o `/health` |
| `llm colab --limpar` | remove URL e chave |
| `llm local` | fixa o backend em local |
| `llm auto` | volta ao automático |
| `llm parar` | para o servidor local iniciado pelo `llm` |

No chat: `/sair`, `/limpar` (zera o histórico), `/backend` (mostra o em uso), `/pensar` (liga/desliga thinking). Ctrl+C durante uma resposta interrompe só a resposta.

Se o Colab falhar no meio, o `llm` avisa, sobe o local e reenvia o mesmo histórico.

## Solução de problemas
- **RAM baixa / servidor local não sobe:** feche navegador e outros programas; veja `%USERPROFILE%\.llm\llama-server.log`.
- **Porta 8080 ocupada:** edite `porta_local` em `%USERPROFILE%\.llm\config.json`, ou pare o outro programa. Se for um llama-server antigo, `llm parar`.
- **Túnel caiu:** o chat troca para o local sozinho; para voltar ao Colab, rode as células de novo e `llm colab` com a nova URL/chave.
- **Binário CUDA falhou no Colab:** use a célula 1b (compila com `-DCMAKE_CUDA_ARCHITECTURES=75`, ~10-15 min).
- **"llama-server ou modelo local ausente":** rode `scripts\instalar_local.ps1`.

## Desenvolvimento
`python -m unittest discover -s tests` (sem rede). Documentos: `start_instructions/`, `memoria/`.
