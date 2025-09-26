# 🧪 Guia de Testes - Sistema E-Learning

Este guia fornece instruções detalhadas para testar todas as funcionalidades do sistema e-learning, incluindo a feature de recomendações IA que passa por todas as camadas da arquitetura.

## 🚀 Preparação para Testes

### 1. Configuração Inicial
```bash
# Execute o setup
./setup.sh  # Linux/Mac
# ou
setup.bat   # Windows

# Aguarde todos os serviços iniciarem
docker-compose ps
```

### 2. Verificação dos Serviços
```bash
# Verificar saúde da aplicação
curl http://localhost:8000/health

# Verificar API status
curl http://localhost:8000/api/v1/status
```

### 3. Configurar Chave do Gemini
Edite o arquivo `.env` e adicione sua chave API do Google Gemini:
```env
GEMINI_API_KEY=sua-chave-api-aqui
```

## 🎯 Testando a Feature Principal: Recomendações IA

Esta feature demonstra o fluxo completo através de todas as camadas da arquitetura.

### Camada 1: Infraestrutura
**Teste da conexão com banco de dados e IA:**

```bash
# Testar conexão com PostgreSQL
docker-compose exec postgres psql -U elearning_user -d elearning_db -c "SELECT version();"

# Testar Redis
docker-compose exec redis redis-cli ping

# Testar integração Gemini (via Python)
python -c "
from infrastructure.integration.gemini_client import gemini_client
import asyncio
async def test():
    try:
        response = await gemini_client.generate_chatbot_response('Hello', {})
        print('✓ Gemini API conectado')
        return True
    except Exception as e:
        print(f'✗ Erro Gemini: {e}')
        return False
asyncio.run(test())
"
```

### Camada 2: Acesso a Dados
**Teste dos repositórios:**

```bash
# Testar criação de usuário via API
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Teste",
    "email": "joao@teste.com",
    "perfil_aprend": "beginner"
  }'
```

**Resposta esperada:**
```json
{
  "success": true,
  "message": "User created successfully",
  "data": {
    "id": 1,
    "nome": "João Teste",
    "email": "joao@teste.com",
    "perfil_aprend": "beginner"
  }
}
```

### Camada 3: Lógica de Negócio
**Teste do sistema de recomendações:**

```bash
# Obter recomendações IA para o usuário
curl "http://localhost:8000/api/v1/recommendations/1"
```

**Resposta esperada:**
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "ai_recommendations": "Baseado no seu perfil iniciante...",
    "structured_recommendations": {
      "content_recommendations": [
        {
          "type": "trilha",
          "titulo": "Python para Iniciantes",
          "dificuldade": "beginner",
          "reason": "Matches your beginner learning profile",
          "confidence": 0.85
        }
      ]
    }
  }
}
```

### Camada 4: Apresentação
**Teste da interface web:**

1. Acesse http://localhost:8000
2. Clique em "Cadastrar"
3. Preencha o formulário de registro
4. Faça login
5. Navegue para o Dashboard
6. Verifique as recomendações personalizadas

## 🤖 Testando o Chatbot IA

### Via API
```bash
# Enviar mensagem para o chatbot
curl -X POST "http://localhost:8000/api/v1/chatbot/chat/1" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Me recomende um curso de Python",
    "context": {"current_course": null}
  }'
```

### Via Interface Web
1. Acesse a seção "Assistente IA"
2. Digite: "Me recomende um curso"
3. Verifique a resposta inteligente
4. Teste os botões de ação rápida

## 📚 Testando Trilhas de Aprendizado

### 1. Listar Trilhas
```bash
curl "http://localhost:8000/api/v1/trilhas/"
```

### 2. Inscrever-se em Trilha
```bash
curl -X POST "http://localhost:8000/api/v1/trilhas/1/enroll" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

### 3. Atualizar Progresso
```bash
curl -X POST "http://localhost:8000/api/v1/trilhas/progress/update" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "conteudo_id": 1,
    "progresso": 75,
    "nota": 85,
    "tempo_estudo": 30
  }'
```

## 📊 Testando Analytics e Dashboard

### 1. Obter Analytics do Usuário
```bash
curl "http://localhost:8000/api/v1/users/1/analytics?days=30"
```

### 2. Verificar Dashboard
1. Faça login na interface web
2. Acesse o Dashboard
3. Verifique:
   - Progresso geral
   - Trilhas ativas
   - Tempo de estudo
   - Sequência de aprendizado
   - Recomendações personalizadas

## 🔍 Testando Busca Inteligente

### Via API
```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python programming",
    "content_type": "course",
    "difficulty": "beginner",
    "limit": 10
  }'
```

