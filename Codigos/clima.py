from __future__ import annotations # Permite utilizar anotações de tipos de forma adiada.

import asyncio # Importa recursos para programação assíncrona.
import json # Importa funções para trabalhar com arquivos e dados JSON.
import math # Importa funções matemáticas.
from datetime import date, timedelta # Importa date para datas e timedelta para intervalos de tempo.
from pathlib import Path  # Importa Path para manipular caminhos de arquivos e diretórios.
from typing import Any, Dict, Iterable, List, Optional, Tuple  # Importa tipos para documentação e verificação de tipos.

import httpx # Importa a biblioteca HTTPX para realizar requisições HTTP a APIs e sites.

NORMAL_INI = 1 # Define uma constante chamada NORMAL_INI com o valor inicial 1
CACHE_DIR = Path(__file__).resolve().parent / ".cache_clima" # Define o caminho da pasta ".cache_clima", localizada no mesmo diretório deste arquivo Python.
CACHE_DIR.mkdir(exist_ok=True, parents=True) # Cria a pasta ".cache_clima".
# parents=True permite criar diretórios intermediários, caso necessário.
# exist_ok=True evita erros se a pasta já existir.


async def _get_json(client: Optional[httpx.AsyncClient], url: str, params: Dict[str, Any], tentativas: int = 3, timeout: float = 25.0): # Recebe um cliente HTTP assíncrono ou None. # (url:str)Endereço da API que será consultada. # params: Dict[str, Any], Parâmetros enviados na requisição. #(tentativas: int = 3,)  # Define o número máximo de tentativas (padrão: 3). #(timeout: float = 25.0) # Define o tempo máximo de espera (25 segundos).
    last_error = None  # Inicializa uma variável para armazenar o último erro ocorrido.
    headers = {"User-Agent": "ETEMAR/1.0"} # Define o cabeçalho que identifica a aplicação nas requisições HTTP.
    for _ in range(max(1, tentativas)): # Executa o processo pelo menos uma vez, respeitando o número de tentativas.
        try: # Inicia um bloco para tentar realizar a requisição.

            if client is None: # Verifica se nenhum cliente HTTP foi fornecido.
                async with httpx.AsyncClient(headers=headers, timeout=timeout) as c: # Cria um novo cliente HTTP assíncrono com cabeçalhos e tempo limite definidos.
                    r = await c.get(url, params=params: # Faz uma requisição GET à API, enviando os parâmetros.
                    r.raise_for_status() # Verifica se a resposta HTTP contém algum erro.
                    return r.json() # Converte a resposta recebida para JSON e retorna os dados.
            r = await client.get(url, params=params) # Utiliza o cliente recebido para consultar a API.
            r.raise_for_status() # Verifica se a resposta HTTP foi bem-sucedida.
            return r.json() # Converte a resposta da API para JSON e retorna os dados.
        except Exception as exc:  # pragma: no cover - defensivo
            last_error = exc  # Armazena o último erro ocorrido.

            await asyncio.sleep(0.1)  # Aguarda 0,1 segundo antes de realizar uma nova tentativa.
    if last_error is not None: # Verifica se algum erro foi registrado durante as tentativas.
        raise last_error # Lança novamente o último erro ocorrido.
    return {} # Retorna um dicionário vazio caso nenhuma resposta ou erro tenha sido registrado.


def hoje_br() -> date: # Define uma função chamada hoje_br que retorna uma data no formato date.
    return date.today()  # Retorna a data atual do computador onde o programa está sendo executado.


def _ultimo_dia_mes(ano: int, mes: int) -> int:
     # Define uma função que recebe o ano e o mês e retorna o último dia desse mês.
    # ano: representa o ano (exemplo: 2026).
    # mes: representa o mês (exemplo: 2 para fevereiro).
    # -> int indica que a função retorna um número inteiro.

    if mes == 12:  # Verifica se o mês informado é dezembro (mês 12).
        return 31  # Se for dezembro, retorna 31, pois dezembro sempre tem 31 dias.
    prox = date(ano + (mes // 12), ((mes % 12) + 1), 1)
    # Cria uma data correspondente ao primeiro dia do mês seguinte.
    # mes // 12 verifica se é necessário avançar um ano.
    # mes % 12 calcula o restante da divisão por 12.
    # + 1 determina o próximo mês.
    # O último argumento (1) representa o primeiro dia do mês.
    return (prox - timedelta(days=1)).day
    # Subtrai um dia do primeiro dia do próximo mês.
    # Assim, obtém o último dia do mês desejado.
    # .day extrai somente o número do dia.


def resolver_periodo(ex: Dict[str, Any], hoje: Optional[date] = None) -> Tuple[Optional[date], Optional[date], Optional[str]]: # Recebe um dicionário com informações sobre o período solicitado.
    hoje = hoje or hoje_br() 
    # Se a data de referência não for informada, utiliza a data atual.
    # A função hoje_br() retorna a data atual do computador.
    mes = ex.get("mes")
     # Busca no dicionário o valor correspondente à chave "mes".
    # Se a chave não existir, retorna None.

    if mes is not None:  # Verifica se foi informado um mês.
        ano = int(ex.get("ano") or hoje.year)
        # Obtém o ano informado no dicionário.
        # Se o ano não existir ou estiver vazio, utiliza o ano atual.
        # int() converte o valor para número inteiro.
        if mes > hoje.month: # Verifica se o mês informado é maior que o mês atual.
            ano -= 1  # Se for maior, considera que o mês pertence ao ano anterior.
        ini = date(ano, int(mes), 1) 
        fim = date(ano, int(mes), _ultimo_dia_mes(ano, int(mes)))
        return ini, fim, f"Período: {ini.isoformat()} a {fim.isoformat()}"

    ini_raw = ex.get("data_inicio")
    fim_raw = ex.get("data_fim")
    if ini_raw or fim_raw:
        ini = date.fromisoformat(ini_raw) if ini_raw else date.fromisoformat(fim_raw)
        fim = date.fromisoformat(fim_raw) if fim_raw else ini
        if ini > hoje or fim > hoje:
            return ini, fim, "Datas futuras foram consideradas como erro de relato"
        return ini, fim, None

    return None, None, None


async def _localizar_municipio(municipio: str, uf: str = "") -> Optional[Dict[str, Any]]:
    if not municipio:
        return None
    params = {"name": municipio, "count": 10, "language": "pt", "format": "json"}
    if uf:
        params["country_code"] = "BR"
    payload = await _get_json(None, "https://geocoding-api.open-meteo.com/v1/search", params)
    resultados = payload.get("results") or []
    if not resultados:
        return None
    for item in resultados:
        nome = (item.get("name") or "").lower()
        uf_item = (item.get("admin1") or "").lower()
        if uf:
            if nome == municipio.lower() and uf_item == uf.lower():
                return item
        if nome == municipio.lower():
            return item
    return resultados[0]


def _normal_mm_por_mes(mes: int, ano: int) -> float:
    if mes == 1:
        return 93.0
    if mes == 2:
        return 70.0
    if mes == 3:
        return 85.0
    if mes == 4:
        return 60.0
    if mes == 5:
        return 42.0
    if mes == 6:
        return 20.0
    if mes == 7:
        return 15.0
    if mes == 8:
        return 10.0
    if mes == 9:
        return 30.0
    if mes == 10:
        return 55.0
    if mes == 11:
        return 72.0
    return 90.0


def _total_mm(chuva: Iterable[Any]) -> float:
    total = 0.0
    for valor in chuva:
        try:
            if valor is not None:
                total += float(valor)
        except (TypeError, ValueError):
            pass
    return total


def _formatar_resumo(total: float, normal: float, periodo: Optional[str]) -> str:
    if not periodo:
        periodo = "período informado"
    return (
        f"{periodo}: chuva acumulada {total:.1f} mm; normal do período {normal:.1f} mm "
        f"({(total / normal * 100) if normal else 0:.0f}% do normal)."
    )


def _alerta(nivel: str, mensagem: str) -> Dict[str, str]:
    return {"nivel": nivel, "mensagem": mensagem}


async def coletar_clima(ex: Dict[str, Any]) -> Dict[str, Any]:
    hoje = hoje_br()
    municipio = (ex.get("municipio") or "").strip()
    uf = (ex.get("uf") or "").strip().upper()
    local = await _localizar_municipio(municipio, uf)
    local_payload = {"cidade": municipio, "estado": (local or {}).get("admin1") or uf or ""}

    ini, fim, sup = resolver_periodo(ex, hoje)
    alertas: List[Dict[str, str]] = []
    suposicoes: List[str] = []
    avisos_sistema: List[str] = []
    analise: Dict[str, Any] = {"total_mm": 0.0, "normal_mm": 0.0, "periodo": None}
    previsao: List[Dict[str, Any]] = []
    resumo = "Não foi possível consultar o clima."

    if not municipio:
        alertas.append(_alerta("info", "Não foi informado o município para verificar o relato climático."))
        return {
            "local": local_payload,
            "resumo": resumo,
            "analise": analise,
            "previsao": previsao,
            "alertas": alertas,
            "suposicoes": suposicoes,
            "avisos_sistema": avisos_sistema,
        }

    if ini is not None and fim is not None and (ini > hoje or fim > hoje):
        alertas.append(_alerta("contradicao", f"A data do relato ({ini.isoformat()} a {fim.isoformat()}) está no futuro."))
        return {
            "local": {"cidade": municipio, "estado": local_payload["estado"]},
            "resumo": "Data futura informada; clima não foi consultado.",
            "analise": analise,
            "previsao": previsao,
            "alertas": alertas,
            "suposicoes": suposicoes,
            "avisos_sistema": avisos_sistema,
        }

    if ini is None and fim is None:
        return {
            "local": local_payload,
            "resumo": "Sem período definido para consultar o clima.",
            "analise": analise,
            "previsao": previsao,
            "alertas": [_alerta("info", "Sem período definido para consultar o clima.")],
            "suposicoes": suposicoes,
            "avisos_sistema": avisos_sistema,
        }

    latitude = (local or {}).get("latitude")
    longitude = (local or {}).get("longitude")
    if latitude is None or longitude is None:
        alertas.append(_alerta("contradicao", f"Não localizei '{municipio}' em {uf or 'Brasil'} para verificar o clima."))
        return {
            "local": local_payload,
            "resumo": "Não foi possível geolocalizar o município.",
            "analise": analise,
            "previsao": previsao,
            "alertas": alertas,
            "suposicoes": suposicoes,
            "avisos_sistema": avisos_sistema,
        }

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": ini.isoformat(),
        "end_date": fim.isoformat(),
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
    }
    payload = await _get_json(None, "https://archive-api.open-meteo.com/v1/archive", params)
    daily = (payload.get("daily") or {})
    times = daily.get("time") or []
    chuva = daily.get("precipitation_sum") or [0.0] * len(times)
    total = _total_mm(chuva)
    normal = _normal_mm_por_mes(ini.month, ini.year)
    analise = {"total_mm": total, "normal_mm": normal, "periodo": f"{ini.isoformat()} a {fim.isoformat()}", "dia_max": max(chuva, default=0.0)}
    resumo = _formatar_resumo(total, normal, f"{ini.isoformat()} a {fim.isoformat()}")
    previsao = [{"dia": d, "chuva_mm": c} for d, c in zip(times, chuva)]

    if ini.month == 1 and ini.year == hoje.year:
        suposicoes.append(f"considerei janeiro como referência histórica: normal de {normal:.1f} mm.")
    elif ini.month == 1:
        suposicoes.append(f"considerei janeiro como referência histórica: normal de {normal:.1f} mm.")

    evento = (ex.get("evento") or "").lower()
    chuva_rel = ex.get("chuva_relatada_mm")
    rel_mm = float(chuva_rel) if chuva_rel is not None else None

    if evento == "chuva_excessiva":
        if rel_mm is not None:
            if rel_mm > 500:
                alertas.append(_alerta("contradicao", f"O relato de {rel_mm:g} mm parece excessivo para a chuva observada em {municipio}."))
            elif total >= rel_mm * 0.8:
                alertas.append(_alerta("confirmado", f"A chuva observada ({total:.1f} mm) confirma a intensidade relatada de {rel_mm:g} mm."))
                alertas.append(_alerta("confirmado", f"Os dados climáticos sustentam a ocorrência de chuva intensa em {municipio}."))
            else:
                alertas.append(_alerta("contradicao", f"O relato de {rel_mm:g} mm não bate com os dados climáticos ({total:.1f} mm)."))
        else:
            if total >= normal * 1.2:
                alertas.append(_alerta("confirmado", f"A chuva acumulada ({total:.1f} mm) supera o normal do período ({normal:.1f} mm)."))
            elif total < normal * 0.5:
                alertas.append(_alerta("contradicao", f"A chuva acumulada ({total:.1f} mm) está muito abaixo do normal do período ({normal:.1f} mm)."))
            else:
                alertas.append(_alerta("aviso", f"A chuva acumulada ({total:.1f} mm) está próxima do normal do período ({normal:.1f} mm)."))

    if not alertas:
        alertas.append(_alerta("info", f"Sem indício claro de anomalia climática para {municipio}."))

    return {
        "local": {"cidade": municipio, "estado": local_payload["estado"], "uf": uf or (local or {}).get("admin1") or ""},
        "resumo": resumo,
        "analise": analise,
        "previsao": previsao,
        "alertas": alertas,
        "suposicoes": suposicoes,
        "avisos_sistema": avisos_sistema,
    }


def montar_graficos(analise: Dict[str, Any], previsao: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not previsao:
        return [{"tipo": "texto", "titulo": "Clima", "valor": "Sem dados de previsão"}]
    return [{
        "tipo": "barra",
        "titulo": "Chuva acumulada",
        "dados": [{"label": item.get("dia", "-"), "valor": float(item.get("chuva_mm", 0) or 0)} for item in previsao[:10]],
        "normal_mm": float(analise.get("normal_mm", 0) or 0),
    }]
