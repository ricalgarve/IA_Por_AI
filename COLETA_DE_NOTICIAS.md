# Estratégia de Coleta de Notícias (Grátis e Legal)

Para o projeto **IA por AI**, utilizaremos métodos gratuitos e legais para buscar as últimas notícias sobre Inteligência Artificial. Evitaremos APIs pagas (como NewsAPI), focando no uso de RSS Feeds públicos e bibliotecas especializadas em Python. Essa abordagem funciona perfeitamente no ambiente do FastAPI e é facilmente hospedável no Vercel (que impõe limitações de uso e necessita de soluções "serverless" amigáveis).

---

## 1. Ferramentas e Bibliotecas

As seguintes bibliotecas (já incluídas no `requirements.txt`) serão o núcleo do nosso motor de busca:

- **`feedparser`**: Para buscar e interpretar feeds RSS clássicos.
- **`pygooglenews`**: Para extrair tópicos quentes do Google News de forma estruturada.
- **`newspaper3k`**: Para fazer o download e raspagem (*scraping*) limpa do conteúdo completo da notícia (se necessário extrair um bom resumo).

*Comando de instalação geral:*
```bash
pip install feedparser pygooglenews newspaper3k
```

---

## 2. Abordagens Práticas

### A. Buscando Feeds Diretos com `feedparser`
Esta é a maneira mais confiável e estável de se obter conteúdo de portais que disponibilizam suas notícias de propósito.

**Exemplo de implementação (Adaptado para o FastAPI):**
```python
import feedparser

def fetch_rss_news():
    feeds = [
        "https://feeds.feedburner.com/TechCrunch",
        "https://venturebeat.com/category/ai/feed/"
    ]
    
    articles = []
    for feed_url in feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]: # Pegando as 5 mais recentes
            articles.append({
                "title": entry.title,
                "url": entry.link,
                "source": feed.feed.title,
                "published": entry.published
            })
    return articles
```
**Vantagens:** 
- Grátis e sem limites de requisições rígidos (Rate Limits).
- Totalmente legal.

### B. Usando o `pygooglenews` (Foco em tendências)
Isso nos permite simular a aba de notícias do Google de forma elegante, focando apenas no tema "inteligência artificial". Perfeito para classificar as notícias em "Quentes" (Hot) baseado no ranqueamento do Google.

```python
from pygooglenews import GoogleNews

def fetch_google_news_ai():
    gn = GoogleNews(lang='pt', country='BR')
    search_results = gn.search('inteligência artificial', when='1d')
    
    articles = []
    for item in search_results['entries'][:5]:
        articles.append({
            "title": item['title'],
            "url": item['link'],
            "source": item['source']['title']
        })
    return articles
```

### C. Extração Profunda com `newspaper3k`
Às vezes, os feeds RSS retornam apenas um título ou um resumo muito curto. Com o URL em mãos, podemos usar o `newspaper3k` para ler o artigo, extrair a imagem principal e gerar um resumo para exibir no frontend.

```python
from newspaper import Article

def get_article_summary(url):
    article = Article(url, language='pt')
    article.download()
    article.parse()
    article.nlp() # Necessário para resumos automáticos
    
    return {
        "title": article.title,
        "summary": article.summary, # Resumo gerado
        "text": article.text[:200]  # Os primeiros 200 caracteres
    }
```

---

## 3. Fontes de RSS Selecionadas (Foco em IA e Tecnologia)

Estes são os **endpoints sugeridos** para alimentarmos o sistema com dados reais em breve:

| Fonte | URL do RSS Feed | Foco |
| :--- | :--- | :--- |
| **Google News (PT-BR)** | `https://news.google.com/rss/search?q=IA+inteligência+artificial` | Geral / Destaques |
| **Canaltech (IA)** | `https://canaltech.com.br/rss/ia/` | Mercado BR |
| **TechCrunch (Agregado)** | `https://feeds.feedburner.com/TechCrunch` | Mercado Global / Startups |
| **VentureBeat AI** | `https://venturebeat.com/category/ai/feed/` | Especializado em IA |
| **MIT Tech Review** | `https://www.technologyreview.com/feed/` | Avanços Científicos |

---

## Próximos Passos
Em nossa próxima sessão de programação, iremos substituir o `MOCK_NEWS` no arquivo `main.py` por uma função assíncrona que coleta as informações usando uma combinação dessas abordagens, determina a "temperatura" (Quente, Morna, Fria) da notícia baseado na sua idade ou fonte, e envia para o frontend Tailwind que acabamos de estilizar.
