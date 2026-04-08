import sqlite3
import sys

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def inicializar_bd():
    conn = sqlite3.connect('sistema_vendas.db')
    cursor = conn.cursor()

    # Tabela de Usuários (Unificada)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL -- 'admin' ou 'cliente'
        )
    ''')

    # Tabela de Produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL
        )
    ''')

    # Tabela de Vendas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER,
            id_produto INTEGER,
            quantidade INTEGER,
            data_venda DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario) REFERENCES usuarios (id),
            FOREIGN KEY (id_produto) REFERENCES produtos (id)
        )
    ''')

    # Criar Admin padrão se não existir
    cursor.execute("INSERT OR IGNORE INTO usuarios (nome, login, senha, tipo) VALUES (?, ?, ?, ?)",
                   ('Admin Geral', 'admin', 'admin123', 'admin'))
    
    conn.commit()
    conn.close()

# --- FUNÇÕES DE NEGÓCIO ---
def cadastrar_usuario():
    print("\n--- CADASTRO DE CLIENTE ---")
    nome = input("Nome completo: ")
    login = input("Escolha um login: ")
    senha = input("Escolha uma senha: ")
    
    try:
        conn = sqlite3.connect('sistema_vendas.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nome, login, senha, tipo) VALUES (?, ?, ?, 'cliente')", 
                       (nome, login, senha))
        conn.commit()
        print("Cadastro realizado com sucesso! Agora faça login.")
    except sqlite3.IntegrityError:
        print("Erro: Este login já existe.")
    finally:
        conn.close()

def login():
    print("\n--- LOGIN SISVENDA ---")
    u = input("Login: ")
    s = input("Senha: ")
    
    conn = sqlite3.connect('sistema_vendas.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, tipo FROM usuarios WHERE login = ? AND senha = ?", (u, s))
    user = cursor.fetchone()
    conn.close()
    return user # Retorna (id, nome, tipo) ou None

# --- MENUS ---
def menu_admin():
    while True:
        print("\n--- PAINEL ADMINISTRATIVO ---")
        print("1. Cadastrar Produto")
        print("2. Ver Todas as Vendas")
        print("0. Logout")
        op = input("Opção: ")
        
        if op == '1':
            nome = input("Nome do produto: ")
            preco = float(input("Preço: "))
            qtd = int(input("Estoque inicial: "))
            conn = sqlite3.connect('sistema_vendas.db')
            conn.execute("INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)", (nome, preco, qtd))
            conn.commit()
            conn.close()
            print("Produto cadastrado!")
        elif op == '0': break

def menu_cliente(user_id):
    while True:
        print("\n--- ÁREA DO CLIENTE ---")
        print("1. Ver Produtos Disponíveis")
        print("2. Comprar Produto")
        print("0. Logout")
        op = input("Opção: ")

        conn = sqlite3.connect('sistema_vendas.db')
        cursor = conn.cursor()

        if op == '1':
            cursor.execute("SELECT * FROM produtos")
            for p in cursor.fetchall():
                print(f"ID: {p[0]} | {p[1]} | R$ {p[2]} | Estoque: {p[3]}")
        
        elif op == '2':
            id_p = int(input("ID do produto: "))
            qtd = int(input("Quantidade: "))
            cursor.execute("SELECT estoque FROM produtos WHERE id = ?", (id_p,))
            res = cursor.fetchone()
            if res and res[0] >= qtd:
                cursor.execute("INSERT INTO vendas (id_usuario, id_produto, quantidade) VALUES (?, ?, ?)", (user_id, id_p, qtd))
                cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (qtd, id_p))
                conn.commit()
                print("Compra realizada!")
            else:
                print("Estoque insuficiente!")
        
        elif op == '0': 
            conn.close()
            break
        conn.close()

# --- LOOP PRINCIPAL ---
inicializar_bd()
while True:
    print("\n=== BEM-VINDO AO SISVENDA ===")
    print("1. Login")
    print("2. Cadastrar-se")
    print("0. Sair")
    escolha = input("Opção: ")

    if escolha == '1':
        dados = login()
        if dados:
            u_id, u_nome, u_tipo = dados
            print(f"\nOlá {u_nome}!")
            if u_tipo == 'admin': menu_admin()
            else: menu_cliente(u_id)
    elif escolha == '2':
        cadastrar_usuario()
    elif escolha == '0':
        sys.exit()