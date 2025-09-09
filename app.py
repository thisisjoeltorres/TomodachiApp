import streamlit as st
import subprocess
import os
import json
import pandas as pd

# --- Estilos personalizados con CSS (inspirado en tu prompt) ---
# st.set_page_config(layout="centered")
st.markdown('<style>' + open('styles.css').read() + '</style>', unsafe_allow_html=True)

# --- Contenido de la UI ---
st.container()
st.title("トモダチ")
st.markdown("<h2 style='text-align: center;'>Análisis Paralelo de Textos en Japonés</h2>", unsafe_allow_html=True)
st.markdown("""
<p style='text-align: center; color: #8C6A7D; font-size: 1.1em;'>
Esta aplicación te ayuda a analizar textos extensos en japonés. Pega tu texto y la herramienta lo procesará en paralelo para extraer y traducir palabras y verbos clave.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Contenedor para la entrada de texto y botones
with st.container():
    texto_input = st.text_area("Pega aquí tu texto en japonés:", label_visibility="hidden", value="", placeholder="ここに日本語のテキストを貼り付けてください", height=250)
    
    col_btn1, col_btn2 = st.columns([1, 1])
    analizar_con_traduccion = col_btn1.button("Analizar con Traducciones", use_container_width=True)
    analizar_sin_traduccion = col_btn2.button("Analizar sin Traducciones", use_container_width=True)

# Lógica de procesamiento
if analizar_con_traduccion or analizar_sin_traduccion:
    if not texto_input:
        st.error("Por favor, ingresa un texto para analizar.")
    else:
        with open("temp_text.txt", "w", encoding="utf-8") as f:
            f.write(texto_input)

        modo = "con traducciones"
        argumento_extra = "--translate"
        if analizar_sin_traduccion:
            modo = "sin traducciones"
            argumento_extra = "--no-translate"

        st.info(f"Procesando en modo '{modo}'... Esto puede tomar un momento.")
        try:
            num_procesos = 4
            cmd = ['mpiexec', '-n', str(num_procesos), 'python', 'analizador_mpi.py', 'temp_text.txt', argumento_extra]
            
            proceso = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if os.path.exists('resultados.json'):
                with open('resultados.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                resultados = data.get('resultados', [])
                metadatos = data.get('metadatos', {})
                
                df_resultados = pd.DataFrame(resultados)
                
                # --- AÑADE ESTE BLOQUE DE CÓDIGO ---
                nombres_nuevos = {
                    'palabra_japones': 'Palabra (漢字)',
                    'lectura_kanji': 'Lectura (ひらがな)',
                    'traduccion_espanol': 'Traducción',
                    'tipo': 'Tipo',
                    'nivel_jlpt': 'Nivel JLPT',
                    'on_lecturas': 'Lecturas ON',
                    'kun_lecturas': 'Lecturas KUN',
                    'recuento_trazos': 'Trazos',
                    'grado': 'Grado'
                }
                
                # Cambiar el nombre de las columnas
                df_resultados = df_resultados.rename(columns=nombres_nuevos)
                # ------------------------------------

                columnas_ordenadas = [
                    'Palabra (漢字)', 
                    'Lectura (ひらがな)', 
                    'Traducción',
                    'Tipo', 
                    'Nivel JLPT',
                    'Lecturas ON',
                    'Lecturas KUN',
                    'Trazos',
                    'Grado'
                ]

                columnas_existentes = [col for col in columnas_ordenadas if col in df_resultados.columns]
                df_resultados = df_resultados[columnas_existentes]
                
                st.markdown("---")
                
                # --- NUEVA SECCIÓN DE MÉTRICAS (con el nivel promedio) ---
                total_palabras = metadatos.get('total_palabras', len(df_resultados) if not df_resultados.empty else 0)
                nivel_promedio = metadatos.get('nivel_promedio', 'N/A')
                tiempo_ejecucion = "N/A" # Aquí podrías capturar el tiempo real si el script lo reporta

                col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
                with col_metrics1:
                    st.metric(label="Palabras clave encontradas", value=total_palabras)
                with col_metrics2:
                    st.metric(label="Tiempo de ejecución (aprox.)", value="~10s" if total_palabras > 0 else "N/A")
                with col_metrics3:
                    st.metric(label="Nivel de dificultad promedio", value=nivel_promedio)

                st.markdown("---")
                
                if not df_resultados.empty:
                    styled_df = df_resultados.style \
                        .set_properties(**{'background-color': '#F5F5F5', 'color': '#333333'})

                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No se encontraron resultados para mostrar.")
                
            else:
                st.error("El archivo de resultados no se encontró. Hubo un error en el procesamiento.")

        except subprocess.CalledProcessError as e:
            st.error(f"Error al ejecutar el proceso MPI: {e.stderr}")
        finally:
            if os.path.exists('temp_text.txt'):
                os.remove('temp_text.txt')
            if os.path.exists('resultados.json'):
                os.remove('resultados.json')