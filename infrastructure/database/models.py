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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    usuarios = relationship("Usuario", secondary=user_trilha_association, back_populates="trilhas")
    conteudos = relationship("Conteudo", back_populates="trilha")
    
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
