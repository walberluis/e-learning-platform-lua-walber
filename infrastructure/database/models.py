"""
Database models for the e-learning system.
Infrastructure Layer - Database Package
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from infrastructure.database.connection import Base

# Association table for User-Trilha relationship (many-to-many)
user_trilha_association = Table(
    'user_trilha',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('usuarios.id'), primary_key=True),
    Column('trilha_id', Integer, ForeignKey('trilhas.id'), primary_key=True)
)

class Usuario(Base):
    """
    User model representing learners in the system.
    Maps to the Usuario class in the class diagram.
    """
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    senha = Column(String(255), nullable=True)  # Hashed password
    perfil_aprend = Column(String(50), nullable=True)  # Learning profile
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    trilhas = relationship("Trilha", secondary=user_trilha_association, back_populates="usuarios")
    desempenhos = relationship("Desempenho", back_populates="usuario")
    sessoes_quiz = relationship("SessaoQuiz", back_populates="usuario")
    respostas_quiz = relationship("RespostaUsuario", back_populates="usuario")
    
    def __repr__(self):
        return f"<Usuario(id={self.id}, nome='{self.nome}', email='{self.email}')>"

class Trilha(Base):
    """
    Learning path model.
    Maps to the Trilha class in the class diagram.
    """
    __tablename__ = "trilhas"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    dificuldade = Column(String(20), nullable=False)  # beginner, intermediate, advanced
    criador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)  # User who created this trilha
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    criador = relationship("Usuario", foreign_keys=[criador_id])
    usuarios = relationship("Usuario", secondary=user_trilha_association, back_populates="trilhas")
    conteudos = relationship("Conteudo", back_populates="trilha")
    sessoes_quiz = relationship("SessaoQuiz", back_populates="trilha")
    
    def __repr__(self):
        return f"<Trilha(id={self.id}, titulo='{self.titulo}', dificuldade='{self.dificuldade}')>"

class Conteudo(Base):
    """
    Content model for learning materials.
    Maps to the Conteudo class in the class diagram.
    """
    __tablename__ = "conteudos"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    tipo = Column(String(50), nullable=False)  # video, text, quiz, exercise
    material = Column(Text, nullable=True)  # Content or path to content
    trilha_id = Column(Integer, ForeignKey("trilhas.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    trilha = relationship("Trilha", back_populates="conteudos")
    desempenhos = relationship("Desempenho", back_populates="conteudo")
    questoes = relationship("Questao", back_populates="conteudo")
    sessoes_quiz = relationship("SessaoQuiz", back_populates="conteudo")
    
    def __repr__(self):
        return f"<Conteudo(id={self.id}, titulo='{self.titulo}', tipo='{self.tipo}')>"

class Desempenho(Base):
    """
    Performance tracking model.
    Maps to the Desempenho class in the class diagram.
    """
    __tablename__ = "desempenhos"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    conteudo_id = Column(Integer, ForeignKey("conteudos.id"), nullable=False)
    progresso = Column(Float, default=0.0)  # Progress percentage (0-100)
    nota = Column(Float, nullable=True)  # Grade/score
    tempo_estudo = Column(Integer, default=0)  # Study time in minutes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    usuario = relationship("Usuario", back_populates="desempenhos")
    conteudo = relationship("Conteudo", back_populates="desempenhos")
    
    def __repr__(self):
        return f"<Desempenho(id={self.id}, usuario_id={self.usuario_id}, progresso={self.progresso})>"

class Questao(Base):
    """
    Question model for quizzes and assessments.
    """
    __tablename__ = "questoes"
    
    id = Column(Integer, primary_key=True, index=True)
    conteudo_id = Column(Integer, ForeignKey("conteudos.id"), nullable=False)
    pergunta = Column(Text, nullable=False)
    alternativas = Column(Text, nullable=False)  # JSON string with options a, b, c, d, e
    resposta_correta = Column(String(1), nullable=False)  # a, b, c, d, or e
    explicacao = Column(Text, nullable=True)
    ordem = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    conteudo = relationship("Conteudo", back_populates="questoes")
    respostas = relationship("RespostaUsuario", back_populates="questao")
    
    def __repr__(self):
        return f"<Questao(id={self.id}, conteudo_id={self.conteudo_id}, pergunta='{self.pergunta[:50]}...')>"

class SessaoQuiz(Base):
    """
    Quiz session model to track user quiz attempts.
    """
    __tablename__ = "sessoes_quiz"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    conteudo_id = Column(Integer, ForeignKey("conteudos.id"), nullable=False)
    trilha_id = Column(Integer, ForeignKey("trilhas.id"), nullable=False)
    total_questoes = Column(Integer, nullable=False)
    questao_atual = Column(Integer, default=1)
    respostas_corretas = Column(Integer, default=0)
    respostas_erradas = Column(Integer, default=0)
    status = Column(String(20), default="started")  # started, in_progress, completed, abandoned
    iniciado_em = Column(DateTime(timezone=True), server_default=func.now())
    completado_em = Column(DateTime(timezone=True), nullable=True)
    tempo_limite = Column(Integer, default=1800)  # 30 minutes in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    usuario = relationship("Usuario", back_populates="sessoes_quiz")
    conteudo = relationship("Conteudo", back_populates="sessoes_quiz")
    trilha = relationship("Trilha", back_populates="sessoes_quiz")
    respostas = relationship("RespostaUsuario", back_populates="sessao")
    
    def __repr__(self):
        return f"<SessaoQuiz(id={self.id}, usuario_id={self.usuario_id}, status='{self.status}')>"

class RespostaUsuario(Base):
    """
    User answer model for quiz questions.
    """
    __tablename__ = "respostas_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    sessao_id = Column(Integer, ForeignKey("sessoes_quiz.id"), nullable=False)
    questao_id = Column(Integer, ForeignKey("questoes.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    resposta_selecionada = Column(String(1), nullable=False)  # a, b, c, d, or e
    resposta_correta = Column(String(1), nullable=False)
    esta_correta = Column(Boolean, nullable=False)
    respondido_em = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sessao = relationship("SessaoQuiz", back_populates="respostas")
    questao = relationship("Questao", back_populates="respostas")
    usuario = relationship("Usuario", back_populates="respostas_quiz")
    
    def __repr__(self):
        return f"<RespostaUsuario(id={self.id}, questao_id={self.questao_id}, esta_correta={self.esta_correta})>"

class Chatbot(Base):
    """
    Chatbot interaction model.
    Maps to the Chatbot class in the class diagram.
    """
    __tablename__ = "chatbot_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), default="AI Assistant")
    tipo = Column(String(50), default="recommendation")  # recommendation, support, quiz
    linguagem_ia = Column(String(50), default="gemini")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Chatbot(id={self.id}, nome='{self.nome}', tipo='{self.tipo}')>"
