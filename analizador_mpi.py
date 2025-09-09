import sys
import json
import concurrent.futures
from mpi4py import MPI
from translate import Translator
import time
from sudachipy import tokenizer, dictionary
import requests
import os
from collections import Counter

# Inicializar el tokenizador de SudachiPy
tokenizer_obj = dictionary.Dictionary().create()
mode = tokenizer.Tokenizer.SplitMode.A

# Cache para almacenar resultados de la API (más que solo la traducción)
cache_resultados = {}

def contiene_kanji(texto):
    """Retorna True si la cadena contiene al menos un caracter kanji."""
    return any(u'\u4e00' <= char <= u'\u9faf' for char in texto)

def obtener_datos_kanji(palabra):
    try:
        response = requests.get(f"https://kanjiapi.dev/v1/kanji/{palabra}")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

def procesar_palabra(palabra, traducir_modo):
    """Procesa una palabra y obtiene todos los datos relevantes."""
    if not traducir_modo:
        return {
            'traduccion_espanol': "No traducido",
            'kun_lecturas': [],
            'on_lecturas': [],
            'nivel_jlpt': 'N/A', # Cambiado a string para consistencia
            'recuento_trazos': None,
            'grado': None
        }

    if palabra in cache_resultados:
        return cache_resultados[palabra]

    resultado = {}
    
    if contiene_kanji(palabra):
        datos_kanji = obtener_datos_kanji(palabra)
        if datos_kanji:
            # Si se encuentran datos de kanji, los usamos
            resultado['traduccion_espanol'] = datos_kanji.get('meanings', ['N/A'])[0]
            resultado['kun_lecturas'] = datos_kanji.get('kun_readings', [])
            resultado['on_lecturas'] = datos_kanji.get('on_readings', [])
            resultado['nivel_jlpt'] = f"N{datos_kanji.get('jlpt', 'N/A')}"
            resultado['recuento_trazos'] = datos_kanji.get('stroke_count', 'N/A')
            resultado['grado'] = datos_kanji.get('grade', 'N/A')
        else:
            # Si es un kanji pero la API falla, usamos el traductor genérico
            try:
                translator = Translator(from_lang="ja", to_lang="es")
                resultado['traduccion_espanol'] = translator.translate(palabra)
            except Exception:
                resultado['traduccion_espanol'] = "Traducción no disponible"
            resultado.update({'kun_lecturas': [], 'on_lecturas': [], 'nivel_jlpt': 'N/A', 'recuento_trazos': 'N/A', 'grado': 'N/A'})
    else:
        # Si no es un kanji, usamos el traductor genérico
        try:
            translator = Translator(from_lang="ja", to_lang="es")
            resultado['traduccion_espanol'] = translator.translate(palabra)
        except Exception:
            resultado['traduccion_espanol'] = "Traducción no disponible"
        resultado.update({'kun_lecturas': [], 'on_lecturas': [], 'nivel_jlpt': 'N/A', 'recuento_trazos': 'N/A', 'grado': 'N/A'})
        
    cache_resultados[palabra] = resultado
    return resultado

def analizar_texto(texto, traducir_modo):
    """Analiza y procesa un fragmento de texto usando multithreading y cache."""
    
    start_analisis = time.time()
    palabras_analizadas = []
    tokens = tokenizer_obj.tokenize(texto, mode)
    
    palabras_a_procesar = []
    lista_de_tokens = []
    
    partes_de_habla_interesantes = {'名詞', '動詞', '形容詞', '形容動詞', '副詞', '連体詞'}

    for token in tokens:
        pos_list = token.part_of_speech()
        es_interesante = any(pos in partes_de_habla_interesantes for pos in pos_list)
        
        if not es_interesante or '数詞' in pos_list:
            continue
            
        palabra_norm = token.normalized_form()
        
        if contiene_kanji(palabra_norm) or '動詞' in pos_list:
            palabras_a_procesar.append(palabra_norm)
            lista_de_tokens.append(token)
    end_analisis = time.time()
    
    start_traduccion = time.time()
    
    procesar_con_args = [(palabra, traducir_modo) for palabra in palabras_a_procesar]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        resultados_procesamiento = list(executor.map(lambda p: procesar_palabra(*p), procesar_con_args))
    end_traduccion = time.time()
    
    for i, token in enumerate(lista_de_tokens):
        lectura_kanji = token.reading_form()
        
        datos_palabra = {
            'palabra_japones': token.surface(),
            'lectura_kanji': lectura_kanji,
            'palabra_normalizada': token.normalized_form(),
            'tipo': token.part_of_speech()[0]
        }
        
        datos_palabra.update(resultados_procesamiento[i])
        palabras_analizadas.append(datos_palabra)
    
    return palabras_analizadas, {
        "tiempo_analisis": end_analisis - start_analisis,
        "tiempo_traduccion": end_traduccion - start_traduccion,
        "palabras_procesadas": len(palabras_a_procesar),
        "palabras_cache": len(cache_resultados)
    }

