from flask import Flask, jsonify, render_template
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import json
from io import StringIO
import subprocess
import time
import threading


app = Flask(__name__)

# Configuración (puedes mover esto a un archivo Config.py si prefieres)
class Config:
    NGROK_DOMAIN = 'poorly-free-insect.ngrok-free.app'
    FLASK_PORT = 5000

# Función para iniciar ngrok en un hilo separado
def start_ngrok(domain, port):
    def run():
        time.sleep(2)
        process = subprocess.Popen(
            ['ngrok', 'http', '--domain='+domain, str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)
        print(f"\n* NGROK URL FIJADA: https://{domain} -> http://localhost:{port} *\n")
        return process
    
    ngrok_thread = threading.Thread(target=run)
    ngrok_thread.daemon = True
    ngrok_thread.start()
    return ngrok_thread

# Cargar y procesar datos
def load_data():
    df = pd.read_csv('data/sales_data_sample.csv', encoding='unicode_escape')
    df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'])
    
    # Procesamiento como en el notebook original
    df_drop = ['ADDRESSLINE1', 'ADDRESSLINE2', 'POSTALCODE', 'CITY', 
               'TERRITORY', 'PHONE', 'STATE', 'CONTACTFIRSTNAME', 
               'CONTACTLASTNAME', 'CUSTOMERNAME', 'ORDERNUMBER', 'STATUS']
    df = df.drop(df_drop, axis=1)
    
    # Convertir variables categóricas
    countries = pd.get_dummies(df['COUNTRY'], prefix='COUNTRY')
    productlines = pd.get_dummies(df['PRODUCTLINE'], prefix='PRODUCTLINE')
    dealsizes = pd.get_dummies(df['DEALSIZE'], prefix='DEALSIZE')
    
    df = pd.concat([df, countries, productlines, dealsizes], axis=1)
    df.drop(['COUNTRY', 'PRODUCTLINE', 'DEALSIZE', 'ORDERDATE'], axis=1, inplace=True)
    
    df['PRODUCTCODE'] = pd.Categorical(df['PRODUCTCODE']).codes
    
    return df

# Endpoint principal
@app.route('/')
def index():
    return render_template('index.html')

# API Endpoints
@app.route('/api/data/head')
def data_head():
    df = load_data()
    return jsonify(df.head(10).to_dict(orient='records'))

@app.route('/api/task1')
def task1():
    # Datos conceptuales para el diagrama
    diagram_data = {
        "nodes": [
            {"id": "problem", "label": "Problema", "level": 0},
            {"id": "data", "label": "Recolección\nde Datos", "level": 1},
            {"id": "analysis", "label": "Análisis", "level": 1},
            {"id": "segmentation", "label": "Segmentación", "level": 2},
            {"id": "strategy", "label": "Estrategia\nMarketing", "level": 3}
        ],
        "links": [
            {"source": "problem", "target": "data"},
            {"source": "data", "target": "analysis"},
            {"source": "analysis", "target": "segmentation"},
            {"source": "segmentation", "target": "strategy"}
        ]
    }
    return jsonify(diagram_data)

@app.route('/api/task2')
def task2():
    df = load_data()
    
    # Tipos de datos
    dtype_counts = df.dtypes.astype(str).value_counts().reset_index()
    dtype_counts.columns = ['type', 'count']
    
    # Valores nulos (usamos datos originales para esto)
    df_raw = pd.read_csv('data/sales_data_sample.csv', encoding='unicode_escape')
    nulls = df_raw.isnull().sum().reset_index()
    nulls.columns = ['column', 'null_count']
    
    return jsonify({
        "dtypes": dtype_counts.to_dict(orient='records'),
        "nulls": nulls.to_dict(orient='records'),
        "data_info": {
            "original_columns": len(df_raw.columns),
            "final_columns": len(df.columns),
            "rows": len(df)
        }
    })

@app.route('/api/task3')
def task3():
    df_raw = pd.read_csv('data/sales_data_sample.csv', encoding='unicode_escape')
    
    country_counts = df_raw['COUNTRY'].value_counts().reset_index()
    country_counts.columns = ['country', 'count']
    
    productline_counts = df_raw['PRODUCTLINE'].value_counts().reset_index()
    productline_counts.columns = ['productline', 'count']
    
    dealsize_counts = df_raw['DEALSIZE'].value_counts().reset_index()
    dealsize_counts.columns = ['dealsize', 'count']
    
    return jsonify({
        "country": country_counts.to_dict(orient='records'),
        "productline": productline_counts.to_dict(orient='records'),
        "dealsize": dealsize_counts.to_dict(orient='records')
    })

@app.route('/api/task4')
def task4():
    df = load_data()
    
    # Matriz de correlación (existente)
    corr_matrix = df.iloc[:, :10].corr().reset_index()
    corr_data = []
    for _, row in corr_matrix.iterrows():
        corr_data.append(row.to_dict())
    
    # Datos para pairplot (existente)
    sample_df = df.sample(n=100)
    pairplot_data = sample_df[['SALES', 'QUANTITYORDERED', 'PRICEEACH', 'MSRP', 'MONTH_ID']].to_dict(orient='records')
    
    # Distribuciones (existentes)
    sales_dist = df['SALES'].describe().to_dict()
    qty_dist = df['QUANTITYORDERED'].describe().to_dict()
    
    # Nuevos datos para las gráficas faltantes
    # 1. Gráfica de línea de ventas
    sales_df_group = df.groupby('MONTH_ID')['SALES'].sum().reset_index()
    sales_trend = {
        'months': sales_df_group['MONTH_ID'].tolist(),
        'sales': sales_df_group['SALES'].tolist()
    }
    
    # 2. Datos para distplots (excluyendo ORDERLINENUMBER)
    distplot_data = {}
    for i in range(8):
        col_name = df.columns[i]
        if col_name != 'ORDERLINENUMBER':
            distplot_data[col_name] = df[col_name].apply(float).tolist()
    
    return jsonify({
        "correlation": corr_data,
        "pairplot": pairplot_data,
        "sales_dist": sales_dist,
        "qty_dist": qty_dist,
        "sales_trend": sales_trend,  # Nueva
        "distplots": distplot_data   # Nueva
    })

@app.route('/api/task5')
def task5():
    # Datos conceptuales para K-Means
    points = [
        {"x": 1, "y": 2, "cluster": 0},
        {"x": 1.5, "y": 2.5, "cluster": 0},
        {"x": 3, "y": 3, "cluster": 0},
        {"x": 5, "y": 3, "cluster": 2},
        {"x": 3.5, "y": 2.5, "cluster": 0},
        {"x": 4.5, "y": 2.5, "cluster": 1},
        {"x": 3.5, "y": 4, "cluster": 1},
        {"x": 4.5, "y": 4, "cluster": 1},
        {"x": 5.5, "y": 4, "cluster": 2},
        {"x": 6, "y": 3.5, "cluster": 2}
    ]
    
    centroids = [
        {"x": 2, "y": 2.5, "cluster": 0},
        {"x": 4.5, "y": 3.5, "cluster": 1},
        {"x": 5.5, "y": 3, "cluster": 2}
    ]
    
    return jsonify({
        "points": points,
        "centroids": centroids,
        "description": {
            "what_is": "K-Means es un algoritmo de aprendizaje no supervisado que agrupa datos en K clusters basándose en su similitud.",
            "steps": [
                "Seleccionar número de clusters (K)",
                "Inicializar centroides aleatoriamente",
                "Asignar puntos al centroide más cercano",
                "Recalcular centroides como promedios",
                "Repetir hasta convergencia"
            ],
            "pros": [
                "Simple y rápido",
                "Escala bien con grandes datasets",
                "Fácil de interpretar"
            ],
            "cons": [
                "Requiere especificar K",
                "Sensible a valores atípicos",
                "Asume clusters esféricos"
            ]
        }
    })

@app.route('/api/task6')
def task6():
    df = load_data()
    scaler = StandardScaler()
    sales_df_scaled = scaler.fit_transform(df)
    
    scores = []
    range_values = list(range(1, 15))
    
    for i in range_values:
        kmeans = KMeans(n_clusters=i, random_state=42)
        kmeans.fit(sales_df_scaled)
        scores.append(kmeans.inertia_)
    
    return jsonify({
        "range": range_values,
        "scores": scores,
        "optimal_k": 5  # Determinado por el método del codo
    })

@app.route('/api/task7')
def task7():
    """
    Endpoint para el análisis de clusters con K-Means
    Devuelve:
    - Datos para visualización 2D
    - Estadísticas de clusters
    - Centroides
    - Histogramas por cluster
    """
    # Cargar y preparar datos
    df = load_data()
    scaler = StandardScaler()
    sales_df_scaled = scaler.fit_transform(df)
    
    # Aplicar K-Means (5 clusters)
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    labels = kmeans.fit_predict(sales_df_scaled)
    
    # PCA para visualización 2D
    pca = PCA(n_components=2)
    principal_comp = pca.fit_transform(sales_df_scaled)
    pca_df = pd.DataFrame(data=principal_comp, columns=['x', 'y'])
    pca_df['cluster'] = labels
    
    # Estadísticas por cluster
    sale_df_cluster = pd.concat([df, pd.DataFrame({'cluster':labels})], axis=1)
    cluster_stats = []
    for i in range(5):
        cluster_data = sale_df_cluster[sale_df_cluster['cluster'] == i]
        stats = {
            "cluster": i,
            "size": len(cluster_data),
            "avg_quantity": cluster_data['QUANTITYORDERED'].mean(),
            "avg_price": cluster_data['PRICEEACH'].mean(),
            "total_sales": cluster_data['SALES'].sum()
        }
        cluster_stats.append(stats)
    
    # Centroides (transformados inversamente para interpretación)
    cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
    cluster_centers = pd.DataFrame(data=cluster_centers, columns=df.columns)
    
    # Datos para histogramas (primeras 8 columnas)
    histograms = {}
    for col in df.columns[:8]:
        histograms[col] = []
        for cluster_num in range(5):
            cluster_data = sale_df_cluster[sale_df_cluster['cluster'] == cluster_num][col]
            histograms[col].append(cluster_data.tolist())
    
    return jsonify({
        "clusters": pca_df.to_dict(orient='records'),  # Para visualización 2D
        "cluster_stats": cluster_stats,  # Estadísticas
        "centroids": cluster_centers.to_dict(orient='records'),  # Centroides
        "histograms": histograms,  # Datos para histogramas
        "feature_names": df.columns[:8].tolist(),  # Nombres de columnas
        "cluster_descriptions": [  # Descripciones interpretativas
            "Clientes que compran en grandes cantidades y gastan mucho",
            "Clientes que prefieren productos premium",
            "Clientes ocasionales con bajo gasto",
            "Clientes estacionales con gasto moderado",
            "Clientes regulares con gasto consistente"
        ]
    })

@app.route('/api/task8')
def task8():
    df = load_data()
    scaler = StandardScaler()
    sales_df_scaled = scaler.fit_transform(df)
    
    # PCA 3D
    pca = PCA(n_components=3)
    principal_comp = pca.fit_transform(sales_df_scaled)
    pca_df = pd.DataFrame(data=principal_comp, columns=['x', 'y', 'z'])
    
    # K-Means para clusters
    kmeans = KMeans(n_clusters=5, random_state=42)
    pca_df['cluster'] = kmeans.fit_predict(sales_df_scaled)
    
    # Varianza explicada
    pca_full = PCA().fit(sales_df_scaled)
    variance = np.cumsum(pca_full.explained_variance_ratio_)
    
    return jsonify({
        "points": pca_df.to_dict(orient='records'),
        "variance": variance.tolist(),
        "components": pca_full.components_.tolist()
    })

@app.route('/api/task9')
def task9():
    # Datos conceptuales para Autoencoder
    layers = [
        {"id": "input", "name": "Input", "units": 37, "x": 0.1, "y": 0.5},
        {"id": "enc1", "name": "Encoder", "units": 50, "x": 0.3, "y": 0.5},
        {"id": "enc2", "name": "Encoder", "units": 500, "x": 0.5, "y": 0.5},
        {"id": "bottleneck", "name": "Bottleneck", "units": 8, "x": 0.7, "y": 0.5},
        {"id": "dec1", "name": "Decoder", "units": 500, "x": 0.9, "y": 0.5},
        {"id": "output", "name": "Output", "units": 37, "x": 1.1, "y": 0.5}
    ]
    
    connections = [
        {"source": "input", "target": "enc1"},
        {"source": "enc1", "target": "enc2"},
        {"source": "enc2", "target": "bottleneck"},
        {"source": "bottleneck", "target": "dec1"},
        {"source": "dec1", "target": "output"}
    ]
    
    return jsonify({
        "layers": layers,
        "connections": connections,
        "description": {
            "what_is": "Un autoencoder es una red neuronal que aprende a comprimir datos (codificar) y luego reconstruirlos (decodificar).",
            "components": [
                {"name": "Encoder", "desc": "Reduce la dimensionalidad de los datos"},
                {"name": "Bottleneck", "desc": "Representación comprimida de los datos"},
                {"name": "Decoder", "desc": "Reconstruye los datos desde la representación comprimida"}
            ],
            "pros": [
                "Reducción no lineal de dimensionalidad",
                "Capaz de aprender características complejas",
                "Útil para datos no etiquetados"
            ],
            "cons": [
                "Requiere más datos que métodos lineales como PCA",
                "Más difícil de interpretar",
                "Computacionalmente más costoso"
            ]
        }
    })

@app.route('/api/task10')
def task10():
    df = load_data()
    scaler = StandardScaler()
    sales_df_scaled = scaler.fit_transform(df)
    
    # Reducción de dimensionalidad con PCA
    pca = PCA(n_components=8)
    reduced_data = pca.fit_transform(sales_df_scaled)
    
    # Gráfica de elbow method
    scores = []
    range_values = range(1, 15)
    for i in range_values:
        kmeans = KMeans(n_clusters=i, random_state=42)
        kmeans.fit(reduced_data)
        scores.append(kmeans.inertia_)
    
    # Clustering con 3 clusters
    kmeans = KMeans(n_clusters=3, random_state=42)
    labels = kmeans.fit_predict(reduced_data)
    
    # PCA para visualización 3D
    pca_3d = PCA(n_components=3)
    principal_comp = pca_3d.fit_transform(reduced_data)
    pca_df = pd.DataFrame(data=principal_comp, columns=['x', 'y', 'z'])
    pca_df['cluster'] = labels
    
    # Preparar datos para histogramas (solo una vez)
    df_cluster = pd.concat([df, pd.DataFrame({'cluster': labels})], axis=1)
    histograms = {}
    for col in df.columns[:8]:  # Primeras 8 columnas
        histograms[col] = []
        for cluster_num in range(3):  # 3 clusters
            cluster_data = df_cluster[df_cluster['cluster'] == cluster_num][col]
            histograms[col].append({
                'values': cluster_data.tolist(),
                'mean': float(cluster_data.mean()),
                'std': float(cluster_data.std()),
                'min': float(cluster_data.min()),
                'max': float(cluster_data.max())
            })
    
    # Estadísticas por cluster
    cluster_stats = []
    for i in range(3):
        cluster_data = df_cluster[df_cluster['cluster'] == i]
        stats = {
            'size': len(cluster_data),
            'avg_quantity': float(cluster_data['QUANTITYORDERED'].mean()),
            'avg_price': float(cluster_data['PRICEEACH'].mean()),
            'avg_sales': float(cluster_data['SALES'].mean())
        }
        cluster_stats.append(stats)
    
    return jsonify({
        "points": pca_df.to_dict(orient='records'),
        "histograms": histograms,
        "cluster_stats": cluster_stats,
        "feature_names": df.columns[:8].tolist(),
        "elbow_data": {
            "clusters": list(range_values),
            "scores": scores
        },
        "cluster_descriptions": [
            "Clientes que compran en grandes cantidades (media: {:.1f} unidades) y prefieren productos caros (${:.2f} promedio)".format(
                cluster_stats[0]['avg_quantity'], cluster_stats[0]['avg_price']),
            "Clientes con compras promedio (media: {:.1f} unidades) que prefieren productos de alto precio (${:.2f} promedio)".format(
                cluster_stats[1]['avg_quantity'], cluster_stats[1]['avg_price']),
            "Clientes que compran en pequeñas cantidades (media: {:.1f} unidades) y prefieren productos económicos (${:.2f} promedio)".format(
                cluster_stats[2]['avg_quantity'], cluster_stats[2]['avg_price'])
        ],
        "cluster_colors": ["#4CA1AF", "#2C3E50", "#D4B483"]
    })

if __name__ == '__main__':
    # Iniciar ngrok en un hilo separado
    start_ngrok(Config.NGROK_DOMAIN, Config.FLASK_PORT)
    
    # Iniciar la aplicación Flask
    app.run(port=Config.FLASK_PORT, debug=True)