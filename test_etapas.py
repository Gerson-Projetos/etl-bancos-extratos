"""
Utilitário de Teste e Diagnóstico para as Etapas do Pipeline ETL.
Permite testar e validar cada etapa isoladamente ou executar uma bateria completa.

Uso:
    python test_etapas.py              # Menu interativo
    python test_etapas.py --etapa 1    # Testar Banco de Dados & Contas
    python test_etapas.py --etapa 2    # Testar Google Drive (Conexão e Listagem)
    python test_etapas.py --etapa 3    # Testar Conversor de Arquivos (FileConverter)
    python test_etapas.py --etapa 4    # Testar Extratores e Loaders (ETL)
    python test_etapas.py --etapa 5    # Testar Limpeza de Arquivos
    python test_etapas.py --todas      # Executar teste geral de todas as etapas
"""

import os
import sys
import argparse
from datetime import date
import dotenv

dotenv.load_dotenv()


def log_header(titulo: str):
    print("\n" + "=" * 65)
    print(f"  {titulo.center(61)}")
    print("=" * 65)


def log_success(msg: str):
    print(f"  [OK] {msg}")


def log_warn(msg: str):
    print(f"  [AVISO] {msg}")


def log_error(msg: str):
    print(f"  [ERRO] {msg}")


def testar_etapa_1_banco():
    """Etapa 1: Testa conexão com o banco de dados, tabelas e arquivos já processados."""
    log_header("TESTE DA ETAPA 1: BANCO DE DADOS & ARQUIVOS PROCESSADOS")
    try:
        from Conn.Database import Database, get_db_session
        from sqlalchemy import text
        from Models.Conta import Conta
        from Models.ExtratoItau import ExtratoItau
        from Models.ExtratoMercadoPago import ExtratoMercadoPago
        from Util.Util import Util

        db = Database()
        db.create_tables()
        log_success("Conexão com PostgreSQL estabelecida e tabelas verificadas.")

        with get_db_session() as session:
            contas = session.query(Conta).all()
            print(f"\n  Contas cadastradas na tabela 'contas': {len(contas)}")
            for c in contas:
                print(f"    - ID {c.id}: Banco '{c.banco}' | Tabela: '{c.tbl_extrato}'")

            # Verifica contagem de lançamentos
            res_itau = session.execute(text("SELECT count(*) FROM extrato_itau;")).scalar()
            res_mp = session.execute(text("SELECT count(*) FROM extrato_mercado_pago;")).scalar()
            print(f"\n  Registros atuais no banco:")
            print(f"    - extrato_itau: {res_itau} lançamentos")
            print(f"    - extrato_mercado_pago: {res_mp} lançamentos")

        util = Util()
        processados = util.getArquivosProcessados()
        print(f"\n  Arquivos únicos já registrados no banco ({len(processados)}):")
        for p in sorted(processados)[:10]:
            print(f"    - {p}")
        if len(processados) > 10:
            print(f"    ... e mais {len(processados) - 10} arquivo(s).")

        log_success("Etapa 1 concluída com sucesso!\n")
        return True
    except Exception as e:
        log_error(f"Falha na Etapa 1: {e}\n")
        return False