def calcular_nivel_promedio(resultados):
    """Calcula el nivel JLPT más frecuente en los resultados."""
    niveles = [item['nivel_jlpt'] for item in resultados if item.get('nivel_jlpt') and item['nivel_jlpt'] != 'N/A']
    if not niveles:
        return 'N/A'
    
    # La moda es el valor que más se repite
    # Para JLPT, ordenamos de N5 a N1 para elegir el más bajo en caso de empate
    jlpt_orden = ['N5', 'N4', 'N3', 'N2', 'N1']
    conteo_niveles = Counter(niveles)
    
    # Buscamos el nivel con la cuenta más alta
    nivel_mas_frecuente = conteo_niveles.most_common(1)[0][0]
    return nivel_mas_frecuente


if __name__ == '__main__':
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    traducir_modo = '--no-translate' not in sys.argv
    
    start_time = MPI.Wtime()

    if rank == 0:
        if len(sys.argv) < 2:
            print("Error: Se requiere un archivo de texto como argumento.")
            comm.Abort()
        
        archivo_temporal = sys.argv[1]
        if not os.path.exists(archivo_temporal):
            print(f"Error: El archivo '{archivo_temporal}' no fue encontrado.")
            comm.Abort()
        
        with open(archivo_temporal, 'r', encoding='utf-8') as f:
            texto_completo = f.read()

        texto_parts = [texto_completo[i::size] for i in range(size)]
    else:
        texto_parts = None

    texto_local = comm.scatter(texto_parts, root=0)
    
    resultado_local, metricas_locales = analizar_texto(texto_local, traducir_modo)
    
    resultados_totales = comm.gather(resultado_local, root=0)
    metricas_totales = comm.gather(metricas_locales, root=0)

    if rank == 0:
        end_time = MPI.Wtime()
        
        resultados_unificados = [item for sublist in resultados_totales for item in sublist]
        
        vistos = set()
        resultados_finales = []
        for item in resultados_unificados:
            palabra_norm = item['palabra_normalizada']
            if palabra_norm not in vistos:
                vistos.add(palabra_norm)
                resultados_finales.append(item)
        
        # NUEVO: Calculamos el nivel promedio
        nivel_promedio = calcular_nivel_promedio(resultados_finales)
        
        total_palabras_procesadas = sum(m['palabras_procesadas'] for m in metricas_totales)
        total_tiempo_analisis = sum(m['tiempo_analisis'] for m in metricas_totales)
        total_tiempo_traduccion = sum(m['tiempo_traduccion'] for m in metricas_totales)
        total_palabras_cache = len(cache_resultados)

        print("\n--- DETALLES DEL PROCESAMIENTO ---")
        print(f"Total de palabras procesadas: {total_palabras_procesadas}")
        print(f"Nivel de dificultad promedio: {nivel_promedio}")
        print(f"Palabras unicas obtenidas de la API/cache: {total_palabras_cache}")
        print(f"Tiempo total de analisis (paralelo): {total_tiempo_analisis:.2f} segundos")
        print(f"Tiempo total de obtencion de datos (concurrente): {total_tiempo_traduccion:.2f} segundos")
        print(f"Tiempo total de ejecucion del programa: {end_time - start_time:.2f} segundos")
        print("-----------------------------------")
        
        # Añadimos el nivel promedio al JSON de resultados
        output_data = {
            "resultados": resultados_finales,
            "metadatos": {
                "nivel_promedio": nivel_promedio,
                "total_palabras": len(resultados_finales)
            }
        }
        
        with open('resultados.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        print("Analisis completado y guardado en resultados.json")