# 🎵 Whisper AI Local Song Translate

Transcreve músicas do YouTube usando **IA local** (faster-whisper) e traduz automaticamente para **Português Brasileiro (PT-BR)** — qualquer que seja o idioma original (inglês, alemão, espanhol, etc).

Feito para uso pessoal: entender a letra de uma música sem precisar caçar tradução pronta na internet ou depender de legendas do próprio vídeo.

---

## ✨ O que ele faz

1. Baixa o áudio de um vídeo do YouTube.
2. Transcreve a letra no idioma original usando um modelo de reconhecimento de fala (Whisper), rodando **localmente no seu computador** — sem enviar o áudio pra nenhum servidor externo.
3. Traduz o texto para PT-BR, usando **DeepL** (online, melhor qualidade) ou **Argos Translate** (100% offline, sem precisar de internet nem de chave de API).
4. Salva dois arquivos `.txt`: a transcrição original e a tradução.
5. Funciona em **lote** — você pode processar várias músicas de uma vez, e se uma falhar, ele continua com as próximas.

---

## 📋 Pré-requisitos

Antes de começar, você precisa ter instalado:

| Ferramenta | Para que serve | Link |
|---|---|---|
| **Python 3.10+** | Rodar o script | [python.org/downloads](https://www.python.org/downloads/) |
| **FFmpeg** | Processar o áudio baixado | `winget install ffmpeg` (Windows) |
| **Git** (opcional) | Clonar/atualizar o projeto | [git-scm.com](https://git-scm.com/) |

> ⚠️ Ao instalar o Python no Windows, marque a caixa **"Add python.exe to PATH"** — sem isso, os comandos abaixo não vão funcionar no terminal.

---

## 🚀 Instalação

**1. Baixe o projeto**

Clonando via Git:
```bash
git clone https://github.com/SEU_USUARIO/song-translate.git
cd song-translate
```

Ou baixe o `.zip` direto do GitHub (botão verde **Code → Download ZIP**) e extraia numa pasta de sua preferência.

**2. Crie um ambiente virtual (recomendado)**

Isso evita que as bibliotecas do projeto entrem em conflito com outras instalações Python que você já tenha.

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Se aparecer erro de permissão ao ativar, rode o PowerShell como administrador e execute:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**3. Instale as dependências**

```bash
pip install -r requirements.txt
```

A primeira instalação pode levar alguns minutos (o `faster-whisper` baixa algumas bibliotecas maiores).

---

## 🔑 Configurando a chave do DeepL (opcional)

Só é necessário se você for usar o motor de tradução `deepl` (recomendado para melhor qualidade).

1. Crie uma conta gratuita em [deepl.com/pro-api](https://www.deepl.com/pro-api) (o plano free já é suficiente para uso pessoal).
2. Copie sua **API Key**.
3. Renomeie o arquivo `.env.example` para `.env` e cole sua chave nele:

```
DEEPL_API_KEY=sua-chave-aqui
```

> 🔒 O arquivo `.env` nunca é enviado pro GitHub (ele está no `.gitignore`) — sua chave fica só na sua máquina.

Se preferir usar apenas o motor **offline** (`argos`), pode pular essa etapa inteira — não precisa de nenhuma chave.

---

## ▶️ Como usar

**Traduzir uma única música:**

```bash
python song_translate.py --urls "https://youtube.com/watch?v=XXXXXXX" --engine deepl
```

**Traduzir várias músicas de uma vez (lote):**

1. Crie um arquivo de texto (ex: `lista.txt`) com uma URL do YouTube por linha:
```
https://youtube.com/watch?v=AAAAAAA
https://youtube.com/watch?v=BBBBBBB
https://youtube.com/watch?v=CCCCCCC
```

2. Rode:
```bash
python song_translate.py --urls-file lista.txt --engine deepl
```

**Usando o motor offline (sem internet, sem API key):**
```bash
python song_translate.py --urls-file lista.txt --engine argos
```

Os arquivos traduzidos aparecem na pasta `saida/`, com o nome da música:
```
saida/
├── nome_da_musica_original.txt
└── nome_da_musica_pt-br.txt
```

---

## ⚙️ Opções disponíveis

| Parâmetro | Descrição | Padrão |
|---|---|---|
| `--urls` | Uma ou mais URLs do YouTube, separadas por espaço | — |
| `--urls-file` | Arquivo `.txt` com uma URL por linha (para lote) | — |
| `--engine` | Motor de tradução: `deepl` ou `argos` | `deepl` |
| `--model` | Tamanho do modelo Whisper: `tiny`, `base`, `small`, `medium`, `large-v3` | `small` |
| `--output-dir` | Pasta onde salvar os arquivos traduzidos | `saida` |
| `--keep-audio` | Mantém os `.mp3` baixados em vez de apagar após o uso | desativado |

> 💡 **Sobre o modelo:** `small` é um bom equilíbrio entre velocidade e precisão para computadores sem placa de vídeo dedicada (GPU integrada Intel/AMD). Se sua máquina tiver uma GPU NVIDIA dedicada ou muita RAM livre, `medium` ou `large-v3` entregam mais precisão, porém mais lento e consumindo mais memória.

---

## 🛠️ Solução de problemas

**"yt-dlp falhou ao baixar áudio"**
Pode ser um vídeo privado, removido, ou o `yt-dlp` estar desatualizado. Tente atualizar: `pip install -U yt-dlp`.

**Processo muito lento ou travando**
Verifique se sua RAM não está no limite (Gerenciador de Tarefas). Feche outros programas pesados antes de rodar, ou use um modelo menor (`--model tiny` ou `--model base`).

**Erro da API do DeepL**
Confira se a chave no `.env` está correta e se você não ultrapassou o limite mensal gratuito (500.000 caracteres/mês no plano free).

**Erro do Argos Translate sobre pacote de idioma**
Na primeira vez que você traduz de um idioma novo, o Argos baixa o pacote automaticamente — isso exige conexão com a internet apenas nesse primeiro uso daquele idioma específico.

---

## ⚖️ Aviso legal

Este projeto é destinado **exclusivamente para uso pessoal e educacional** — entender letras de músicas em outros idiomas. Ele não redistribui, hospeda ou publica letras de terceiros; todo o conteúdo é gerado localmente na máquina do próprio usuário, a partir de áudio processado por ele mesmo. Respeite os direitos autorais das músicas e dos artistas.

---

## 📄 Licença

Uso livre para fins pessoais. Sinta-se à vontade para adaptar o script às suas necessidades.