def testar_etapa_2_drive():
    """Etapa 2: Testa credenciais e listagem de arquivos da pasta do Google Drive."""
    log_header("TESTE DA ETAPA 2: CONEXÃO E LISTAGEM DO GOOGLE DRIVE")
    try:
        drive_id = os.getenv("DRIVE_ID")
        if not drive_id:
            log_error("Variável 'DRIVE_ID' não encontrada no arquivo .env.")
            return False

        has_creds = os.path.exists("creds.json") or os.path.exists("client_secret.json")
        if not has_creds:
            log_error("Nenhum arquivo 'creds.json' ou 'client_secret.json' encontrado na raiz.")
            return False
        log_success("Arquivos de credenciais locais encontrados.")

        from Services.GoogleDriveService import GoogleDriveData
        from Util.Util import Util

        drive = GoogleDriveData()
        log_success("Serviço da API do Google Drive autenticado com sucesso.")

        print(f"  Consultando arquivos na pasta do Drive ID: {drive_id}...")
        arquivos = drive.list_files_in_folder(drive_id)
        print(f"  Total de arquivos encontrados na pasta do Drive: {len(arquivos)}")

        util = Util()
        ignorados = util.getArquivosProcessados()

        novos = 0
        ja_processados = 0
        for f in arquivos:
            nome = f['name']
            base = nome.rsplit('.', 1)[0]
            if base in ignorados:
                ja_processados += 1
            else:
                novos += 1
                if novos <= 5:
                    print(f"    * Novo para download: {nome}")

        print(f"\n  Resumo da pasta remota:")
        print(f"    - Novos (pendentes de download): {novos}")
        print(f"    - Já registrados no banco: {ja_processados}")

        log_success("Etapa 2 concluída com sucesso!\n")
        return True
    except Exception as e:
        log_error(f"Falha na Etapa 2: {e}\n")
        return False


def testar_etapa_3_conversao():
    """Etapa 3: Testa o serviço de conversão FileConverterService."""
    log_header("TESTE DA ETAPA 3: CONVERSÃO DE ARQUIVOS (FILECONVERTER)")
    try:
        from Services.FileConverterService import FileConverter
        import pandas as pd

        pasta_baixados = './arquivos/baixados'
        pasta_processados = './arquivos/processados'
        os.makedirs(pasta_baixados, exist_ok=True)
        os.makedirs(pasta_processados, exist_ok=True)

        arquivos = os.listdir(pasta_baixados)
        if not arquivos:
            log_warn("A pasta './arquivos/baixados' está vazia.")
            print("  Criando um arquivo CSV de teste temporário para validar a conversão...")
            arquivo_teste = os.path.join(pasta_baixados, "teste_conversao_temp.csv")
            df_dummy = pd.DataFrame({
                "Data": ["01/01/2026", "02/01/2026"],
                "Lancamentos": ["Teste Depósito", "Teste Compra"],
                "Valor": ["100,50", "-50,25"],
                "Saldo": ["100,50", "50,25"]
            })
            df_dummy.to_csv(arquivo_teste, sep=';', index=False)
            arquivos = [os.path.basename(arquivo_teste)]
            criou_dummy = True
        else:
            criou_dummy = False

        print(f"  Convertendo {len(arquivos)} arquivo(s) de baixados para processados:")
        for nome in arquivos:
            origem = os.path.join(pasta_baixados, nome)
            print(f"    -> Convertendo: {nome}...")
            saida = FileConverter.to_xlsx(origem, pasta_processados)
            log_success(f"Gerado com sucesso: {saida}")

            # Valida se o XLSX gerado é legível pelo pandas
            df_check = pd.read_excel(saida)
            print(f"       Colunas ({len(df_check.columns)}): {list(df_check.columns[:5])} | Linhas: {len(df_check)}")

        if criou_dummy:
            # Remove o arquivo temporário de teste
            os.remove(os.path.join(pasta_baixados, "teste_conversao_temp.csv"))
            xlsx_temp = os.path.join(pasta_processados, "teste_conversao_temp.xlsx")
            if os.path.exists(xlsx_temp):
                os.remove(xlsx_temp)
            print("  Arquivo temporário de teste removido.")

        log_success("Etapa 3 concluída com sucesso!\n")
        return True
    except Exception as e:
        log_error(f"Falha na Etapa 3: {e}\n")
        return False


