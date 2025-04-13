function formatarData(data) {
    if (!data) return "";
    const partes = data.split('-');
    if (partes.length !== 3) return data;
    return `${partes[2]}/${partes[1]}/${partes[0]}`;
}

function criarGraficoClientes(dadosPeriodo1, dadosPeriodo2) {
    const ctx = document.getElementById('graficoClientes').getContext('2d');
    
    // Agrupar dados por cliente
    const dadosPorCliente = {};
    
    // Processar dados do período 1
    dadosPeriodo1.forEach(item => {
        if (!dadosPorCliente[item.cliente]) {
            dadosPorCliente[item.cliente] = { periodo1: 0, periodo2: 0 };
        }
        dadosPorCliente[item.cliente].periodo1 += parseFloat(item.valor);
    });
    
    // Processar dados do período 2
    if (dadosPeriodo2) {
        dadosPeriodo2.forEach(item => {
            if (!dadosPorCliente[item.cliente]) {
                dadosPorCliente[item.cliente] = { periodo1: 0, periodo2: 0 };
            }
            dadosPorCliente[item.cliente].periodo2 += parseFloat(item.valor);
        });
    }
    
    // Ordenar clientes por valor total (soma dos dois períodos) em ordem decrescente
    const clientesOrdenados = Object.keys(dadosPorCliente).sort((a, b) => {
        const totalA = dadosPorCliente[a].periodo1 + dadosPorCliente[a].periodo2;
        const totalB = dadosPorCliente[b].periodo1 + dadosPorCliente[b].periodo2;
        return totalB - totalA;
    });
    
    // Limitar aos 10 maiores clientes
    const topClientes = clientesOrdenados.slice(0, 10);
    
    const data = {
        labels: topClientes,
        datasets: [
            {
                label: `Período 1 (${formatarData(document.getElementById('dataInicial').value)} a ${formatarData(document.getElementById('dataFinal').value)})`,
                data: topClientes.map(cliente => dadosPorCliente[cliente].periodo1),
                backgroundColor: 'rgba(75, 192, 192, 0.7)',
            },
            {
                label: `Período 2 (${formatarData(document.getElementById('dataInicial2').value)} a ${formatarData(document.getElementById('dataFinal2').value)})`,
                data: topClientes.map(cliente => dadosPorCliente[cliente].periodo2),
                backgroundColor: 'rgba(153, 102, 255, 0.7)',
            }
        ]
    };
    
    if (window.graficoClientes) {
        window.graficoClientes.destroy();
    }
    
    window.graficoClientes = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            indexAxis: 'y', // Barras horizontais
            scales: {
                x: {
                    beginAtZero: true,
                    stacked: true
                },
                y: {
                    stacked: true
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Movimentação por Cliente'
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

function criarGraficoOperacoes(dadosPeriodo1, dadosPeriodo2) {
    const ctx = document.getElementById('graficoOperacoes').getContext('2d');
    
    // Agrupar dados por operação
    const dadosPorOperacao = {};
    
    // Processar dados do período 1
    dadosPeriodo1.forEach(item => {
        if (!dadosPorOperacao[item.operacao]) {
            dadosPorOperacao[item.operacao] = { periodo1: 0, periodo2: 0 };
        }
        dadosPorOperacao[item.operacao].periodo1 += parseFloat(item.valor);
    });
    
    // Processar dados do período 2
    if (dadosPeriodo2) {
        dadosPeriodo2.forEach(item => {
            if (!dadosPorOperacao[item.operacao]) {
                dadosPorOperacao[item.operacao] = { periodo1: 0, periodo2: 0 };
            }
            dadosPorOperacao[item.operacao].periodo2 += parseFloat(item.valor);
        });
    }
    
    // Ordenar operações por valor total (soma dos dois períodos) em ordem decrescente
    const operacoesOrdenadas = Object.keys(dadosPorOperacao).sort((a, b) => {
        const totalA = dadosPorOperacao[a].periodo1 + dadosPorOperacao[a].periodo2;
        const totalB = dadosPorOperacao[b].periodo1 + dadosPorOperacao[b].periodo2;
        return totalB - totalA;
    });
    
    const data = {
        labels: operacoesOrdenadas,
        datasets: [
            {
                label: `Período 1 (${formatarData(document.getElementById('dataInicial').value)} a ${formatarData(document.getElementById('dataFinal').value)})`,
                data: operacoesOrdenadas.map(operacao => dadosPorOperacao[operacao].periodo1),
                backgroundColor: 'rgba(75, 192, 192, 0.7)',
            },
            {
                label: `Período 2 (${formatarData(document.getElementById('dataInicial2').value)} a ${formatarData(document.getElementById('dataFinal2').value)})`,
                data: operacoesOrdenadas.map(operacao => dadosPorOperacao[operacao].periodo2),
                backgroundColor: 'rgba(153, 102, 255, 0.7)',
            }
        ]
    };
    
    if (window.graficoOperacoes) {
        window.graficoOperacoes.destroy();
    }
    
    window.graficoOperacoes = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            indexAxis: 'y', // Barras horizontais
            scales: {
                x: {
                    beginAtZero: true,
                    stacked: true
                },
                y: {
                    stacked: true
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Movimentação por Operação'
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
}