import pandas as pd
import re
# Função para normalizar máscaras no padrão X.X.X.X.X.XX.XX
def normalizar_mascara(mascara):
    if pd.isna(mascara):  # Verifica se a máscara é NaN
        return None
    
    # Remove o padrão "200" de máscaras que contenham esse valor
    if isinstance(mascara, str) and '200' in mascara:
        mascara = mascara.replace('200', '')  # Remove "200"
    
    # Divide a máscara em partes usando o ponto como separador
    partes = mascara.split('.')
    
    # Trunca a máscara para garantir no máximo 7 níveis
    partes = partes[:7]
    
    # Preenche os níveis ausentes com zeros até atingir o formato completo: X.X.X.X.X.XX.XX
    while len(partes) < 7:  # O formato completo tem 7 níveis
        partes.append('00' if len(partes) >= 5 else '0')  # Níveis 6 e 7 têm dois dígitos
    
    # Garante que cada parte tenha o número correto de dígitos
    partes = [
        parte.zfill(2) if i >= 5 else parte.zfill(1)  # Níveis 6+ têm dois dígitos
        for i, parte in enumerate(partes)
    ]
    
    # Junta as partes novamente em uma máscara normalizada
    return '.'.join(partes[:7])  # Limita ao formato X.X.X.X.X.XX.XX

