import os
import csv
import tempfile
import requests
import streamlit as st
from xml.etree import ElementTree as ET

def extrair_dados_kml(arquivo_kml):
    """Extrai os dados de placemarks do tipo Point de um arquivo KML."""
    tree = ET.parse(arquivo_kml)
    root = tree.getroot()
    placemarks = root.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
    dados_placemarks = []
    
    for placemark in placemarks:
        point = placemark.find('.//{http://www.opengis.net/kml/2.2}Point')
        if point is not None:
            name = placemark.findtext('.//{http://www.opengis.net/kml/2.2}name')
            coordinates = point.findtext('.//{http://www.opengis.net/kml/2.2}coordinates')
            if coordinates:
                parts = coordinates.strip().split(',')
                if len(parts) >= 2:
                    longitude = parts[0]
                    latitude = parts[1]
                    latitude_longitude = f"{latitude},{longitude}"
                    dados_placemarks.append((name, latitude_longitude))
    
    return dados_placemarks

def salvar_csv(dados, nome_arquivo):
    """Salva os dados extraídos em um arquivo CSV temporário."""
    with open(nome_arquivo, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Name', 'Latitude Longitude'])
        for linha in dados:
            writer.writerow(linha)
    return nome_arquivo

# Interface Streamlit
st.title("Extrator de Dados KML para CSV de Nuvem")

kml_url = st.text_input("https://drive.google.com/file/d/16sPR0qxkCVZm7fEy2hGz0IcHokC1jJvU/view?usp=drive_link")

if kml_url:
    try:
        # Download do arquivo KML
        response = requests.get(kml_url)
        response.raise_for_status()
        
        # Salvar em arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as temp_kml:
            temp_kml.write(response.content)
            temp_kml_path = temp_kml.name
        
        # Processar arquivo
        dados_placemarks = extrair_dados_kml(temp_kml_path)
        
        if dados_placemarks:
            st.success(f"{len(dados_placemarks)} registros encontrados!")
            
            # Criar CSV temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_csv:
                temp_csv_path = salvar_csv(dados_placemarks, temp_csv.name)
            
            # Botão de download
            with open(temp_csv_path, "rb") as file:
                st.download_button(
                    label="Baixar CSV",
                    data=file,
                    file_name="dados_geograficos.csv",
                    mime="text/csv"
                )
            
            # Limpar arquivos temporários
            os.unlink(temp_kml_path)
            os.unlink(temp_csv_path)
        else:
            st.warning("Nenhum dado geográfico encontrado no arquivo.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao baixar o arquivo: {str(e)}")
    except ET.ParseError as e:
        st.error("Erro na análise do arquivo KML. Verifique se o formato está correto.")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {str(e)}")
