const REFRESCO = 5000; // cada 5 s, igual que el simulador
let aulaSeleccionada = null;
let grafica = null;

const hora = ts => new Date(ts).toLocaleTimeString("es-MX");

function escapar(texto) {
  const d = document.createElement("div");
  d.textContent = String(texto);
  return d.innerHTML;
}

async function cargarUltimas() {
  const datos = await (await fetch("/api/ultimas")).json();
  const cont = document.getElementById("tarjetas");
  const selector = document.getElementById("selector-aula");
  cont.innerHTML = "";

  datos.forEach(d => {
    const div = document.createElement("div");
    div.className = `tarjeta ${escapar(d.estado)}`;
    div.innerHTML = `
      <h3>${escapar(d.aula)}</h3>
      <div class="co2">${d.co2} ppm</div>
      <small>${d.temperatura} °C · ${d.humedad} % hum.</small>
      <small>${escapar(d.estado).toUpperCase()} · ${hora(d.timestamp)}</small>`;
    div.onclick = () => {
      aulaSeleccionada = d.aula;
      selector.value = d.aula;
      cargarHistorial();
    };
    cont.appendChild(div);
  });

  // Llenar el selector solo la primera vez
  if (selector.options.length === 0 && datos.length) {
    datos.forEach(d => selector.add(new Option(d.aula, d.aula)));
    aulaSeleccionada = datos[0].aula;
  }
}

async function cargarHistorial() {
  if (!aulaSeleccionada) return;
  const url = `/api/historial?aula=${encodeURIComponent(aulaSeleccionada)}&minutos=30`;
  const datos = await (await fetch(url)).json();

  const etiquetas = datos.map(d => hora(d.timestamp));
  const co2 = datos.map(d => d.co2);
  const temp = datos.map(d => d.temperatura);

  if (!grafica) {
    grafica = new Chart(document.getElementById("grafica"), {
      type: "line",
      data: {
        labels: etiquetas,
        datasets: [
          { label: "CO₂ (ppm)", data: co2, yAxisID: "y", borderColor: "#e03131" },
          { label: "Temperatura (°C)", data: temp, yAxisID: "y1", borderColor: "#1971c2" },
        ],
      },
      options: {
        animation: false,
        elements: { point: { radius: 0 } },
        scales: {
          y:  { position: "left",  title: { display: true, text: "ppm" } },
          y1: { position: "right", title: { display: true, text: "°C" }, grid: { drawOnChartArea: false } },
        },
      },
    });
  } else {
    grafica.data.labels = etiquetas;
    grafica.data.datasets[0].data = co2;
    grafica.data.datasets[1].data = temp;
    grafica.update();
  }
}

async function cargarRechazados() {
  const r = await (await fetch("/api/rechazados")).json();
  document.getElementById("total-rechazados").textContent = r.total;
  document.getElementById("tabla-rechazados").innerHTML = r.ultimos.map(m => `
    <tr>
      <td>${hora(m.recibido)}</td>
      <td>${escapar(m.errores.join(", "))}</td>
      <td><code>${escapar(m.original)}</code></td>
    </tr>`).join("");
}

async function refrescar() {
  const estado = document.getElementById("actualizado");
  try {
    await cargarUltimas();
    await Promise.all([cargarHistorial(), cargarRechazados()]);
    estado.textContent = "Actualizado: " + new Date().toLocaleTimeString("es-MX");
  } catch (e) {
    estado.textContent = "Error al cargar datos";
    console.error(e);
  }
}

document.getElementById("selector-aula").addEventListener("change", e => {
  aulaSeleccionada = e.target.value;
  cargarHistorial();
});

refrescar();
setInterval(refrescar, REFRESCO);
