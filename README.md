### **README del Proyecto**

-----

# Tomodachi: Analizador Paralelo de Textos en Japonés

## Descripción del Proyecto

Tomodachi es una herramienta diseñada para el análisis rápido y eficiente de textos extensos en japonés. Utilizando el poder del procesamiento paralelo a través de MPI (Message Passing Interface), la aplicación tokeniza y procesa palabras clave, proporcionando información detallada como la traducción, la lectura en Hiragana, el tipo de palabra y el nivel de dificultad JLPT.

El objetivo principal es ofrecer una herramienta de estudio y análisis lingüístico que maneje grandes volúmenes de texto de manera eficiente, ideal para estudiantes de japonés, investigadores o cualquier persona que trabaje con material en este idioma.

## Características Principales

  * **Procesamiento Paralelo:** Distribuye la carga de trabajo entre múltiples procesos para un análisis ultra-rápido.
  * **Análisis Lingüístico Detallado:** Extrae y clasifica palabras clave (sustantivos, verbos, adjetivos, etc.) con el motor de tokenización SudachiPy.
  * **Traducciones y Lecturas:** Obtiene la traducción al español y las lecturas (kun'yomi, on'yomi) para los kanjis.
  * **Nivel de Dificultad:** Estima el nivel de dificultad promedio del texto basándose en el JLPT de los kanjis encontrados.
  * **Interfaz Intuitiva:** Interfaz de usuario limpia y fácil de usar construida con Streamlit.

## Requisitos de Instalación

Antes de ejecutar la aplicación, asegúrate de tener Python 3.7+ instalado y un entorno MPI configurado (como [MS-MPI](https://docs.microsoft.com/en-us/message-passing-interface/microsoft-mpi) o [Open MPI](https://www.open-mpi.org/)).

Puedes instalar todas las bibliotecas de Python necesarias con un solo comando:

```
pip install streamlit mpi4py translate sudachipy pandas requests
```

## Uso de la Aplicación

Para ejecutar la aplicación, navega al directorio del proyecto en tu terminal y usa el siguiente comando.

1.  **Asegúrate de que tu entorno MPI esté activo.**

2.  **Ejecuta la aplicación con Streamlit:**

    ```
    streamlit run app.py
    ```

    Streamlit iniciará un servidor local y abrirá la aplicación en tu navegador web por defecto. Si el navegador no se abre automáticamente, puedes acceder a la URL proporcionada en la terminal (generalmente `http://localhost:8501`).

3.  **Pega tu texto en el área designada y selecciona la opción de análisis que prefieras.**

## Estructura del Proyecto

  * `app.py`: El archivo principal de la aplicación Streamlit que contiene la interfaz de usuario.
  * `analizador_mpi.py`: El script de procesamiento paralelo que realiza el análisis del texto.
  * `styles.css`: Hoja de estilos CSS para personalizar la apariencia de la interfaz de Streamlit.