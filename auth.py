#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Autenticação - Google OAuth e Email/Senha
Gerencia login e logout de usuários
"""

import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from flask import session, redirect, url_for, request, flash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Carregar variáveis de ambiente
load_dotenv()

# Permitir HTTP em desenvolvimento (apenas para localhost)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class User(UserMixin):
    """Classe de usuário para Flask-Login"""
    def __init__(self, id_, name, email, profile_pic, db_id=None):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.db_id = db_id

    @staticmethod
    def get(user_id):
        """Recupera usuário da sessão"""
        if 'user' in session:
            user_data = session['user']
            if user_data['id'] == user_id:
                return User(
                    id_=user_data['id'],
                    name=user_data['name'],
                    email=user_data['email'],
                    profile_pic=user_data['profile_pic'],
                    db_id=session.get('user_db_id')
                )
        return None

    @staticmethod
    def create(id_, name, email, profile_pic, auth_type='google'):
        """Cria novo usuário"""
        from database import get_database
        
        # Salvar usuário no banco de dados
        db = get_database()
        if db:
            try:
                if auth_type == 'google':
                    user_db_id = db.save_user(id_, email, name, profile_pic)
                else:
                    user_db_id = db.save_email_user(email, name, profile_pic)
                    
                if user_db_id:
                    session['user_db_id'] = user_db_id
                    print(f"✅ Usuário salvo no banco com ID: {user_db_id}")
                else:
                    print("⚠️ Não foi possível obter ID do usuário do banco")
            except Exception as e:
                print(f"❌ Erro ao salvar usuário no banco: {e}")
        
        user = User(id_, name, email, profile_pic, db_id=user_db_id)
        session['user'] = {
            'id': id_,
            'name': name,
            'email': email,
            'profile_pic': profile_pic
        }
        return user
    
    @staticmethod
    def create_email_user(email, name, password):
        """Cria usuário com autenticação por email"""
        from database import get_database
        
        db = get_database()
        if not db:
            return None
            
        try:
            # Verificar se email já existe
            existing_user = db.get_user_by_email(email)
            if existing_user:
                return None  # Email já existe
            
            # Criar hash da senha
            password_hash = generate_password_hash(password)
            
            # Gerar token de verificação
            verification_token = secrets.token_urlsafe(32)
            
            # Salvar usuário
            user_db_id = db.create_email_user(email, name, password_hash, verification_token)
            
            if user_db_id:
                # Criar ID único para sessão
                user_id = f"email_{user_db_id}"
                
                user = User(user_id, name, email, '', db_id=user_db_id)
                session['user'] = {
                    'id': user_id,
                    'name': name,
                    'email': email,
                    'profile_pic': ''
                }
                session['user_db_id'] = user_db_id
                return user
                
        except Exception as e:
            print(f"❌ Erro ao criar usuário por email: {e}")
            
        return None
    
    @staticmethod
    def authenticate_email(email, password):
        """Autentica usuário por email e senha"""
        from database import get_database
        
        db = get_database()
        if not db:
            return None
            
        try:
            user_data = db.authenticate_email_user(email, password)
            if user_data:
                user_id = f"email_{user_data['id']}"
                
                user = User(
                    id_=user_id,
                    name=user_data['name'],
                    email=user_data['email'],
                    profile_pic=user_data.get('profile_pic', ''),
                    db_id=user_data['id']
                )
                
                session['user'] = {
                    'id': user_id,
                    'name': user_data['name'],
                    'email': user_data['email'],
                    'profile_pic': user_data.get('profile_pic', '')
                }
                session['user_db_id'] = user_data['id']
                return user
                
        except Exception as e:
            print(f"❌ Erro na autenticação por email: {e}")
            
        return None

class GoogleAuth:
    """Classe para gerenciar autenticação Google OAuth"""
    
    def __init__(self, app=None):
        self.app = app
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/callback')
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa a autenticação com a aplicação Flask"""
        self.app = app
        
        # Configurações do Google OAuth
        if not self.client_id or not self.client_secret:
            print("⚠️ Credenciais do Google OAuth não configuradas")
            print("📝 Configure GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET no arquivo .env")
            return False
        
        # Configuração do Flow OAuth
        self.flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]
        )
        self.flow.redirect_uri = self.redirect_uri
        
        return True
    
    def get_authorization_url(self):
        """Gera URL de autorização do Google"""
        if not hasattr(self, 'flow'):
            return None
        
        authorization_url, state = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        session['state'] = state
        return authorization_url
    
    def handle_callback(self, authorization_response):
        """Processa callback do Google OAuth"""
        if not hasattr(self, 'flow'):
            return None
        
        # Verificar state para segurança
        if 'state' not in session or request.args.get('state') != session['state']:
            return None
        
        try:
            # Trocar código por token
            self.flow.fetch_token(authorization_response=authorization_response)
            
            # Obter informações do usuário
            credentials = self.flow.credentials
            request_session = google_requests.Request()
            
            # Verificar token ID
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                request_session,
                self.client_id
            )
            
            # Criar usuário
            user = User.create(
                id_=id_info['sub'],
                name=id_info['name'],
                email=id_info['email'],
                profile_pic=id_info.get('picture', '')
            )
            
            return user
            
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            return None
    
    def is_configured(self):
        """Verifica se as credenciais estão configuradas"""
        return bool(self.client_id and self.client_secret)

def init_auth(app):
    """Inicializa sistema de autenticação"""
    google_auth = GoogleAuth(app)
    return google_auth