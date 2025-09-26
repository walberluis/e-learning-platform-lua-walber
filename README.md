# Sistema E-Learning com IA

Uma plataforma de e-learning moderna e inteligente que utiliza IA para personalizar a experiência de aprendizado, com arquitetura limpa, microserviços e integração com Google Gemini.

## Sobre o Projeto

O Sistema E-Learning com IA é uma plataforma educacional avançada que combina tecnologias modernas de desenvolvimento web com inteligência artificial para criar uma experiência de aprendizado personalizada e eficiente. O sistema foi projetado seguindo os princípios da Arquitetura Limpa (Clean Architecture), garantindo separação de responsabilidades, testabilidade e manutenibilidade.

### Características Principais

#### Inteligência Artificial
- **Recomendações Personalizadas**: Sistema de recomendação baseado em IA usando Google Gemini
- **Chatbot Inteligente**: Assistente virtual 24/7 com processamento de linguagem natural
- **Análise de Padrões**: Análise inteligente do comportamento de aprendizado
- **Scripts Lua**: Lógica de negócio implementada em Lua para flexibilidade

#### Gestão de Aprendizado
- **Trilhas Adaptativas**: Caminhos de aprendizado que se adaptam ao progresso do usuário
- **Acompanhamento de Progresso**: Métricas detalhadas e analytics em tempo real
- **Conteúdo Diversificado**: Suporte a vídeos, textos, quizzes e exercícios práticos
- **Avaliações Inteligentes**: Sistema de avaliação com feedback automático

#### Arquitetura Moderna
- **Arquitetura Limpa**: Separação clara de responsabilidades em camadas
- **API RESTful**: API completa com FastAPI e documentação automática
- **Frontend Responsivo**: Interface moderna com HTML5, CSS3 e JavaScript
- **Banco de Dados**: SQLite para desenvolvimento, PostgreSQL para produção

## Arquitetura do Sistema

O sistema segue os princípios da Arquitetura Limpa (Clean Architecture), organizando o código em camadas bem definidas:

### Camadas da Arquitetura

#### 1. Camada de Apresentação (Presentation Layer)
- **Responsabilidade**: Interface com o usuário e controle de entrada/saída
- **Componentes**:
  - API REST com FastAPI
  - Interface web HTML/CSS/JavaScript
  - Validação de entrada
  - Serialização de dados

#### 2. Camada de Negócio (Business Layer)
- **Responsabilidade**: Regras de negócio e lógica da aplicação
- **Componentes**:
  - Serviços de domínio
  - Casos de uso (Use Cases)
  - Entidades de negócio
  - Regras de validação

#### 3. Camada de Acesso a Dados (Data Access Layer)
- **Responsabilidade**: Persistência e recuperação de dados
- **Componentes**:
  - Repositórios
  - Mapeamento objeto-relacional
  - Queries e comandos
  - Cache de dados

#### 4. Camada de Infraestrutura (Infrastructure Layer)
- **Responsabilidade**: Detalhes técnicos e integrações externas
- **Componentes**:
  - Configuração de banco de dados
  - Integrações com APIs externas
  - Segurança e autenticação
  - Logging e monitoramento

### Fluxo de Dados

```
Frontend → API (Presentation) → Business Logic → Data Access → Database
                    ↓                ↓              ↓
                 Validation    Use Cases     Repositories
                    ↓                ↓              ↓
                 Response      Domain Logic    Infrastructure
```

### Tecnologias Utilizadas

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Banco de Dados**: SQLite (desenvolvimento), PostgreSQL (produção)
- **IA**: Google Gemini API
- **Scripts**: Lua para lógica de negócio
- **Autenticação**: JWT com Argon2 para hashing de senhas

## Pré-requisitos

### Desenvolvimento
- Python 3.11+
- Git
- Chave API do Google Gemini (opcional)

### Produção
- Servidor Linux (Ubuntu 20.04+ recomendado)
- Python 3.11+
- PostgreSQL (opcional, usa SQLite por padrão)
- Domínio e certificado SSL (opcional)
- Pelo menos 1GB RAM e 5GB de espaço em disco

## Instalação Rápida

### 1. Clone o Repositório
```bash
git clone <repository-url>
cd e-learning
```

### 2. Execute o Setup Automático

#### Linux/Mac/Windows (Git Bash):
```bash
chmod +x setup.sh
./setup.sh
```

O script irá:
- Verificar e instalar Python 3.11+
- Criar ambiente virtual
- Instalar todas as dependências
- Configurar banco de dados SQLite
- Criar dados de exemplo
- Iniciar a aplicação

### 3. Configure a API do Gemini (Opcional)
Edite o arquivo `.env` e adicione sua chave API:
```env
GEMINI_API_KEY=sua-chave-api-aqui
```

### 4. Acesse a Aplicação
- **Aplicação**: http://localhost:8000
- **Documentação da API**: http://localhost:8000/docs
- **API Interativa**: http://localhost:8000/redoc

## Instalação Manual

### 1. Ambiente Virtual Python
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configuração do Ambiente
```bash
# O arquivo .env será criado automaticamente pelo setup.sh
# Ou crie manualmente:
cat > .env << EOF
DEBUG=true
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./elearning.db
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key-here
EOF
```

### 3. Banco de Dados
```bash
# Inicializar banco SQLite (automático)
python -c "from infrastructure.database.connection import init_database; init_database()"

# Criar dados de exemplo (opcional)
python scripts/create_sample_data.py
```

