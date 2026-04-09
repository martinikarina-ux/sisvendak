import sqlite3
import sys
import string

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def inicializar_bd():
    with sqlite3.connect('cinema_vendas.db') as conn:
        cursor = conn.cursor()

        # Tabela de Usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                login TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                tipo TEXT NOT NULL
            )
        ''')

        # Tabela de Sessões (Agora com mapa de sala)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filme TEXT NOT NULL,
                sala TEXT NOT NULL,
                horario TEXT NOT NULL,
                preco_inteira REAL NOT NULL,
                num_fileiras INTEGER NOT NULL,
                assentos_por_fileira INTEGER NOT NULL
            )
        ''')

        # Tabela de Ingressos (Agora registra o assento exato)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingressos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER,
                id_sessao INTEGER,
                assento TEXT NOT NULL,
                tipo_ingresso TEXT NOT NULL,
                total_pago REAL,
                data_compra DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_usuario) REFERENCES usuarios (id),
                FOREIGN KEY (id_sessao) REFERENCES sessoes (id),
                UNIQUE(id_sessao, assento) -- Impede que o mesmo assento seja vendido 2 vezes
            )
        ''')

        cursor.execute("INSERT OR IGNORE INTO usuarios (nome, login, senha, tipo) VALUES (?, ?, ?, ?)",
                       ('Gerente do Cinema', 'admin', 'admin123', 'admin'))
        conn.commit()

# --- FUNÇÕES DE USUÁRIO ---
def cadastrar_usuario():
    print("\n--- CADASTRO DE ESPECTADOR ---")
    nome = input("Nome completo: ")
    login = input("Escolha um login: ")
    senha = input("Escolha uma senha: ")
    
    try:
        with sqlite3.connect('cinema_vendas.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (nome, login, senha, tipo) VALUES (?, ?, ?, 'cliente')", 
                           (nome, login, senha))
            conn.commit()
            print("Cadastro realizado com sucesso! Agora faça login.")
    except sqlite3.IntegrityError:
        print("Erro: Este login já existe. Tente outro.")

def fazer_login():
    print("\n--- LOGIN CINEMA ---")
    u = input("Login: ")
    s = input("Senha: ")
    
    with sqlite3.connect('cinema_vendas.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, tipo FROM usuarios WHERE login = ? AND senha = ?", (u, s))
        user = cursor.fetchone()
        
    if not user:
        print("Login ou senha incorretos!")
    return user

# --- MENUS ---
def menu_admin():
    while True:
        print("\n--- PAINEL DO GERENTE ---")
        print("1. Cadastrar Nova Sessão")
        print("2. Ver Ingressos Vendidos")
        print("0. Logout")
        op = input("Opção: ")
        
        if op == '1':
            filme = input("Nome do filme: ")
            sala = input("Sala (ex: Sala 1 - 3D): ")
            horario = input("Horário (ex: 19:30): ")
            try:
                preco = float(input("Preço da Inteira: R$ "))
                num_fileiras = int(input("Número de fileiras (Max 26): "))
                assentos_por_fileira = int(input("Cadeiras por fileira: "))
                
                if num_fileiras > 26 or num_fileiras < 1 or assentos_por_fileira < 1:
                    print("Erro: Valores inválidos para o mapa da sala.")
                    continue

                with sqlite3.connect('cinema_vendas.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('''INSERT INTO sessoes 
                                      (filme, sala, horario, preco_inteira, num_fileiras, assentos_por_fileira) 
                                      VALUES (?, ?, ?, ?, ?, ?)''', 
                                   (filme, sala, horario, preco, num_fileiras, assentos_por_fileira))
                    conn.commit()
                print("Sessão cadastrada com sucesso!")
            except ValueError:
                print("Erro: Digite apenas números para preço e dimensões da sala.")
                
        elif op == '2':
            with sqlite3.connect('cinema_vendas.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT i.id, u.nome, s.filme, s.horario, i.assento, i.tipo_ingresso, i.total_pago
                    FROM ingressos i
                    JOIN usuarios u ON i.id_usuario = u.id
                    JOIN sessoes s ON i.id_sessao = s.id
                ''')
                vendas = cursor.fetchall()
                
                print("\n--- RELATÓRIO DE BILHETERIA ---")
                if not vendas:
                    print("Nenhum ingresso vendido ainda.")
                else:
                    for v in vendas:
                        print(f"Ticket #{v[0]} | Cliente: {v[1]} | Filme: {v[2]} às {v[3]} | Assento: {v[4]} | {v[5]} | R$ {v[6]:.2f}")
                        
        elif op == '0': 
            break
        else:
            print("Opção inválida!")

def exibir_mapa_assentos(cursor, id_sessao, num_fileiras, assentos_por_fileira):
    # Busca assentos já vendidos para esta sessão
    cursor.execute("SELECT assento FROM ingressos WHERE id_sessao = ?", (id_sessao,))
    vendidos = [row[0] for row in cursor.fetchall()]
    
    alfabeto = string.ascii_uppercase
    todos_assentos_validos = []

    print("\n[ TELA DO CINEMA ]".center(assentos_por_fileira * 7))
    print("-" * (assentos_por_fileira * 7))

    for i in range(num_fileiras):
        letra = alfabeto[i]
        linha_visual = []
        for j in range(1, assentos_por_fileira + 1):
            nome_assento = f"{letra}{j}"
            todos_assentos_validos.append(nome_assento)
            
            if nome_assento in vendidos:
                linha_visual.append("[ XX ]") # Ocupado
            else:
                linha_visual.append(f"[{nome_assento:^4}]") # Livre
        print(" ".join(linha_visual))
    
    print("-" * (assentos_por_fileira * 7))
    return vendidos, todos_assentos_validos

