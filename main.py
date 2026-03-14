import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Notícias Rápidas")

# Define base path to ensure templates are found whether run locally or on Vercel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

MOCK_NEWS = [
    {
        "id": 1,
        "title": "Avanços em Inteligência Artificial Prometem Revolucionar a Medicina",
        "description": "Pesquisadores ao redor do mundo estão utilizando modelos de IA generativa para acelerar a descoberta de novos medicamentos e otimizar processos de diagnóstico. Em um estudo recente, um novo modelo foi testado com sucesso, identificando com precisão anomalias em exames de imagem que escapariam a olhos não treinados. Especialistas acreditam que, nos próximos anos, a adoção destas ferramentas reduzirá o tempo no diagnóstico precoce de doenças graves, melhorando o tratamento para milhares de pacientes e ajudando a personalizar os tratamentos de acordo com o padrão genético de cada indivíduo, elevando a medicina moderna ao próximo nível.",
        "source": "Tech Health Journal",
        "link": "https://example.com/noticia-ia",
        "temperature": "hot"
    },
    {
        "id": 2,
        "title": "Mercado Financeiro Adota Algoritmos Quânticos para Previsões",
        "description": "Instituições financeiras estão investindo pesado em computação quântica para modelagem de risco e projeções de mercado. O uso de qubits permite a simulação de múltiplos cenários econômicos simultaneamente, algo impossível de ser alcançado com a mesma velocidade em supercomputadores clássicos. Um grande banco europeu anunciou recentemente que sua nova plataforma quântica conseguiu processar em minutos cálculos que levariam semanas, proporcionando vantagens competitivas únicas. Apesar do alto custo inicial, a expectativa de longo prazo é de um grande retorno.",
        "source": "Economia Quântica",
        "link": "https://example.com/noticia-quantica",
        "temperature": "warm"
    },
    {
        "id": 3,
        "title": "Novas Tecnologias de Baterias Aumentam Autonomia de Veículos Elétricos",
        "description": "Com o avanço das baterias de estado sólido, a indústria automotiva prevê um salto substancial na autonomia dos veículos elétricos (VEs) ainda nesta década. Diversas startups relataram progressos na estabilidade de seus protótipos, que são capazes de oferecer até o dobro de densidade energética em comparação às tradicionais baterias de íons de lítio. Além disso, essa nova geração de baterias promete tempos de recarga ultra rápidos e muito mais segurança, reduzindo riscos de incêndio e superaquecimento durante o uso contínuo das células.",
        "source": "Auto Tech News",
        "link": "https://example.com/noticia-baterias",
        "temperature": "cold"
    },
    {
        "id": 4,
        "title": "Exploração Espacial: Nova Missão Comercial Planejada para Marte",
        "description": "Uma coalizão de empresas aeroespaciais anunciou hoje o lançamento de uma missão conjunta para estabelecer a primeira base de pesquisa comercial no planeta vermelho. Com o apoio de inovações em propulsão nuclear térmica e sistemas avançados de suporte à vida, a viagem deverá ser mais curta e segura para os astronautas. A missão visa explorar minerais raros e realizar testes biológicos sob condições extremas de gravidade reduzida, marcando definitivamente uma nova fase na corrida espacial e ampliando os horizontes da exploração interplanetária.",
        "source": "Galactic Times",
        "link": "https://example.com/noticia-espaco",
        "temperature": "hot"
    }
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "news": MOCK_NEWS})
