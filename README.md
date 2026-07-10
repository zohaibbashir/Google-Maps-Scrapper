# Google Maps Scraper (Versao Aprimorada / Enhanced Version)

> [!NOTE]
> **Creditos / Credits:** Este projeto e uma versao aprimorada do projeto original criado por [zohaibbashir/Google-Maps-Scrapper](https://github.com/zohaibbashir/Google-Maps-Scrapper). Mantemos o script original com melhorias de robustez e adicionamos uma nova camada de API local integrada ao Ngrok.

This Python script utilizes the Playwright library to perform web scraping and data extraction from Google Maps. It is designed for obtaining information about businesses, including their name, address, website, phone number, reviews, and more.

---

## 🚀 Novas Funcionalidades (Versao Aprimorada)

Além do script original em linha de comando, esta versão traz as seguintes melhorias:
1. **API Local (FastAPI)**: Servidor local pronto para receber requisições de outros sistemas externos.
2. **Integração com Ngrok**: Exposição automática da API local na internet pública de forma segura, contornando limitações de pastas temporárias do Windows.
3. **Divisão de Horários**: Extração independente dos horários de **abertura** (`opens_at`) e **fechamento** (`closes_at`).
4. **Resoluções de Bugs**:
   - Correção na paginação de contagem de avaliações (suporte ao formato brasileiro, ex: `4.704` avaliações).
   - Prevenção de perda de colunas ao gerar arquivos CSV com um único resultado.

---

## 🛠️ Requisitos / Prerequisites
- **Python 3.13+** (ou versões estáveis compatíveis).
- **Google Chrome** ou **Chromium** instalado.

---

## 📦 Como Instalar

1. Clone o repositório:
   ```bash
   git clone <url-do-seu-repositorio>
   cd zohaibbashir-scraper
   ```
2. Crie e ative seu ambiente virtual:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

---

## 📡 Como Usar a API (Modo Servidor com Ngrok)

Para expor o servidor local na internet pública de forma segura:

### Passo 1: Configurar seu Token do Ngrok
1. Obtenha seu Authtoken gratuito criando uma conta em [ngrok.com](https://ngrok.com).
2. Dê dois cliques no arquivo **`configurar_token.bat`** na pasta do projeto.
3. Cole o seu token no terminal e pressione **Enter**.

### Passo 2: Ligar a API
1. Dê dois cliques no arquivo **`iniciar_api.bat`**.
2. O servidor iniciará e gerará automaticamente uma URL pública do Ngrok, por exemplo:
   ```text
   ========================================================
             NGROK TÚNEL ATIVADO COM SUCESSO!
     API Pública no endereço: https://xxxx-xxxx.ngrok-free.app
     Exemplo de requisição: POST https://xxxx-xxxx.ngrok-free.app/scrape
   ========================================================
   ```

### Passo 3: Enviar Requisição POST
Envie uma chamada **POST** em formato JSON para a URL pública gerada ou para a local (`http://127.0.0.1:8000/scrape`):

**Corpo (JSON):**
```json
{
  "search": "cafeteria abreu e lima",
  "total": 1
}
```

**Exemplo de Resposta (JSON):**
```json
[
  {
    "name": "Arte Café 81",
    "address": "R. Cento e Quarenta e Oito, 436 - Caetés I, Abreu e Lima - PE, 53530-380",
    "website": "",
    "phone_number": "(81) 98793-6047",
    "reviews_count": 12,
    "reviews_average": 5.0,
    "store_shopping": "No",
    "in_store_pickup": "No",
    "store_delivery": "No",
    "place_type": "Cafeteria",
    "opens_at": "09:00",
    "closes_at": "17:00",
    "introduction": "None Found"
  }
]
```

---

## 💻 Como Usar via Linha de Comando (CLI)

Você também pode executar diretamente pelo terminal ou usando o script interativo **`iniciar.bat`**:

```bash
python main.py -s "Turkish Restaurants in Toronto Canada" -t 20
```

- `-s` ou `--search`: Termo de busca (ex: "restaurantes recife").
- `-t` or `--total`: Quantidade máxima de resultados (padrão: 1).
- `-o` or `--output`: Caminho do arquivo CSV de saída (padrão: `result.csv`).
- `--append`: Adiciona os resultados ao fim do arquivo CSV em vez de sobrescrevê-lo.

---

## 📄 License
MIT License.
