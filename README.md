# 🧭 Guia de Uso --- Programa **Baixar YouTube**

Este programa permite **baixar vídeos e áudios do YouTube** de forma
simples e automatizada, diretamente pelo terminal (Prompt de Comando).\
Ele oferece opções para **baixar vídeos individuais, playlists inteiras
ou listas de links armazenadas em arquivos `.txt`**.

------------------------------------------------------------------------

## ⚙️ Pré-requisitos

Antes de usar o programa, certifique-se de ter:

1.  **Python 3.8 ou superior** instalado.

    ``` bash
    python --version
    ```

2.  As bibliotecas necessárias instaladas:

    ``` bash
    pip install pytubefix mutagen
    ```

3.  (Opcional, mas recomendado) o **ffmpeg** instalado no sistema.

    ``` bash
    ffmpeg -version
    ```

------------------------------------------------------------------------

## 🧩 Estrutura de Pastas Criada Automaticamente

Ao executar o programa, ele cria automaticamente as seguintes pastas:

-   **pasta_video/** → vídeos baixados\
-   **pasta_audio/** → áudios em MP3\
-   **downloads/** → playlists organizadas

------------------------------------------------------------------------

## 🖥️ Como Executar

No terminal:

``` bash
python baixar_youtube.py
```

Menu principal:

    1 - Baixar Vídeo
    2 - Baixar MP3
    3 - Baixar Ambos
    4 - Baixar Lista de URLs
    5 - Baixar Playlist do YouTube

------------------------------------------------------------------------

## 🔢 Opções do Menu

### 1 - Baixar Vídeo

Baixa o vídeo completo e salva em `pasta_video/`.

### 2 - Baixar MP3

Baixa apenas o áudio (MP3) com tags ID3, salvo em `pasta_audio/`.

### 3 - Baixar Ambos

Baixa vídeo e áudio (MP3) simultaneamente.

### 4 - Baixar Lista de URLs

Baixa múltiplos vídeos ou áudios a partir de um arquivo `.txt` com URLs.

### 5 - Baixar Playlist do YouTube

Baixa automaticamente todos os vídeos de uma playlist, podendo numerar
arquivos.

------------------------------------------------------------------------

## ⚙️ Recursos Internos

-   Sanitização de nomes de arquivos\
-   Conversão automática para MP3\
-   Aplicação de metadados (tags ID3)\
-   Criação de pastas automáticas\
-   Fallback caso `ffmpeg` não esteja disponível

------------------------------------------------------------------------

## ⚠️ Observações

-   É necessária conexão com a internet.\
-   Não use o programa para contornar direitos autorais.\
-   Evite caminhos com caracteres especiais.

------------------------------------------------------------------------

## 🧾 Resumo das Saídas

  Tipo de Download   Pasta          Extensão      Inclui Tags
  ------------------ -------------- ------------- -------------
  Vídeo              pasta_video/   .mp4          Não
  Áudio              pasta_audio/   .mp3          Sim
  Ambos              Ambas          .mp4 + .mp3   Sim
