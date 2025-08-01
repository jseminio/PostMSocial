# Histórico de Alterações (Changelog)

Este arquivo documenta todas as interações e modificações feitas no projeto através do Gemini CLI.

## 2025-08-01 (Refatoração)

-   **Reorganização da Estrutura de Pastas**
    -   **Ação**: Movidos os scripts para a pasta `controles/` e os arquivos de credenciais para a pasta `credenciais/`.
    -   **Resultado**:
        -   Caminhos de importação e de acesso a arquivos atualizados nos scripts para refletir a nova estrutura.
        -   O arquivo `.gitignore` foi atualizado para ignorar a pasta `credenciais/`.
        -   A documentação (`README.md`) foi atualizada para refletir a nova estrutura de pastas e os novos comandos.
    -   **Solicitado por**: Usuário.
    -   **Observações**: Esta refatoração melhora a organização e a segurança do projeto, separando o código, os dados e as credenciais.

## 2025-08-01

-   **Análise e Documentação Inicial**
    -   **Ação**: Realizada uma análise completa da estrutura e dos arquivos do projeto.
    -   **Resultado**:
        -   Criação de um `README.md` detalhado com a visão geral do projeto, funcionalidades, estrutura de pastas, guia de uso e dependências.
        -   Criação deste arquivo `CHANGELOG.md` para rastrear futuras alterações.
    -   **Solicitado por**: Usuário.
    -   **Observações**: A análise identificou múltiplos scripts para download de vídeos do TikTok e YouTube, além de um script para upload automático para o YouTube.