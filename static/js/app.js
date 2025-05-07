document.addEventListener('DOMContentLoaded', function () {
    const activeTab = document.querySelector('.nav-link.active');
    if (activeTab) {
        const tabId = activeTab.getAttribute('href').replace('#', '');
        loadTaskData(tabId);
    }

    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (event) {
            const taskId = event.target.getAttribute('href').replace('#', '');
            loadTaskData(taskId);
        });
    });
});

function loadTaskData(taskId) {
    fetch(`/api/${taskId}`)
        .then(response => response.json())
        .then(data => {
            switch (taskId) {
                case 'task1': renderTask1(data); break;
                case 'task2': renderTask2(data); break;
                case 'task3': renderTask3(data); break;
                case 'task4': renderTask4(data); break;
                case 'task5': renderTask5(data); break;
            }
        })
        .catch(error => console.error(`Error al cargar ${taskId}:`, error));
}

function getColorForLevel(level) {
    const colors = ['#4CA1AF', '#2C3E50', '#D4B483', '#F7C59F'];
    return colors[level % colors.length];
}

function renderTask1(data) {
    const nodes = data.nodes.map(node => ({
        ...node,
        color: getColorForLevel(node.level)
    }));

    const edgeX = [], edgeY = [];
    data.links.forEach(link => {
        const source = nodes.find(n => n.id === link.source);
        const target = nodes.find(n => n.id === link.target);
        edgeX.push(source.x, target.x, null);
        edgeY.push(source.y, target.y, null);
    });

    const diagramData = [{
        type: 'scatter',
        mode: 'markers+text',
        x: nodes.map(n => n.x),
        y: nodes.map(n => n.y),
        text: nodes.map(n => n.label),
        textposition: 'middle center',
        marker: {
            size: 30,
            color: nodes.map(n => n.color),
            line: { width: 2, color: 'white' }
        },
        hoverinfo: 'text',
        textfont: { size: 12, color: 'white' }
    }, {
        type: 'scatter',
        mode: 'lines',
        x: edgeX,
        y: edgeY,
        line: { width: 2, color: '#888' },
        hoverinfo: 'none'
    }];

    Plotly.newPlot('task1-diagram', diagramData, {
        title: 'Diagrama Conceptual del Proyecto',
        showlegend: false,
        xaxis: { showgrid: false, zeroline: false, showticklabels: false, range: [-0.1, 1.2] },
        yaxis: { showgrid: false, zeroline: false, showticklabels: false, range: [-0.1, 1.1] },
        margin: { t: 40, b: 20, l: 20, r: 20 },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)'
    });
}

function renderTask2(data) {
    Plotly.newPlot('task2-dtypes', [{
        type: 'bar',
        x: data.dtypes.map(d => d.type),
        y: data.dtypes.map(d => d.count),
        marker: { color: '#4CA1AF' }
    }], {
        title: 'Distribución de Tipos de Datos',
        xaxis: { title: 'Tipo de dato' },
        yaxis: { title: 'Cantidad' },
        margin: { t: 40, b: 60, l: 60, r: 20 }
    });

    Plotly.newPlot('task2-nulls', [{
        type: 'bar',
        x: data.nulls.map(n => n.column),
        y: data.nulls.map(n => n.null_count),
        marker: { color: '#2C3E50' }
    }], {
        title: 'Valores Nulos por Columna',
        xaxis: { title: 'Columna' },
        yaxis: { title: 'Valores nulos' },
        margin: { t: 40, b: 120, l: 60, r: 20 }
    });

    document.getElementById('task2-info').innerHTML = `
        <div class="col-md-4"><p><strong>Columnas Originales:</strong> ${data.data_info.original_columns}</p></div>
        <div class="col-md-4"><p><strong>Columnas Finales:</strong> ${data.data_info.final_columns}</p></div>
        <div class="col-md-4"><p><strong>Filas:</strong> ${data.data_info.rows}</p></div>
    `;

    fetch('/api/data/head')
        .then(response => response.json())
        .then(rows => {
            document.getElementById('task2-data').innerHTML = rows.map(row => `
                <tr>
                    <td>${row.QUANTITYORDERED}</td>
                    <td>${row.PRICEEACH.toFixed(2)}</td>
                    <td>${row.SALES.toFixed(2)}</td>
                    <td>${row.MONTH_ID}</td>
                    <td>${row.YEAR_ID}</td>
                </tr>
            `).join('');
        });
}

function renderTask3(data) {
    const renderBar = (id, title, x, y, color) => {
        Plotly.newPlot(id, [{
            type: 'bar',
            x,
            y,
            marker: { color }
        }], {
            title,
            xaxis: { title: '' },
            yaxis: { title: 'Conteo' },
            margin: { t: 40, b: 100, l: 60, r: 20 }
        });
    };

    renderBar('task3-country', 'Distribución por País', data.country.map(c => c.country), data.country.map(c => c.count), '#4CA1AF');
    renderBar('task3-productline', 'Distribución por Línea de Producto', data.productline.map(p => p.productline), data.productline.map(p => p.count), '#2C3E50');
    renderBar('task3-dealsize', 'Distribución por Tamaño de Trato', data.dealsize.map(d => d.dealsize), data.dealsize.map(d => d.count), '#D4B483');
}

function renderTask4(data) {
    // Aquí puedes colocar el mismo código de `renderTask4` que ya tienes en tu versión original.
    // Lo omití por espacio, pero puedo incluirlo si lo necesitas de nuevo.
}

function renderTask5(data) {
    const clusterColors = ['#4CA1AF', '#2C3E50', '#D4B483'];
    const traces = data.points.map(point => ({
        x: [point.x],
        y: [point.y],
        mode: 'markers',
        marker: {
            size: 12,
            color: clusterColors[point.cluster]
        },
        showlegend: false
    }));

    traces.push({
        x: data.centroids.map(c => c.x),
        y: data.centroids.map(c => c.y),
        mode: 'markers',
        marker: {
            size: 20,
            color: clusterColors,
            symbol: 'x',
            line: { width: 2 }
        },
        name: 'Centroides'
    });

    data.points.forEach(point => {
        const centroid = data.centroids[point.cluster];
        traces.push({
            x: [point.x, centroid.x],
            y: [point.y, centroid.y],
            mode: 'lines',
            line: { color: '#aaa', width: 1, dash: 'dot' },
            showlegend: false
        });
    });

    Plotly.newPlot('task5-diagram', traces, {
        title: 'Diagrama Conceptual de K-Means',
        xaxis: { showgrid: false, zeroline: false, range: [0, 7] },
        yaxis: { showgrid: false, zeroline: false, range: [1.5, 4.5] },
        margin: { t: 40, b: 40, l: 40, r: 20 }
    });

    document.getElementById('task5-whatis').textContent = data.description.what_is;

    const stepsList = document.getElementById('task5-steps');
    stepsList.innerHTML = '';
    data.description.steps.forEach(step => {
        const li = document.createElement('li');
        li.textContent = step;
        stepsList.appendChild(li);
    });
}
