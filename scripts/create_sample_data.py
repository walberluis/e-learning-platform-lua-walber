#!/usr/bin/env python3
"""
Script to create sample data for the e-learning platform.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.database.connection import SessionLocal
from infrastructure.database.models import Usuario, Trilha, Conteudo, Desempenho
from datetime import datetime

def create_sample_data():
    """Create sample data for testing."""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Usuario).count() > 0:
            print("Sample data already exists. Skipping...")
            return
        
        print("Creating sample data...")
        
        # Create sample users
        users = [
            Usuario(
                nome="Daniel Silva",
                email="daniel@example.com",
                perfil_aprend="intermediate"
            ),
            Usuario(
                nome="Maria Santos",
                email="maria@example.com", 
                perfil_aprend="beginner"
            ),
            Usuario(
                nome="João Oliveira",
                email="joao@example.com",
                perfil_aprend="advanced"
            )
        ]
        
        for user in users:
            db.add(user)
        
        # Create sample trilhas
        trilhas = [
            Trilha(
                titulo="Python para Iniciantes",
                dificuldade="beginner"
            ),
            Trilha(
                titulo="JavaScript Avançado",
                dificuldade="intermediate"
            ),
            Trilha(
                titulo="Machine Learning com Python",
                dificuldade="advanced"
            ),
            Trilha(
                titulo="Desenvolvimento Web Full Stack",
                dificuldade="intermediate"
            ),
            Trilha(
                titulo="Data Science Fundamentals",
                dificuldade="beginner"
            )
        ]
        
        for trilha in trilhas:
            db.add(trilha)
        
        # Commit to get IDs
        db.commit()
        
        # Create sample content for each trilha
        contents = [
            # Python para Iniciantes
            Conteudo(
                titulo="Introdução ao Python",
                tipo="video",
                material="Conceitos básicos da linguagem Python",
                trilha_id=1
            ),
            Conteudo(
                titulo="Variáveis e Tipos de Dados",
                tipo="text",
                material="Como trabalhar com diferentes tipos de dados",
                trilha_id=1
            ),
            Conteudo(
                titulo="Estruturas de Controle",
                tipo="exercise",
                material="Exercícios práticos com if, for e while",
                trilha_id=1
            ),
            
            # JavaScript Avançado
            Conteudo(
                titulo="Closures e Scope",
                tipo="video",
                material="Entendendo closures em JavaScript",
                trilha_id=2
            ),
            Conteudo(
                titulo="Promises e Async/Await",
                tipo="text",
                material="Programação assíncrona em JavaScript",
                trilha_id=2
            ),
            
            # Machine Learning
            Conteudo(
                titulo="Introdução ao ML",
                tipo="video",
                material="Conceitos fundamentais de Machine Learning",
                trilha_id=3
            ),
            Conteudo(
                titulo="Algoritmos de Classificação",
                tipo="exercise",
                material="Implementando algoritmos de classificação",
                trilha_id=3
            ),
            
            # Web Full Stack
            Conteudo(
                titulo="Frontend com React",
                tipo="video",
                material="Desenvolvimento de interfaces com React",
                trilha_id=4
            ),
            Conteudo(
                titulo="Backend com Node.js",
                tipo="text",
                material="Criando APIs com Node.js e Express",
                trilha_id=4
            ),
            
            # Data Science
            Conteudo(
                titulo="Análise Exploratória de Dados",
                tipo="video",
                material="Como explorar e visualizar dados",
                trilha_id=5
            )
        ]
        
        for content in contents:
            db.add(content)
        
        # Create sample performance data
        performances = [
            Desempenho(
                usuario_id=1,
                conteudo_id=1,
                progresso=100.0,
                nota=85.0,
                tempo_estudo=45
            ),
            Desempenho(
                usuario_id=1,
                conteudo_id=2,
                progresso=75.0,
                nota=78.0,
                tempo_estudo=30
            ),
            Desempenho(
                usuario_id=2,
                conteudo_id=1,
                progresso=50.0,
                nota=65.0,
                tempo_estudo=25
            )
        ]
        
        for perf in performances:
            db.add(perf)
        
        db.commit()
        print("✅ Sample data created successfully!")
        print(f"Created {len(users)} users, {len(trilhas)} trilhas, {len(contents)} contents, and {len(performances)} performance records")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()

