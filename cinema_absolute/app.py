from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import string
import os

app = Flask(__name__)
app.secret_key = 'pipoca_secreta'

# Função para conectar ao banco
def get_db_connection():
    conn = sqlite3.connect('cinema_vendas.db')
    conn.row_factory = sqlite3.Row
    return conn

# Criar tabelas se não existirem
def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, login TEXT UNIQUE, senha TEXT, tipo TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessoes (id INTEGER PRIMARY KEY AUTOINCREMENT, filme TEXT, sala TEXT, horario TEXT, preco_inteira REAL, num_fileiras INTEGER, assentos_por_fileira INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ingressos (id INTEGER PRIMARY KEY AUTOINCREMENT, id_usuario INTEGER, id_sessao INTEGER, assento TEXT, tipo_ingresso TEXT, total_pago REAL, FOREIGN KEY (id_usuario) REFERENCES usuarios (id), FOREIGN KEY (id_sessao) REFERENCES sessoes (id))''')
        cursor.execute("INSERT OR IGNORE INTO usuarios (nome, login, senha, tipo) VALUES ('Admin', 'admin', 'admin123', 'admin')")
        conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    login_user = request.form['login']
    senha_user = request.form['senha']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE login = ? AND senha = ?', (login_user, senha_user)).fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['user_tipo'] = user['tipo']
        session['user_nome'] = user['nome']
        return redirect(url_for('dashboard'))
    
    flash('Login ou senha incorretos!')
    return redirect(url_for('index'))

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    nome = request.form['nome']
    login_reg = request.form['login']
    senha_reg = request.form['senha']
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO usuarios (nome, login, senha, tipo) VALUES (?, ?, ?, 'cliente')", (nome, login_reg, senha_reg))
            conn.commit()
        flash('Cadastro realizado! Faça login.')
    except:
        flash('Erro: Login já existe.')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = get_db_connection()
    
    if session['user_tipo'] == 'admin':
        vendas = conn.execute('''SELECT i.id, u.nome, s.filme, i.assento, i.total_pago 
                                 FROM ingressos i 
                                 JOIN usuarios u ON i.id_usuario = u.id 
                                 JOIN sessoes s ON i.id_sessao = s.id''').fetchall()
        return render_template('admin.html', vendas=vendas)
    
    sessoes = conn.execute('SELECT * FROM sessoes').fetchall()
    return render_template('cliente.html', sessoes=sessoes)

@app.route('/admin/nova_sessao', methods=['POST'])
def nova_sessao():
    if session.get('user_tipo') != 'admin': return redirect(url_for('index'))
    filme = request.form['filme']
    sala = request.form['sala']
    horario = request.form['horario']
    preco = float(request.form['preco'])
    fileiras = int(request.form['fileiras'])
    colunas = int(request.form['colunas'])
    with get_db_connection() as conn:
        conn.execute('INSERT INTO sessoes (filme, sala, horario, preco_inteira, num_fileiras, assentos_por_fileira) VALUES (?,?,?,?,?,?)',
                     (filme, sala, horario, preco, fileiras, colunas))
        conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/sessao/<int:id_sessao>')
def ver_sessao(id_sessao):
    conn = get_db_connection()
    sessao = conn.execute('SELECT * FROM sessoes WHERE id = ?', (id_sessao,)).fetchone()
    vendidos = [r['assento'] for r in conn.execute('SELECT assento FROM ingressos WHERE id_sessao = ?', (id_sessao,)).fetchall()]
    
    mapa = []
    alfabeto = string.ascii_uppercase
    for i in range(sessao['num_fileiras']):
        fila = []
        for j in range(1, sessao['assentos_por_fileira'] + 1):
            n = f"{alfabeto[i]}{j}"
            fila.append({'nome': n, 'ocupado': n in vendidos})
        mapa.append(fila)
    return render_template('sessao.html', sessao=sessao, mapa=mapa)

@app.route('/comprar', methods=['POST'])
def comprar():
    id_s = request.form['id_sessao']
    assentos = request.form.getlist('assentos')
    conn = get_db_connection()
    sessao = conn.execute('SELECT preco_inteira FROM sessoes WHERE id = ?', (id_s,)).fetchone()
    for a in assentos:
        conn.execute('INSERT INTO ingressos (id_usuario, id_sessao, assento, tipo_ingresso, total_pago) VALUES (?,?,?,?,?)',
                     (session['user_id'], id_s, a, 'Inteira', sessao['preco_inteira']))
    conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    # O host '0.0.0.0' expõe o app na rede local
    app.run(host='0.0.0.0', port=5000, debug=True)