def testar_etapa_4_etl():
    """Etapa 4: Testa extratores, loaders, geração de hash SHA-256 e idempotência."""
    log_header("TESTE DA ETAPA 4: EXTRAÇÃO, LOADERS E IDEMPOTÊNCIA (ETL)")
    try:
        from Models.ExtratoItau import ExtratoItau
        from Models.ExtratoMercadoPago import ExtratoMercadoPago
        from Loaders.ItauLoader import ItauLoader
        from Loaders.MercadoPagoLoader import MercadoPagoLoader
        from Conn.Database import get_db_session

        print("  1. Testando modelos e geração de hashes criptográficos...")
        m_itau = ExtratoItau(
            data_lancamento=date(2026, 1, 15),
            descricao="TESTE ITAU PIX",
            valor=150.00,
            saldo=1150.00,
            arquivo_origem="teste_itau.xlsx"
        )
        hash_itau = m_itau.gerar_hash()
        assert hash_itau and len(hash_itau) == 64, "Hash Itaú inválido"
        log_success(f"Hash Itaú gerado: {hash_itau[:16]}...")

        m_mp = ExtratoMercadoPago(
            data_lancamento=date(2026, 1, 15),
            descricao="TESTE MERCADO PAGO RENDIMENTOS",
            id_operacao="1999888777",
            valor=4.50,
            saldo=504.50,
            arquivo_origem="teste_mp.pdf"
        )
        hash_mp = m_mp.gerar_hash()
        assert hash_mp and len(hash_mp) == 64, "Hash Mercado Pago inválido"
        log_success(f"Hash Mercado Pago gerado: {hash_mp[:16]}...")

        print("\n  2. Testando Loaders com verificação de tipo e idempotência no Postgres...")
        with get_db_session() as session:
            loader_itau = ItauLoader(session)
            loader_mp = MercadoPagoLoader(session)

            # Teste de carga de 1 registro teste
            ins_itau = loader_itau.load_to_database([m_itau])
            ins_mp = loader_mp.load_to_database([m_mp])
            session.commit()
            print(f"     Inseridos na 1ª tentativa: Itaú={ins_itau}, Mercado Pago={ins_mp}")

            # Teste de re-inserção (idempotência: deve ser 0)
            ins_itau_dup = loader_itau.load_to_database([m_itau])
            ins_mp_dup = loader_mp.load_to_database([m_mp])
            session.commit()
            print(f"     Inseridos na 2ª tentativa (duplicados ignorados): Itaú={ins_itau_dup}, Mercado Pago={ins_mp_dup}")
            assert ins_itau_dup == 0 and ins_mp_dup == 0, "Falha na prevenção de duplicidade!"
            log_success("Controle de duplicidade via hash verificado com sucesso.")

            # Limpeza do registro de teste
            from sqlalchemy import text
            session.execute(text(f"DELETE FROM extrato_itau WHERE hash_transacao = '{hash_itau}';"))
            session.execute(text(f"DELETE FROM extrato_mercado_pago WHERE hash_transacao = '{hash_mp}';"))
            session.commit()
            print("     Registros de teste excluídos do banco.")

        log_success("Etapa 4 concluída com sucesso!\n")
        return True
    except Exception as e:
        log_error(f"Falha na Etapa 4: {e}\n")
        return False


def testar_etapa_5_limpeza():
    """Etapa 5: Testa a rotina de limpeza de arquivos das pastas baixados e processados."""
    log_header("TESTE DA ETAPA 5: ROTINA DE LIMPEZA DE ARQUIVOS")
    try:
        from main import deletaArquivosBaixados, deletaArquivosProcessados

        pasta_baixados = './arquivos/baixados'
        pasta_processados = './arquivos/processados'
        os.makedirs(pasta_baixados, exist_ok=True)
        os.makedirs(pasta_processados, exist_ok=True)

        # Cria arquivos fictícios para teste de limpeza
        dummy_b = os.path.join(pasta_baixados, "dummy_limpeza.txt")
        dummy_p = os.path.join(pasta_processados, "dummy_limpeza.txt")
        with open(dummy_b, "w") as f:
            f.write("teste")
        with open(dummy_p, "w") as f:
            f.write("teste")

        assert os.path.exists(dummy_b) and os.path.exists(dummy_p), "Falha ao criar arquivos dummy"
        print("  Arquivos fictícios criados em baixados/ e processados/.")

        deletaArquivosBaixados()
        deletaArquivosProcessados()

        restantes_b = len(os.listdir(pasta_baixados))
        restantes_p = len(os.listdir(pasta_processados))
        print(f"  Arquivos restantes em baixados/: {restantes_b}")
        print(f"  Arquivos restantes em processados/: {restantes_p}")
        assert restantes_b == 0 and restantes_p == 0, "Ainda restam arquivos após a limpeza!"

        log_success("Etapa 5 concluída com sucesso!\n")
        return True
    except Exception as e:
        log_error(f"Falha na Etapa 5: {e}\n")
        return False


