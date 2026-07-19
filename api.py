import os
# Redireciona a pasta temporária para a pasta do projeto, evitando erros do Windows na pasta Temp padrão
project_path = os.path.abspath(os.path.dirname(__file__))
os.environ['TEMP'] = project_path
os.environ['TMP'] = project_path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from main import scrape_places, Place
from dataclasses import asdict

app = FastAPI(
    title="Google Maps Scraper API",
    description="API local para extrair dados do Google Maps usando Playwright",
    version="1.0.0"
)

class ScrapeRequest(BaseModel):
    search: str = Field(..., description="Termo de busca no Google Maps")
    total: int = Field(10, description="Quantidade de resultados a extrair")

@app.post("/scrape")
def run_scraper(request: ScrapeRequest):
    try:
        search_query = request.search.strip()
        if not search_query:
            raise HTTPException(status_code=400, detail="O termo de busca não pode ser vazio.")
        
        places = scrape_places(search_query, request.total)
        # Converte as dataclasses para dicionários para que o FastAPI serialize como JSON
        return [asdict(place) for place in places]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante o scraping: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    from pyngrok import ngrok, conf
    
    # Define o caminho do binário do Ngrok na pasta do projeto para evitar erros de permissão na pasta Temp do Windows
    project_dir = os.path.abspath(os.path.dirname(__file__))
    conf.get_default().ngrok_path = os.path.join(project_dir, "ngrok.exe")
    
    # Tenta abrir o túnel do Ngrok se houver token configurado
    try:
        port = 8000
        public_url = ngrok.connect(port).public_url
        print("\n========================================================", flush=True)
        print("          NGROK TÚNEL ATIVADO COM SUCESSO!", flush=True)
        print(f"  API Pública no endereço: {public_url}", flush=True)
        print(f"  Exemplo de requisição: POST {public_url}/scrape", flush=True)
        print("========================================================\n", flush=True)
    except Exception as e:
        print("\n[Aviso] Não foi possível iniciar o túnel Ngrok.", flush=True)
        print("Certifique-se de ter configurado o token rodando o 'configurar_token.bat'", flush=True)
        print(f"Erro detalhado: {e}\n", flush=True)
        print("Iniciando a API apenas no modo local (localhost)...", flush=True)
        print("========================================================\n", flush=True)

    # Roda o servidor localmente na porta 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
