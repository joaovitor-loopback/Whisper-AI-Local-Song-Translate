# Whisper AI Local Song Translate

Baixa o áudio de vídeos do YouTube, transcreve automaticamente com [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (com detecção automática de idioma) e traduz o resultado para **português brasileiro (PT-BR)**, usando [DeepL](https://www.deepl.com/) (online) ou [Argos Translate](https://github.com/argosopentech/argos-translate) (offline/local).

## Funcionalidades

- Download de áudio direto do YouTube via `yt-dlp`
- Transcrição local com `faster-whisper`, rodando em CPU (int8)
- Tradução para PT-BR via DeepL (API) ou Argos Translate (100% offline)
- Processamento em lote: uma URL ou várias, de linha de comando ou de um arquivo `.txt`
- Erros individuais não interrompem o lote — o script segue para a próxima música e reporta um resumo no final

## Saída

Para cada música processada, o script gera dois arquivos em `--output-dir` (padrão: `./saida`):

```
<nome>_original.txt   # transcrição no idioma original
<nome>_pt-br.txt       # tradução para PT-BR
```

## Requisitos

- Python 3.11 ou 3.12
- [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) (ffmpeg + ffprobe no PATH)
- [Deno](https://deno.com/) (runtime JS usado pelo `yt-dlp` para extração no YouTube)
- Chave de API do DeepL, **apenas** se for usar `--engine deepl`

## Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repo>
cd Whisper-AI-Local-Song-Translate

# 2. Crie e ative um ambiente virtual
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate

# 3. Instale as dependências Python
pip install faster-whisper yt-dlp requests python-dotenv

# Se for usar o engine "argos" (tradução offline):
pip install argostranslate
```

### FFmpeg

O `yt-dlp` depende do FFmpeg para extrair e converter o áudio.

- **Windows:** `winget install Gyan.FFmpeg`
- **Linux (Debian/Ubuntu):** `sudo apt install ffmpeg`
- **macOS:** `brew install ffmpeg`

Confirme com `ffmpeg -version` e `ffprobe -version` em um terminal novo.

### Deno

Necessário para o `yt-dlp` resolver corretamente os desafios de extração do YouTube.

- **Windows:** `winget install DenoLand.Deno`
- **Linux / macOS:** veja [deno.com/manual/getting_started/installation](https://docs.deno.com/runtime/getting_started/installation/)

## Configuração (apenas para o engine DeepL)

Crie um arquivo `.env` na raiz do projeto:

```
DEEPL_API_KEY=sua_chave_aqui
```

Alternativamente, passe a chave diretamente via `--deepl-key`. Se for usar apenas `--engine argos`, essa etapa não é necessária.

## Uso

### Uma única música

```bash
python song_translate.py --urls "https://youtube.com/watch?v=XXXX" --engine argos --model small
```

### Várias músicas de uma vez

```bash
python song_translate.py --urls "URL1" "URL2" "URL3" --engine argos --model small
```

### Lote via arquivo de texto

Crie um `lista.txt` com uma URL por linha (linhas iniciadas com `#` são ignoradas):

```
https://youtube.com/watch?v=XXXX
https://youtube.com/watch?v=YYYY
```

```bash
python song_translate.py --urls-file lista.txt --engine argos --model small
```

### Usando o DeepL

```bash
python song_translate.py --urls "URL" --engine deepl --deepl-key SUACHAVE
```

## Argumentos disponíveis

| Argumento | Descrição |
|---|---|
| `--urls` | Uma ou mais URLs do YouTube |
| `--urls-file` | Arquivo `.txt` com uma URL por linha |
| `--engine` | `deepl` (online, melhor qualidade) ou `argos` (offline). Padrão: `deepl` |
| `--deepl-key` | Chave da API DeepL (ou defina `DEEPL_API_KEY` no `.env`) |
| `--model` | Modelo do faster-whisper: `tiny`, `base`, `small`, `medium`, `large-v3`. Recomendado `small` para CPU |
| `--output-dir` | Pasta de saída dos arquivos traduzidos. Padrão: `saida` |
| `--keep-audio` | Mantém os arquivos `.mp3` baixados (por padrão são apagados após o processamento) |

## Notas

- Na primeira execução com `--engine argos`, o Argos Translate baixa automaticamente o pacote de idioma necessário (requer internet nessa etapa).
- O modelo do faster-whisper também é baixado automaticamente na primeira execução.
- O script roda sempre em CPU (`device="cpu"`); não há suporte a GPU/CUDA nesta versão.
- Se aparecer `HTTP Error 403: Forbidden` ao baixar do YouTube, atualize o `yt-dlp` (`pip install -U yt-dlp`) e confirme que o Deno está instalado e no PATH.

## Licença

Defina aqui a licença do projeto (ex: MIT, GPL-3.0, ou "uso pessoal").
