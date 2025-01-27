from datetime import datetime, date
import locale

locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")  # Configura para português brasileiro

def fulldate(someDate):
    if isinstance(someDate, date):  # Verifica se é um objeto date ou datetime
        return someDate.strftime("%d de %B de %Y")
    
    # Caso seja string, tenta convertê-la para uma data válida
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]  # Lista de formatos aceitos
    for formato in formatos:
        try:
            date_obj = datetime.strptime(someDate, formato).date()  # Converte para um objeto date
            return date_obj.strftime("%d de %B de %Y")  # Retorna por extenso
        except (ValueError, TypeError):
            continue  # Tenta o próximo formato
    
    return someDate  # Retorna a entrada original se nenhum formato for aceito