###################################### INICIA O TRATATAMENTO DOS PADRÔES DE CONTAS ##########################################
# Função para extrair e formatar a conta corrente ou outros padrões
def extrair_conta_corrente(descricao):
    """
    Extrai e formata descrições de acordo com diferentes padrões.
    Entrada: Descrição no formato específico do Betha.
    Saída: Descrição formatada conforme o padrão desejado.
    """
    if pd.isna(descricao):  # Verifica se a descrição é NaN
        return None

    # Caso 1: Remover "2-Destinação de Recursos - " e manter apenas o número REVISADO
    if descricao.startswith("2-Destinação de Recursos - "):
        return descricao.replace("2-Destinação de Recursos - ", "").strip()
    
    # Caso 2: Transformar padrão "5-Conta Bancária+FR - ..." FEITO PARA 2 CASOS FUNCIONANDO.
    elif descricao.startswith("5-Conta Bancária+FR - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("5-Conta Bancária+FR - ", "").strip()
            # Remove espaços extras entre os campos
            descricao = " ".join(descricao.split())
            # Divide a descrição em partes
            partes = descricao.split()
            if len(partes) >= 4:
                banco = partes[0].zfill(4)  # Garante 4 dígitos
                agencia = partes[1].zfill(5)  # Garante 5 dígitos
                conta_digito = partes[2]  # Ex: "9.633-4" ou "96.630-4"
                destino = partes[3]  # Ex: "18997000"
                # Monta a conta corrente no formato desejado
                if len(conta_digito) == 7:
                    conta_corrente = f"{banco}{'0'}{agencia}{conta_digito}{' ' * 8}{destino}"  # FUNCIONA.
                elif len(conta_digito) == 8: 
                    conta_corrente = f"{banco}{'0'}{agencia}{conta_digito}{' ' * 7}{destino}"
                else:
                    return descricao
                
        except Exception as e:
            print(f"Erro ao processar '5-Conta Bancária+FR': {e}")
            return descricao  # Retorna a descrição original em caso de erro
        return conta_corrente
        
    # Caso 3: Remover "6-Credor - " e normalizar o CPF REVISADO
    elif descricao.startswith("6-Credor - "):
        cpf = descricao.replace("6-Credor - ", "").strip()
        return normalizar_cpf(cpf)  # Normaliza o CPF
    
    # Caso 4: Processar "1-Célula da Receita - ..." REVISADO
    elif descricao.startswith("1-Célula da Receita - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("1-Célula da Receita - ", "").strip()
            # Remove todos os espaços
            descricao = descricao.replace(" ", "")
            return descricao
        except Exception:
            return descricao  # Retorna a descrição original em caso de erro
    
    # Caso 5: Processar "7-Empenho - ..."  REVISADO
    elif descricao.startswith("7-Empenho - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("7-Empenho - ", "").strip()
            # Remove espaços extras entre os campos
            descricao = " ".join(descricao.split())
            # Divide a descrição em partes
            partes = descricao.split()
            if len(partes) >= 5:
                orgao = partes[0]  # Ex: "13001"
                ano = partes[1]  # Ex: "2024"
                empenho = partes[2].zfill(6)  # Preenche com zeros à esquerda (6 dígitos)
                fase = partes[3]  # Ex: "0"
                destino = partes[4]  # Ex: "15001002"
            # Monta o padrão desejado
                padrao_empenho = f"{orgao}{ano}{'0' * 10}{empenho}{'0' * 16}{destino}"
                return padrao_empenho
        except Exception:
            return descricao  # Retorna a descrição original em caso de erro
    
    # Caso 6: Processar "4-Fonte de Recurso para abertura de créditos - X" REVISADO, tinha que adicionar o 0
    elif descricao.startswith("4-Fonte de Recurso para abertura de créditos - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("4-Fonte de Recurso para abertura de créditos - ", "").strip()
            descricao = f"{'0'}{descricao}"
            return descricao  # Retorna apenas o número isolado
        except Exception:
            return descricao  # Retorna a descrição original em caso de erro
    
    # Caso 7: Processar "14-Contratos e Convênios - ..." REVISADO
    elif descricao.startswith("14-Contratos e Convênios - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("14-Contratos e Convênios - ", "").strip()
            # Divide a descrição em partes
            partes = descricao.split()
            if len(partes) >= 4:
                ano = partes[0]  # Ex: "2019"
                mes = partes[1]  # Ex: "08"
                numero_contrato = partes[2]  # Ex: "Nº03/2022_17/19" ou "Nº15/2019"
                cnpj = partes[3] # Ex: "08584873000109"
                # Garantir que o número do contrato tenha um comprimento fixo de 15 caracteres
                numero_contrato = numero_contrato.ljust(15)
                # Monta o padrão TCE
                padrao_contrato = f"{ano}{mes}{numero_contrato}{' '}{cnpj}"
                return padrao_contrato
        except Exception:
            return descricao  # Retorna a descrição original em caso de erro
    
    # Caso 8: Processar "13-Consórcios - ..." REVISADO
    elif descricao.startswith("13-Consórcios - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("13-Consórcios - ", "").strip()
            # Remove espaços extras entre os campos
            descricao = " ".join(descricao.split())
            # Divide a descrição em partes
            partes = descricao.split()
            if len(partes) == 7:
                ano = partes[0]           # Ex: "2023"
                numero = partes[1]        # Ex: "Nº03/2023"
                cnpj = partes[2]          # Ex: "42499226000129"
                codigo1 = partes[3]       # Ex: "10"
                codigo2 = partes[4]       # Ex: "301"
                codigo3 = partes[5][:4]   # Ex: "3171" (primeiros 4 caracteres) ELEMENTO DA DESPESA
                destino = partes[6]   # Concatena "15001002"

                # Monta o padrão TCE
                consorcio_formatado = f"{ano}{numero}{' ' * 7}{cnpj}{codigo1}{codigo2}{codigo3}{'00'}{destino}"
                return consorcio_formatado
        except Exception:
            return descricao  # Retorna a descrição original em caso de erro
    
    # Caso 9: Processar "3-Célula da Despesa - ..." (padrão TCE) REVISADO
    
    elif descricao.startswith("3-Célula da Despesa - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("3-Célula da Despesa - ", "").strip()
            
            # Divide a descrição em partes
            partes = descricao.split()
            # Verifica se há exatamente 4 partes
            if len(partes) == 4:
                orgao = partes[0].zfill(5)  # Ex: "13001"
                mascara = partes[1]        # Ex: "2038"
                conta = partes[2]  # Ex: "449000"
                destino = partes[3]        # Ex: "15001002"
                
                # Formata a máscara conforme o padrão TCE
                mascara_formatada = formatar_mascara(mascara)
                
                # Monta a conta no formato TCE
                conta_tce = f"{orgao}{'0'}{mascara_formatada}{conta}{destino}"
                #conta_tce = f"{orgao}{mascara_formatada}{conta}{destino}"
                return conta_tce
        except Exception as e:
            print(f"Erro ao processar a descrição: {descricao}. Erro: {e}")
            return descricao  # Retorna a descrição original em caso de erro
    return descricao  # Retorna a descrição original se não for uma célula da despesa
    
    # Caso genérico: Retorna a descrição original caso não se encaixe nos padrões
    return descricao
###################################### FINALIZA O TRATATAMENTO DOS PADRÔES DE CONTAS ##########################################

def formatar_mascara(mascara):  # Corrigir a mascara para o caso 9: 3-Célula da Despesa
    """
    Formata a máscara conforme o padrão TCE:
    - Primeiro dígito.
    - Seguido por '00000'.
    - Seguido pelo restante da máscara (completado com zeros à esquerda).
    """
    try:
        # Garante que a máscara seja uma string
        mascara = str(mascara)
        
        # Separa o primeiro dígito e o restante da máscara
        primeiro_digito = mascara[0]  # Primeiro dígito (ex.: "1", "2", "3")
        resto_mascara = mascara[1:].zfill(6)  # Restante da máscara (ex.: "037", "038", "039")
        # Formata conforme o padrão TCE
        mascara_formatada = f"{primeiro_digito}{resto_mascara}"
        return mascara_formatada
    except Exception as e:
        print(f"Erro ao formatar a máscara: {mascara}. Erro: {e}")
        return mascara  # Retorna a máscara original em caso de erro

# Função para normalizar CPFs
def normalizar_cpf(cpf):
    """Normaliza um CPF para garantir que tenha 11 dígitos, adicionando zeros à esquerda se necessário."""
    if pd.isna(cpf):  # Verifica se o valor é NaN
        return None
    # Remove caracteres não numéricos (caso existam)
    cpf = ''.join(filter(str.isdigit, str(cpf)))
    # Adiciona zeros à esquerda até atingir 11 dígitos
    return cpf.zfill(11)

# Função para limpar saldos
def limpar_saldo(valor):
    if isinstance(valor, str):
        valor = valor.replace('.', '').replace(',', '.')
    return float(valor)

# Função para corrigir o tipo das contas
def corrigir_tipo(df):
    """
    Substitui valores NaN na coluna 'Tipo' por 'Analitica'.
    Mantém os valores existentes (ex.: 'Sintética') inalterados.
    """
    # Verifica se a coluna 'Tipo' existe no DataFrame
    if 'Tipo' in df.columns:
        # Substitui apenas os valores NaN por 'Analitica'
        df['Tipo'] = df['Tipo'].apply(lambda x: 'Analitica' if pd.isna(x) else x)
    return df

def normalizar_conta_tce(conta):
    """
    Normaliza uma conta do TCE para garantir que tenha 18 dígitos.
    - Adiciona zeros à esquerda se necessário.
    - Ignora contas que começam com "99".
    - Aplica a correção apenas para contas com exatamente 16 dígitos.
    """
    if pd.isna(conta):  # Verifica se a conta é NaN
        return None

    # Converte a conta para string (caso ainda não seja)
    conta = str(conta)

    # Ignora contas que começam com "99"
    if conta.startswith("99"):
        return conta

    # Verifica se a conta tem exatamente 16 dígitos
    if len(conta) == 16:
        # Adiciona "00" à esquerda para completar 18 dígitos
        conta_normalizada = "00" + conta
        return conta_normalizada

    # Retorna a conta inalterada se não tiver 16 dígitos
    return conta

def converter_notacao_cientifica(valor):
    """
    Converte valores em notação científica para números inteiros.
    Se o valor não for um número, retorna o valor original.
    """
    try:
        # Remove vírgulas e pontos para evitar problemas de formatação regional
        valor_limpo = str(valor).replace(',', '').replace('.', '')
        
        # Tenta converter para float e depois para int
        numero = int(float(valor_limpo))
        return str(numero)  # Retorna como string para consistência
    except ValueError:
        # Se falhar, retorna o valor original (texto)
        return valor
    
# FILTRO ADICIONAL: Remover contas correntes que não contêm números
def contem_numeros(texto):
    """Verifica se o texto contém pelo menos um número."""
    if pd.isna(texto):  # Ignora valores NaN
        return False
    return bool(re.search(r'\d', str(texto)))  # Retorna True se houver pelo menos um número