### Via Interface
1. Acesse a seção "Trilhas"
2. Use os filtros de dificuldade
3. Teste a busca por termos específicos

## 🧪 Testes Automatizados

### Executar Suite de Testes
```bash
# Ativar ambiente virtual
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instalar dependências de teste
pip install pytest pytest-asyncio httpx

# Executar testes
pytest tests/ -v

# Testes com cobertura
pytest tests/ --cov=. --cov-report=html
```

### Testes Específicos
```bash
# Testar apenas API
pytest tests/test_api.py

# Testar repositórios
pytest tests/test_repositories.py

# Testar IA
pytest tests/test_ai.py
```

## 🔄 Testando Fluxo Completo

### Cenário: Novo Usuário até Recomendação

1. **Criar Usuário** (Camada de Apresentação → Negócio → Dados → Infraestrutura)
```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Maria Silva",
    "email": "maria@exemplo.com",
    "perfil_aprend": "intermediate"
  }'
```

2. **Inscrever em Trilha** (Todas as camadas)
```bash
curl -X POST "http://localhost:8000/api/v1/trilhas/1/enroll" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2}'
```

3. **Simular Progresso** (Camada de Negócio + Dados)
```bash
curl -X POST "http://localhost:8000/api/v1/trilhas/progress/update" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "conteudo_id": 1,
    "progresso": 50,
    "tempo_estudo": 25
  }'
```

4. **Obter Recomendações IA** (Todas as camadas + IA)
```bash
curl "http://localhost:8000/api/v1/recommendations/2"
```

5. **Conversar com Chatbot** (IA + Lua Scripts)
```bash
curl -X POST "http://localhost:8000/api/v1/chatbot/chat/2" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Como está meu progresso?",
    "context": {}
  }'
```

## 🐛 Testes de Erro e Edge Cases

### 1. Usuário Inexistente
```bash
curl "http://localhost:8000/api/v1/users/999"
# Deve retornar 404
```

### 2. Dados Inválidos
```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{"nome": "", "email": "email-inválido"}'
# Deve retornar erro de validação
```

### 3. API Gemini Indisponível
```bash
# Temporariamente remover/invalidar GEMINI_API_KEY no .env
# Testar recomendações - deve falhar graciosamente
```

## 📈 Testes de Performance

### 1. Teste de Carga Básico
```bash
# Instalar Apache Bench
sudo apt install apache2-utils  # Linux
brew install httpie            # Mac

# Teste de carga
ab -n 100 -c 10 http://localhost:8000/health
```

### 2. Teste de Concorrência
```bash
# Múltiplas requisições simultâneas
for i in {1..10}; do
  curl "http://localhost:8000/api/v1/trilhas/" &
done
wait
```

## 🔧 Troubleshooting

### Problemas Comuns

#### Serviços não iniciam
```bash
# Verificar logs
docker-compose logs

# Reiniciar serviços
docker-compose restart
```

#### Erro de conexão com banco
```bash
# Verificar PostgreSQL
docker-compose exec postgres pg_isready -U elearning_user

# Recriar banco se necessário
docker-compose down -v
docker-compose up -d postgres
```

#### API Gemini não responde
```bash
# Verificar chave API
grep GEMINI_API_KEY .env

# Testar conectividade
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key:', os.getenv('GEMINI_API_KEY')[:10] + '...' if os.getenv('GEMINI_API_KEY') else 'Not found')
"
```

## ✅ Checklist de Testes

### Funcionalidades Básicas
- [ ] Criar usuário
- [ ] Fazer login/logout
- [ ] Listar trilhas
- [ ] Inscrever-se em trilha
- [ ] Atualizar progresso
- [ ] Ver dashboard

### IA e Recomendações
- [ ] Obter recomendações personalizadas
- [ ] Chatbot responde adequadamente
- [ ] Análise de padrões funciona
- [ ] Scripts Lua executam corretamente

### Interface Web
- [ ] Navegação entre seções
- [ ] Formulários funcionam
- [ ] Responsividade mobile
- [ ] Chatbot interface

### API
- [ ] Todos endpoints respondem
- [ ] Validação de dados
- [ ] Tratamento de erros
- [ ] Documentação acessível

### Infraestrutura
- [ ] Docker containers rodando
- [ ] Banco de dados acessível
- [ ] Redis funcionando
- [ ] Nginx proxy ativo

## 📝 Relatório de Testes

Após executar os testes, documente:

1. **Funcionalidades testadas**
2. **Resultados obtidos**
3. **Problemas encontrados**
4. **Performance observada**
5. **Sugestões de melhoria**

---

**🎉 Parabéns! Se todos os testes passaram, sua plataforma e-learning com IA está funcionando perfeitamente!**