def menu_cliente(user_id):
    while True:
        print("\n--- BILHETERIA ---")
        print("1. Ver Filmes em Cartaz")
        print("2. Comprar Ingresso (Escolher Assento)")
        print("0. Logout")
        op = input("Opção: ")

        if op == '1':
            with sqlite3.connect('cinema_vendas.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sessoes")
                sessoes = cursor.fetchall()
                
                print("\n--- FILMES EM CARTAZ ---")
                if not sessoes:
                    print("Nenhuma sessão disponível.")
                else:
                    for s in sessoes:
                        capacidade_total = s[5] * s[6]
                        # Conta quantos ingressos já saíram para esta sessão
                        cursor.execute("SELECT COUNT(*) FROM ingressos WHERE id_sessao = ?", (s[0],))
                        vendidos = cursor.fetchone()[0]
                        vagas_restantes = capacidade_total - vendidos
                        
                        print(f"ID: {s[0]} | Filme: {s[1]} | Horário: {s[3]} | Inteira: R$ {s[4]:.2f} | Vagas: {vagas_restantes}/{capacidade_total}")
        
        elif op == '2':
            try:
                id_s = int(input("Digite o ID da sessão desejada: "))
            except ValueError:
                print("Erro: ID inválido.")
                continue

            with sqlite3.connect('cinema_vendas.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT filme, sala, horario, preco_inteira, num_fileiras, assentos_por_fileira FROM sessoes WHERE id = ?", (id_s,))
                res = cursor.fetchone()
                
                if not res:
                    print("❌ Sessão não encontrada!")
                    continue
                    
                filme, sala, horario, preco_inteira, num_fileiras, assentos_por_fileira = res
                
                # Mostra o mapa e retorna listas de validação
                vendidos, validos = exibir_mapa_assentos(cursor, id_s, num_fileiras, assentos_por_fileira)
                
                escolha_assentos = input("\nDigite os assentos que deseja separados por vírgula (ex: A1, A2, B5): ").upper()
                assentos_desejados = [a.strip() for a in escolha_assentos.split(',') if a.strip()]

                if not assentos_desejados:
                    continue

                ingressos_para_processar = []
                valor_total_compra = 0

                # Validação prévia
                erro_validacao = False
                for assento in assentos_desejados:
                    if assento not in validos:
                        print(f"❌ Assento {assento} não existe nesta sala!")
                        erro_validacao = True
                        break
                    if assento in vendidos:
                        print(f"❌ Assento {assento} já está ocupado!")
                        erro_validacao = True
                        break
                
                if erro_validacao:
                    print("Compra cancelada. Tente novamente.")
                    continue

                # Definir tipo de ingresso para cada assento
                for assento in assentos_desejados:
                    tipo = input(f"Assento {assento} - Tipo (1-Inteira, 2-Meia): ")
                    if tipo not in ['1', '2']:
                        print("Tipo inválido, assumindo Inteira.")
                        tipo = '1'
                    
                    preco_final = preco_inteira if tipo == '1' else preco_inteira / 2
                    nome_tipo = 'Inteira' if tipo == '1' else 'Meia'
                    
                    ingressos_para_processar.append((user_id, id_s, assento, nome_tipo, preco_final))
                    valor_total_compra += preco_final

                # Efetivar a compra no banco de dados
                try:
                    cursor.executemany('''
                        INSERT INTO ingressos (id_usuario, id_sessao, assento, tipo_ingresso, total_pago)
                        VALUES (?, ?, ?, ?, ?)
                    ''', ingressos_para_processar)
                    conn.commit()
                    
                    print(f"\n🎟️ COMPRA REALIZADA COM SUCESSO! 🎟️")
                    print(f"Filme: {filme} ({sala} - {horario})")
                    print(f"Assentos garantidos: {', '.join(assentos_desejados)}")
                    print(f"Total pago: R$ {valor_total_compra:.2f}")
                except sqlite3.IntegrityError:
                    print("❌ Erro grave: Um desses assentos foi comprado por outra pessoa agorinha! Tente novamente.")

        elif op == '0': 
            break
        else:
            print("Opção inválida!")

# --- LOOP PRINCIPAL ---
inicializar_bd()
while True:
    print("\n=== CINE-PYTHON ===")
    print("1. Entrar")
    print("2. Cadastrar-se")
    print("0. Sair")
    escolha = input("Opção: ")

    if escolha == '1':
        dados = fazer_login()
        if dados:
            u_id, u_nome, u_tipo = dados
            print(f"\nOlá, {u_nome}! Pegue sua pipoca.")
            if u_tipo == 'admin': 
                menu_admin()
            else: 
                menu_cliente(u_id)
    elif escolha == '2':
        cadastrar_usuario()
    elif escolha == '0':
        print("Saindo... Bom filme!")
        sys.exit()
    else:
        print("Opção inválida!")