def testar_todas_as_etapas():
    """Executa todos os testes sequencialmente e exibe resumo."""
    log_header("BATERIA COMPLETA DE DIAGNÓSTICO DO PIPELINE ETL")
    resultados = {
        "Etapa 1 - Banco de Dados": testar_etapa_1_banco(),
        "Etapa 2 - Google Drive": testar_etapa_2_drive(),
        "Etapa 3 - Conversão FileConverter": testar_etapa_3_conversao(),
        "Etapa 4 - ETL (Extratores & Loaders)": testar_etapa_4_etl(),
        "Etapa 5 - Limpeza de Arquivos": testar_etapa_5_limpeza(),
    }

    log_header("RESUMO FINAL DOS TESTES")
    todos_ok = True
    for etapa, status in resultados.items():
        simbolo = "[OK]   " if status else "[FALHA]"
        if not status:
            todos_ok = False
        print(f"  {simbolo} {etapa}")

    print("=" * 65)
    if todos_ok:
        log_success("TODAS AS ETAPAS ESTÃO OPERACIONAIS E VALIDADAS!\n")
    else:
        log_warn("Algumas etapas apresentaram problemas. Verifique os logs acima.\n")


def menu_interativo():
    while True:
        log_header("MENU DE TESTE DAS ETAPAS DO ETL")
        print("  [1] Testar Etapa 1: Banco de Dados & Arquivos Processados")
        print("  [2] Testar Etapa 2: Conexão e Listagem do Google Drive")
        print("  [3] Testar Etapa 3: Conversão de Arquivos (FileConverter)")
        print("  [4] Testar Etapa 4: Extração, Loaders e Hash (ETL)")
        print("  [5] Testar Etapa 5: Limpeza de Arquivos")
        print("  [6] Testar TODAS as Etapas (Diagnóstico Completo)")
        print("  [0] Sair")
        print("-" * 65)
        opcao = input("  Escolha uma opção: ").strip()

        if opcao == "1":
            testar_etapa_1_banco()
        elif opcao == "2":
            testar_etapa_2_drive()
        elif opcao == "3":
            testar_etapa_3_conversao()
        elif opcao == "4":
            testar_etapa_4_etl()
        elif opcao == "5":
            testar_etapa_5_limpeza()
        elif opcao == "6":
            testar_todas_as_etapas()
        elif opcao in ["0", "sair", "exit", "q"]:
            print("\nEncerrando utilitário de teste.")
            break
        else:
            print("\nOpção inválida. Tente novamente.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Utilitário de Teste das Etapas do ETL")
    parser.add_argument(
        "--etapa", "-e",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Executa o teste de uma etapa específica (1 a 5)"
    )
    parser.add_argument(
        "--todas", "-t",
        action="store_true",
        help="Executa o teste de todas as etapas em sequência"
    )
    args = parser.parse_args()

    if args.etapa == 1:
        testar_etapa_1_banco()
    elif args.etapa == 2:
        testar_etapa_2_drive()
    elif args.etapa == 3:
        testar_etapa_3_conversao()
    elif args.etapa == 4:
        testar_etapa_4_etl()
    elif args.etapa == 5:
        testar_etapa_5_limpeza()
    elif args.todas:
        testar_todas_as_etapas()
    else:
        menu_interativo()
