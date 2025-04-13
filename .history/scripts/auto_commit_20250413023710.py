import os
import subprocess
from datetime import datetime

# Configurações
REPO_PATH = r"c:\Users\Robson Vieira\Documents\VS_CODE\Projeto Análise de Dados\v3.0\projeto-dashboard"
GITHUB_URL = "https://github.com/RobsonFSVieira/dashboard-atendimento-v3.git"

def run_command(command):
    """Executa um comando shell e retorna a saída"""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print(f"ERRO: {stderr.decode('utf-8')}")
        return False
    
    return stdout.decode('utf-8')

def auto_commit():
    """Realiza verificação de alterações, commit e push automaticamente"""
    # Mudar para o diretório do repositório
    os.chdir(REPO_PATH)
    
    # Verifica o status atual do repositório
    status = run_command("git status --porcelain")
    
    if not status:
        print("Nenhuma alteração para commitar.")
        return
    
    # Adiciona todas as alterações
    run_command("git add .")
    
    # Cria uma mensagem de commit com timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Auto commit: Atualização automática em {now}"
    
    # Realiza o commit
    result = run_command(f'git commit -m "{commit_message}"')
    if not result:
        print("Erro ao fazer commit.")
        return
    
    print("Commit realizado com sucesso.")
    
    # Push para o GitHub
    result = run_command("git push origin main")  # Substitua 'main' pela sua branch, se necessário
    if not result:
        print("Erro ao fazer push para o GitHub.")
        return
    
    print("Push para GitHub realizado com sucesso.")

if __name__ == "__main__":
    auto_commit()
