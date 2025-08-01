# PostMSocial

## Visão Geral

O **PostMSocial** é um conjunto de ferramentas de linha de comando em Python para automatizar o download de vídeos de plataformas como TikTok e YouTube. Ele permite que os usuários encontrem conteúdo com base em hashtags, termos de pesquisa ou tendências e, em seguida, baixem os vídeos para uso posterior. O projeto também inclui um script para fazer o upload automático dos vídeos baixados para o YouTube.

## Obtendo a Versão Mais Recente

Para garantir que você tenha a versão mais atual do projeto, use o comando `git pull` no diretório do projeto:

```bash
git pull origin main  # Ou o nome da branch principal
```

## Funcionalidades

-   **Download de Vídeos do TikTok**:
    -   Busca as hashtags mais populares (trending).
    -   Permite ao usuário escolher hashtags e o número de vídeos a serem baixados.
    -   Baixa vídeos de links autorizados.
-   **Download de Vídeos do YouTube**:
    -   Busca vídeos com base em termos de pesquisa.
    -   Filtra os resultados para incluir apenas vídeos enviados nas últimas 24 horas.
    -   Ordena os vídeos por número de visualizações.
    -   Exibe informações detalhadas sobre os vídeos antes de baixar.
    -   Busca os vídeos mais vistos nas últimas 24 horas.
-   **Upload para o YouTube**:
    -   Faz o upload de arquivos de vídeo `.mp4` da pasta `downloads`.
    -   Utiliza a API de Dados do YouTube v3 para o upload.
    -   Gerencia a autenticação com o OAuth 2.0.

## Estrutura do Projeto

```
/
├─── .gitignore
├─── README.md
├─── requirements.txt
├─── controles/
│    ├─── downloadtiktok.py
│    ├─── downloadyoutube_v1.py
│    ├─── downloadyoutube.py
│    ├─── downloadyoutube24henviadoemaisvistos.py
│    ├─── downloadyoutube24hmaisvistos.py
│    ├─── downloadyoutubecomdescricoesdetalhada.py
│    ├─── postautomaticoyoutube.py
│    └─── downloads/
└─── venv/
```

-   **`controles/`**: Contém os scripts principais do projeto.
    -   **`downloadtiktok.py`**: Script para baixar vídeos do TikTok.
    -   **`downloadyoutube.py`**: Script para baixar vídeos do YouTube com base em termos de pesquisa.
    -   **`downloadyoutube24henviadoemaisvistos.py`**: Script para baixar os vídeos mais vistos no YouTube nas últimas 24 horas.
    -   **`postautomaticoyoutube.py`**: Script para fazer o upload de vídeos para o YouTube.
-   **`downloads/`**: Pasta onde os vídeos baixados são salvos.
-   **`requirements.txt`**: Lista as dependências do Python.

## Como Usar

### 1. Instalação Detalhada

Siga os passos abaixo para configurar o ambiente do projeto:

1.  **Clone o Repositório**:

    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd PostMSocial
    ```

2.  **Crie e Ative o Ambiente Virtual**:
    É uma boa prática usar um ambiente virtual para isolar as dependências do projeto.

    ```bash
    # Crie o ambiente virtual
    python -m venv venv

    # Ative o ambiente (Linux/macOS)
    source venv/bin/activate

    # Ative o ambiente (Windows)
    .\venv\Scripts\activate
    ```

3.  **Instale as Dependências**:
    As dependências estão listadas no arquivo `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

4.  **Instale os Navegadores do Playwright**:
    O Playwright requer que os navegadores que ele controla sejam instalados.

    ```bash
    playwright install
    ```

### 2. Configuração

-   **API do YouTube**: Para usar o script de upload (`postautomaticoyoutube.py`), você precisa de credenciais da API do YouTube.
    1.  Acesse o [Google Cloud Console](https://console.cloud.google.com/).
    2.  Crie um novo projeto.
    3.  Ative a **API de Dados do YouTube v3**.
    4.  Crie credenciais do tipo **"Tela de consentimento OAuth"** e configure-a.
    5.  Crie credenciais do tipo **"ID do cliente OAuth"** para um aplicativo **"Computador"**.
    6.  Baixe o arquivo JSON das credenciais e renomeie-o para `credentials.json` na pasta `controles`.

### 3. Execução dos Scripts

Execute os scripts a partir da pasta `controles`:

```bash
cd controles
```

-   **Para baixar do TikTok**:

    ```bash
    python downloadtiktok.py
    ```

-   **Para baixar do YouTube por termo**:

    ```bash
    python downloadyoutube.py
    ```

-   **Para baixar os mais vistos do YouTube**:

    ```bash
    python downloadyoutube24hmaisvistos.py
    ```

-   **Para fazer o upload para o YouTube**:
    A primeira vez que você executar, será necessário autorizar o aplicativo através do seu navegador.

    ```bash
    python postautomaticoyoutube.py
    ```

## Dependências

As principais dependências incluem:

-   `playwright`: Para automação de navegador e web scraping.
-   `yt-dlp`: Para baixar vídeos do YouTube e outras plataformas.
-   `google-api-python-client`: Para interagir com a API do YouTube.
-   `google-auth-oauthlib`: Para autenticação com a API do YouTube.

Consulte o arquivo `requirements.txt` para a lista completa.