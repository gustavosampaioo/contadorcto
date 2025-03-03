import os
import csv
import tempfile
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
st.title("Extrator de Dados KML para CSV")

arquivo_kml = st.file_uploader("Faça upload de um arquivo KML", type=["kml"])

if arquivo_kml is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as temp_kml:
        temp_kml.write(arquivo_kml.read())
        temp_kml_path = temp_kml.name
    
    dados_placemarks = extrair_dados_kml(temp_kml_path)
    
    if dados_placemarks:
        st.success("Dados extraídos com sucesso!")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_csv:
            temp_csv_path = salvar_csv(dados_placemarks, temp_csv.name)
        
        with open(temp_csv_path, "rb") as file:
            st.download_button(
                label="Baixar CSV",
                data=file,
                file_name="dados_extraidos.csv",
                mime="text/csv"
            )
    else:
        st.warning("Nenhum placemark válido encontrado no arquivo.")