### 4. Executar Aplicação
```bash
# Desenvolvimento
python -m uvicorn presentation.api.main:app --host 0.0.0.0 --port 8000 --reload

# Produção
python -m uvicorn presentation.api.main:app --host 0.0.0.0 --port 8000
```

## Estrutura do Projeto

```
e-learning/
├── infrastructure/           # Camada de Infraestrutura
│   ├── database/            # Configuração do banco de dados
│   ├── security/            # Autenticação e segurança
│   └── integration/         # Integrações externas (Gemini, Redis)
├── data_access/             # Camada de Acesso a Dados
│   ├── repositories/        # Padrão Repository
│   └── external_services/   # Serviços externos
├── business/                # Camada de Negócio
│   ├── core/               # Lógica central
│   ├── learning/           # Gestão de aprendizado
│   └── ai/                 # Serviços de IA
├── presentation/            # Camada de Apresentação
│   ├── api/                # Endpoints FastAPI
│   └── web/                # Frontend HTML/CSS/JS
├── lua_bridge/             # Integração Python-Lua
├── lua_core/               # Scripts Lua para lógica de negócio
├── scripts/                # Scripts utilitários
└── docs/                   # Documentação
```

## API Endpoints

### Usuários
- `POST /api/v1/users/` - Criar usuário
- `GET /api/v1/users/{id}` - Obter perfil do usuário
- `PUT /api/v1/users/{id}` - Atualizar usuário
- `GET /api/v1/users/{id}/analytics` - Analytics do usuário

### Trilhas de Aprendizado
- `GET /api/v1/trilhas/` - Listar trilhas
- `POST /api/v1/trilhas/` - Criar trilha
- `GET /api/v1/trilhas/{id}` - Detalhes da trilha
- `POST /api/v1/trilhas/{id}/enroll` - Inscrever-se na trilha

### Chatbot IA
- `POST /api/v1/chatbot/chat/{user_id}` - Conversar com o bot
- `GET /api/v1/chatbot/history/{user_id}` - Histórico de conversas
- `POST /api/v1/chatbot/quick-help/{user_id}` - Ajuda rápida

### Recomendações IA
- `GET /api/v1/recommendations/{user_id}` - Recomendações personalizadas
- `POST /api/v1/recommendations/analyze/{user_id}` - Análise de padrões
- `POST /api/v1/recommendations/search` - Busca inteligente

## Testes

### Executar Testes
```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Executar testes
pytest

# Testes com cobertura
pytest --cov=.

# Testes específicos
pytest tests/test_api.py
```

### Teste Manual da API
```bash
# Health check
curl http://localhost:8000/health

# Criar usuário
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Teste", "email": "teste@example.com", "perfil_aprend": "beginner"}'
```

## Configuração

### Variáveis de Ambiente (.env)
```env
# Banco de Dados
DATABASE_URL=postgresql://user:pass@localhost:5432/elearning_db
POSTGRES_USER=elearning_user
POSTGRES_PASSWORD=elearning_pass
POSTGRES_DB=elearning_db

# Segurança
SECRET_KEY=sua-chave-secreta-super-segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google Gemini API
GEMINI_API_KEY=sua-chave-api-gemini

# Redis
REDIS_URL=redis://localhost:6379/0

# Aplicação
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

## Integração com IA

### Google Gemini
A plataforma utiliza o Google Gemini para:
- Gerar recomendações personalizadas
- Processar conversas do chatbot
- Analisar conteúdo de aprendizado
- Identificar padrões de comportamento

### Scripts Lua
Lógica de negócio implementada em Lua para:
- Análise de intenções do chatbot
- Cálculo de pontuações de recomendação
- Processamento de regras de negócio
- Validações customizadas

## Monitoramento

### Métricas Disponíveis
- Usuários ativos
- Taxa de conclusão de trilhas
- Tempo médio de estudo
- Eficácia das recomendações IA
- Performance do sistema

### Logs
```bash
# Logs da aplicação
tail -f logs/app.log

# Logs de erro
tail -f logs/error.log

# Logs de acesso
tail -f logs/access.log
```

## Deploy em Produção

### 1. Preparação do Servidor
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Instalar PostgreSQL (opcional)
sudo apt install postgresql postgresql-contrib
```

### 2. Configuração de Produção
```bash
# Clonar repositório
git clone <repository-url>
cd e-learning

# Configurar ambiente
cp env.example .env
# Editar .env com configurações de produção

# Executar setup
./setup.sh
```

### 3. Configuração do Nginx (Opcional)
```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /path/to/static/files/;
        expires 1y;
    }
}
```

### 4. SSL/HTTPS (Opcional)
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com
```

## Contribuição

### Como Contribuir
1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código
- Seguir PEP 8 para Python
- Usar type hints
- Documentar funções e classes
- Escrever testes para novas funcionalidades
- Manter cobertura de testes > 80%

## Suporte

### Problemas Comuns

#### Erro de Conexão com Banco
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Reiniciar serviços
sudo systemctl restart postgresql
```

#### Erro na API do Gemini
```bash
# Verificar chave API no .env
grep GEMINI_API_KEY .env

# Testar conexão
python -c "import google.generativeai as genai; genai.configure(api_key='sua-chave'); print('OK')"
```

#### Problemas de Performance
```bash
# Verificar uso de recursos
htop

# Verificar logs de erro
tail -f logs/error.log
```
